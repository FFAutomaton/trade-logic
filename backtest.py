import os
from trade_logic.trader import Trader
from main import backtest_calis
from trade_logic.utils import *


if __name__ == '__main__':
    os.environ["PYTHON_ENV"] = "TEST"
    bitis_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    bitis_gunu = bitis_gunu.replace(tzinfo=None)
    trader = Trader(bitis_gunu)
    trader.config["doldur"] = False
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()

    st_mult = [0.5]
    rapor = {}
    for mult in st_mult:
        trader = Trader(bitis_gunu)
        trader.config["supertrend_mult"] = mult

        backtest_calis(trader)
        sonuc = trader.sonuc_getir()
        trader.bitis_gunu = bitis_gunu
        rapor[mult] = (sonuc.get("usdt") - 1000)/1000

    for res in rapor:
        print(f"{res} icin ", "{0:.0%}".format(rapor[res]))

    trader.ciz()
