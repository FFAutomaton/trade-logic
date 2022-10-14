import math
from trade_logic.utils import egim_hesapla, heikinashiye_cevir, heikinashi_mum_analiz, islem_doldur
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar
from trade_logic.trader_base import TraderBase


class Trader(TraderBase):
    def karar_calis(self):
        if self.rsi_strategy.karar == Karar.alis:
            self.karar = Karar.alis
        if self.rsi_strategy.karar == Karar.satis:
            self.karar = Karar.satis

        if self.pozisyon != Pozisyon(0):
            if self.rsi_strategy.karar == Karar.cikis:
                self.karar = Karar.cikis
                self.super_trend_strategy.reset_super_trend()

    def super_trend_tp_daralt(self):
        kar = self.pozisyon.value * (self.suanki_fiyat - self.islem_fiyati)
        if kar > 0 and kar / self.islem_fiyati > 0.02:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.onceki_tp * (1 + self.pozisyon.value * self.config.get("tp_daralt_katsayi"))

    def super_trend_mult_guncelle(self):
        self.egim = egim_hesapla(self.rsi_strategy.ema_series[0], self.rsi_strategy.ema_series[1])
        if True:
        # if 1.0001 < self.egim or self.egim < 0.999:
            self.config["supertrend_mult"] = 1.5
            self.super_trend_strategy.config["supertrend_mult"] = 1.5
            if self.config.get("ema_ucustaydi") == 1:
                self.config["ema_ucustaydi"] = 0
                self.super_trend_strategy.onceki_tp = self.super_trend_strategy.calculate_tp(self.pozisyon)
        else:
            self.config["supertrend_mult"] = 1.5
            self.super_trend_strategy.config["supertrend_mult"] = 1.5
            self.config["ema_ucustaydi"] = 1

    def super_trend_cikis_yap(self):
        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

    # @dongu_kontrol_decorator
    def cikis_kontrol(self):
        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_mult_guncelle()
        self.super_trend_strategy.tp_hesapla(self.pozisyon)
        # self.super_trend_tp_daralt()

        self.super_trend_strategy.update_tp(self)

        self.super_trend_cikis_yap()

    def rsi_ema_karar_hesapla(self):
        self.rsi_strategy.bitis_gunu = self.bitis_gunu
        series = self.series.sort_values(by='open_ts_int', ascending=True)
        self.rsi_strategy.init_strategy(series, self.config.get("rsi_window"), self.config.get("sma_window"), self.config.get("ema_window"))
        self.rsi_strategy.karar_hesapla(self)


    # @dongu_kontrol_decorator
    def heikinashi_kontrol_1d(self):
        series_1d = heikinashiye_cevir(self.series_1d)
        self.heikinashi_yon_value, self.heikinashi_karar_value = heikinashi_mum_analiz(series_1d[0:1])
        self.heikinashi_karar = Karar(self.heikinashi_karar_value or self.heikinashi_yon_value)

    def heikinashi_kontrol_4h(self):
        series_4h = heikinashiye_cevir(self.series)
        self.heikinashi_yon_value, self.heikinashi_karar_value = heikinashi_mum_analiz(series_4h)
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
