import math
from datetime import timedelta
from trade_logic.utils import dongu_kontrol_decorator, heikinashiye_cevir, heikinashi_mum_analiz, bugunun_heikinashisi, \
    bitis_gunu_truncate_day_precision, islem_doldur
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar
from trade_logic.trader_base import TraderBase


class Trader(TraderBase):
    def karar_calis(self):
        if self.heikinashi_karar == Karar.alis:
            if self.rsi_ema_1d_karar != Karar.satis:
                if self.rsi_1d_strategy.rsi_trend == 1:
                    self.karar = Karar.alis

        if self.heikinashi_karar == Karar.satis:
            if self.rsi_ema_1d_karar != Karar.alis:
                if self.rsi_1d_strategy.rsi_trend == -1:
                    self.karar = Karar.satis

    # @dongu_kontrol_decorator
    def heikinashi_kontrol(self):
        series_1d = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere_1d"), "mum",
            self.bitis_gunu - timedelta(days=200), self.bitis_gunu
        )
        series_1d = heikinashiye_cevir(series_1d)

        m5_baslanagic = self.bitis_gunu
        m5_baslanagic = m5_baslanagic.replace(hour=0, minute=0,) - timedelta(minutes=5)

        series_5m = self.sqlite_service.veri_getir(
            self.config.get("coin"), "5m", "mum",
            m5_baslanagic, self.bitis_gunu
        )
        last_row = bugunun_heikinashisi(series_1d, series_5m, self.suanki_fiyat)
        self.heikinashi_yon_value, self.heikinashi_karar_value = heikinashi_mum_analiz(last_row)
        self.heikinashi_karar = Karar(self.heikinashi_karar_value or self.heikinashi_yon_value)

    # @dongu_kontrol_decorator
    def cikis_kontrol(self):
        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_strategy.tp_hesapla(self.pozisyon)

        # pozisyon 0 iken bu fonksiyon aslinda calismiyor
        if self.pozisyon.value * self.super_trend_strategy.onceki_tp < self.pozisyon.value * self.super_trend_strategy.tp:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.tp

        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

        if self.pozisyon != Pozisyon.notr and self.pozisyon.value != self.rsi_1d_strategy.rsi_trend:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

    def reset_trader(self):
        self.heikinashi_karar = Karar.notr
        self.pozisyon = Pozisyon(0)
        self.karar = Karar(0)
        self.rsi_ema_1d_karar = Karar(0)
        self.rsi_1d_strategy.karar = Karar(0)
        self.onceki_karar = Karar(3)

    def rsi_ema_1d_karar_hesapla(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere_1d"), "mum",
            self.bitis_gunu - timedelta(days=100), bitis_gunu_truncate_day_precision(self.bitis_gunu) - timedelta(days=1)
        ).sort_values(by='open_ts_int', ascending=True)
        self.rsi_value_1d = self.rsi_1d_strategy.rsi_hesapla(series, self.config.get("rsi_1d_window"))
        self.ema_value_1d = self.rsi_1d_strategy.ema_hesapla(series, self.config.get("ema_1d_window"))
        self.rsi_1d_strategy.rsi_kesme_durumu_hesapla()
        self.rsi_1d_strategy.ema_kesme_durumu_hesapla(self.suanki_fiyat)
        self.rsi_1d_strategy.karar_hesapla(self.pozisyon.value)
        self.rsi_1d_strategy.rsi_trend_hesapla()
        self.rsi_ema_1d_karar = Karar(self.rsi_1d_strategy.karar)

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
