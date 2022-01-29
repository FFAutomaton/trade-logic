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

    def al_sat_hesapla(self, trader, tahmin, swing_data, _config):
        self.suanki_fiyat = tahmin["Open"]
        tahmin["Alis"] = float("nan")
        tahmin["Satis"] = float("nan")
        self.high = tahmin.get("High")
        self.low = tahmin.get("Low")

        trader.kesme_durumu_hesapla()
        if trader.kesme_durumu in ['uste kesti', 'alttan uste kesti'] :
            trader.karar = 'al'
        elif trader.kesme_durumu in ['alta kesti', 'ustten alta kesti']:
            trader.karar = 'sat'
        else:
            trader.karar = 'notr'

        # if trader.kesme_durumu == 'alttan uste kesti':
        #     _max = max(swing_data.highNodes[len(swing_data.highNodes) - 1].close,
        #                swing_data.highNodes[len(swing_data.highNodes) - 1].open)
        #     if suanki_fiyat > _max:
        #         trader.karar = 'al'
        #         trader.kesme_durumu = None
        #     else:
        #         trader.karar = 'notr'
        # elif trader.kesme_durumu == 'ustten alta kesti':
        #     _min = min(swing_data.lowNodes[len(swing_data.lowNodes) - 1].close,
        #                swing_data.lowNodes[len(swing_data.lowNodes) - 1].open)
        #     if suanki_fiyat < _min:
        #         trader.karar = 'sat'
        #         trader.kesme_durumu = None
        #     else:
        #         trader.karar = 'notr'


        # tahmin["Neden"] = neden
        return self.backtest_cuzdana_isle(tahmin, _config)

    def kesme_durumu_hesapla(self):
        if self.kesme_durumu in [None, 'arada']:
            if self.high > self.suanki_fiyat > self.low:
                self.kesme_durumu = 'arada'
            # TODO:: bir onceki tahmine gore de kontrol etmek lazim belki ustten alta kesti su an arada
            elif self.suanki_fiyat >= self.high:
                self.kesme_durumu = 'uste kesti'
            elif self.suanki_fiyat <= self.low:
                self.kesme_durumu = 'alta kesti'
            else:
                raise Exception("Bu kodun burada olmamasi lazim! trader.kesme_durumu_hesapla fonksiyonu!")
        elif self.kesme_durumu == 'uste kesti':
            if self.suanki_fiyat < self.high:
                self.kesme_durumu = 'ustten alta kesti'
        elif self.kesme_durumu == 'alta kesti':
            if self.suanki_fiyat > self.low:
                self.kesme_durumu = 'alttan uste kesti'
        elif self.kesme_durumu in ['ustten alta kesti', 'alttan uste kesti']:
            self.kesme_durumu = 'arada'
            self.kesme_durumu_hesapla()

    @staticmethod
    def en_dusuk_veya_yuksek_hesapla(node, tip):
        if tip == 'max':
            return max(node.close, node.open)
        else:
            return min(node.close, node.open)

    def backtest_cuzdana_isle(self, tahmin, _config):
        wallet = _config.get("wallet")
        if self.karar == 'al':
            if self.pozisyon == 'short':
                self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["Alis"] = self.islem_fiyati
                self.pozisyon = 'long'
            elif self.pozisyon is None:
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["Alis"] = self.islem_fiyati
                self.pozisyon = 'long'
        elif self.karar == 'sat':
            if self.pozisyon == 'long':
                self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["Satis"] = self.islem_fiyati
                self.pozisyon = 'short'
            elif self.pozisyon is None:
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["Satis"] = self.islem_fiyati
                self.pozisyon = 'short'


        wallet["ETH"] = 0
        wallet["USDT"] = self.dolar

        _config["wallet"] = wallet
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]
        return tahmin, _config
