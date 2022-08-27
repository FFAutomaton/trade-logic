import os
from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *
from main import trader_calis


def backtest_calis(trader):
    trader.sqlite_service.islemleri_temizle()
    _son = bitis_gunu_truncate_min_precision(trader.config.get("arttir_5m"))
    # _son = datetime.strptime('2022-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')

    while trader.bitis_gunu <= _son:
        trader_calis(trader)
        # islem ds eziyor 5 dakilaiktan ds'yi granularity arttir
        if trader.dondu_4h:
            print(f'#################### {trader.bitis_gunu} icin bitti! ###################')
        trader.sqlite_service.veri_yaz(trader.tahmin, "islem")
        if trader.karar.value == 3:
            trader.reset_trader()
        trader.bitis_gunu = trader.bitis_gunu + timedelta(minutes=trader.config.get('arttir_5m'))


if __name__ == '__main__':
    os.environ["PYTHON_ENV"] = "TEST"
    # os.environ["MODE"] = "BACKTEST"
    bitis_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    bitis_gunu = bitis_gunu.replace(tzinfo=timezone.utc)
    trader = Trader(bitis_gunu)
    # trader.config["doldur"] = False
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()

    st_mult = [0.1]
    rapor = {}
    for mult in st_mult:
        trader.config["tp_datalt_katsayi"] = mult
        backtest_calis(trader)

        sonuc = trader.sonuc_getir()
        trader.bitis_gunu = bitis_gunu
        rapor[mult] = (sonuc.get("usdt") - 1000)/1000

    for res in rapor:
        print(f"{res} icin ", "{0:.0%}".format(rapor[res]))

    trader.ciz()
