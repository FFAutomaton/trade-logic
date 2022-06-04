from datetime import datetime, timedelta
import time
from trade_logic.utils import tahmin_onceden_hesaplanmis_mi, pd, train_kirp_yeniden_adlandir, \
    model_egit_tahmin_et
from schemas.enums.karar import Karar


class ProphetStrategy:
    def __init__(self, conf, sqlite_service):
        self.config = conf
        self.sqlite_service = sqlite_service
        self.agirlik = 1
        self.karar = 0
        self.kesme_durumu = None
        self.onceki_kesme_durumu = None
        self.suanki_fiyat = 0
        self.suanki_ts = None
        self.islem_fiyati = 0
        self.high = 0
        self.low = 0

    def tahmin_hesapla(self, baslangic, bitis):
        start = time.time()
        tahmin = {"ds": datetime.strftime(bitis, '%Y-%m-%d %H:%M:%S')}
        tahmin = self.tahmin_islemlerini_hallet(tahmin, baslangic, bitis)
        self.high = tahmin.get("high")
        self.low = tahmin.get("low")
        print(f'egitim bitti sure: {time.time() - start}')
        return tahmin

    def update_trader_onceki_durumlar(self):
        for attr, value in vars(self).items():
            if "onceki" in attr:
                atr_ = attr.split('_')
                atr_ = "_".join(atr_[1:]) if len(atr_) > 2 else atr_[1]
                setattr(self, attr, getattr(self, atr_))

    def tahmin_islemlerini_hallet(self, tahmin, baslangic, bitis):
        tahminler_cache = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), 'prophet')
        if not tahmin_onceden_hesaplanmis_mi(bitis, self.config, tahminler_cache):
            print(f'prophet calisiyor......{bitis}')
            high_tahmin, _close = self.tahmin_getir(baslangic, bitis, self.config.get("high"))
            low_tahmin, _close = self.tahmin_getir(baslangic, bitis, self.config.get("low"))
            tahmin["high"] = high_tahmin["yhat_upper"].values[0]
            tahmin["low"] = low_tahmin["yhat_lower"].values[0]
            tahmin["open"] = _close
            self.sqlite_service.veri_yaz(tahmin, "tahmin")
        else:
            print('prophet onceden calismis devam ediyorum')
            _row = tahminler_cache[tahminler_cache["ds_str"] == pd.Timestamp(bitis)]
            tahmin["high"] = _row["high"].values[0]
            tahmin["low"] = _row["low"].values[0]
            tahmin["open"] = _row["open"].values[0]

        return tahmin

    def tahmin_getir(self, baslangic, bitis, cesit):
        arttir = self.config.get('arttir')
        coin = self.config.get('coin')
        pencere = self.config.get('pencere')

        df = self.sqlite_service.veri_getir(coin, pencere, "mum", baslangic, bitis)
        train = train_kirp_yeniden_adlandir(df, cesit)

        forecast = model_egit_tahmin_et(train, self.config.get("pencere").upper())
        try:
            _close = train[train['ds'] == bitis - timedelta(hours=arttir)].get("close").values[0]
        except:
            _close = train[train['ds'] == bitis - timedelta(hours=arttir)].get("y").values[0]
        return forecast, _close

    def kesme_durumundan_karar_hesapla(self):
        if (self.onceki_kesme_durumu == 0 and self.kesme_durumu == 1) \
                or (self.onceki_kesme_durumu == -1 and self.kesme_durumu == 0):
            self.karar = Karar.alis
        elif (self.onceki_kesme_durumu == 1 and self.kesme_durumu == 0) \
                or (self.onceki_kesme_durumu == 0 and self.kesme_durumu == -1):
            self.karar = Karar.satis
        else:
            self.karar = Karar.notr

    def kesme_durumu_hesapla(self):
        if self.kesme_durumu in [None, 0]:
            if self.high > self.suanki_fiyat > self.low:
                self.onceki_kesme_durumu = self.kesme_durumu
                self.kesme_durumu = 0
            elif self.suanki_fiyat >= self.high:
                self.onceki_kesme_durumu = self.kesme_durumu
                self.kesme_durumu = 1
            elif self.suanki_fiyat <= self.low:
                self.onceki_kesme_durumu = self.kesme_durumu
                self.kesme_durumu = -1
            else:
                raise Exception("Bu kodun burada olmamasi lazim! trader.kesme_durumu_hesapla fonksiyonu!")
        elif self.kesme_durumu == 1:
            self.onceki_kesme_durumu = 1
            if self.suanki_fiyat < self.high:
                self.kesme_durumu = 0
        elif self.kesme_durumu == -1:
            self.onceki_kesme_durumu = -1
            if self.suanki_fiyat > self.low:
                self.kesme_durumu = 0
