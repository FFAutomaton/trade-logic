from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from schemas.enums.karar import Karar
from schemas.enums.pozisyon import Pozisyon


class RsiEmaStrategy:
    def __init__(self):
        self.rsi_series = None
        self.rsi_value = None
        self.rsi_ust_limit = 70
        self.rsi_alt_limit = 30

        self.ema_series = None
        self.ema_value = None

        self.rsi_emasi_series = None
        self.rsi_emasi_value = None
        self.rsi_emasi_karar = Karar(0)

        self.rsi_smasi_trend = Karar(0)
        self.rsi_in_the_zone = False
        self.buy_zone = False
        self.sell_zone = False

        self.rsi_peaked_short = False
        self.rsi_peaked_long = False

        self.rsi_kesme = 0
        self.ema_kesme = 0
        self.karar = Karar(0)

    def init_strategy(self, series, rsi_w, sma_w , ema_w):
        self.reset()
        self.rsi_hesapla(series, rsi_w)
        self.ema_hesapla(series, ema_w)
        self.rsi_smasi_trend_hesapla(sma_w)
        self.rsi_emasi_long_short()
        self.rsi_in_the_zone_calc()
        self.rsi_peaked_calc()
        self.zone_calc()

    def reset(self):
        self.karar = Karar(0)
        self.rsi_emasi_karar = Karar(0)
        self.rsi_smasi_trend = Karar(0)
        self.rsi_peaked_short = False
        self.rsi_peaked_long = False
        self.rsi_in_the_zone = False
        self.buy_zone = False
        self.sell_zone = False

    def karar_hesapla(self, trader):
        if self.rsi_peaked_long:
            self.karar = Karar(-1)
            return
        elif self.rsi_peaked_short:
            self.karar = Karar(1)
            return

        if self.rsi_in_the_zone:
            if self.ema_value > trader.suanki_fiyat:
                if self.rsi_smasi_trend == Karar.satis:
                    if self.rsi_emasi_karar == Karar.satis:
                        # if not self.buy_zone or self.sell_zone:
                        if self.sell_zone:
                            self.karar = Karar(-1)
                            return
            else:
                if self.rsi_smasi_trend == Karar.alis:
                    if self.rsi_emasi_karar == Karar.alis:
                        # if self.buy_zone or not self.sell_zone:
                        if self.buy_zone:
                            self.karar = Karar(1)
                            return

    def rsi_hesapla(self, series, window):
        rsi_ = RSIIndicator(series["close"], window)
        self.rsi_4h = rsi_.rsi()
        self.rsi_value = self.rsi_4h[0]

    def ema_hesapla(self, series, window):
        ema_ = EMAIndicator(series["close"], window)
        self.ema_series = ema_.ema_indicator()
        self.ema_value = self.ema_series[0]

    def rsi_smasi_hesapla(self, window):
        rs_ema_ = SMAIndicator(self.rsi_4h, window)
        self.rsi_emasi_series = rs_ema_.sma_indicator()
        self.rsi_emasi_value = self.rsi_emasi_series[0]

    def rsi_smasi_trend_hesapla(self, window):
        ratio_limit = 0.0005
        self.rsi_smasi_hesapla(window)
        self.rsi_smasi_trend = Karar(0)

        prev_rsi_emasi = self.rsi_emasi_series[1]
        if prev_rsi_emasi < self.rsi_emasi_value:
            diff = self.rsi_emasi_value - prev_rsi_emasi
            if diff == 0:
                return
            ratio = diff / self.rsi_emasi_value
            if ratio > ratio_limit:
                self.rsi_smasi_trend = Karar(1)
        else:
            diff = prev_rsi_emasi - self.rsi_emasi_value
            if diff == 0:
                return
            ratio = diff / prev_rsi_emasi
            if ratio > ratio_limit:
                self.rsi_smasi_trend = Karar(-1)

    def rsi_in_the_zone_calc(self):
        if self.rsi_ust_limit > self.rsi_value > self.rsi_alt_limit:
            self.rsi_in_the_zone = True
        else:
            self.rsi_in_the_zone = False

    def rsi_peaked_calc(self):
        prev_rsi = self.rsi_4h[1]
        _rsi = self.rsi_4h[0]
        if prev_rsi < self.rsi_alt_limit:
            if _rsi > self.rsi_alt_limit:
                self.rsi_peaked_short = True
        elif prev_rsi > self.rsi_ust_limit:
            if _rsi < self.rsi_ust_limit:
                self.rsi_peaked_long = True

    def zone_calc(self):
        if 60 < self.rsi_value < 70:
            self.sell_zone = True
        if 50 < self.rsi_value < 60:
            self.buy_zone = True
        if 30 < self.rsi_value < 40:
            self.buy_zone = True
        if 40 < self.rsi_value < 50:
            self.sell_zone = True

    def rsi_emasi_long_short(self):
        if self.rsi_emasi_value < self.rsi_value:
            self.rsi_emasi_karar = Karar.alis
        else:
            self.rsi_emasi_karar = Karar.satis
