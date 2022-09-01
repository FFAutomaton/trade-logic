import os
import threading
from multiprocessing import Process
import time
from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *
from main import trader_calis


def backtest_thread_func(start_date, end_date):
    trader = Trader(start_date)
    islem_sonuc = None
    while trader.bitis_gunu < end_date:
        trader_calis(trader)
        # if trader.dondu_4h:
            # print(f'#################### {trader.bitis_gunu} icin bitti! ###################')
        # trader.sqlite_service.veri_yaz(trader.tahmin, "islem")
        islem_sonuc = trader.tahmin
        if trader.karar.value == 3:
            trader.reset_trader()
        trader.bitis_gunu = trader.bitis_gunu + timedelta(minutes=trader.config.get('arttir_5m'))
    kar = "{0:.0}".format((islem_sonuc.get("usdt") - 1000) / 1000)
    print(f"{start_date} - {end_date}:\t{kar}")


def backtest_calis_thread(start_date, end_date):
    _start = bitis_gunu_truncate_month_precision(start_date)
    # _start = datetime.strptime('2022-08-29 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    threads = []
    while _start < end_date:
        __end = _start + timedelta(days=31)
        __end = bitis_gunu_truncate_month_precision(__end)
        _end = __end if __end < end_date else end_date
        # backtest_thread_func(_start, _end)
        x = threading.Thread(target=backtest_thread_func, args=(_start, _end,))
        threads.append(x)
        x.start()

        _start = _end

    for index, thread in enumerate(threads):
        thread.join()


def backtest_calis_multi(start_date, end_date):
    _start = bitis_gunu_truncate_month_precision(start_date)
    if os.getenv("DEBUG") == "1":
        _start = datetime.strptime('2022-08-29 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    multi = []
    while _start < end_date:
        __end = _start + timedelta(days=31)
        __end = bitis_gunu_truncate_month_precision(__end)
        _end = __end if __end < end_date else end_date
        if os.getenv("DEBUG") == "1":
            backtest_thread_func(_start, _end)
        else:
            x = Process(target=backtest_thread_func, args=(_start, _end,))
            multi.append(x)
            x.start()

        _start = _end

    for index, thread in enumerate(multi):
        thread.join()


if __name__ == '__main__':
    print(f"backtest basladi!!")
    _s = time.time()
    os.environ["PYTHON_ENV"] = "TEST"
    # os.environ["DEBUG"] = "1"

    bitis_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    trader = Trader(bitis_gunu)
    _son = bitis_gunu_truncate_min_precision(trader.config.get("arttir_5m"))

    trader.sqlite_service.islemleri_temizle()
    # trader.config["doldur"] = False
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()

    backtest_calis_multi(bitis_gunu, _son)
    # backtest_calis_thread(bitis_gunu, _son)

    # trader.ciz()
    print(f"it took {(time.time() - _s)/60} minutes")


def optimization():
    st_mult = [0.01]
    rapor = {}
    for mult in st_mult:
        trader.config["tp_datalt_katsayi"] = mult

        sonuc = trader.sonuc_getir()
        rapor[mult] = (sonuc.get("usdt") - 1000) / 1000

    for res in rapor:
        print(f"{res} icin ", "{0:.0%}".format(rapor[res]))
