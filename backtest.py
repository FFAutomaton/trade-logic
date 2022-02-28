from trade_logic.utils import *
from trade_logic.app import App

if __name__ == '__main__':
    baslangic_gunu = datetime.strptime('2021-03-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    baslangic_gunu = baslangic_gunu.replace(tzinfo=None)
    app = App(baslangic_gunu)

    if app.config["doldur"]:
        app.mum_verilerini_guncelle()

    st_mult = [0.5, 1, 1.5]
    rapor = {}
    for mult in st_mult:
        app.config["supertrend_mult"] = mult

        app.backtest_basla()
        sonuc = app.sonuc_getir()
        rapor[mult] = (sonuc.get("usdt") - 1000)/1000

    for res in rapor:
        print(f"{res} icin ", "{0:.0%}".format(rapor[res]))
    # app.ciz()
