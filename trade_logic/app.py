import json
import time
import math
from config import *
from trade_logic.traders.prophet_trader import Trader as prophet_trader
from trade_logic.traders.swing_trader import Trader as swing_trader
from swing_trader.swing_trader_class import SwingTrader
from service.sqlite_service import SqlLite_Service
from signal_prophet.prophet_service import TurkishGekkoProphetService
from signal_atr.atr import ATR
from trade_logic.utils import *
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService
from service.bam_bam_service import bam_bama_sinyal_gonder
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class App:
    def __init__(self, baslangic_gunu=None):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}
        self.config = {
            "symbol": "ETH", "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4,
            "swing_pencere": "1d", "swing_arttir": 24,
            "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
            "prophet_window": 200, "doldur": True, "swing_window": 200,
            "atr_window": 10, "supertrend_mult": 3,
            "cooldown": 4
        }
        self.secrets.update(self.config)
        self.tp = 0
        self.onceki_tp = 0
        self.islem_ts = 0
        self.islem_miktari = 0
        self.pozisyon = 0  # 0-baslangic, 1 long, -1 short
        self.bitis_gunu = bitis_gunu_truncate(self.config.get("arttir"))
        # self.bitis_gunu = datetime.strptime('2021-10-15 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.bitis_gunu = self.bitis_gunu.replace(tzinfo=None)
        self.baslangic_gunu = self.bitis_gunu - timedelta(hours=240) if baslangic_gunu is None else baslangic_gunu

        self.prophet_service = TurkishGekkoProphetService(self.secrets)
        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.swing_trader = swing_trader(self.config)
        self.prophet_trader = prophet_trader(self.config)
        # self.atr_trader = Trader(self.config)  # trailing stop icin

    def karar_calis(self):
        swing_karar = self.swing_trader.karar.value
        prophet_karar = self.prophet_trader.karar.value
        if swing_karar * prophet_karar > 0:
            self.pozisyon = Pozisyon.long
        elif swing_karar * prophet_karar < 0:
            self.pozisyon = Pozisyon.short
        elif swing_karar == 0:
            if prophet_karar == Karar.alis.value:
                self.pozisyon = Pozisyon.long
            elif prophet_karar == Karar.satis.value:
                self.pozisyon = Pozisyon.short
            else:
                self.pozisyon = Pozisyon.notr
        else:
            raise NotImplementedError("karar fonksiyonu beklenmedik durum")

    def prophet_karar_hesapla(self):
        self.prophet_trader.tahmin_hesapla(self.bitis_gunu - timedelta(hours=4))
        self.prophet_trader.kesme_durumu_hesapla()
        self.prophet_trader.update_trader_onceki_durumlar()
        self.prophet_trader.tahmin_hesapla(self.bitis_gunu)
        self.prophet_trader.kesme_durumu_hesapla()
        self.prophet_trader.kesme_durumundan_karar_hesapla()

    def swing_trader_karar_hesapla(self):
        series = self.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("swing_pencere"), "mum",
            self.bitis_gunu - timedelta(days=self.config.get("swing_window")), self.bitis_gunu
        )
        self.swing_trader.swing_data = SwingTrader(series)
        return self.swing_trader.swing_data_trend_hesapla()

    def al_sat_hesapla(self, tahmin):
        self.suanki_fiyat = tahmin["open"]
        self.suanki_ts = tahmin["ds"]
        # if tahmin["ds"] == "2022-01-20 00:00:00":
        #     print('here')
        tahmin["alis"] = float("nan")
        tahmin["satis"] = float("nan")
        tahmin["cikis"] = float("nan")
        tahmin["ETH"] = self.config["wallet"]["ETH"]
        tahmin["USDT"] = self.config["wallet"]["USDT"]

        # self.tp_guncelle()

    def tahmin_getir(self, baslangic_gunu, cesit):
        arttir = self.config.get('arttir')
        coin = self.config.get('coin')
        pencere = self.config.get('pencere')

        df = self.sqlite_service.veri_getir(coin, pencere, "mum", baslangic_gunu, self.bitis_gunu)
        train = train_kirp_yeniden_adlandir(df, cesit)

        forecast = model_egit_tahmin_et(train, self.config.get("pencere").upper())
        try:
            _close = train[train['ds'] == baslangic_gunu - timedelta(hours=arttir)].get("close").values[0]
        except:
            _close = train[train['ds'] == baslangic_gunu - timedelta(hours=arttir)].get("y").values[0]
        return forecast, _close

    def backtest_cuzdana_isle(self, tahmin):
        wallet = self.config.get("wallet")
        if self.karar == 1:

            if self.pozisyon in [0, -1]:
                if self.islem_miktari:
                    self.dolar = self.dolar + (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["alis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds']
                self.pozisyon = 1
                self.reset_trader()
        elif self.karar == -1:
            # pass
            if self.pozisyon in [0, 1]:
                if self.islem_miktari:
                    self.dolar = self.dolar - (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
                self.islem_miktari = self.dolar / self.suanki_fiyat
                self.islem_fiyati = self.suanki_fiyat
                tahmin["satis"] = self.islem_fiyati
                self.islem_ts = tahmin['ds']
                self.pozisyon = -1
                self.reset_trader()

        elif self.karar == 3:
            self.dolar = self.dolar - self.pozisyon * (self.islem_fiyati - self.suanki_fiyat) * self.islem_miktari
            tahmin["cikis"] = self.suanki_fiyat
            self.islem_miktari = 0
            self.islem_fiyati = 0
            self.pozisyon = 0
            self.karar = 0
            self.reset_trader()

        wallet["ETH"] = 0
        wallet["USDT"] = self.dolar

        self.config["wallet"] = wallet
        tahmin["ETH"] = wallet["ETH"]
        tahmin["USDT"] = wallet["USDT"]
        return tahmin, self.config

    def wallet_isle(self):
        for symbol in self.wallet:
            self.config["wallet"][symbol.get("asset")] = symbol.get("balance")
        self.dolar = float(self.config["wallet"].get('USDT'))
        self.coin = float(self.config["wallet"].get(self.config.get('symbol')))

    def trader_geri_yukle(self):
        trader = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), "trader")
        if not trader.empty:
            conf_ = json.loads(trader.config[0])
            for key in conf_:
                setattr(self.trader, key, conf_[key])

    def trader_kaydet(self):
        self.trader.atr = None  # atr'yi veritabaninda tutmaya gerek yok, json.dumps patliyor zaten
        data = {"ds": okunur_date_yap(datetime.utcnow().timestamp()*1000), "trader": json.dumps(self.trader.__dict__)}
        self.sqlite_service.veri_yaz(data, "trader")

    def calis(self):
        # self.trader_geri_yukle()
        # self.trader.wallet = self.binance_service.futures_hesap_bakiyesi()
        # self.trader.wallet_isle()

        # self.trader_kaydet()
        islem = None
        yon = None
        # TODO:: miktar hesapla

        if islem["alis"] > 0:
            _exit_, yon = self.prophet_service.tg_binance_service. \
                futures_market_exit(self.config.get("coin"))
            miktar = self.trader.dolar / self.trader.suanki_fiyat
            miktar = math.floor(miktar * 100)/100
            self.prophet_service.tg_binance_service.\
                futures_market_islem(self.config.get("coin"), taraf='BUY', miktar=miktar, kaldirac=1)
            print(f"Alış gerçekleştirdi  up!")
        elif islem["satis"] > 0:
            _exit_, yon = self.prophet_service.tg_binance_service. \
                futures_market_exit(self.config.get("coin"))
            miktar = self.wallet.get(self.config.get("symbol"))
            self.prophet_service.tg_binance_service.\
                futures_market_islem(self.config.get("coin"), taraf='SELL', miktar=miktar, kaldirac=1)
            print(f"Satış gerçekleştirdi  down!")
        elif islem["cikis"] > 0:
            _exit_, yon = self.prophet_service.tg_binance_service.\
                futures_market_exit(self.config.get("coin"))
            print(f"Kaçışşşşş  go go go!!")
        bam_bama_sinyal_gonder(islem, yon)
        print(f"işlem detaylar: {json.dumps(islem)}")
        print(f"############^^^^^###########")
        print(f"trader detaylar: {json.dumps(self.trader.__dict__)}")
        # TODO:: normal islemleri ayri bir tabloya kaydet
        # TODO:: makineye baglanip repoyu cek, calistir


    def backtest_basla(self):
        self.sqlite_service.islemleri_temizle()
        baslangic_gunu = self.baslangic_gunu
        while baslangic_gunu <= self.bitis_gunu:
            islem = self.tekil_islem_hesapla(baslangic_gunu)
            self.sqlite_service.veri_yaz(islem, "islem")
            print('##################################')
            print(f'{baslangic_gunu} icin bitti!')
            baslangic_gunu = baslangic_gunu + timedelta(hours=self.config.get('arttir'))

    def mum_verilerini_guncelle(self):
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("pencere"), self.prophet_service, self.baslangic_gunu, self.bitis_gunu
        )
        self.sqlite_service.mum_datasi_yukle(
            self.config.get("swing_pencere"), self.prophet_service, self.baslangic_gunu, self.bitis_gunu
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
