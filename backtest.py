import os
from trade_logic.utils import *
from trade_logic.trader import Trader, timedelta
from main import trader_calis


def backtest_basla(trader):
    trader.sqlite_service.islemleri_temizle()
    _son = bitis_gunu_truncate(trader.config.get("arttir"))

    while trader.bitis_gunu <= _son:
        islem = trader_calis(trader)
        islem = trader.tahmin
        trader.sqlite_service.veri_yaz(islem, "islem")
        print(f'#################### {trader.bitis_gunu} icin bitti! ###################')
        trader.bitis_gunu = trader.bitis_gunu + timedelta(hours=trader.config.get('arttir'))


if __name__ == '__main__':
    os.environ["PYTHON_ENV"] = "TEST"
    bitis_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    bitis_gunu = bitis_gunu.replace(tzinfo=None)
    trader = Trader(bitis_gunu)

    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()

    st_mult = [0.5, 1, 2]
    rapor = {}
    for mult in st_mult:
        trader.config["supertrend_mult"] = mult

        backtest_basla(trader)
        sonuc = trader.sonuc_getir()
        rapor[mult] = (sonuc.get("usdt") - 1000)/1000

    for res in rapor:
        print(f"{res} icin ", "{0:.0%}".format(rapor[res]))

    trader.ciz()
