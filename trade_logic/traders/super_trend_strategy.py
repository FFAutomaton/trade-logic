from signal_atr.atr import ATR


class SuperTrendStrategy:
    def __init__(self, conf):
        self.config = conf
        self.atr = None
        self.atr_value = None
        self.suanki_fiyat = 0
        self.tp = 0
        self.onceki_tp = 0

    def atr_hesapla(self, series):
        self.atr = ATR(series, self.config.get("atr_window")).average_true_range
        self.atr_value = self.atr[len(self.atr) - 1]

    def tp_hesapla(self, pozisyon):
        if pozisyon.value != 0:
            self.tp = self.suanki_fiyat + (-1 * pozisyon.value * self.config.get("supertrend_mult") * self.atr_value)
        if self.onceki_tp == 0:
            self.onceki_tp = self.tp

    def reset_super_trend(self):
        self.onceki_tp = 0
        self.tp = 0
