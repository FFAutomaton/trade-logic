import os
import time

from schemas.enums.karar import Karar
from schemas.enums.pozisyon import Pozisyon
from trade_logic.trader import Trader
from trade_logic.utils import bitis_gunu_truncate_min_precision, print_islem_detay
from datetime import datetime, timezone, timedelta
import traceback
from service.file_service import list_files_in_folder, write_already_working
from service.trader_service import close_traders


def app_calis(bitis_gunu, coin, candle_data):
    trader = Trader(bitis_gunu, coin, candle_data)
    trader.yukle(coin)

    trader.init_prod()
    trader.fiyat_guncelle()
    trader.super_trader.kur(trader.series_candle)
    trader.super_trend_daralan_takip.kur(trader)
    trader.karar_calis()

    if trader.stop_oldu_mu and trader.onceki_pozisyon.value == trader.karar.value:
        trader.karar = Karar.cikis
    else:
        trader.stop_oldu_mu = 0
        trader.onceki_pozisyon = Pozisyon(0)
    trader.borsada_islemleri_hallet()
    print_islem_detay(trader)
    trader.kaydet(coin)


def wait_for_next_candle():
    start_ = datetime.utcnow().replace(tzinfo=timezone.utc)
    rounded_ = bitis_gunu_truncate_min_precision(start_, 5) + timedelta(minutes=5)
    diff = rounded_ - start_
    start_ = int(diff.seconds)
    print(f"sleeping {start_} seconds to start")
    time.sleep(start_)


if __name__ == '__main__':
    wait_for_next_candle()
    working_traders = []
    while True:
        time.sleep(1)
        print(f"FFAutomaton --> {'!' * 20} <-- FFAutomaton")
        bitis_gunu = datetime.utcnow()
        bitis_gunu = bitis_gunu_truncate_min_precision(bitis_gunu, 5) - timedelta(minutes=5)
        try:
            c = 3
            while c > 0:
                time.sleep(1)
                try:  # wait for the new files to be written
                    to_open, working_traders, dataframes = list_files_in_folder(bitis_gunu, working_traders)
                    if not dataframes:
                        print(f"FFAutomaton --> df bos geliyor c:{c} !! <-- FFAutomaton")
                        break
                    break
                except Exception as e:
                    traceback.print_exc()
                    print(f"FFAutomaton --> dosylari okuyamiyor c:{c} !! <-- FFAutomaton")
                    c -= 1
            # if to_close:
            #     close_traders(to_close, bitis_gunu)

            if working_traders:
                write_already_working(working_traders)

                for coin in working_traders:
                    app_calis(bitis_gunu, coin, dataframes[coin])

        except Exception as e:
            traceback.print_exc()
        time.sleep(299)