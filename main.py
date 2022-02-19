import time
from config import *
from trade_logic.utils import *
from trade_logic.trader import Trader
from swing_trader.swing_trader_class import SwingTrader
from service.sqlite_service import SqlLite_Service
from signal_prophet.prophet_service import TurkishGekkoProphetService
from signal_atr.atr import ATR


class App:
    def __init__(self, baslangic_gunu):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}
        self.config = {
            "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4,
            "swing_pencere": "1d", "swing_arttir": 24,
            "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
            "prophet_window": 200, "doldur": False,
            "atr_window": 10, "supertrend_mult": 1
        }
        self.secrets.update(self.config)

        self.baslangic_gunu = baslangic_gunu
        self.bitis_gunu = bitis_gunu_truncate(self.config.get("arttir"))
        # self.bitis_gunu = datetime.strptime('2021-11-01 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.bitis_gunu = self.bitis_gunu.replace(tzinfo=None)

        self.prophet_service = TurkishGekkoProphetService(self.secrets)
        self.sqlite_service = SqlLite_Service(self.config)

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

    def backtest_basla(self):
        trader = Trader(self.config)

        tahminler_cache = self.sqlite_service.veri_getir(self.config.get("coin"), self.config.get("pencere"), 'prophet')
        self.sqlite_service.islemleri_temizle()
        baslangic_gunu = self.baslangic_gunu
        while baslangic_gunu <= self.bitis_gunu:
            start = time.time()
            tahmin = {"ds": datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S')}
            if not tahmin_onceden_hesaplanmis_mi(baslangic_gunu, self.config, tahminler_cache):
                print('prophet calisiyor......')
                high_tahmin, _close = self.tahmin_getir(baslangic_gunu, self.config.get("high"))
                low_tahmin, _close = self.tahmin_getir(baslangic_gunu, self.config.get("low"))
                tahmin["high"] = high_tahmin["yhat_upper"].values[0]
                tahmin["low"] = low_tahmin["yhat_lower"].values[0]
                tahmin["open"] = _close
                self.sqlite_service.tahmin_yaz(tahmin)
            else:
                print('prophet onceden calismis devam ediyorum')
                _row = tahminler_cache[tahminler_cache["ds_str"] == pd.Timestamp(baslangic_gunu)]
                tahmin["high"] = _row["high"].values[0]
                tahmin["low"] = _row["low"].values[0]
                tahmin["open"] = _row["open"].values[0]

            print(f'egitim bitti sure: {time.time() - start}')
            # gunluk veriden swing trader ile dalga analizi, eger yukari ise sadece alis ile kisitla ve tam tersi

            series = self.sqlite_service.veri_getir(
                self.config.get("coin"), self.config.get("swing_pencere"), "mum", baslangic_gunu, self.bitis_gunu
            )
            swing_data = SwingTrader(series)
            trader.atr = ATR(series, self.config.get("atr_window")).average_true_range
            islem, self.config = trader.al_sat_hesapla(tahmin, swing_data)
            self.sqlite_service.islem_yaz(islem)

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

    def ciz(self):
        sonuclar = app.sqlite_service.veri_getir(
            self.config.get("coin"), self.config.get("pencere"), "islem"
        )
        # sonuclar = sonuclar.iloc[-200:]
        # plt.style.use('dark_background')

        sonuclar = sonuclar.set_index(sonuclar['ds_str'])
        plt.plot(sonuclar['high'], label='high', linestyle='--', color='green')
        plt.plot(sonuclar['low'], label='low', linestyle='--', color='red')
        plt.plot(sonuclar['open'], label='open', color='black')
        # cuzdan = sonuclar['USDT'] + (sonuclar['Open'] * sonuclar['ETH'])
        # plt.plot(cuzdan)
        plt.scatter(sonuclar.index, sonuclar['alis'], s=500, marker='^', color='#00ff00')
        plt.scatter(sonuclar.index, sonuclar['satis'], s=500, marker='v', color='#ff0f02')
        plt.scatter(sonuclar.index, sonuclar['cikis'], s=500, marker='.', color='#1a1d33')
        plt.legend(loc='upper right')
        plt.show()


if __name__ == '__main__':
    baslangic_gunu = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    baslangic_gunu = baslangic_gunu.replace(tzinfo=None)
    app = App(baslangic_gunu)

    # if app.config["doldur"]:
    #     app.mum_verilerini_guncelle()
    #
    # app.backtest_basla()

    app.ciz()
