import time
from config import *
from trade_logic.utils import *
from trade_logic.trader import Trader
from swing_trader.swing_trader_class import SwingTrader


def al_sat_basla(_config, baslangic_gunu, bitis_gunu):
    arttir = _config.get('arttir')
    coin = _config.get('coin')
    pencere = _config.get('pencere')
    trader = Trader()

    tahminler_cache = eski_tahminleri_yukle(_config)
    while baslangic_gunu <= bitis_gunu:
        start = time.time()
        tahmin = {"ds": datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S')}
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

        print(f'egitim bitti sure: {time.time() - start}')
        # gunluk veriden swing trader ile dalga analizi, eger yukari ise sadece alis ile kisitla ve tam tersi
        
        series = dosya_yukle(coin, baslangic_gunu, '1d')  # veri oldugunu varsayar
        swing_data = SwingTrader(series)


        tahmin, _config = trader.al_sat_hesapla(trader, tahmin, swing_data, _config)
        tahminlere_ekle(_config, tahmin)

        baslangic_gunu = baslangic_gunu + timedelta(hours=arttir)

        print('##################################')
        print(f'{baslangic_gunu} icin bitti!')


if __name__ == '__main__':
    _config = {
        "API_KEY": API_KEY, "API_SECRET": API_SECRET, "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4,
        "high": "High", "low": "Low", "wallet": {"ETH": 0, "USDT": 1000}
    }

    baslangic_gunu = datetime.strptime('2021-10-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    bitis_gunu = datetime.strptime('2022-01-31 20:00:00', '%Y-%m-%d %H:%M:%S')

    # from signal_prophet.prophet_service import TurkishGekkoProphetService
    # prophet_service = TurkishGekkoProphetService(_config)
    # export_all_data(prophet_service, _config, baslangic_gunu, bitis_gunu)

    # al_sat_basla(_config, baslangic_gunu, bitis_gunu)
    ciz(_config.get('coin'))
