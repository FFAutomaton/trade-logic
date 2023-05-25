import os
from datetime import timedelta, datetime

from trade_logic.utils import egim_hesapla, \
    islem_doldur, dongu_kontrol_decorator
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar
from trade_logic.trader_base import TraderBase


class Trader(TraderBase):
    def init(self):
        # calisma siralari onemli
        self.tarihleri_guncelle()
        self.mumlari_guncelle()
        self.fiyat_guncelle()
        self.super_trend_strategy.atr_hesapla(self)
        self.tahmin = {"ds_str": datetime.strftime(self.bitis_gunu, '%Y-%m-%d %H:%M:%S'), "open": self.suanki_fiyat}
        if not self.cooldown == 0:
            self.cooldown -= 1

    def karar_calis(self):
        # TODO:: Bazı kolonları one-hot encoding dedikleri teknik ile biraz daha kategorik hale getirebiliriz.
        #        Hatta tahmin ettiğimiz fiyat için bile bunu yapıp modelin tahmin ettim datayı
        #        biraz daha temizleyebiliriz.
        # TODO:: Sezonsallığı ve trendi veriden çıkarıp daha sonrasında tahmin etmeye çalışmalıyız
        # TODO:: Başka veriler ile desteklemeliyiz
        if self.cooldown == 0:
            if self.oracle_sentiment.karar == Karar.alis and self.super_trader.karar == Karar.alis:
                self.karar = Karar.alis

            if self.oracle_sentiment.karar == Karar.satis and self.super_trader.karar == Karar.satis:
                self.karar = Karar.satis

    def cikis_kontrol(self):
        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_update()
        self.super_trend_tp_daralt()
        self.super_trend_cikis_yap()

    def super_trend_tp_daralt(self):
        kar = self.pozisyon.value * (self.suanki_fiyat - self.islem_fiyati)
        katsayi = self.config.get("tp_daralt_katsayi")
        if kar > 0:
            kar_orani = kar / self.islem_fiyati
            if kar_orani > katsayi * self.daralt and self.daralt > 0:

                onceki = self.super_trend_strategy.onceki_tp
                new_tp = self.super_trend_strategy.onceki_tp * (1 + self.pozisyon.value * katsayi * self.daralt)
                self.super_trend_strategy.onceki_tp = round(float(new_tp), 2)
                if os.getenv("PYTHON_ENV") != 'TEST':
                    print(f"$$$$$$ Daralatma - {onceki} --> {self.super_trend_strategy.onceki_tp} -- daralt:{self.daralt}")
                self.daralt += 1
            elif kar_orani > self.config.get("inceltme_limit") and self.daralt < 1:
                onceki = self.super_trend_strategy.onceki_tp
                new_tp = self.islem_fiyati * (1 + self.pozisyon.value * self.config.get("inceltme_oran"))
                self.super_trend_strategy.onceki_tp = round(float(new_tp), 2)
                if os.getenv("PYTHON_ENV") != 'TEST':
                    print(f"$$$$$$ Daralatma - {onceki} --> {self.super_trend_strategy.onceki_tp} -- daralt:{self.daralt}")
                self.daralt += 1

    def super_trend_mult_guncelle(self):
        self.egim = egim_hesapla(self.rsi_ema_strategy.ema_value_big, self.rsi_ema_strategy.ema_value_big_prev)
        # if True:
        if 1 + self.config.get("multiplier_egim_limit") < self.egim or self.egim < 1 - self.config.get("multiplier_egim_limit"):
            self.config["supertrend_mult"] = self.config.get("st_mult_big")
            self.super_trend_strategy.config["supertrend_mult"] = self.config.get("st_mult_big")
            self.ema_ucustaydi = 1

        else:
            self.config["supertrend_mult"] = self.config.get("st_mult_small")
            self.super_trend_strategy.config["supertrend_mult"] = self.config.get("st_mult_small")
            if self.ema_ucustaydi == 1:
                self.ema_ucustaydi = 0
                self.super_trend_strategy.onceki_tp = self.super_trend_strategy.calculate_tp(self.pozisyon)

    def super_trend_update(self):
        # self.super_trend_mult_guncelle()
        self.super_trend_strategy.tp_hesapla(self.pozisyon)
        self.super_trend_strategy.update_tp(self)

    def super_trend_cikis_yap(self):
        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            print(f"super_trend cikis {self.super_trend_strategy.onceki_tp}")
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()
            # zarar = self.pozisyon.value * (self.islem_fiyati - self.suanki_fiyat)
            # if zarar > 0:
            #     self.cooldown = 4

    def rsi_ema_karar_hesapla(self):
        self.rsi_ema_strategy.bitis_gunu = self.bitis_gunu
        series = self.series_15m.sort_values(by='open_ts_int', ascending=True)
        self.rsi_ema_strategy.init_strategy(series, self.config.get("rsi_window"), self.config.get("sma_window"), self.config.get("ema_window_buyuk"), self.config.get("ema_window_kucuk"))
        self.rsi_ema_strategy.karar_hesapla(self)

    @dongu_kontrol_decorator
    def super_trader_kur(self):
        self.super_trader.run(self.series_1h.sort_values(by='open_ts_int', ascending=True))

    @dongu_kontrol_decorator
    def oracle_sentiment_hesapla(self):
        self.oracle_sentiment.run(self.bitis_gunu)

    @dongu_kontrol_decorator
    def lstm_karar_hesapla(self):
        self.lstm_strategy.suanki_fiyat = self.suanki_fiyat
        self.lstm_strategy.init_lstm_strategy(self)
        self.lstm_strategy.karar_hesapla(self)

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
