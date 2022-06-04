from datetime import datetime
from trade_logic.trader import Trader


def trader_calis(trader):
    trader.init()
    trader.swing_trader_karar_hesapla()
    trader.prophet_karar_hesapla()
    trader.karar_calis()
    trader.super_trend_takip()
    trader.pozisyon_al()


def app_calis(bitis_gunu):
    trader = Trader(bitis_gunu)
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()
    trader.durumu_geri_yukle()  # backtestte surekli db'ye gitmemek icin memory'den traderi zaman serisinde tasiyoruz
    trader_calis(trader)
    trader.borsada_islemleri_hallet()
    trader.durumu_kaydet()



if __name__ == '__main__':
    bitis_gunu = None
    app_calis(bitis_gunu)
    # self.backtest_cuzdana_isle(tahmin)


    # TODO:: backtest ayarla
    # TODO:: bakiye islemmkerini binance'den hallet

    # TODO:: takipte sünen tp/sl islem surelerini kisaltip diger sinyallere yer acmak icin
    # TODO:: swing traderda noise temizlemek icin acilis ve kapanisin ortalamasini alip swing traderi ona gore hesapla

    # self.al_sat_hesapla(tahmin)
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
