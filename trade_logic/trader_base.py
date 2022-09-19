import os
import pandas as pd
import copy
from datetime import timedelta, datetime
from trade_logic.traders.super_trend_strategy import SuperTrendStrategy
from trade_logic.traders.rsi_1d_long_strategy import RsiEmaStrategy
from config import *
from service.sqlite_service import SqlLite_Service
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService
from trade_logic.utils import bitis_gunu_truncate_min_precision, bitis_gunu_truncate_hour_precision,\
    bitis_gunu_truncate_day_precision
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
            "doldur": True, "supertrend_mult": 1.5, "rsi_limit": 25
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
        self.onceki_karar = Karar.notr
        self.return_karar = 0
        self.pozisyon = Pozisyon.notr  # 0-baslangic, 1 long, -1 short
        self.dolar = 1000
        self.coin = 0
        self.islem_ts = 0
        self.islem_miktari = 0
        self.islem_fiyati = 0
        self.rsi_value_1d = 0
        self.ema_value_1d = 0
        self.bitis_gunu = bitis_gunu
        self.bitis_gunu_str =  datetime.strftime(bitis_gunu, '%Y-%m-%d %H:%M:%S')
        self.series_1d = None
        self.series_4h = None
        self.bugunun_mumu = None

        self.backfill_baslangic_gunu = bitis_gunu_truncate_min_precision(5) - timedelta(
            days=self.config.get("backfill_window"))
        self.backfill_bitis_gunu = bitis_gunu_truncate_min_precision(5)

        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.super_trend_strategy = SuperTrendStrategy(self.config)
        self.rsi_strategy = RsiEmaStrategy()

        # trader.config["doldur"] = False
        if self.config["doldur"]:
            self.mum_verilerini_guncelle()

    def init(self):
        # calisma siralari onemli
        self.mumlari_guncelle()
        self.tarihleri_guncelle()
        self.fiyat_guncelle()
        self.super_trend_strategy.atr_hesapla(self)
        self.tahmin = {"ds_str": datetime.strftime(self.bitis_gunu, '%Y-%m-%d %H:%M:%S'), "open": self.suanki_fiyat}

    def mumlari_guncelle(self):
        self.series_1d = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere_1d"), "mum",
            self.bitis_gunu - timedelta(days=250), self.bitis_gunu
        )
        self.series_4h = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere_4h"), "mum",
            self.bitis_gunu - timedelta(days=20), self.bitis_gunu
        )
        self.bugunun_mumu = self.bugunun_4hlik_mumlarini_topla()
        self.son_mumu_guncelle()

    def son_mumu_guncelle(self):
        _bas = bitis_gunu_truncate_day_precision(self.bitis_gunu)
        if self.series_1d[self.series_1d["open_ts_str"] == datetime.strftime(_bas, '%Y-%m-%d %H:%M:%S')].empty:
            self.series_1d = pd.concat([self.bugunun_mumu, self.series_1d], ignore_index=True)
        else:
            self.series_1d[0:1] = self.bugunun_mumu

    def bugunun_4hlik_mumlarini_topla(self):
        _bas = bitis_gunu_truncate_day_precision(self.bitis_gunu)
        _son = self.bitis_gunu
        df = copy.deepcopy(self.series_4h[0:6])

        bugun_mum = copy.deepcopy(self.series_4h[0:1])

        bugun_mum.at[0, "open_ts_int"] = int(_bas.timestamp()) * 1000
        bugun_mum.at[0, "open_ts_str"] = datetime.strftime(_bas, '%Y-%m-%d %H:%M:%S')
        bugun_mum.at[0, "open"] = df.iloc[-1]["open"]
        bugun_mum.at[0, "close"] = df.iloc[0]["close"]
        bugun_mum.at[0, 'high'] = df["high"].max()
        bugun_mum.at[0, 'low'] = df["low"].min()
        bugun_mum.at[0, "volume"] = df["volume"].sum()

        return bugun_mum

    def fiyat_guncelle(self):
        data = self.series_4h
        self.suanki_fiyat = data.get("close")[0]
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
            _exit_, yon = self.binance_service.futures_market_exit(self.config.get("coin"))
            self.binance_service.futures_market_islem(self.config.get("coin"), taraf='BUY', miktar=self.miktar_hesapla(), kaldirac=1)
        elif islem["satis"] > 0:
            _exit_, yon = self.binance_service.futures_market_exit(self.config.get("coin"))
            self.binance_service.futures_market_islem(self.config.get("coin"), taraf='SELL', miktar=self.miktar_hesapla(), kaldirac=1)
        elif islem["cikis"] > 0:
            _exit_, yon = self.binance_service.futures_market_exit(self.config.get("coin"))
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
        # self.sqlite_service.mum_datasi_yukle(
        #     "5m", self.binance_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        # )

    def sonuc_getir(self):
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere_4h"), 'islem')
        return sonuclar.iloc[0]

    def ciz(self):
        import matplotlib.pyplot as plt
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
