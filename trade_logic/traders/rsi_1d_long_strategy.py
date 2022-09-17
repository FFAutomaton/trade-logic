from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator


class RsiEmaStrategy:
    def __init__(self):
        self.rsi_1d = None
        self.ema_1d = None
        self.rsi_kesme = 0
        self.ema_kesme = 0
        self.karar = 0
        self.rsi_ema_trend = 0

    def rsi_hesapla(self, series, window):
        rsi_ = RSIIndicator(series["close"], window)
        self.rsi_1d = rsi_.rsi()
        self.rsi_value_1d = self.rsi_1d[0]

    def ema_hesapla(self, series, window):
        ema_ = EMAIndicator(series["close"], window)
        self.ema_1d = ema_.ema_indicator()
        self.ema_value_1d = self.ema_1d[0]

    def rsi_smasi_hesapla(self):
        rs_ema_ = SMAIndicator(self.rsi_1d, 35)
        self.rsi_emasi_1d = rs_ema_.sma_indicator()

    def rsi_ema_trend_hesapla(self):
        self.rsi_smasi_hesapla()
        self.rsi_ema_trend = 0
        rsi_emasi = self.rsi_emasi_1d[0]
        prev_rsi_emasi = self.rsi_emasi_1d[1]
        if prev_rsi_emasi < rsi_emasi:
            diff = rsi_emasi - prev_rsi_emasi
            ratio = diff / rsi_emasi
            if ratio > 0.01:
                self.rsi_ema_trend = 1
        else:
            diff = prev_rsi_emasi - rsi_emasi
            ratio = diff / prev_rsi_emasi
            if ratio > 0.01:
                self.rsi_ema_trend = -1
