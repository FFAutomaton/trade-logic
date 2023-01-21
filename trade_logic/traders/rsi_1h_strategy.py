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
        self.ema_series_big = None
        self.ema_series_small = None
        self.ema_value_big = None
        self.ema_value_small = None
        self.rsi_emasi_series = None
        self.rsi_emasi_value = None

        self.rsi_bounding_limit = config.get("rsi_bounding_limit")
        self.ema_bounding_buyuk = config.get("ema_bounding_buyuk")
        self.ema_bounding_kucuk = config.get("ema_bounding_kucuk")
        self.momentum_egim_hesabi_window = config.get("momentum_egim_hesabi_window")
        self.trend_ratio = config.get("trend_ratio")

        self.rsi_smasi_trend = Karar.notr

        self.prev_rsi_emasi = None
        self.diff = None

        self.tavan_yapti = 0
        self.dipten_dondu = False
        self.tavandan_dondu = False
        # self.momentum_trend_rsi = Karar.notr

        self.rsi_kesme = 0
        self.ema_kesme = 0
        self.karar = Karar.notr

    def init_strategy(self, series, rsi_w, sma_w , ema_w, ema_k):
        self.reset()
        self.rsi_hesapla(series, rsi_w)
        self.ema_hesapla(series, ema_w, ema_k)
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
        ema_alt_ust_small = 0
        if self.ema_value_big * (1 - self.ema_bounding_buyuk) > trader.suanki_fiyat:
            ema_alt_ust = -1
        elif self.ema_value_big * (1 + self.ema_bounding_buyuk) < trader.suanki_fiyat:
            ema_alt_ust = 1

        if self.ema_value_small * (1 - self.ema_bounding_kucuk) > trader.suanki_fiyat:
            ema_alt_ust_small = -1
        elif self.ema_value_small * (1 + self.ema_bounding_kucuk) < trader.suanki_fiyat:
            ema_alt_ust_small = 1

        if ema_alt_ust * ema_alt_ust_small < 0:
            if trader.pozisyon != Pozisyon.notr:
                self.karar = Karar.cikis
                return
            self.karar = Karar.notr
            return

        if ema_alt_ust == -1:
            if (self.rsi_smasi_trend == Karar.satis and self.rsi_value > self.rsi_bounding_limit) or \
                    self.tavandan_dondu :
                self.karar = Karar.satis
                return
            if ema_alt_ust_small == -1:
                self.karar = Karar.satis
                return

        if ema_alt_ust == 1:
            if (self.rsi_smasi_trend == Karar.alis and self.rsi_value < 100 - self.rsi_bounding_limit) or \
                    self.dipten_dondu :
                self.karar = Karar.alis
                return
            if ema_alt_ust_small == 1:
                self.karar = Karar.alis
                return

    def rsi_hesapla(self, series, window):
        rsi_ = RSIIndicator(series["close"], window)
        self.rsi_series = rsi_.rsi()
        self.rsi_value = round(float(self.rsi_series[0]), 2)

    def ema_hesapla(self, series, window_big, window_small):
        ema_big = EMAIndicator(series["close"], window_big)
        ema_small = EMAIndicator(series["close"], window_small)
        self.ema_series_big = ema_big.ema_indicator()
        self.ema_series_small = ema_small.ema_indicator()
        self.ema_value_big = round(float(self.ema_series_big[0]), 2)
        self.ema_value_big_prev = round(float(self.ema_series_big[1]), 2)
        self.ema_value_small = round(float(self.ema_series_small[0]), 2)

    def rsi_smasi_hesapla(self, window):
        rs_ema_ = SMAIndicator(self.rsi_series, window)
        self.rsi_emasi_series = rs_ema_.sma_indicator()
        self.rsi_emasi_value = round(float(self.rsi_emasi_series[0]), 2)

    def egim_hesapla(self):
        diff = []
        for i in range(0, self.momentum_egim_hesabi_window):
            diff.append(self.rsi_series[i] - self.rsi_series[i+1])
        if diff != 0 or len(diff) != 0:
            return round(float(sum(diff) / len(diff)), 2)
        return 0

    def rsi_smasi_trend_hesapla(self, window):
        self.rsi_smasi_hesapla(window)
        self.rsi_smasi_trend = Karar(0)
        self.prev_rsi_emasi = round(float(self.rsi_emasi_series[1]), 2)
        if self.prev_rsi_emasi < self.rsi_emasi_value:
            self.diff = self.rsi_emasi_value - self.prev_rsi_emasi
            if self.diff == 0:
                return
            ratio = round(float(self.diff / self.rsi_emasi_value), 5)
            if ratio > self.trend_ratio:
                self.rsi_smasi_trend = Karar.alis
        else:
            self.diff = self.prev_rsi_emasi - self.rsi_emasi_value
            if self.diff == 0:
                return
            ratio = round(float(self.diff / self.prev_rsi_emasi), 5)
            if ratio > self.trend_ratio:
                self.rsi_smasi_trend = Karar.satis

    def tavandan_dondu_mu(self):
        prev_rsi = round(float(self.rsi_series[1]), 2)
        _rsi = round(float(self.rsi_series[0]), 2)
        if prev_rsi < self.rsi_bounding_limit:
            if _rsi > self.rsi_bounding_limit:
                self.dipten_dondu = True
        elif prev_rsi > 100 - self.rsi_bounding_limit:
            if _rsi < 100 - self.rsi_bounding_limit:
                self.tavandan_dondu = True

    def tavan_yapti_mi(self):
        _rsi = round(float(self.rsi_series[0]), 2)
        if _rsi > 100 - self.rsi_bounding_limit:
            self.tavan_yapti = 1
        if _rsi < self.rsi_bounding_limit:
            self.tavan_yapti = -1
