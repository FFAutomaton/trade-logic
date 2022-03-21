from trade_logic.utils import *
from trade_logic.app import App
import pytz


if __name__ == '__main__':
    baslangic_gunu = datetime.strptime('2022-03-19 22:10:00', '%Y-%m-%d %H:%M:%S')
    baslangic_gunu = baslangic_gunu.replace(tzinfo=pytz.utc)
    app = App(baslangic_gunu)

    if app.config["doldur"]:
        app.mum_verilerini_guncelle()

    app.backtest_basla()
    sonuc = app.sonuc_getir()

    app.ciz()
