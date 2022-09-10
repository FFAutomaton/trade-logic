from datetime import timedelta

from signal_atr.atr import ATR


class SuperTrendStrategy:
    def __init__(self, conf):
        self.config = conf
        self.atr = None
        self.atr_value = None
        self.suanki_fiyat = 0
        self.tp = 0
        self.onceki_tp = 0

    def atr_hesapla(self, trader):
        series_4h = trader.sqlite_service.veri_getir(
            trader.config.get("coin"), trader.config.get("pencere_4h"), "mum",
            trader.bitis_gunu - timedelta(days=20), trader.bitis_gunu - timedelta(hours=4)
        ).sort_values(by='open_ts_int', ascending=True)
        series_1d = trader.sqlite_service.veri_getir(
            trader.config.get("coin"), trader.config.get("pencere_1d"), "mum",
            trader.bitis_gunu - timedelta(days=100), trader.bitis_gunu - timedelta(days=1)
        ).sort_values(by='open_ts_int', ascending=True)
        self.atr_4h_15 = ATR(series_4h, 15).average_true_range
        # self.atr_4h_50 = ATR(series_4h, 50).average_true_range
        self.atr_1d_15 = ATR(series_1d, 15).average_true_range
        self.atr_1d_50 = ATR(series_1d, 50).average_true_range
        self.atr_value_4h_15 = float(self.atr_4h_15[0])
        # self.atr_value_4h_50 = float(self.atr_4h_50[0])
        self.atr_value_1d_15 = float(self.atr_1d_15[0])
        self.atr_value_1d_50 = float(self.atr_1d_50[0])

    def tp_hesapla(self, pozisyon):
        if pozisyon.value != 0:
            self.tp = self.suanki_fiyat + (-1 * pozisyon.value * self.config.get("supertrend_mult") * self.atr_value_1d_15)
        if self.onceki_tp == 0:
            self.onceki_tp = self.tp
        # print(f'multiplier: {self.config.get("supertrend_mult")}')
        # print(f'tp: {self.tp}')
        # print(f'onceki: {self.onceki_tp}')

    def reset_super_trend(self):
        self.onceki_tp = 0
        self.tp = 0
