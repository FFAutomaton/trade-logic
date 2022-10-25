
from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from schemas.enums.karar import Karar
from schemas.enums.pozisyon import Pozisyon


class EmaStrategy:
    def __init__(self, config):
        self.ema_series = None
        self.ema_value = None
        self.bitis_gunu = None
        self.suanki_fiyat = None

        self.ema_bounding_limit = config.get("ema_bounding_limit")

        self.karar = Karar.notr

    def init_strategy(self, series, ema_w):
        self.reset()
        self.ema_hesapla(series, ema_w)

    def reset(self):
        self.karar = Karar.notr

    def karar_hesapla(self, trader):
        if trader.cooldown == 0:
            if self.ema_value * (1+self.ema_bounding_limit) > trader.suanki_fiyat:
                self.karar = Karar.satis
                return
            elif self.ema_value * (1-self.ema_bounding_limit) < trader.suanki_fiyat:
                self.karar = Karar.alis
                return

    def ema_hesapla(self, series, window):
        ema_ = EMAIndicator(series["close"], window)
        self.ema_series = ema_.ema_indicator()
        self.ema_value = self.ema_series[0]
