from datetime import datetime
from trade_logic.app import App

if __name__ == '__main__':
    app = App()
    if app.config["doldur"]:
        app.mum_verilerini_guncelle()

    app.swing_trader_karar_hesapla()
    app.prophet_karar_hesapla()

    app.karar_calis()
    # TODO:: onceki pozisyona gore hareket etmeyi ayarlar
    # TODO:: bunu trader kaydet ve geri yukle ile yapabiliriz
    # self.backtest_cuzdana_isle(tahmin)
    # TODO:: trailing stop karar durumu ??
    # TODO:: backtest ayarla

    # self.al_sat_hesapla(tahmin)
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
