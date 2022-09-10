import os
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from trade_logic.traders.super_trend_strategy import SuperTrendStrategy
from trade_logic.traders.rsi_1d_long_strategy import RSI5mStrategy
from config import *
from service.sqlite_service import SqlLite_Service
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService
from trade_logic.utils import bitis_gunu_truncate_min_precision, bitis_gunu_truncate_hour_precision
from service.bam_bam_service import bam_bama_sinyal_gonder

from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class TraderBase:
    def __init__(self, bitis_gunu):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}

        self.config = {
            "symbol": "ETH", "coin": 'ETHUSDT',
            "pencere_1d": "1d", "pencere_4h": "4h", "pencere_5m": "5m",
            "swing_arttir": 24, "arttir": 4,
            "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
            "backfill_window": 5, "super_trend_window": 200,
            "doldur": True, "supertrend_mult": 1.5,
            "rsi_1d_window": 35, "ema_1d_window": 21
        }
        self.binance_wallet = None
        self.tp_daralt = 0
        self.secrets.update(self.config)
        self.wallet = None
        self.tahmin = None
        self.heikinashi_yon_value, self.heikinashi_karar_value = 0, 0
        self.suanki_fiyat, self.running_price = 0, 0
        self.karar = Karar.notr
        self.heikinashi_karar = Karar.notr
        self.rsi_ema_1d_karar = Karar.notr
        self.onceki_karar = Karar.notr
        self.pozisyon = Pozisyon.notr  # 0-baslangic, 1 long, -1 short
        self.dolar = 1000
        self.coin = 0
        self.islem_ts = 0
        self.islem_miktari = 0
        self.islem_fiyati = 0
        self.rsi_value_1d = 0
        self.ema_value_1d = 0
        self.bitis_gunu = bitis_gunu

        self.backfill_baslangic_gunu = bitis_gunu_truncate_min_precision(5) - timedelta(
            days=self.config.get("backfill_window"))
        self.backfill_bitis_gunu = bitis_gunu_truncate_min_precision(5)

        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.super_trend_strategy = SuperTrendStrategy(self.config)
        self.rsi_1d_strategy = RSI5mStrategy()

        # trader.config["doldur"] = False
        if self.config["doldur"]:
            self.mum_verilerini_guncelle()

    def init(self):
        self.tarihleri_guncelle()
        self.fiyat_guncelle()
        self.super_trend_strategy.atr_hesapla(self)
        self.tahmin = {"ds_str": datetime.strftime(self.bitis_gunu, '%Y-%m-%d %H:%M:%S'), "open": self.suanki_fiyat}

    def fiyat_guncelle(self):
        data = self.sqlite_service.veri_getir(
            self.config.get("coin"), "5m", "mum",
            self.bitis_gunu - timedelta(minutes=5), self.bitis_gunu
        )
        self.suanki_fiyat = data.get("open")[0]

        self.super_trend_strategy.suanki_fiyat = self.suanki_fiyat

    def tarihleri_guncelle(self):
        self._b = bitis_gunu_truncate_hour_precision(self.bitis_gunu, 4)
        self.dondu_4h = True if self._b == self.bitis_gunu else False
        self.super_trend_baslangic_gunu = self._b - timedelta(hours=self.config.get("super_trend_window"))

    def init_prod(self):
        self.binance_wallet = self.binance_service.futures_hesap_bakiyesi()
        self.wallet_isle()
        self.sqlite_service.trader_durumu_geri_yukle(
            self)  # backtestte surekli db'ye gitmemek icin memory'den traderi zaman serisinde tasiyoruz

    def wallet_isle(self):
        for symbol in self.binance_wallet:
            self.config["wallet"][symbol.get("asset")] = symbol.get("balance")
        self.dolar = float(self.config["wallet"].get('USDT'))
        self.coin = float(self.config["wallet"].get(self.config.get('symbol')))

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
            self.config.get("pencere_4h"), self.binance_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("pencere_1d"), self.binance_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            "5m", self.binance_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )

    def sonuc_getir(self):
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere_4h"), 'islem')
        return sonuclar.iloc[0]

    def ciz(self):
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere_4h"), "islem")
        # sonuclar = sonuclar.iloc[-200:]
        # plt.style.use('dark_background')
        sonuclar = sonuclar[sonuclar.high != 0]
        sonuclar = sonuclar[sonuclar.low != 0]
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