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

    def al_sat_hesapla(self, rsi, ema, series, baslangic_gunu):
        suanki_fiyat = series["close"][len(series) - 1]
        self.suanki_fiyat = suanki_fiyat

        emir = {}
        emir["ds"] = datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S')
        emir["high"] = series["high"][len(series) - 1]
        emir["low"] = series["low"][len(series) - 1]
        emir["open"] = series["open"][len(series) - 1]
        emir["alis"] = float("nan")
        emir["satis"] = float("nan")
        emir["cikis"] = float("nan")
        emir["ETH"] = self.config["wallet"]["ETH"]
        emir["USDT"] = self.config["wallet"]["USDT"]

        # Stop Loss
        if self.pozisyon > 0:
            if suanki_fiyat / self.islem_fiyati < 0.99:
                self.karar = 3

        # AL EMRI
        if self.pozisyon < 1:
            if float(rsi[len(rsi) - 1]) <= 10 and suanki_fiyat < ema[len(ema) - 1]:
                self.karar = 1
                self.islem_fiyati = suanki_fiyat

        # TP
        if suanki_fiyat > ema[len(ema) - 1]:
            self.karar = 3

        return self.backtest_cuzdana_isle(emir)

    def backtest_cuzdana_isle(self, tahmin):
        wallet = self.config.get("wallet")
        if self.karar == 1 and self.pozisyon < 1:
            if self.islem_miktari:
                self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            self.islem_miktari = self.dolar / self.suanki_fiyat
            self.islem_fiyati = self.suanki_fiyat
            tahmin["alis"] = self.islem_fiyati
            self.islem_ts = tahmin['ds']
            self.pozisyon = 1

        elif self.karar == 3 and self.pozisyon > 0:
            self.dolar = self.dolar - self.pozisyon * (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            tahmin["cikis"] = self.suanki_fiyat
            self.islem_miktari = 0
            self.islem_fiyati = 0
            self.karar = 0
            self.pozisyon = 0

        wallet["ETH"] = 0
        wallet["USDT"] = self.dolar

        self.config["wallet"] = wallet
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]
        return tahmin, self.config
