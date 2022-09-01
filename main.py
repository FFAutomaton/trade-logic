import os
from trade_logic.trader import Trader
from trade_logic.utils import bitis_gunu_truncate_min_precision, print_islem_detay
# from datetime import datetime, timezone


def trader_calis(trader):
    trader.init()
    trader.rsi_5m_long_karar_hesapla()
    trader.swing_trader_karar_hesapla()
    trader.prophet_karar_hesapla()

    trader.heikinashi_kontrol()

    trader.karar_calis()
    trader.super_trend_cikis_kontrol()
    trader.pozisyon_al()


def app_calis():
    bitis_gunu = bitis_gunu_truncate_min_precision(5)

    # bitis_gunu = datetime.strptime('2022-08-19 16:00:00', '%Y-%m-%d %H:%M:%S')
    # bitis_gunu = bitis_gunu.replace(tzinfo=timezone.utc)

    trader = Trader(bitis_gunu)
    trader.sqlite_service.trader_eski_verileri_temizle(bitis_gunu)
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()
    trader.init_prod()
    trader_calis(trader)
    if os.getenv("PYTHON_ENV") != "TEST":
        trader.borsada_islemleri_hallet()
    print_islem_detay(trader)
    if trader.karar.value == 3:
        trader.reset_trader()
    trader.sqlite_service.trader_durumu_kaydet(trader)


if __name__ == '__main__':
    app_calis()
    # TODO:: cooldown?
    # TODO:: heikin ashi fine tune edilebilir, bugunku mum hesaplanabilir

    # TODO:: aylik kar ciktisi hesapla backtest icin, bunu multithread'de yapabilirsin
    # TODO:: basarili islem oranini da islemler tablosundan hesapla

    # TODO:: decorator videosu yap
    # TODO:: thread videosu yap
    # TODO:: islem acikken wallet'da usdt gozukuyor, acik islem bilgisini cekip state'i ona gore ezmek lazim
    # TODO:: binance servis exception alirsa uygulamayi bastan baslat
    # TODO:: yeni versiyon cikmadan once calistirabilcegin testler yaz
    #        mesela alis yapiyor mu belli bir case'de, tp dogru takip ediyor mu, cikis yapiyor mu tp de,
    #        binance baglanti hatasi alirsa tekrar program basliyor mu gibi

    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
