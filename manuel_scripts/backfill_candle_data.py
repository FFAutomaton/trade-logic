from datetime import timedelta

from service.sqlite_service import SqlLite_Service
from config import *
from trade_logic.utils import bitis_gunu_truncate_min_precision, datetime,timezone
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService


_secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}

_config = {
    "symbol": "ETH", "coin": 'ETHUSDT', "arttir": 15,
    "pencere_1d": "1d", "pencere_1h": "1h", "pencere_5m": "5m",
    "wallet": {"ETH": 0, "USDT": 1000},
    "backfill_window": 20,
    "atr_window": 10, "supertrend_mult": 0.5, "doldur": True
}

sqlite_service = SqlLite_Service(_config)
binance_serve = TurkishGekkoBinanceService(_secrets)

window_end = datetime.strptime('2021-08-14 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
start = datetime.strptime('2021-08-20 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
_son = bitis_gunu_truncate_min_precision(start, 15)

while window_end < _son:

    sqlite_service.mum_datasi_yukle(
        "15m", binance_serve, window_end - timedelta(days=1), window_end
    )
    print(f" one turn finished for {window_end}")
    window_end += timedelta(days=7)
