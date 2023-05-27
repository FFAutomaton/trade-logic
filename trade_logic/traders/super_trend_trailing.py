from signal_atr.atr import ATR


class SuperTrendStrategy:
    def __init__(self, conf):
        self.config = conf
        self.atr_15m_series = None
        self.atr_15m_value = None
        self.atr = None
        self.atr_value = None
        self.atr_15m_m10 = None
        self.atr_15m_m10_value = None
        self.suanki_fiyat = 0
        self.tp = 0
        self.onceki_tp = 0

    def atr_hesapla(self, trader):
        series_15m = trader.series_15m.sort_values(by='open_ts_int', ascending=True)
        self.atr_15m_m10 = ATR(series_15m, 10).average_true_range
        self.atr_15m_m10_value = round(float(self.atr_15m_m10[0]), 2)

    def update_tp(self, trader):
        # pozisyon 0 iken bu fonksiyon aslinda calismiyor
        if trader.pozisyon.value * self.onceki_tp < trader.pozisyon.value * self.tp:
            self.onceki_tp = self.tp

    def calculate_tp(self, pozisyon):
        tp = self.suanki_fiyat + (-1 * pozisyon.value * self.config.get("supertrend_mult") * self.atr_15m_m10_value)
        return round(float(tp), 2)

    def tp_hesapla(self, pozisyon):
        if pozisyon.value != 0:
            self.tp = self.calculate_tp(pozisyon)
        if self.onceki_tp == 0:
            self.onceki_tp = self.tp

    def reset_super_trend(self):
        self.onceki_tp = 0
        self.tp = 0
