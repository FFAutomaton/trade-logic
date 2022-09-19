import os
import threading
from multiprocessing import Process
import time
from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *
from main import trader_calis


islemler_rapor = {}


def backtest_thread_func(start_date, end_date):
    st_mult = [1.5]

    for mult in st_mult:
        trader = Trader(start_date)
        trader.config["supertrend_mult"] = mult
        trader.super_trend_strategy.config["supertrend_mult"] = mult

        islem_sonuc = None
        while trader.bitis_gunu < end_date:
            trader_calis(trader)
            if trader.dondu_4h and os.getenv("DEBUG") == "1":
                print(f'#################### {trader.bitis_gunu} icin bitti! ###################')
            trader.sqlite_service.veri_yaz(trader.tahmin, "islem") if os.getenv("DEBUG") == "1" else None
            islem_sonuc = trader.tahmin
            if trader.karar.value == 3:
                trader.reset_trader()
            trader.bitis_gunu = trader.bitis_gunu + timedelta(hours=trader.config.get('arttir'))
        sonuc_yazdir(start_date, end_date, mult, trader, islem_sonuc)


def backtest_calis_thread(start_date, end_date):
    _start = bitis_gunu_truncate_month_precision(start_date)

    threads = []
    while _start < end_date:
        __end = _start + timedelta(days=31)
        __end = bitis_gunu_truncate_month_precision(__end)
        _end = __end if __end < end_date else end_date
        x = threading.Thread(target=backtest_thread_func, args=(_start, _end,))
        threads.append(x)
        x.start()

        _start = _end

    for index, thread in enumerate(threads):
        thread.join()


def backtest_calis_multi(start_date, end_date):
    multi = []
    while start_date < end_date:
        if os.getenv("DEBUG") == "1":
            _end = end_date
            backtest_thread_func(start_date, _end)
        else:
            start_date = bitis_gunu_truncate_month_precision(start_date)
            __end = start_date + timedelta(days=31)
            __end = bitis_gunu_truncate_month_precision(__end)
            _end = __end if __end < end_date else end_date
            x = Process(target=backtest_thread_func, args=(start_date, _end,))
            multi.append(x)
            x.start()

        start_date = _end

    for index, thread in enumerate(multi):
        thread.join()


if __name__ == '__main__':
    print(f"backtest basladi!!")
    _s = time.time()
    os.environ["PYTHON_ENV"] = "TEST"
    os.environ["DEBUG"] = "1"

    bitis_gunu = datetime.strptime('2022-06-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    trader = Trader(bitis_gunu)
    _son = datetime.strptime('2022-07-01 20:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    # _son = datetime.strptime('2022-09-16 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    trader.sqlite_service.islemleri_temizle()
    backtest_calis_multi(bitis_gunu, _son)
    # backtest_calis_thread(bitis_gunu, _son)
    if os.getenv("DEBUG") == "1":
        trader.ciz()
    print(f"it took {(time.time() - _s)/60} minutes")
