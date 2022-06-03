import time
from datetime import datetime


class BackTest:
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

