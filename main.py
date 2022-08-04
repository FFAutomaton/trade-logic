import os
from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *


def backtest_calis(trader):
    trader.sqlite_service.islemleri_temizle()
    _son = bitis_gunu_truncate(trader.config.get("arttir"))
    # _son = datetime.strptime('2022-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')

    while trader.bitis_gunu <= _son.replace(tzinfo=None):
        print(f'#################### {trader.bitis_gunu} icin basladi! ###################')
        trader_calis(trader)
        islem = trader.tahmin
        trader.sqlite_service.veri_yaz(islem, "islem")
        trader.bitis_gunu = trader.bitis_gunu + timedelta(hours=trader.config.get('arttir'))


def trader_calis(trader):
    trader.init()
    trader.swing_trader_karar_hesapla()
    trader.prophet_karar_hesapla()

    trader.karar_calis()

    trader.super_trend_cikis_kontrol()
    trader.pozisyon_al()


def app_calis():
    bitis_gunu = bitis_gunu_truncate(4)
    trader = Trader(bitis_gunu)
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()
    trader.init_prod()
    trader_calis(trader)
    if os.getenv("PYTHON_ENV") != "TEST":
        trader.borsada_islemleri_hallet()
    print_islem_detay(trader)
    trader.sqlite_service.trader_durumu_kaydet(trader)


if __name__ == '__main__':
    app_calis()
    # TODO:: 5 dakikalik cron'u da yaz hemen aktive et fiyat kontrolu yapamadigi icin zarar yaziyor su anda,
    #        kara gectikten sonra cikis yapacak sekilde ayar cek backtest yap
    # TODO:: mumlari 5dakikalikta kaydedip 4h'likte aggrege et, buna class yazicaz sonra... kullanilma yerinden basla 5
    #        dakikalik stratejinin uzerine
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
