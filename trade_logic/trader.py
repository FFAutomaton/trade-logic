import math
import os

from config import *
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from trade_logic.traders.prophet_strategy import ProphetStrategy
from trade_logic.traders.swing_strategy import SwingStrategy
from trade_logic.traders.super_trend_strategy import SuperTrendStrategy
from trade_logic.traders.rsi_5m_long_strategy import RSI5mStrategy

from swing_trader.swing_trader_class import SwingTrader

from service.sqlite_service import SqlLite_Service
from signal_prophet.prophet_service import TurkishGekkoProphetService
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService
from service.bam_bam_service import bam_bama_sinyal_gonder
from trade_logic.utils import bitis_gunu_truncate_min_precision, bitis_gunu_truncate_hour_precision, \
    tahmin_doldur, dongu_kontrol_decorator, heikinashiye_cevir, heikinashi_mum_analiz

from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class Trader:
    def __init__(self, bitis_gunu):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}

        self.config = {
            "symbol": "ETH", "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4, "arttir_5m": 5,
            "swing_pencere": "1d", "swing_arttir": 24, "prophet_pencere": "4h", "super_trend_pencere": "4h",
            "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
            "prophet_window": 2400, "swing_window": 200, "backfill_window": 5, "super_trend_window": 200,
            "atr_window": 10, "supertrend_mult": 0.5, "doldur": True, "tp_datalt_katsayi": 0.1
        }
        self.binance_wallet = None
        self.secrets.update(self.config)
        self.wallet = None
        self.tahmin = None
        self.heikinashi_yon, self.heikinashi_karar = 0, 0
        self.suanki_fiyat, self.running_price = 0, 0
        self.karar = Karar.notr
        self.onceki_karar = Karar.notr
        self.pozisyon = Pozisyon.notr  # 0-baslangic, 1 long, -1 short
        self.dolar = 1000
        self.coin = 0
        self.islem_ts = 0
        self.islem_miktari = 0
        self.islem_fiyati = 0

        self.bitis_gunu = bitis_gunu

        self.backfill_baslangic_gunu = bitis_gunu_truncate_min_precision(5) - timedelta(days=self.config.get("backfill_window"))
        self.backfill_bitis_gunu = bitis_gunu_truncate_min_precision(5)

        self.prophet_service = TurkishGekkoProphetService(self.secrets)
        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.swing_strategy = SwingStrategy(self.config)
        self.prophet_strategy = ProphetStrategy(self.config, self.sqlite_service)
        self.super_trend_strategy = SuperTrendStrategy(self.config)
        self.rsi_5m_long_strategy = RSI5mStrategy(self.config)

    def init(self):
        self.tarihleri_guncelle()
        self.fiyat_guncelle()

        # TODO:: bunu supertrend stratejinin icine al hatta complexity saklama seklinde ornek verilebilir object oriented design icin
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("super_trend_pencere"), "mum",
            self.bitis_gunu - timedelta(hours=60), self.bitis_gunu - timedelta(hours=4)
        )
        self.super_trend_strategy.atr_hesapla(series)
        self.tahmin = {"ds_str": datetime.strftime(self.bitis_gunu, '%Y-%m-%d %H:%M:%S')}

    def fiyat_guncelle(self):
        data = self.sqlite_service.veri_getir(
            self.config.get("coin"), "5m", "mum",
            self.bitis_gunu - timedelta(minutes=5), self.bitis_gunu
        )
        self.suanki_fiyat = data.get("open")[0]

        self.swing_strategy.suanki_fiyat = self.suanki_fiyat
        self.prophet_strategy.suanki_fiyat = self.suanki_fiyat
        self.super_trend_strategy.suanki_fiyat = self.suanki_fiyat

    def tarihleri_guncelle(self):
        self._b = bitis_gunu_truncate_hour_precision(self.bitis_gunu, 4)
        self.dondu_4h = True if self._b == self.bitis_gunu else False
        self.swing_baslangic_gunu = self._b - timedelta(days=self.config.get("swing_window"))
        self.prophet_baslangic_gunu = self._b - timedelta(hours=self.config.get("prophet_window"))
        self.super_trend_baslangic_gunu = self._b - timedelta(hours=self.config.get("super_trend_window"))

    def init_prod(self):
        self.binance_wallet = self.binance_service.futures_hesap_bakiyesi()
        self.wallet_isle()
        self.sqlite_service.trader_durumu_geri_yukle(
            self)  # backtestte surekli db'ye gitmemek icin memory'den traderi zaman serisinde tasiyoruz

    def run_5m_strategies(self):
        # eger pozisyon zaten acik degilse isleme girer
        # su anki pozisyon ile celisirse cikmaz test edilmeli
        # sadece rsi stratejisi
        self.rsi_5m_long_karar_hesapla()

    def run_4h_strategies(self):
        if not self.dondu_4h:
            return
        self.swing_trader_karar_hesapla()
        self.prophet_karar_hesapla()

    # @dongu_kontrol_decorator
    def heikinashi_kontrol(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("swing_pencere"), "mum",
            self.swing_baslangic_gunu, self.bitis_gunu
        )
        heikinashi_series = heikinashiye_cevir(series)
        last_row = heikinashi_series.iloc[-1]
        self.heikinashi_yon, self.heikinashi_karar = heikinashi_mum_analiz(last_row)

    def wallet_isle(self):
        for symbol in self.binance_wallet:
            self.config["wallet"][symbol.get("asset")] = symbol.get("balance")
        self.dolar = float(self.config["wallet"].get('USDT'))
        self.coin = float(self.config["wallet"].get(self.config.get('symbol')))

    def pozisyon_al(self):
        wallet = self.config.get("wallet")
        tahmin = tahmin_doldur(self.tahmin, wallet, self.prophet_strategy)

        if self.karar == Karar.alis:
            if self.pozisyon.value in [0, -1]:
                if self.islem_miktari:
                    self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.miktar_hesapla()
                self.islem_fiyati = self.suanki_fiyat
                tahmin["alis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds_str']
                self.pozisyon = Pozisyon(1)
                self.super_trend_strategy.reset_super_trend()
                self.onceki_karar = self.karar

        elif self.karar == Karar.satis:
            if self.pozisyon.value in [0, 1]:
                if self.islem_miktari:
                    self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.miktar_hesapla()
                self.islem_fiyati = self.suanki_fiyat
                tahmin["satis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds_str']
                self.pozisyon = Pozisyon(-1)
                self.super_trend_strategy.reset_super_trend()
                self.onceki_karar = self.karar

        elif self.karar == Karar.cikis:
            self.dolar = self.dolar - self.pozisyon.value * (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            tahmin["cikis"] = self.suanki_fiyat
            self.islem_miktari = 0
            self.islem_fiyati = 0
            self.onceki_karar = self.karar
            self.super_trend_strategy.reset_super_trend()

        wallet["ETH"] = self.islem_miktari
        wallet["USDT"] = self.dolar

        self.config["wallet"] = wallet
        tahmin["eth"] = wallet["ETH"]
        tahmin["usdt"] = wallet["USDT"]
        self.tahmin = tahmin

    def karar_calis(self):
        swing_karar = self.swing_strategy.karar.value if self.swing_strategy.karar else 0
        prophet_karar = self.prophet_strategy.karar.value if self.prophet_strategy.karar else 0

        if swing_karar * prophet_karar > 0:
            if swing_karar > 0:
                self.karar = Karar.alis
            else:
                self.karar = Karar.satis
        elif swing_karar * prophet_karar < 0:
            self.karar = Karar.notr
        elif swing_karar * prophet_karar == 0:
            if swing_karar == 0:
                if prophet_karar == Karar.alis.value:
                    self.karar = Karar.alis
                elif prophet_karar == Karar.satis.value:
                    self.karar = Karar.satis
            elif prophet_karar == 0:
                if swing_karar == Karar.alis.value:
                    self.karar = Karar.alis
                elif swing_karar == Karar.satis.value:
                    self.karar = Karar.satis
        else:
            raise NotImplementedError("karar fonksiyonu beklenmedik durum")

        if self.karar.value * self.heikinashi_karar < 0 or self.karar.value * self.heikinashi_yon < 0:
            self.karar = Karar.notr

        if self.karar.value == 0:
            if self.heikinashi_karar == 1 or self.heikinashi_yon == 1:
                self.karar = Karar.alis
            elif self.heikinashi_karar == -1 or self.heikinashi_yon == -1:
                self.karar = Karar.satis

    def dinamik_atr_carpan(self):
        # TODO:: eger degisirse tp'yi guncellemek gerekir normalde geriye almiyoruz,
        #        0.5'den 1.5'a gecerse geri almak lazim
        if self.super_trend_strategy.atr_value < 55:
            self.super_trend_strategy.config["supertrend_mult"] = 1.5
        else:
            self.super_trend_strategy.config["supertrend_mult"] = 0.5

    # @dongu_kontrol_decorator
    def super_trend_cikis_kontrol(self):
        self.dinamik_atr_carpan()

        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_strategy.tp_hesapla(self.pozisyon)
        self.super_trend_tp_daralt()

        # pozisyon 0 iken bu fonksiyon aslinda calismiyor
        if self.pozisyon.value * self.super_trend_strategy.onceki_tp < self.pozisyon.value * self.super_trend_strategy.tp:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.tp

        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

    def super_trend_tp_daralt(self):
        kar = self.pozisyon.value * (self.suanki_fiyat - self.islem_fiyati)
        if kar > 0 and kar / self.islem_fiyati > 0.03:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.onceki_tp * (1 + self.pozisyon.value * self.config.get("tp_datalt_katsayi"))

    def reset_trader(self):
        self.swing_strategy.karar = Karar.notr
        self.prophet_strategy.karar = Karar.notr
        self.pozisyon = Pozisyon(0)
        self.karar = Karar(0)
        self.onceki_karar = Karar(3)

    # @dongu_kontrol_decorator
    def rsi_5m_long_karar_hesapla(self):
        # 5m'lik stratejinin karar parametresini ekle (RSI < 20 ise isleme gir

        # print("5 dakikalik strateji calisti...." + random.randint(1, 20) * '.')
        pass

    @dongu_kontrol_decorator
    def prophet_karar_hesapla(self):
        self.prophet_strategy.tahmin_hesapla(self.tahmin, self.prophet_baslangic_gunu, self._b - timedelta(hours=4))
        self.prophet_strategy.kesme_durumu_hesapla()
        self.prophet_strategy.update_trader_onceki_durumlar()
        self.tahmin = self.prophet_strategy.tahmin_hesapla(self.tahmin, self.prophet_baslangic_gunu, self._b)
        self.prophet_strategy.kesme_durumu_hesapla()
        self.prophet_strategy.kesme_durumundan_karar_hesapla()

    @dongu_kontrol_decorator
    def swing_trader_karar_hesapla(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("swing_pencere"), "mum",
            self.swing_baslangic_gunu, self.bitis_gunu - timedelta(days=1)
        )
        self.swing_strategy.swing_data = SwingTrader(series)
        return self.swing_strategy.swing_data_trend_hesapla()

    def miktar_hesapla(self):
        # TODO:: burda su anki fiyati baska bir endpoint'den cekip ona gore miktar hesapla
        miktar = self.dolar / self.suanki_fiyat
        self.islem_miktari = miktar
        self.islem_fiyati = self.suanki_fiyat
        return math.floor(miktar * 100) / 100

    def borsada_islemleri_hallet(self):
        islem = self.tahmin
        yon = None
        if islem["alis"] > 0:
            _exit_, yon = self.prophet_service.tg_binance_service. \
                futures_market_exit(self.config.get("coin"))
            self.prophet_service.tg_binance_service.\
                futures_market_islem(self.config.get("coin"), taraf='BUY', miktar=self.miktar_hesapla(), kaldirac=1)
        elif islem["satis"] > 0:
            _exit_, yon = self.prophet_service.tg_binance_service. \
                futures_market_exit(self.config.get("coin"))
            self.prophet_service.tg_binance_service.\
                futures_market_islem(self.config.get("coin"), taraf='SELL', miktar=self.miktar_hesapla(), kaldirac=1)
        elif islem["cikis"] > 0:
            _exit_, yon = self.prophet_service.tg_binance_service.\
                futures_market_exit(self.config.get("coin"))
            self.islem_fiyati = 0
            self.islem_miktari = 0
        if not os.getenv("PYTHON_ENV") == "TEST":
            bam_bama_sinyal_gonder(islem, yon)

    def mum_verilerini_guncelle(self):
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("pencere"), self.prophet_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("swing_pencere"), self.prophet_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            "5m", self.prophet_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )

    def sonuc_getir(self):
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), 'islem')
        return sonuclar.iloc[0]

    def ciz(self):
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), "islem")
        # sonuclar = sonuclar.iloc[-200:]
        # plt.style.use('dark_background')

        sonuclar = sonuclar.set_index(sonuclar['ds_str'])
        plt.plot(sonuclar['high'], label='high', linestyle='--', color='green')
        plt.plot(sonuclar['low'], label='low', linestyle='--', color='red')
        plt.plot(sonuclar['open'], label='open', color='black')
        # cuzdan = sonuclar['USDT'] + (sonuclar['Open'] * sonuclar['ETH'])
        # plt.plot(cuzdan)
        plt.scatter(sonuclar.index, sonuclar['alis'].astype(float), s=500, marker='^', color='#00ff00')
        plt.scatter(sonuclar.index, sonuclar['satis'].astype(float), s=500, marker='v', color='#ff0f02')
        plt.scatter(sonuclar.index, sonuclar['cikis'].astype(float), s=500, marker='.', color='#1a1d33')
        plt.legend(loc='upper right')
        plt.show()
