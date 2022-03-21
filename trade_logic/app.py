import json
import time
import pytz
from config import *
from trade_logic.trader import Trader
from swing_trader.swing_trader_class import SwingTrader
from service.sqlite_service import SqlLite_Service
from signal_prophet.prophet_service import TurkishGekkoProphetService
from signal_atr.atr import ATR
from trade_logic.utils import *
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService
# from ta.trend import SMAIndicator
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

class App:
    def __init__(self, baslangic_gunu=None):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}
        self.config = {
            "coin": 'ETHUSDT', "pencere": "1m", "arttir": 1,
            "swing_pencere": "1d", "swing_arttir": 24,
            "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
            "prophet_window": 200, "doldur": False,
            "atr_window": 10, "supertrend_mult": 2,
            "cooldown": 4
        }
        self.secrets.update(self.config)

        self.bitis_gunu = bitis_gunu_truncate(self.config.get("arttir"))
        self.bitis_gunu = datetime.strptime('2022-03-20 10:00:00', '%Y-%m-%d %H:%M:%S')
        self.bitis_gunu = self.bitis_gunu.replace(tzinfo=pytz.utc)
        self.baslangic_gunu = self.bitis_gunu - timedelta(hours=240) if baslangic_gunu is None else baslangic_gunu

        self.prophet_service = TurkishGekkoProphetService(self.secrets)
        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)
        self.trader = Trader(self.config)

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

    def tahmin_islemlerini_hallet(self, tahmin, baslangic_gunu):
        tahminler_cache = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), 'prophet')
        if not tahmin_onceden_hesaplanmis_mi(baslangic_gunu, self.config, tahminler_cache):
            print('prophet calisiyor......')
            high_tahmin, _close = self.tahmin_getir(baslangic_gunu, self.config.get("high"))
            low_tahmin, _close = self.tahmin_getir(baslangic_gunu, self.config.get("low"))
            tahmin["high"] = high_tahmin["yhat_upper"].values[0]
            tahmin["low"] = low_tahmin["yhat_lower"].values[0]
            tahmin["open"] = _close
            self.sqlite_service.veri_yaz(tahmin, "tahmin")
        else:
            print('prophet onceden calismis devam ediyorum')
            _row = tahminler_cache[tahminler_cache["ds_str"] == pd.Timestamp(baslangic_gunu)]
            tahmin["high"] = _row["high"].values[0]
            tahmin["low"] = _row["low"].values[0]
            tahmin["open"] = _row["open"].values[0]

        return tahmin

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

    def update_trader_onceki_durumlar(self, onceki_durumlar):
        for attr, value in vars(self.trader).items():
            print(attr, '=', value)
            if "onceki" in attr:
                atr_ = attr.split('_')
                atr_ = "_".join(atr_[1:]) if len(atr_) > 2 else atr_[1]
                setattr(self.trader, attr, getattr(self.trader, atr_))

    def calis(self):
        self.trader_geri_yukle()
        self.trader.wallet = self.binance_service.futures_hesap_bakiyesi()

        onceki_durumlar = self.tekil_islem_hesapla(self.bitis_gunu - timedelta(hours=4))
        self.update_trader_onceki_durumlar(onceki_durumlar)
        islem = self.tekil_islem_hesapla(self.bitis_gunu)
        self.trader_kaydet()
        if islem:
            self.prophet_service.tg_binance_service.market_buy()
        elif islem["bisey"]:
            self.prophet_service.tg_binance_service.market_sell()


        # TODO:: normal islemleri ayri bir tabloya kaydet
        # TODO:: islem verisine gore api istek gonder

    def backtest_basla(self):
        self.sqlite_service.islemleri_temizle()
        baslangic_gunu = self.baslangic_gunu
        while baslangic_gunu <= self.bitis_gunu:
            islem = self.tekil_islem_hesapla(baslangic_gunu)
            self.sqlite_service.veri_yaz(islem, "islem")
            print('##################################')
            print(f'{baslangic_gunu} icin bitti!')
            baslangic_gunu = baslangic_gunu + timedelta(minutes=self.config.get('arttir'))

    def tekil_islem_hesapla(self, baslangic_gunu):
        start = time.time()
        series = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), "mum",
                                                baslangic_gunu, self.bitis_gunu)
        rsi_ = RSIIndicator(series["close"], 14)
        rsi_ = rsi_.rsi()
        ema_ = EMAIndicator(series["close"], 35)
        ema_ = ema_.ema_indicator()
        islem, self.config = self.trader.al_sat_hesapla(rsi_, ema_, series, baslangic_gunu)
        print(f'egitim bitti sure: {time.time() - start}')
        return islem

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
        # plt.plot(sonuclar['high'], label='high', linestyle='--', color='green')
        # plt.plot(sonuclar['low'], label='low', linestyle='--', color='red')
        plt.plot(sonuclar['open'], label='open', color='black')
        # cuzdan = sonuclar['USDT'] + (sonuclar['Open'] * sonuclar['ETH'])
        # plt.plot(cuzdan)
        plt.scatter(sonuclar.index, sonuclar['alis'].astype(float), s=500, marker='^', color='#00ff00')
        plt.scatter(sonuclar.index, sonuclar['satis'].astype(float), s=500, marker='v', color='#ff0f02')
        plt.scatter(sonuclar.index, sonuclar['cikis'].astype(float), s=500, marker='.', color='#1a1d33')
        plt.legend(loc='upper right')
        plt.show()
