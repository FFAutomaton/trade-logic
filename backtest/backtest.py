import os
from multiprocessing import Process
import time
from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *
from main import trader_calis
from baktest_params import opt_confs, params
from manuel_scripts.sonuc_rapor import sonuc_rapor


def backtest_multi_func(start_date, end_date):
    c = 0
    for opt_conf in opt_confs:
        trader = Trader(start_date)
        for key in opt_conf:
            trader.config[key] = opt_conf.get(key)
        islem_sonuc = None
        while trader.bitis_gunu < end_date:
            trader_calis(trader)
            if trader.dondu_1h and os.getenv("DEBUG") == "1":
                print(f'#LOG# {trader.bitis_gunu} - [{trader.suanki_fiyat}, {trader.super_trend_strategy.onceki_tp}] - {trader.config["supertrend_mult"]}  {trader.egim} ###################')
            trader.sqlite_service.veri_yaz(trader.tahmin, "islem") if os.getenv("DEBUG") == "1" else None
            islem_sonuc = trader.tahmin
            if trader.karar.value == 3:
                trader.reset_trader()
            trader.bitis_gunu = trader.bitis_gunu + timedelta(minutes=trader.config.get('arttir'))
        sonuc_yazdir(start_date, end_date, trader, islem_sonuc, opt_conf, c)
        c += 1


def backtest_calis_multi(start_date, end_date):
    multi = []
    while start_date < end_date:
        if os.getenv("DEBUG") == "1":
            _end = end_date
            backtest_multi_func(start_date, _end)
        else:
            start_date = bitis_gunu_truncate_month_precision(start_date)
            __end = start_date + timedelta(days=31)
            __end = bitis_gunu_truncate_month_precision(__end)
            _end = __end if __end < end_date else end_date
            x = Process(target=backtest_multi_func, args=(start_date, _end,))
            multi.append(x)
            x.start()

        start_date = _end

    for index, thread in enumerate(multi):
        thread.join()


if __name__ == '__main__':
    message = "KERAS LSTM"

    try:
        f1 = open('../manuel_scripts/data/sonuclar.csv', 'w')
        f1.close()
    except:
        pass
    print(f"backtest basladi {message}!!")
    _s = time.time()
    os.environ["PYTHON_ENV"] = "TEST"
    os.environ["DEBUG"] = "1"
    # bitis_gunu = datetime.strptime('2022-02-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    bitis_gunu = datetime.strptime('2023-02-01 00:00:20', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    # _son = datetime.strptime('2022-08-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    _son = datetime.strptime('2023-04-04 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    trader = Trader(bitis_gunu)

    trader.sqlite_service.islemleri_temizle()
    backtest_calis_multi(bitis_gunu, _son)
    sonuc_rapor(params)
    if os.getenv("DEBUG") == "1":
        trader.ciz()
    print(f"it took {(time.time() - _s)/60} minutes")
