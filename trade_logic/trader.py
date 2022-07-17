import json
import math
from config import *
import matplotlib.pyplot as plt
from datetime import timedelta
from trade_logic.traders.prophet_strategy import ProphetStrategy
from trade_logic.traders.swing_strategy import SwingStrategy
from trade_logic.traders.super_trend_strategy import SuperTrendStrategy

from swing_trader.swing_trader_class import SwingTrader

from service.sqlite_service import SqlLite_Service
from signal_prophet.prophet_service import TurkishGekkoProphetService
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService
from service.bam_bam_service import bam_bama_sinyal_gonder

from trade_logic.utils import *
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class Trader:
    def __init__(self, bitis_gunu):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}
        self._kaydedilecek = ["islem_miktari", "islem_ts", "karar", "onceki_karar", "pozisyon", "suanki_fiyat"]
        self.config = {
            "symbol": "ETH", "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4,
            "swing_pencere": "1d", "swing_arttir": 24, "prophet_pencere": "4h", "super_trend_pencere": "4h",
            "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
            "prophet_window": 2400, "swing_window": 200, "backfill_window": 20, "super_trend_window": 200,
            "atr_window": 10, "supertrend_mult": 1.5,
            "cooldown": 4, "doldur": True
        }
        self.secrets.update(self.config)
        self.wallet = None
        self.tahmin = None
        self.suanki_fiyat = 0
        self.running_price = 0
        self.suanki_ts = None
        self.karar = Karar.notr
        self.onceki_karar = Karar.notr
        self.pozisyon = Pozisyon.notr  # 0-baslangic, 1 long, -1 short
        self.dolar = 1000
        self.islem_ts = 0
        self.islem_miktari = 0
        self.islem_fiyati = 0

        self.bitis_gunu = bitis_gunu

        self.backfill_baslangic_gunu = self.bitis_gunu - timedelta(days=self.config.get("backfill_window"))
        self.swing_baslangic_gunu = self.bitis_gunu - timedelta(days=self.config.get("swing_window"))
        self.prophet_baslangic_gunu = self.bitis_gunu - timedelta(hours=self.config.get("prophet_window"))
        self.super_trend_baslangic_gunu = self.bitis_gunu - timedelta(hours=self.config.get("super_trend_window"))

        self.prophet_service = TurkishGekkoProphetService(self.secrets)
        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.swing_strategy = SwingStrategy(self.config)
        self.prophet_strategy = ProphetStrategy(self.config, self.sqlite_service)
        self.super_trend_strategy = SuperTrendStrategy(self.config)

    def init(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("prophet_pencere"), "mum",
            self.bitis_gunu - timedelta(days=1), self.bitis_gunu
        )
        self.suanki_fiyat = series.iloc[0]["close"]
        self.swing_strategy.suanki_fiyat = self.suanki_fiyat
        self.prophet_strategy.suanki_fiyat = self.suanki_fiyat
        self.super_trend_strategy.suanki_fiyat = self.suanki_fiyat

    def init_prod(self):
        self.wallet = self.binance_service.futures_hesap_bakiyesi()
        self.wallet_isle()
        self.durumu_geri_yukle()  # backtestte surekli db'ye gitmemek icin memory'den traderi zaman serisinde tasiyoruz

    def pozisyon_al(self):
        tahmin = self.tahmin
        self.suanki_ts = tahmin["ds"]
        tahmin["alis"] = float("nan")
        tahmin["satis"] = float("nan")
        tahmin["cikis"] = float("nan")

        wallet = self.config.get("wallet")
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]

        if self.karar == Karar.alis:
            if self.pozisyon.value in [0, -1]:
                if self.islem_miktari:
                    self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.miktar_hesapla()
                self.islem_fiyati = self.suanki_fiyat
                tahmin["alis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds']
                self.pozisyon = Pozisyon(1)
                self.super_trend_strategy.reset_super_trend()
        elif self.karar == Karar.satis:
            if self.pozisyon.value in [0, 1]:
                if self.islem_miktari:
                    self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.miktar_hesapla()
                self.islem_fiyati = self.suanki_fiyat
                tahmin["satis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds']
                self.pozisyon = Pozisyon(-1)
                self.super_trend_strategy.reset_super_trend()

        elif self.karar == Karar.cikis:
            self.dolar = self.dolar - self.pozisyon.value * (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            tahmin["cikis"] = self.suanki_fiyat
            self.islem_miktari = 0
            self.islem_fiyati = 0
            self.pozisyon = Pozisyon(0)
            self.karar = Karar(0)
            self.super_trend_strategy.reset_super_trend()

        wallet["ETH"] = self.islem_miktari
        wallet["USDT"] = self.dolar

        self.config["wallet"] = wallet
        self.onceki_karar = self.karar
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]
        self.tahmin = tahmin

    def karar_calis(self):
        swing_karar = self.swing_strategy.karar.value
        prophet_karar = self.prophet_strategy.karar.value

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

    def super_trend_takip(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("super_trend_pencere"), "mum",
            self.prophet_baslangic_gunu, self.bitis_gunu
        )
        self.super_trend_strategy.atr_hesapla(series)
        self.super_trend_cikis_kontrol()

    def super_trend_cikis_kontrol(self):
        if self.onceki_karar.value * self.karar.value < 0:  # eger pozisyon zaten yon degistirmisse, stop yapip exit yapma
            self.super_trend_strategy.reset_super_trend()
            return

        self.super_trend_strategy.tp_hesapla(self.pozisyon)

        if self.pozisyon.value * self.super_trend_strategy.onceki_tp < self.pozisyon.value * self.super_trend_strategy.tp:
            self.super_trend_strategy.onceki_tp = self.super_trend_strategy.tp

        if self.pozisyon.value * self.suanki_fiyat < self.pozisyon.value * self.super_trend_strategy.onceki_tp:
            self.karar = Karar.cikis
            self.super_trend_strategy.reset_super_trend()

    def prophet_karar_hesapla(self):
        self.prophet_strategy.tahmin_hesapla(self.prophet_baslangic_gunu, self.bitis_gunu - timedelta(hours=4))
        self.prophet_strategy.kesme_durumu_hesapla()
        self.prophet_strategy.update_trader_onceki_durumlar()
        self.tahmin = self.prophet_strategy.tahmin_hesapla(self.prophet_baslangic_gunu, self.bitis_gunu)
        self.prophet_strategy.kesme_durumu_hesapla()
        self.prophet_strategy.kesme_durumundan_karar_hesapla()

    def swing_trader_karar_hesapla(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("swing_pencere"), "mum",
            self.swing_baslangic_gunu, self.bitis_gunu
        )
        self.swing_strategy.swing_data = SwingTrader(series)
        return self.swing_strategy.swing_data_trend_hesapla()

    def wallet_isle(self):
        for symbol in self.wallet:
            self.config["wallet"][symbol.get("asset")] = symbol.get("balance")
        self.dolar = float(self.config["wallet"].get('USDT'))
        self.coin = float(self.config["wallet"].get(self.config.get('symbol')))

    def durumu_geri_yukle(self):
        _trader = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), "trader")
        _oncekiler = ["karar", "pozisyon"]
        if not _trader.empty:
            conf_ = json.loads(_trader.config[0])
            for key in _oncekiler:
                if key == "karar":
                    self.onceki_karar = Karar(conf_[key])
                elif key == "pozisyon":
                    self.pozisyon = Pozisyon(conf_[key])

    def durumu_kaydet(self):
        _trader = {}

        for key in self._kaydedilecek:
            if hasattr(getattr(self, key), "value"):
                _trader[key] = getattr(self, key).value
            else:
                _trader[key] = getattr(self, key)
        data = {"ds": okunur_date_yap(datetime.utcnow().timestamp()*1000), "trader": json.dumps(_trader)}
        self.sqlite_service.veri_yaz(data, "trader")
        print(data)

    def miktar_hesapla(self):
        # TODO:: burda su anki fiyati baska bir endpoint'den cekip ona gore miktar hesapla
        miktar = self.dolar / self.suanki_fiyat
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
        self.print_islem_detay(islem)
        bam_bama_sinyal_gonder(islem, yon)

    def print_islem_detay(self, islem):
        print(f"islem detaylar ==> ds: {islem.get('ds')} ")
        print(f"\t\t\t\t ==> alis: {islem.get('alis')} satis: {islem.get('satis')} cikis: {islem.get('cikis')}")
        print(f"\t\t\t\t ==> USDT: {islem.get('USDT')} ETH: {islem.get('ETH')}")

    def mum_verilerini_guncelle(self):
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("pencere"), self.prophet_service, self.backfill_baslangic_gunu, self.bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("swing_pencere"), self.prophet_service, self.backfill_baslangic_gunu, self.bitis_gunu
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
