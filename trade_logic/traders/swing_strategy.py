from schemas.enums.karar import Karar


class SwingStrategy:
    def __init__(self, conf):
        self.config = conf
        self.swing_data = None
        self.karar = None
        self.agirlik = 1

    def swing_data_trend_hesapla(self):
        swing_data = self.swing_data
        last_high = max(swing_data.highNodes[0].close, swing_data.highNodes[0].open)
        prev_high = max(swing_data.highNodes[1].close, swing_data.highNodes[1].open)

        last_low = min(swing_data.lowNodes[0].close, swing_data.lowNodes[0].open)
        prev_low = min(swing_data.lowNodes[1].close, swing_data.lowNodes[1].open)

        self.karar = Karar.notr

        if last_high >= prev_high and last_low > prev_low:
            self.karar = Karar.alis
            if self.suanki_fiyat < last_low:
                self.karar = Karar.satis
        elif last_high < prev_high and last_low <= prev_low:
            self.karar = Karar.satis
            if self.suanki_fiyat > last_high:
                self.karar = Karar.alis

        return self.karar
