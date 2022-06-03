from datetime import datetime
from trade_logic.app import App

if __name__ == '__main__':
    bitis_gunu = None
    # bitis_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # bitis_gunu = bitis_gunu.replace(tzinfo=None)
    app = App(bitis_gunu)

    if app.config["doldur"]:
        app.mum_verilerini_guncelle()
    app.init()
    app.swing_trader_karar_hesapla()
    app.prophet_karar_hesapla()

    app.karar_calis()
    app.super_trend_takip()
    app.pozisyon_al()
    # TODO:: onceki karar olayini hallet sadece db'den geri yukleyerek olabilir

    # TODO:: bunu trader kaydet ve geri yukle ile yapabiliriz
    # self.backtest_cuzdana_isle(tahmin)

    # TODO:: takipte sünen tp/sl islem surelerini kisaltip diger sinyallere yer acmak icin

    # TODO:: backtest ayarla
    # TODO:: swing traderda noise temizlemek icin acilis ve kapanisin ortalamasini alip swing traderi ona gore hesapla

    # self.al_sat_hesapla(tahmin)
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
