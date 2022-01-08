from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
from config import *
from signal_prophet.prophet_service import TurkishGekkoProphetService
# from swing_utils import *
from swing_trader.swing_trader_class import SwingTrader
from trade_logic.utils import *


def ciz(coin):
    sonuclar = pd.read_csv(f'./coindata/{coin}/tahminler.csv')
    sonuclar = sonuclar.iloc[-200:]
    # plt.style.use('dark_background')
    plt.plot(sonuclar['High'], label='High', linestyle='--', color='green')
    plt.plot(sonuclar['Low'], label='Low', linestyle='--', color='red')
    plt.plot(sonuclar['Open'], label='Open', color='black')
    # cuzdan = sonuclar['USDT'] + (sonuclar['Open'] * sonuclar['ETH'])
    # plt.plot(cuzdan)
    plt.scatter(sonuclar.index, sonuclar['Alis'], marker='^', color='#00ff00')
    plt.scatter(sonuclar.index, sonuclar['Satis'], marker='v', color='#ff00ff')
    plt.legend(loc='upper left')
    plt.show()


def propheti_calistir(_config, baslangic_gunu, bitis_gunu):
    arttir = _config.get('arttir')
    coin = _config.get('coin')
    pencere = _config.get('pencere')
    mod = None

    tahminler_cache = eski_tahminleri_yukle(_config)
    while baslangic_gunu <= bitis_gunu:
        tahmin = {}
        tahmin = {"ds": datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S')}
        start = time.time()
        if not tahmin_onceden_hesaplanmis_mi(baslangic_gunu, _config, tahminler_cache):
            high_tahmin, _close = tahmin_getir(_config, baslangic_gunu, _config.get("high"))
            low_tahmin, _close = tahmin_getir(_config, baslangic_gunu, _config.get("low"))
            tahmin["High"] = high_tahmin["yhat_upper"].values[0]
            tahmin["Low"] = low_tahmin["yhat_lower"].values[0]
            tahmin["Open"] = _close
            export_tahmin(tahmin, _config)
        else:
            _row = tahminler_cache[tahminler_cache["ds"] == datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S')]
            tahmin["High"] = _row["High"].values[0]
            tahmin["Low"] = _row["Low"].values[0]
            tahmin["Open"] = _row["Open"].values[0]

        series = dosya_yukle(coin, baslangic_gunu, pencere)
        swing_data = SwingTrader(series)

        #TODO:: al salt mod hesaplayi guncelle
        mod = swing_data.al_sat_mod_hesapla2(tahmin, mod)
        print(f'egitim bitti sure: {time.time() - start}')

        tahmin, _config = islem_hesapla_swing(_config, tahmin, swing_data)
        tahminlere_ekle(_config, tahmin)
        print(f'{baslangic_gunu} icin bitti!')

        baslangic_gunu = baslangic_gunu + timedelta(hours=arttir)


if __name__ == '__main__':
    _config = {
        "API_KEY": API_KEY, "API_SECRET": API_SECRET, "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4,
        "high": "Open", "low": "Close", "wallet": {"ETH": 0, "USDT": 1000}
    }


    baslangic_gunu = datetime.strptime('2021-12-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # son gun degerinin datasi da geliyor
    bitis_gunu = datetime.strptime('2022-01-07 20:00:00', '%Y-%m-%d %H:%M:%S')

    # propheti_calistir(_config, baslangic_gunu, bitis_gunu)

    prophet_service = TurkishGekkoProphetService(_config)
    # export_all_data(prophet_service, _config, baslangic_gunu, bitis_gunu)

    ciz(_config.get('coin'))
