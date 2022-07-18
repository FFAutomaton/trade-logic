from datetime import timedelta
from trade_logic.trader import Trader
from trade_logic.utils import *



def backtest_calis(trader):
    trader.sqlite_service.islemleri_temizle()
    _son = bitis_gunu_truncate(trader.config.get("arttir"))
    # _son = datetime.strptime('2022-05-01 00:00:00', '%Y-%m-%d %H:%M:%S')

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
    trader.super_trend_takip()
    trader.pozisyon_al()


def app_calis():
    bitis_gunu = bitis_gunu_truncate(4)
    trader = Trader(bitis_gunu)
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()
    trader.init_prod()
    trader_calis(trader)
    trader.borsada_islemleri_hallet()
    trader.durumu_kaydet()


if __name__ == '__main__':
    app_calis()
    # TODO:: ==> USDT: 239.66497894 ETH: 0 burda eth niye gelmiyor
    # TODO:: ==> super trend verilerini de loga ekle

    # TODO:: manuel olarak islem durdugunda trader onceki durumdan faydalanamaz hale geliyor, veritanindan okudugu
    #        durumu wallet uzerinden kontrol edip ezmek lazim.
    # TODO:: README update et, bolumleri duzenle
    # TODO:: takipte sünen tp/sl islem surelerini kisaltip diger sinyallere yer acmak icin
    # TODO:: swing traderda noise temizlemek icin acilis ve kapanisin ortalamasini alip swing traderi ona gore hesapla
    # TODO:: normal islemleri ayri bir tabloya kaydet
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
