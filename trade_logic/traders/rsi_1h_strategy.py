from ta.trend import EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator
from schemas.enums.karar import Karar
from schemas.enums.pozisyon import Pozisyon


class RsiEmaStrategy:
    def __init__(self, config):
        self.bitis_gunu = None
        self.suanki_fiyat = None
        self.rsi_series = None
        self.rsi_value = None
        self.ema_series = None
        self.ema_value = None
        self.rsi_emasi_series = None
        self.rsi_emasi_value = None

        self.rsi_bounding_limit = config.get("rsi_bounding_limit")
        self.ema_bounding_limit = config.get("ema_bounding_limit")
        self.momentum_egim_hesabi_window = config.get("momentum_egim_hesabi_window")
        self.trend_ratio = config.get("trend_ratio")

        self.rsi_smasi_trend = Karar.notr

        self.tavan_yapti = 0
        self.dipten_dondu = False
        self.tavandan_dondu = False
        # self.momentum_trend_rsi = Karar.notr

        self.rsi_kesme = 0
        self.ema_kesme = 0
        self.karar = Karar.notr

    def init_strategy(self, series, rsi_w, sma_w , ema_w):
        self.reset()
        self.rsi_hesapla(series, rsi_w)
        self.ema_hesapla(series, ema_w)
        self.rsi_smasi_trend_hesapla(sma_w)
        self.tavandan_dondu_mu()
        self.tavan_yapti_mi()

    def reset(self):
        self.karar = Karar.notr
        self.rsi_smasi_trend = Karar.notr
        self.tavan_yapti = 0
        self.dipten_dondu = False
        self.tavandan_dondu = False
        # self.momentum_trend_rsi = Karar.notr

    def karar_hesapla(self, trader):
        if trader.pozisyon != Pozisyon.notr:
            if self.tavan_yapti != 0 and self.tavan_yapti != trader.pozisyon.value:
                self.karar = Karar.cikis
                return

        ema_alt_ust = 0
        if self.ema_value_2 * (1 - self.ema_bounding_limit) > trader.suanki_fiyat:
            ema_alt_ust = -1
        elif self.ema_value_2 * (1 + self.ema_bounding_limit) < trader.suanki_fiyat:
            ema_alt_ust = 1

        if trader.cooldown == 0:
            if ema_alt_ust == 1:
                if (self.rsi_smasi_trend == Karar.satis and self.rsi_value > self.rsi_bounding_limit) or \
                        self.dipten_dondu or ema_alt_ust == 1:
                    self.karar = Karar.alis
                    return

            if ema_alt_ust == -1:
                if (self.rsi_smasi_trend == Karar.alis and self.rsi_value < 100 - self.rsi_bounding_limit) or \
                        self.tavandan_dondu or ema_alt_ust == -1:
                    self.karar = Karar.satis
                    return

    def rsi_hesapla(self, series, window):
        rsi_ = RSIIndicator(series["close"], window)
        self.rsi_series = rsi_.rsi()
        self.rsi_value = self.rsi_series[0]

    def ema_hesapla(self, series, window):
        ema_ = EMAIndicator(series["close"], window)
        ema_2 = EMAIndicator(series["close"], window*2)
        self.ema_series = ema_.ema_indicator()
        self.ema_series_2 = ema_2.ema_indicator()
        self.ema_value = self.ema_series[0]
        self.ema_value_2 = self.ema_series_2[0]

    def rsi_smasi_hesapla(self, window):
        rs_ema_ = SMAIndicator(self.rsi_series, window)
        self.rsi_emasi_series = rs_ema_.sma_indicator()
        self.rsi_emasi_value = self.rsi_emasi_series[0]

    def egim_hesapla(self):
        diff = []
        for i in range(0, self.momentum_egim_hesabi_window):
            diff.append(self.rsi_series[i] - self.rsi_series[i+1])
        if diff != 0 or len(diff) != 0:
            return sum(diff) / len(diff)
        return 0

    def rsi_smasi_trend_hesapla(self, window):
        ratio_limit = self.trend_ratio
        self.rsi_smasi_hesapla(window)
        self.rsi_smasi_trend = Karar(0)
        prev_rsi_emasi = self.rsi_emasi_series[1]
        if prev_rsi_emasi < self.rsi_emasi_value:
            diff = self.rsi_emasi_value - prev_rsi_emasi
            if diff == 0:
                return
            ratio = diff / self.rsi_emasi_value
            if ratio > ratio_limit:
                self.rsi_smasi_trend = Karar.alis
        else:
            diff = prev_rsi_emasi - self.rsi_emasi_value
            if diff == 0:
                return
            ratio = diff / prev_rsi_emasi
            if ratio > ratio_limit:
                self.rsi_smasi_trend = Karar.satis

    def tavandan_dondu_mu(self):
        prev_rsi = self.rsi_series[1]
        _rsi = self.rsi_series[0]
        if prev_rsi < self.rsi_bounding_limit:
            if _rsi > self.rsi_bounding_limit:
                self.dipten_dondu = True
        elif prev_rsi > 100 - self.rsi_bounding_limit:
            if _rsi < 100 - self.rsi_bounding_limit:
                self.tavandan_dondu = True

    def tavan_yapti_mi(self):
        _rsi = self.rsi_series[0]
        if _rsi > 100 - self.rsi_bounding_limit:
            self.tavan_yapti = 1
        if _rsi < self.rsi_bounding_limit:
            self.tavan_yapti = -1
