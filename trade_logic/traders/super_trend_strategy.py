from signal_atr.atr import ATR

from schemas.enums.karar import Karar


class SuperTrendStrategy:
    def __init__(self, conf):
        self.config = conf
        self.atr = None
        self.karar = 0
        self.onceki_karar = 0
        self.suanki_fiyat = 0
        self.suanki_ts = None
        self.tp = 0
        self.onceki_tp = 0

    def atr_hesapla(self, series):
        self.atr = ATR(series, self.config.get("atr_window")).average_true_range

    def tp_hesapla(self, pozisyon):
        atr = self.atr[len(self.atr) - 1]
        if pozisyon.value != 0:
            self.tp = self.suanki_fiyat + (-1 * pozisyon.value * self.config.get("supertrend_mult") * atr)
        if self.onceki_tp == 0:
            self.onceki_tp = self.tp

    def reset_super_trend(self):
        self.onceki_tp = 0
        self.tp = 0
