import math
from datetime import timedelta, datetime

from trade_logic.utils import egim_hesapla, heikinashiye_cevir, heikinashi_mum_analiz, \
    islem_doldur
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar
from trade_logic.trader_base import TraderBase
from swing_trader.swing_trader_class import SwingTrader


class Trader(TraderBase):
    def init(self):
        # calisma siralari onemli
        self.mumlari_guncelle()
        self.tarihleri_guncelle()
        self.fiyat_guncelle()
        self.super_trend_strategy.atr_hesapla(self)
        self.tahmin = {"ds_str": datetime.strftime(self.bitis_gunu, '%Y-%m-%d %H:%M:%S'), "open": self.suanki_fiyat}
        if not self.cooldown == 0:
            self.cooldown -= 1

    def karar_calis(self):
        if self.heikinashi_karar == Karar.alis or self.rsi_strategy_1h.karar == Karar.alis:
            # if self.ema_strategy_4h.karar == Karar.alis and self.swing_strategy.karar == Karar.alis:
            if self.swing_strategy.karar == Karar.alis:
                self.karar = Karar.alis
        if self.heikinashi_karar == Karar.satis or self.rsi_strategy_1h.karar == Karar.satis:
            # if self.ema_strategy_4h.karar == Karar.satis and self.swing_strategy.karar == Karar.satis:
            if self.swing_strategy.karar == Karar.satis:
                self.karar = Karar.satis

    def cikis_kontrol(self):
        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_mult_guncelle()
        self.super_trend_strategy.tp_hesapla(self.pozisyon)
        # self.super_trend_tp_daralt()

        self.super_trend_strategy.update_tp(self)
        self.super_trend_cikis_yap()

        self.rsi_cikis_veya_donus()
        # self.swing_cikis()

    def swing_cikis(self):
        if self.pozisyon != Pozisyon.notr:
            if self.swing_strategy.karar != self.karar:
                self.karar = Karar.cikis
                self.super_trend_strategy.reset_super_trend()

    def rsi_cikis_veya_donus(self):
        if self.pozisyon != Pozisyon.notr:
            if self.rsi_strategy_1h.karar == Karar.cikis:
                self.karar = Karar.cikis
                self.super_trend_strategy.reset_super_trend()

    def super_trend_tp_daralt(self):
        kar = self.pozisyon.value * (self.suanki_fiyat - self.islem_fiyati)
        if kar > 0 and kar / self.islem_fiyati > 0.02:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.onceki_tp * (1 + self.pozisyon.value * self.config.get("tp_daralt_katsayi"))

    def super_trend_mult_guncelle(self):
        self.egim = egim_hesapla(self.rsi_strategy_1h.ema_series[0], self.rsi_strategy_1h.ema_series[1])
        if True:
        # if 1.002 < self.egim or self.egim < 0.998:
            self.config["supertrend_mult"] = 2
            self.super_trend_strategy.config["supertrend_mult"] = 2
            self.config["ema_ucustaydi"] = 1

        else:
            self.config["supertrend_mult"] = 0.5
            self.super_trend_strategy.config["supertrend_mult"] = 0.5
            if self.config.get("ema_ucustaydi") == 1:
                self.config["ema_ucustaydi"] = 0
                self.super_trend_strategy.onceki_tp = self.super_trend_strategy.calculate_tp(self.pozisyon)

    def super_trend_cikis_yap(self):
        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

    def swing_karar_hesapla(self):
        self.swing_strategy.bitis_gunu = self.bitis_gunu
        self.swing_strategy.suanki_fiyat = self.suanki_fiyat
        self.swing_strategy.swing_data = SwingTrader(self.series_1h)
        self.swing_strategy.karar_hesapla(self)

    def rsi_ema_1h_karar_hesapla(self):
        self.rsi_strategy_1h.bitis_gunu = self.bitis_gunu
        self.rsi_strategy_1h.suanki_fiyat = self.suanki_fiyat
        series = self.series_1h.sort_values(by='open_ts_int', ascending=True)
        self.rsi_strategy_1h.init_strategy(series, self.config.get("rsi_window"), self.config.get("sma_window"), self.config.get("ema_window"))
        self.rsi_strategy_1h.karar_hesapla(self)

    def ema_4h_karar_hesapla(self):
        self.ema_strategy_4h.bitis_gunu = self.bitis_gunu
        self.ema_strategy_4h.suanki_fiyat = self.suanki_fiyat
        series = self.series_4h.sort_values(by='open_ts_int', ascending=True)
        self.ema_strategy_4h.init_strategy(series, self.config.get("ema_window"))
        self.ema_strategy_4h.karar_hesapla(self)


    def heikinashi_kontrol(self):
        series = heikinashiye_cevir(self.series_1h)
        self.heikinashi_yon_value, self.heikinashi_karar_value = heikinashi_mum_analiz(series)
        self.heikinashi_karar = Karar(self.heikinashi_karar_value or self.heikinashi_yon_value)

    def miktar_hesapla(self):
        miktar = self.dolar / self.suanki_fiyat
        self.islem_miktari = miktar
        self.islem_fiyati = self.suanki_fiyat
        return math.floor(miktar * 100) / 100

    def pozisyon_al(self):
        wallet = self.config.get("wallet")
        islem = islem_doldur(self.tahmin, wallet)

        if self.karar == Karar.alis:
            if self.pozisyon.value in [0, -1]:
                if self.islem_miktari:
                    self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.miktar_hesapla()
                self.islem_fiyati = self.suanki_fiyat
                islem["alis"] = self.islem_fiyati
                self.islem_ts = islem['ds_str']
                self.pozisyon = Pozisyon(1)
                self.super_trend_strategy.reset_super_trend()
                self.onceki_karar = self.karar

        elif self.karar == Karar.satis:
            if self.pozisyon.value in [0, 1]:
                if self.islem_miktari:
                    self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.miktar_hesapla()
                self.islem_fiyati = self.suanki_fiyat
                islem["satis"] = self.islem_fiyati
                self.islem_ts = islem['ds_str']
                self.pozisyon = Pozisyon(-1)
                self.super_trend_strategy.reset_super_trend()
                self.onceki_karar = self.karar

        elif self.karar == Karar.cikis:
            self.dolar = self.dolar - self.pozisyon.value * (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            islem["cikis"] = self.suanki_fiyat
            self.islem_miktari = 0
            self.islem_fiyati = 0
            self.onceki_karar = self.karar
            self.super_trend_strategy.reset_super_trend()

        wallet["ETH"] = self.islem_miktari
        wallet["USDT"] = self.dolar

        self.config["wallet"] = wallet
        islem["eth"] = wallet["ETH"]
        islem["usdt"] = wallet["USDT"]
        self.tahmin = islem
