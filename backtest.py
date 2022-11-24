import os
from multiprocessing import Process
import time
from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *
from main import trader_calis


islemler_rapor = {}


def backtest_multi_func(start_date, end_date):
    params = [
        {"key": "supertrend_mult_small", "print": True, "values": [0.3]}
    ]
    multiplier = [(0.3, 3)]
    multiplier_egim_limit = [0.0005]
    ema_window_buyuk = [400]
    ema_window_kucuk = [14]
    rsi_window = [7]
    # sma_window = [7, 35, 50]
    sma_window = [50]
    momentum_egim_hesabi_window = [8]
    rsi_bounding_limit = [20]
    ema_bounding_buyuk = [0.002]
    ema_bounding_kucuk = [0.02]
    trend_ratio = [0.005]
    daralt_katsayi = [0.02]
    c = 0

    for mult in multiplier:
        for mel in multiplier_egim_limit:
            for em_w in ema_window_buyuk:
                for r in rsi_window:
                    for e in sma_window:
                        for mom in momentum_egim_hesabi_window:
                            for rb in rsi_bounding_limit:
                                for eb in ema_bounding_buyuk:
                                    for ek in ema_bounding_kucuk:
                                        for me in ema_window_kucuk:
                                            for tr in trend_ratio:
                                                for dk in daralt_katsayi:
                                                    trader = Trader(start_date)
                                                    trader.config["supertrend_mult_small"] = mult[0]
                                                    trader.config["supertrend_mult_big"] = mult[1]
                                                    trader.config["multiplier_egim_limit"] = mel
                                                    trader.config["tp_daralt_katsayi"] = dk
                                                    trader.config["ema_window_buyuk"] = em_w
                                                    trader.config["ema_window_kucuk"] = me

                                                    trader.config["rsi_window"] = r
                                                    trader.config["sma_window"] = e
                                                    trader.config["momentum_egim_hesabi_window"] = mom
                                                    trader.rsi_strategy_1h.momentum_egim_hesabi_window = mom
                                                    trader.config["rsi_bounding_limit"] = rb
                                                    trader.rsi_strategy_1h.rsi_bounding_limit = rb
                                                    trader.config["ema_bounding_buyuk"] = eb
                                                    trader.config["ema_bounding_kucuk"] = ek
                                                    trader.rsi_strategy_1h.ema_bounding_buyuk = eb
                                                    trader.rsi_strategy_1h.ema_bounding_kucuk = ek
                                                    trader.config["trend_ratio"] = tr
                                                    trader.rsi_strategy_1h.trend_ratio = tr

                                                    islem_sonuc = None
                                                    while trader.bitis_gunu < end_date:
                                                        trader_calis(trader)
                                                        if trader.dondu_4h and os.getenv("DEBUG") == "1":
                                                            print(f'#LOG# {trader.suanki_fiyat} #### {trader.bitis_gunu} {trader.config["supertrend_mult"]}  {trader.egim} ###################')
                                                        trader.sqlite_service.veri_yaz(trader.tahmin, "islem") if os.getenv("DEBUG") == "1" else None
                                                        islem_sonuc = trader.tahmin
                                                        if trader.karar.value == 3:
                                                            trader.reset_trader()
                                                        trader.bitis_gunu = trader.bitis_gunu + timedelta(minutes=trader.config.get('arttir'))
                                                    sonuc_yazdir(start_date, end_date, mult[0], mult[1], mel, em_w, r, e, c, mom, rb, eb, ek, me, tr, dk, trader, islem_sonuc)
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
    message = "kucuk ema"
    print(f"backtest basladi {message}!!")
    _s = time.time()
    os.environ["PYTHON_ENV"] = "TEST"
    os.environ["DEBUG"] = "1"
    # bitis_gunu = datetime.strptime('2021-05-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    bitis_gunu = datetime.strptime('2022-11-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    # _son = datetime.strptime('2022-08-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    _son = datetime.strptime('2022-11-24 16:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)

    trader = Trader(bitis_gunu)

    trader.sqlite_service.islemleri_temizle()
    backtest_calis_multi(bitis_gunu, _son)
    # backtest_calis_thread(bitis_gunu, _son)
    if os.getenv("DEBUG") == "1":
        trader.ciz()
    print(f"it took {(time.time() - _s)/60} minutes")
