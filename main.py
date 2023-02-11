import os
from trade_logic.trader import Trader
from trade_logic.utils import bitis_gunu_truncate_min_precision, print_islem_detay
from datetime import datetime, timezone


def trader_calis(trader):
    trader.init()
    trader.rsi_ema_karar_hesapla()
    trader.mlp_karar_hesapla()
    trader.karar_calis()
    trader.cikis_kontrol()
    trader.pozisyon_al()


def app_calis():
    # bitis_gunu = datetime.strptime('2023-01-21 17:30:04', '%Y-%m-%d %H:%M:%S')
    # bitis_gunu = bitis_gunu.replace(tzinfo=timezone.utc)
    bitis_gunu = datetime.utcnow()
    bitis_gunu = bitis_gunu_truncate_min_precision(bitis_gunu, 15)

    trader = Trader(bitis_gunu)
    trader.sqlite_service.trader_eski_verileri_temizle(bitis_gunu)
    if os.getenv("PYTHON_ENV") != "TEST":
        trader.init_prod()
    trader_calis(trader)
    if os.getenv("PYTHON_ENV") != "TEST":
    # if os.getenv("PYTHON_ENV") == "TEST":
        trader.borsada_islemleri_hallet()
    print_islem_detay(trader)
    if trader.karar.value == 3:
        trader.reset_trader()
    trader.sqlite_service.trader_durumu_kaydet(trader)


if __name__ == '__main__':
    c = 3
    while c > 0:
        try:
            app_calis()
            c = 0
        except Exception as e:
            # TODO:: send_email
            print(str(e))
            print(f"{c} can kaldi tekrar deniyor..." + (40*"#"))
            c -= 1

    # TODO:: fear index ve eth on chain verileri gibi verileri modele ekleyebilir misin?
    # TODO:: ATR ratio diye bir sey hesaplayip doger butun bounding limitleri bu oran ile scale edebilrsin
    # TODO:: kucuk emayi daha kontrol edecek skilde belki window arttirilabilir
    # TODO:: image delete ekle build scripte
    # TODO:: ATR'den tp daralt katsayi manipule edilebilir, atr dusuk iken daraltma katsayisi da kucultulebilir
    # TODO:: hacim cok az ise farkli strateji girilebilir, 2022 7. ay ve 10. ay civarlarinda hacim cok dustu mesela,
    #        veya net volume indicatorune bak o da etkili olabilir
    # TODO:: destek direnc eklenebilir
    # TODO:: piyasanin durumunu atr'den cikararak rsi ayarlari degistirmek en mantikli yaklasim olabilir
    # TODO:: once alttaki maddeyi ekle sonra stateleri daha duzgun tutup strteji yaz bastan 1-rsi ve emasi, 2-ema_trend, normal ema ile cikis

    # TODO:: basarili islem oranini da islemler tablosundan hesapla
    # TODO:: decorator videosu yap
    # TODO:: thread videosu yap
    # TODO:: islem acikken wallet'da usdt gozukuyor, acik islem bilgisini cekip state'i ona gore ezmek lazim

    # TODO:: yeni versiyon cikmadan once calistirabilcegin testler yaz
    #        mesela alis yapiyor mu belli bir case'de, tp dogru takip ediyor mu, cikis yapiyor mu tp de,
    #        binance baglanti hatasi alirsa tekrar program basliyor mu gibi

    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
