import math
import pandas as pd
import copy
from datetime import timedelta, datetime, timezone

from trade_logic.traders.super_trend_strategy import SuperTrendStrategy
from trade_logic.traders.rsi_1h_strategy import RsiEmaStrategy
from config import *
from service.sqlite_service import SqlLite_Service
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService

# from trade_logic.traders.swing_strategy import SwingStrategy
# from trade_logic.traders.mlp_strategy import MlpStrategy
from trade_logic.utils import bitis_gunu_truncate_min_precision, bitis_gunu_truncate_hour_precision, \
    bitis_gunu_truncate_day_precision
# from service.bam_bam_service import bam_bama_sinyal_gonder
from config_users import users
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class TraderBase:
    def __init__(self, bitis_gunu):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}

        self.config = {
            "symbol": "ETH", "coin": 'ETHUSDT',
            "pencere_1d": "1d", "pencere_1h": "1h", "pencere_30m": "30m",
            "arttir": 30, "wallet": {"ETH": 0, "USDT": 1000}, "backfill_window": 10, "super_trend_window": 200,
            "doldur": True,
            "supertrend_mult_big": 3, "supertrend_mult_small": 0.3, "multiplier_egim_limit": 0.0005,
            "ema_window_buyuk": 400, "ema_window_kucuk": 14, "rsi_window": 7, "sma_window": 50,
            "momentum_egim_hesabi_window": 8, "rsi_bounding_limit": 20,
            "ema_bounding_buyuk": 0.001, "ema_bounding_kucuk": 0.015,
            "trend_ratio": 0.005, "tp_daralt_katsayi": 0.02, "inceltme_limit": 0.007, "inceltme_oran": 0.007
        }
        self.ema_ucustaydi = 0
        self.daralt = 0
        self.binance_wallet = None
        self.tp_daralt = 0
        self.egim = 0
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
        self.bitis_gunu = bitis_gunu
        self.bitis_gunu_str = datetime.strftime(bitis_gunu, '%Y-%m-%d %H:%M:%S')
        # self.series_1d = None
        self.series_1h = None
        self.series_30m = None
        self.bugunun_mumu = None

        self.cooldown = 0
        self.backfill_baslangic_gunu = bitis_gunu_truncate_min_precision(datetime.utcnow().replace(tzinfo=timezone.utc), 30) - timedelta(
            days=self.config.get("backfill_window"))
        self.backfill_bitis_gunu = bitis_gunu_truncate_min_precision(datetime.utcnow().replace(tzinfo=timezone.utc), 30)

        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.super_trend_strategy = SuperTrendStrategy(self.config)
        self.rsi_strategy_1h = RsiEmaStrategy(self.config)
        # self.mlp_strategy = MlpStrategy(self.config)
        # self.swing_strategy = SwingStrategy(self.config)

        # trader.config["doldur"] = False
        if self.config["doldur"]:
            self.mum_verilerini_guncelle()

    def mumlari_guncelle(self):
        self.series_1h = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere_1h"), "mum",
            self.bitis_gunu - timedelta(days=200), self.bitis_gunu
        )
        self.series_30m = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere_30m"), "mum",
            self.bitis_gunu - timedelta(days=50), self.bitis_gunu
        )
        # self.bugunun_mumu = self.bugunun_4hlik_mumlarini_topla()
        # self.son_mumu_guncelle()

    def son_mumu_guncelle(self):
        _bas = bitis_gunu_truncate_day_precision(self.bitis_gunu)
        if self.series_1d[self.series_1d["open_ts_str"] == datetime.strftime(_bas, '%Y-%m-%d %H:%M:%S')].empty:
            self.series_1d = pd.concat([self.bugunun_mumu, self.series_1d], ignore_index=True)
        else:
            self.series_1d[0:1] = self.bugunun_mumu

    def bugunun_4hlik_mumlarini_topla(self):
        _bas = bitis_gunu_truncate_day_precision(self.bitis_gunu)
        _son = self.bitis_gunu
        df = copy.deepcopy(self.series_1h[0:6])

        bugun_mum = copy.deepcopy(self.series_1h[0:1])

        bugun_mum.at[0, "open_ts_int"] = int(_bas.timestamp()) * 1000
        bugun_mum.at[0, "open_ts_str"] = datetime.strftime(_bas, '%Y-%m-%d %H:%M:%S')
        bugun_mum.at[0, "open"] = df.iloc[-1]["open"]
        bugun_mum.at[0, "close"] = df.iloc[0]["close"]
        bugun_mum.at[0, 'high'] = df["high"].max()
        bugun_mum.at[0, 'low'] = df["low"].min()
        bugun_mum.at[0, "volume"] = df["volume"].sum()

        return bugun_mum

    def fiyat_guncelle(self):
        data = self.series_30m
        # data = self.series_1h
        self.suanki_fiyat = data.get("close")[0]
        self.super_trend_strategy.suanki_fiyat = self.suanki_fiyat
        self.rsi_strategy_1h.suanki_fiyat = self.suanki_fiyat

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

    def miktar_hesapla(self):
        miktar = self.dolar / self.suanki_fiyat
        self.islem_miktari = miktar
        self.islem_fiyati = self.suanki_fiyat
        return math.floor(miktar * 100) / 100

    def kullanici_bakiye_hesapla(self, _service):
        self.binance_wallet = _service.futures_hesap_bakiyesi()
        self.wallet_isle()

    def kullanicilari_don(self, _taraf=None):
        _exit_, yon, pos, leverage = None, None, None, None
        for user in users:
            user_secrets = users.get(user)
            c = 5
            while c > 0:
                try:
                    _service = TurkishGekkoBinanceService(user_secrets)
                    self.kullanici_bakiye_hesapla(_service)
                    _exit_, yon = _service.futures_market_exit(self.config.get("coin"))
                    if _taraf:
                        pos, leverage = _service.futures_market_islem(self.config.get("coin"), taraf=_taraf,
                                                                      miktar=self.miktar_hesapla(), kaldirac=1)
                    print(f"{user} - ### ---> {_taraf} {yon} {pos} {_exit_}")
                    c = 0
                except Exception as e:
                    print(f"kullanici donerken hata olustu!!!!!!")
                    print("\n")
                    print(str(e))
                    c -= 1
        return yon

    def borsada_islemleri_hallet(self):
        islem = self.tahmin
        yon = None
        if islem["alis"] > 0:
            yon = self.kullanicilari_don('BUY')
        elif islem["satis"] > 0:
            yon = self.kullanicilari_don('SELL')
        elif islem["cikis"] > 0:
            yon = self.kullanicilari_don(None)
            self.reset_trader()
        # if not os.getenv("PYTHON_ENV") == "TEST":
        # bam_bama_sinyal_gonder(islem, yon)

    def reset_trader(self):
        self.heikinashi_karar = Karar.notr
        self.pozisyon = Pozisyon(0)
        self.karar = Karar(0)
        self.rsi_strategy_1h.karar = Karar(0)
        self.onceki_karar = Karar(3)
        self.islem_fiyati = 0
        self.islem_miktari = 0
        self.cooldown = 0
        self.daralt = 0

    def mum_verilerini_guncelle(self):
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("pencere_1h"), self.binance_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("pencere_30m"), self.binance_service, self.backfill_baslangic_gunu, self.backfill_bitis_gunu
        )

    def sonuc_getir(self):
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere_30m"), 'islem')
        return sonuclar.iloc[0]

    def ciz(self):
        import matplotlib.pyplot as plt
        sonuclar = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere_30m"), "islem")
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
