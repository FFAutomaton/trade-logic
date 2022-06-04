from datetime import datetime
from trade_logic.trader import Trader

if __name__ == '__main__':
    bitis_gunu = None
    # bitis_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # bitis_gunu = bitis_gunu.replace(tzinfo=None)
    trader = Trader(bitis_gunu)

    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()

    # TODO:: onceki karar olayini hallet sadece db'den geri yukleyerek olabilir
    trader.init()

    trader.swing_trader_karar_hesapla()
    trader.prophet_karar_hesapla()

    trader.karar_calis()
    trader.super_trend_takip()

    trader.pozisyon_al()
    trader.durumu_kaydet()

    # TODO:: bunu trader kaydet ve geri yukle ile yapabiliriz
    # self.backtest_cuzdana_isle(tahmin)

    # TODO:: takipte sünen tp/sl islem surelerini kisaltip diger sinyallere yer acmak icin

    # TODO:: backtest ayarla
    # TODO:: swing traderda noise temizlemek icin acilis ve kapanisin ortalamasini alip swing traderi ona gore hesapla

    # self.al_sat_hesapla(tahmin)
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
