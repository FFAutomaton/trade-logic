import pandas_ta as ta
from schemas.enums.karar import Karar


class SuperTrader:
    def __init__(self, config):
        self.config = config
        self.karar = Karar(0)
        self.super_trend, self.super_trend_karar = None, None

    def run(self, series):
        self.super_trend, self.super_trend_karar = self.super_trend_hesapla(series)
        if self.super_trend_karar.iloc[-1] == -1:
            self.karar = Karar(-1)
        elif self.super_trend_karar.iloc[-1] == 1:
            self.karar = Karar(1)

    def super_trend_hesapla(self, df, length=15, multiplier=3):
        super = ta.supertrend(df["high"], df["low"], df["close"], length, multiplier)
        super_karar = super[f"SUPERTd_{length}_{multiplier}.0"]
        return super, super_karar