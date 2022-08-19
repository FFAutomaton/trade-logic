import os
from trade_logic.trader import Trader
from trade_logic.utils import bitis_gunu_truncate_min_precision, print_islem_detay


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
    # TODO:: backtest giris cikis rakamlari tutmuyor, onu bir debug et
    # TODO:: eski trader kayitlarini temizle baslangicta

    # TODO:: range gidip gitmedigini anlamak icin:
    #        gunluk mumlarda heikin ashi bakilabilir cift spike varsa girme gibi
    #        yeni strateji yaz, gunlukde heikin ashi mumu tek spike li ise sadece islem aktif olabilir
    # TODO:: futures ve spot piyasa candle verileri bir kac dolar farkedebiliyor,
    #        candle datasini futures apidan cekmek mantikli mi olur?
    # TODO:: aylik kar ciktisi hesapla backtest icin, bunu multithread'de yapabilirsin
    # TODO:: decorator videosu yap
    # TODO:: cikis kontrolu 4'saatte bir yap decorator ile yapabilir misin?
    #        5 dakikalik surede cikis yapinca swing ve prophet kararlarini resetlemek de ise yarayabilir
    # TODO:: 5 dakikalik islemleri yaz, burda rsi al verirse islemi kitlemeyi dusunebiliriz atiyorum 15*5 dakika gibi
    # TODO:: islem acikken wallet'da usdt gozukuyor, acik islem bilgisini cekip state'i ona gore ezmek lazim
    # TODO:: binance servis exception alirsa uygulamayi bastan baslat
    # TODO:: yeni versiyon cikmadan once calistirabilcegin testler yaz
    #        mesela alis yapiyor mu belli bir case'de, tp dogru takip ediyor mu, cikis yapiyor mu tp de,
    #        binance baglanti hatasi alirsa tekrar program basliyor mu gibi
    # TODO:: main.py gibi 5 dakikalikta calisak ayri bir script olustur
    # TODO:: basarili islem oranini da islemler tablosundan hesapla
    # TODO:: takipte sünen tp/sl islem surelerini kisaltip diger sinyallere yer acmak icin
    #        takip eden stopu default %5 kisalim her turda ???? bunu bi backtest etmek lazim
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
