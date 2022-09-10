from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator


class RSI5mStrategy:
    def __init__(self):
        self.rsi = None
        self.ema = None
        self.rsi_kesme = 0
        self.ema_kesme = 0
        self.karar = 0
        self.rsi_trend = 0

    def rsi_hesapla(self, series, window):
        rsi_ = RSIIndicator(series["close"], window)
        self.rsi = rsi_.rsi()
        self.rsi_value = self.rsi[0]
        return self.rsi_value

    def ema_hesapla(self, series, window):
        ema_ = EMAIndicator(series["close"], window)
        self.ema = ema_.ema_indicator()
        self.ema_value = self.ema[0]
        return self.ema_value

    def rsi_trend_hesapla(self):
        rsi_prev = self.rsi[1]
        rsi_ = self.rsi[0]
        if rsi_prev >= rsi_:
            self.rsi_trend = -1
        else:
            self.rsi_trend = 1
        return self.rsi_trend

    def rsi_kesme_durumu_hesapla(self):
        # if self.rsi_value > 50*1.09:
        if self.rsi_value > 50:
            self.rsi_kesme = 1
        # elif self.rsi_value < 50*0.91:
        elif self.rsi_value <= 50:
            self.rsi_kesme = -1
        else:
            self.rsi_kesme = 0

    def ema_kesme_durumu_hesapla(self, suanki_fiyat):
        if suanki_fiyat > self.ema_value:
            self.ema_kesme = 1
        else:
            self.ema_kesme = -1

    def karar_hesapla(self, pozisyon):
        if self.rsi_kesme > 0 and self.ema_kesme > 0:
            self.karar = 1
        elif self.rsi_kesme < 0 and self.ema_kesme < 0:
            self.karar = -1
        else:
            self.karar = 0
