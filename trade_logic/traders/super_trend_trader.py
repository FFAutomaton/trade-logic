from datetime import datetime, timedelta
import time
from trade_logic.utils import tahmin_onceden_hesaplanmis_mi


class Trader:
    def __init__(self, conf):
        self.config = conf
        self.dolar = 1000
        self.karar = 0
        self.onceki_karar = 0
        self.kesme_durumu = None
        self.onceki_kesme_durumu = None
        self.pozisyon = 0  # 0-baslangic, 1-long, 2-short
        self.suanki_fiyat = 0
        self.suanki_ts = None
        self.islem_fiyati = 0
        self.high = 0
        self.low = 0
        self.trend = 0
        self.tp = 0
        self.onceki_tp = 0
        self.islem_ts = 0
        self.islem_miktari = 0

    def tekil_islem_hesapla(self, sqlite_service, baslangic_gunu):
        start = time.time()
        tahmin = {"ds": datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S')}
        tahmin = self.tahmin_islemlerini_hallet(tahmin, baslangic_gunu)
        print(f'egitim bitti sure: {time.time() - start}')

        # series = sqlite_service.veri_getir(self.config.get("coin"), self.config.get("swing_pencere"), "mum",
        #                                         baslangic_gunu, self.bitis_gunu)
        # self.trader.atr = ATR(series, self.config.get("atr_window")).average_true_range
        self.kesme_durumu_hesapla()
        self.backtest_cuzdana_isle(tahmin)
        islem, self.config = self.al_sat_hesapla(tahmin)
        # return islem

    def update_trader_onceki_durumlar(self):
        for attr, value in vars(self).items():
            if "onceki" in attr:
                atr_ = attr.split('_')
                atr_ = "_".join(atr_[1:]) if len(atr_) > 2 else atr_[1]
                setattr(self, attr, getattr(self, atr_))

    def tahmin_islemlerini_hallet(self, tahmin, baslangic_gunu):
        tahminler_cache = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), 'prophet')
        if not tahmin_onceden_hesaplanmis_mi(baslangic_gunu, self.config, tahminler_cache):
            print(f'prophet calisiyor......{baslangic_gunu}')
            high_tahmin, _close = self.tahmin_getir(baslangic_gunu, self.config.get("high"))
            low_tahmin, _close = self.tahmin_getir(baslangic_gunu, self.config.get("low"))
            tahmin["high"] = high_tahmin["yhat_upper"].values[0]
            tahmin["low"] = low_tahmin["yhat_lower"].values[0]
            tahmin["open"] = _close
            self.sqlite_service.veri_yaz(tahmin, "tahmin")
        else:
            print('prophet onceden calismis devam ediyorum')
            _row = tahminler_cache[tahminler_cache["ds_str"] == pd.Timestamp(baslangic_gunu)]
            tahmin["high"] = _row["high"].values[0]
            tahmin["low"] = _row["low"].values[0]
            tahmin["open"] = _row["open"].values[0]

        return tahmin

    def wallet_isle(self):
        for symbol in self.wallet:
            self.config["wallet"][symbol.get("asset")] = symbol.get("balance")
        self.dolar = float(self.config["wallet"].get('USDT'))
        self.coin = float(self.config["wallet"].get(self.config.get('symbol')))

    def al_sat_hesapla(self, tahmin):
        self.suanki_fiyat = tahmin["open"]
        self.suanki_ts = tahmin["ds"]
        # if tahmin["ds"] == "2022-01-20 00:00:00":
        #     print('here')
        tahmin["alis"] = float("nan")
        tahmin["satis"] = float("nan")
        tahmin["cikis"] = float("nan")
        tahmin["ETH"] = self.config["wallet"]["ETH"]
        tahmin["USDT"] = self.config["wallet"]["USDT"]
        self.high = tahmin.get("high")
        self.low = tahmin.get("low")
        # self.tp_guncelle()

    def kesme_durumundan_karar_hesapla(self):
        if (self.onceki_kesme_durumu == 0 and self.kesme_durumu == 1) \
                or (self.onceki_kesme_durumu == -1 and self.kesme_durumu == 0):
            self.onceki_karar = self.karar
            self.karar = 1
        elif (self.onceki_kesme_durumu == 1 and self.kesme_durumu == 0) \
                or (self.onceki_kesme_durumu == 0 and self.kesme_durumu == -1):
            self.onceki_karar = self.karar
            self.karar = -1
        else:
            self.onceki_karar = self.karar
            self.karar = 0

        # if self.trend * self.karar < 0:
        #     self.onceki_karar = self.karar
        #     self.karar = 0

    def tp_guncelle(self):
        if self.onceki_karar * self.karar < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.reset_trader()
            return

        self.tp_hesapla()
        if self.pozisyon * self.suanki_fiyat < self.pozisyon * self.onceki_tp:
            self.karar = 3  # exit icin 3
            self.reset_trader()
            return

        if self.pozisyon * self.onceki_tp < self.pozisyon * self.tp:
            self.onceki_tp = self.tp

    def tp_hesapla(self):
        atr = self.atr[len(self.atr) - 1]
        _avg = (self.high + self.low) / 2
        if self.pozisyon != 0:
            self.tp = self.suanki_fiyat + (-1 * self.pozisyon * self.config.get("supertrend_mult") * atr)
        if self.onceki_tp == 0:
            self.onceki_tp = self.tp

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

    @staticmethod
    def en_dusuk_veya_yuksek_hesapla(node, tip):
        if tip == 'max':
            return max(node.close, node.open)
        else:
            return min(node.close, node.open)

    def reset_trader(self):
        self.onceki_tp = 0
        self.tp = 0
