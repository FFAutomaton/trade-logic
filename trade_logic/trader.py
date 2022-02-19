class Trader:
    def __init__(self):
        self.dolar = 1000
        self.karar = None
        self.kesme_durumu = None
        self.pozisyon = None
        self.suanki_fiyat = 0
        self.islem_fiyati = 0
        self.high = 0
        self.low = 0
        self.trend = 0

    def swing_data_trend_hesapla(self, swing_data):
        last_high = max(swing_data.highNodes[0].close, swing_data.highNodes[0].open)
        prev_high = max(swing_data.highNodes[1].close, swing_data.highNodes[1].open)

        last_low = min(swing_data.lowNodes[0].close, swing_data.lowNodes[0].open)
        prev_low = min(swing_data.lowNodes[1].close, swing_data.lowNodes[1].open)

        if last_high > prev_high and last_low > prev_low:
            self.trend = 1
        elif last_high < prev_high and last_low < prev_low:
            self.trend = -1

    def al_sat_hesapla(self, trader, tahmin, swing_data, _config):
        self.suanki_fiyat = tahmin["open"]
        tahmin["alis"] = float("nan")
        tahmin["satis"] = float("nan")
        self.high = tahmin.get("high")
        self.low = tahmin.get("low")
        self.swing_data_trend_hesapla(swing_data)
        trader.kesme_durumu_hesapla()
        if (trader.onceki_kesme_durumu == 0 and trader.kesme_durumu == 1) \
                or (trader.onceki_kesme_durumu == -1 and trader.kesme_durumu == 0):
            trader.karar = 'al'
        elif (trader.onceki_kesme_durumu == 1 and trader.kesme_durumu == 0) \
                or (trader.onceki_kesme_durumu == 0 and trader.kesme_durumu == -1):
            trader.karar = 'sat'
        else:
            trader.karar = 'notr'

        return self.backtest_cuzdana_isle(tahmin, _config)

    def kesme_durumu_hesapla(self):
        if self.kesme_durumu in [None, 0]:
            if self.high > self.suanki_fiyat > self.low:
                self.onceki_kesme_durumu = 0
                self.kesme_durumu = 0
            # TODO:: bir onceki tahmine gore de kontrol etmek lazim belki ustten alta kesti su an arada
            elif self.suanki_fiyat >= self.high:
                self.onceki_kesme_durumu = 0
                self.kesme_durumu = 1
            elif self.suanki_fiyat <= self.low:
                self.onceki_kesme_durumu = 0
                self.kesme_durumu = -1
            else:
                raise Exception("Bu kodun burada olmamasi lazim! trader.kesme_durumu_hesapla fonksiyonu!")
        elif self.kesme_durumu == 1:
            if self.suanki_fiyat < self.high:
                self.onceki_kesme_durumu = 1
                self.kesme_durumu = 0
        elif self.kesme_durumu == -1:
            if self.suanki_fiyat > self.low:
                self.onceki_kesme_durumu = -1
                self.kesme_durumu = 0
        # elif self.onceki_kesme_durumu in [1, -1]:
        #     print("##\n\n\n\n\n\n\####\n EXTREME CASE")
        #     self.kesme_durumu = 0
        #     self.kesme_durumu_hesapla()

    @staticmethod
    def en_dusuk_veya_yuksek_hesapla(node, tip):
        if tip == 'max':
            return max(node.close, node.open)
        else:
            return min(node.close, node.open)

    def backtest_cuzdana_isle(self, tahmin, _config):
        wallet = _config.get("wallet")
        tahmin["alis"] = None
        tahmin["satis"] = None
        # if self.karar == 'al' and self.trend > 0:
        if self.karar == 'al':
            if self.pozisyon == 'short':
                self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["alis"] = self.islem_fiyati
                self.pozisyon = 'long'
            elif self.pozisyon is None:
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["alis"] = self.islem_fiyati
                self.pozisyon = 'long'
        # elif self.karar == 'sat' and self.trend < 0:
        elif self.karar == 'sat':
            if self.pozisyon == 'long':
                self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["satis"] = self.islem_fiyati
                self.pozisyon = 'short'
            elif self.pozisyon is None:
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["satis"] = self.islem_fiyati
                self.pozisyon = 'short'


        wallet["ETH"] = 0
        wallet["USDT"] = self.dolar

        _config["wallet"] = wallet
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]
        return tahmin, _config
