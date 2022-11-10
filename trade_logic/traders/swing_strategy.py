
from schemas.enums.karar import Karar
from schemas.enums.pozisyon import Pozisyon


class SwingStrategy:
    def __init__(self, config):
        self.swing_series = None
        self.bitis_gunu = None
        self.suanki_fiyat = None

        self.karar = Karar.notr

    def init_strategy(self, series, ema_w):
        self.reset()

    def reset(self):
        self.karar = Karar.notr

    def karar_hesapla(self, trader):
        swing_data = self.swing_data
        last_high = max(swing_data.highNodes[0].close, swing_data.highNodes[0].open)
        # last_high = max(swing_data.majorHighs[0].close, swing_data.majorHighs[0].open)
        prev_high = max(swing_data.highNodes[1].close, swing_data.highNodes[1].open)
        # prev_high = max(swing_data.majorHighs[1].close, swing_data.majorHighs[1].open)

        last_low = min(swing_data.lowNodes[0].close, swing_data.lowNodes[0].open)
        # last_low = min(swing_data.majorLows[0].close, swing_data.majorLows[0].open)
        prev_low = min(swing_data.lowNodes[1].close, swing_data.lowNodes[1].open)
        # prev_low = min(swing_data.majorLows[1].close, swing_data.majorLows[1].open)

        self.karar = Karar.notr

        # if last_high > prev_high and last_low > prev_low:
        # if trader.ema_strategy_4h.karar == Karar.alis:
        if last_high > prev_high:
            self.karar = Karar.alis
            # if self.suanki_fiyat < last_high:
            #     self.karar = Karar.satis
        # elif last_high < prev_high and last_low < prev_low:
        # elif trader.ema_strategy_4h.karar == Karar.satis:
        if last_low < prev_low:
            self.karar = Karar.satis
            # if self.suanki_fiyat > last_high:
            #     self.karar = Karar.alis
