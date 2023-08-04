from signal_atr.atr import ATR
import os

from schemas.enums.karar import Karar


class SuperTrendDaralanTakip:
    def __init__(self, conf):
        self.config = conf
        self.atr = None
        self.atr_value = None
        self.suanki_fiyat = 0
        self.tp = 0
        self.onceki_tp = 0

    def kur(self, trader):
        trader.super_trend_daralan_takip.atr_hesapla(trader)
        trader.super_trend_daralan_takip.tp_hesapla(trader, trader.pozisyon)
        if trader.pozisyon.value != 0:
            self.super_trend_tp_daralt(trader)
            self.super_trend_cikis_yap(trader)

    def super_trend_cikis_yap(self, trader):
        if trader.pozisyon.value * trader.suanki_fiyat < trader.pozisyon.value * self.onceki_tp:
            print(f"FFAutomaton -->super_trend exit {self.onceki_tp} {trader.config.get('coin')} !c! <-- FFAutomaton")
            trader.karar = Karar.cikis
            self.reset_super_trend()

    def super_trend_tp_daralt(self, trader):
        kar = trader.unRealizedProfit
        katsayi = trader.config.get("tp_daralt_katsayi")
        if kar > 0:
            kar_orani = kar / trader.positionAmt
            if kar_orani > katsayi * trader.daralt and trader.daralt > 0:

                onceki = self.onceki_tp
                new_tp = self.onceki_tp * (1 + trader.pozisyon.value * katsayi * trader.daralt)
                self.onceki_tp = round(float(new_tp), 2)
                print(f"$$$$$$ Daralatma - {onceki} --> {self.onceki_tp} -- daralt:{trader.daralt}")
                trader.daralt += 1
            elif kar_orani > trader.config.get("inceltme_limit") and trader.daralt < 1:
                onceki = self.onceki_tp
                new_tp = trader.entryPrice * (1 + trader.pozisyon.value * trader.config.get("inceltme_oran"))
                if new_tp * trader.pozisyon.value > onceki * trader.pozisyon.value:
                    self.onceki_tp = round(float(new_tp), 2)
                print(f"$$$$$$ Daralatma - {onceki} --> {self.onceki_tp} -- daralt:{trader.daralt}")
                trader.daralt += 1

    def atr_hesapla(self, trader):
        self.atr = ATR(trader.series_candle, 50).average_true_range
        # TODO:: round from tickerSIze
        self.atr_value = round(float(self.atr[len(self.atr) - 1]), 4)

    def tp_hesapla(self, trader, pozisyon):
        if pozisyon.value != 0:
            tp = self.suanki_fiyat + (-1 * pozisyon.value * self.config.get("supertrend_mult") * self.atr_value)
            # TODO:: make those round from tickSize
            self.tp = round(float(tp), 4)
        if self.onceki_tp == 0:
            self.onceki_tp = self.tp
        # pozisyon 0 iken bu fonksiyon aslinda calismiyor
        if trader.pozisyon.value * self.onceki_tp < trader.pozisyon.value * self.tp:
            self.onceki_tp = self.tp

    def reset_super_trend(self):
        self.onceki_tp = 0
        self.tp = 0
