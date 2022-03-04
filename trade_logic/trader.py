from datetime import datetime, timedelta


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

    def swing_data_trend_hesapla(self, swing_data):
        last_high = max(swing_data.highNodes[0].close, swing_data.highNodes[0].open)
        prev_high = max(swing_data.highNodes[1].close, swing_data.highNodes[1].open)

        last_low = min(swing_data.lowNodes[0].close, swing_data.lowNodes[0].open)
        prev_low = min(swing_data.lowNodes[1].close, swing_data.lowNodes[1].open)

        if last_high > prev_high and last_low > prev_low:
            self.trend = 1
            if self.suanki_fiyat < last_high:
                self.trend = -1
        elif last_high < prev_high and last_low < prev_low:
            self.trend = -1
            if self.suanki_fiyat > last_high:
                self.trend = 1

    def al_sat_hesapla(self, tahmin, swing_data):
        self.suanki_fiyat = tahmin["open"]
        self.suanki_ts = tahmin["ds"]
        if tahmin["ds"] == "2022-01-20 00:00:00":
            print('here')
        tahmin["alis"] = float("nan")
        tahmin["satis"] = float("nan")
        tahmin["cikis"] = float("nan")
        tahmin["ETH"] = self.config["wallet"]["ETH"]
        tahmin["USDT"] = self.config["wallet"]["USDT"]
        self.high = tahmin.get("high")
        self.low = tahmin.get("low")
        self.swing_data_trend_hesapla(swing_data)
        self.kesme_durumu_hesapla()

        self.kesme_durumundan_karar_hesapla(swing_data)

        self.tp_guncelle()
        return self.backtest_cuzdana_isle(tahmin)

    def kesme_durumundan_karar_hesapla(self, swing_data):
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

        self.swing_data_trend_hesapla(swing_data)
        if self.trend * self.karar < 0:
            self.onceki_karar = self.karar
            self.karar = 0

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

    def backtest_cuzdana_isle(self, tahmin):
        wallet = self.config.get("wallet")
        if self.karar == 1:
            if self.pozisyon in [0, -1]:
                if self.islem_miktari:
                    self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["alis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds']
                self.pozisyon = 1
                self.reset_trader()
        elif self.karar == -1:
            if self.pozisyon in [0, 1]:
                if self.islem_miktari:
                    self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["satis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds']
                self.pozisyon = -1
                self.reset_trader()

        elif self.karar == 3:
            self.dolar = self.dolar - self.pozisyon * (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            tahmin["cikis"] = self.suanki_fiyat
            self.islem_miktari = 0
            self.islem_fiyati = 0
            self.pozisyon = 0
            self.karar = 0
            self.reset_trader()

        wallet["ETH"] = 0
        wallet["USDT"] = self.dolar

        self.config["wallet"] = wallet
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]
        return tahmin, self.config

    def reset_trader(self):
        self.onceki_tp = 0
        self.tp = 0
