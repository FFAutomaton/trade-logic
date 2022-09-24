import math
from trade_logic.utils import dongu_kontrol_decorator, heikinashiye_cevir, heikinashi_mum_analiz, \
    bitis_gunu_truncate_day_precision, islem_doldur, rsi_limit_kesim_durum_listeden_hesapla
from schemas.enums.pozisyon import Pozisyon
from trade_logic.constants import rsi_bounding_limit, ema_bounding_limit
from schemas.enums.karar import Karar
from trade_logic.trader_base import TraderBase
from trade_logic.constants import tp_daralt_katsayi


class Trader(TraderBase):
    def karar_calis(self):
        if self.rsi_strategy.ema_value_1d < self.suanki_fiyat * (1 - ema_bounding_limit):
            if self.heikinashi_karar == Karar.alis:
                # if self.rsi_strategy.rsi_ema_trend > 0:
                if self.rsi_strategy.rsi_ema_trend > 0 and self.rsi_strategy.rsi_value_1d < 100 - rsi_bounding_limit:
                    self.karar = Karar.alis
                elif rsi_limit_kesim_durum_listeden_hesapla(self.rsi_strategy.rsi_1d[-2:], -1):
                    self.karar = Karar.alis
        elif self.rsi_strategy.ema_value_1d > self.suanki_fiyat * (1 + ema_bounding_limit):
            if self.heikinashi_karar == Karar.satis:
                # if self.rsi_strategy.rsi_ema_trend < 0:
                if self.rsi_strategy.rsi_ema_trend < 0 and self.rsi_strategy.rsi_value_1d > 0 + rsi_bounding_limit:
                    self.karar = Karar.satis
                elif rsi_limit_kesim_durum_listeden_hesapla(self.rsi_strategy.rsi_1d[-2:], 1):
                    self.karar = Karar.satis

    def super_trend_tp_daralt(self):
        kar = self.pozisyon.value * (self.suanki_fiyat - self.islem_fiyati)
        if kar > 0 and kar / self.islem_fiyati > 0.03:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.onceki_tp * (1 + self.pozisyon.value * tp_daralt_katsayi)

    # @dongu_kontrol_decorator
    def cikis_kontrol(self):
        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_strategy.tp_hesapla(self.pozisyon)
        # self.super_trend_tp_daralt()

        # pozisyon 0 iken bu fonksiyon aslinda calismiyor
        if self.pozisyon.value * self.super_trend_strategy.onceki_tp < self.pozisyon.value * self.super_trend_strategy.tp:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.tp

        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

        if self.pozisyon != Pozisyon.notr:
            # if self.heikinashi_karar.value != self.pozisyon.value:
            #     self.karar = Karar.cikis
            #     self.super_trend_strategy.reset_super_trend()
            if self.rsi_strategy.rsi_ema_trend != 0:
                if self.rsi_strategy.rsi_ema_trend != self.pozisyon.value:
                    self.karar = Karar.cikis
                    self.super_trend_strategy.reset_super_trend()
            if self.pozisyon.value > 0:
                if rsi_limit_kesim_durum_listeden_hesapla(self.rsi_strategy.rsi_1d[-2:], self.pozisyon.value):
                    self.karar = Karar.cikis
                    self.super_trend_strategy.reset_super_trend()
                elif self.rsi_strategy.ema_value_1d > self.suanki_fiyat * (1 + ema_bounding_limit):
                    self.karar = Karar.satis

            elif self.pozisyon.value < 0:
                if rsi_limit_kesim_durum_listeden_hesapla(self.rsi_strategy.rsi_1d[-2:], self.pozisyon.value):
                    self.karar = Karar.cikis
                    self.super_trend_strategy.reset_super_trend()
                elif self.rsi_strategy.ema_value_1d < self.suanki_fiyat * (1 - ema_bounding_limit):
                    self.karar = Karar.alis



    def rsi_ema_karar_hesapla(self):
        self.rsi_strategy.bitis_gunu = self.bitis_gunu
        series = self.series_1d[1:].reset_index(drop=True).sort_values(by='open_ts_int', ascending=True)
        self.rsi_strategy.rsi_hesapla(series, 7)
        self.rsi_strategy.ema_hesapla(series, 38)
        self.rsi_strategy.rsi_ema_trend_hesapla()

    # @dongu_kontrol_decorator
    def heikinashi_kontrol(self):
        series_1d = heikinashiye_cevir(self.series_1d)
        self.heikinashi_yon_value, self.heikinashi_karar_value = heikinashi_mum_analiz(series_1d[0:1])
        self.heikinashi_karar = Karar(self.heikinashi_karar_value or self.heikinashi_yon_value)

    def reset_trader(self):
        self.heikinashi_karar = Karar.notr
        self.pozisyon = Pozisyon(0)
        self.karar = Karar(0)
        self.rsi_strategy.karar = Karar(0)
        self.onceki_karar = Karar(3)

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
