from datetime import timedelta

from ta.trend import EMAIndicator


class HolyCrossStrategy:
    def __init__(self):
        self.holy_cross = None
        self.death_cross = None
        self.short_value = None     # 14 days
        self.middle_value = None    # 50 days
        self.long_value = None      # 200 days
        self.wait_holy = False
        self.wait_death = False
        self.leverage = 1
        self.karar = 0

    def calculate_short_value(self, series, window=14):
        self.short_value = EMAIndicator(series["close", window])

    def calculate_middle_value(self, series, window=50):
        self.middle_value = EMAIndicator(series["close", window])

    def calculate_long_value(self, series, window=200):
        self.long_value = EMAIndicator(series["close", window])

    def get_holy(self):
        if self.short_value < self.middle_value:
            self.wait_holy = True
            self.leverage = 2

        elif self.short_value < self.long_value:
            self.wait_holy = True
            self.leverage = 3

        elif self.middle_value < self.long_value:
            self.wait_holy = True
            self.leverage = 4

        elif self.short_value < self.middle_value and self.short_value < self.long_value:
            self.wait_holy = True
            self.leverage = 5

    def get_death(self):
        if self.short_value > self.middle_value:
            self.wait_death = True
            self.leverage = 2

        elif self.short_value > self.long_value:
            self.wait_death = True
            self.leverage = 3

        elif self.middle_value > self.long_value:
            self.wait_death = True
            self.leverage = 4

        elif self.short_value > self.middle_value and self.short_value > self.long_value:
            self.wait_death = True
            self.leverage = 5

    def calculate_crosses(self, series):
        self.calculate_short_value(series)
        self.calculate_middle_value(series)
        self.calculate_long_value(series)
        self.get_holy()
        self.get_death()
        if self.wait_holy and (self.short_value == self.middle_value or
                               self.short_value == self.long_value or
                               self.middle_value == self.long_value):
            self.karar = 1
            self.wait_holy = False
        elif self.wait_death and (self.short_value == self.middle_value or
                                  self.short_value == self.long_value or
                                  self.middle_value == self.long_value):
            self.karar = -1
            self.wait_death = False




