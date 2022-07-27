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

    trader.super_trend_cikis_kontrol()
    trader.pozisyon_al()


def app_calis():
    bitis_gunu = bitis_gunu_truncate(4)
    trader = Trader(bitis_gunu)
    if trader.config["doldur"]:
        trader.mum_verilerini_guncelle()
    trader.init_prod()
    trader_calis(trader)
    trader.borsada_islemleri_hallet()
    trader.sqlite_service.trader_durumu_kaydet(trader)


if __name__ == '__main__':
    app_calis()
    # TODO:: ==> USDT: 239.66497894 ETH: 0 burda eth niye gelmiyor
    # TODO:: 0.5 e degistir super trend multiplier'i
    # TODO:: binance servis exception alirsa uygulamayi bastan baslat
    # TODO:: build.sh scripti yaz deployment restart icin ???
    # TODO:: ATR ile isleme giris filtresi ekle atr>60 ise girsin gibi
    # TODO:: takip eden stopu default %5 kisalim her turda ???? bunu bi backtest etmek lazim
    # TODO:: islem_fiyati ekle trader duruma
    # TODO:: yeni versiyon cikmadan once calistirabilcegin testler yaz
    #        mesela alis yapiyor mu belli bir case'de, tp dogru takip ediyor mu, cikis yapiyor mu tp de,
    #        binance baglanti hatasi alirsa tekrar program basliyor mu gibi

    # TODO:: manuel olarak islem durdugunda trader onceki durumdan faydalanamaz hale geliyor, veritanindan okudugu
    #        durumu wallet uzerinden kontrol edip ezmek lazim.
    # TODO:: README update et, bolumleri duzenle
    # TODO:: takipte sünen tp/sl islem surelerini kisaltip diger sinyallere yer acmak icin
    # TODO:: swing traderda noise temizlemek icin acilis ve kapanisin ortalamasini alip swing traderi ona gore hesapla
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
