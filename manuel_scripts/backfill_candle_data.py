from datetime import timedelta

from service.sqlite_service import SqlLite_Service
from config import *
from trade_logic.utils import bitis_gunu_truncate_min_precision, datetime,timezone


_secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}

_config = {
    "symbol": "ETH", "coin": 'ETHUSDT', "arttir": 4,
    "pencere_1d": "1d", "pencere_4h": "4h", "pencere_5m": "5m",
    "swing_arttir": 24,
    "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
    "backfill_window": 20, "super_trend_window": 200,
    "atr_window": 10, "supertrend_mult": 0.5, "doldur": True
}

sqlite_service = SqlLite_Service(_config)
prophet_service = TurkishGekkoProphetService(_secrets)

window_end = datetime.strptime('2021-08-01 00:00:00', '%Y-%m-%d %H:%M:%S')
window_end = window_end.replace(tzinfo=timezone.utc)

_son = bitis_gunu_truncate_min_precision(_config.get("arttir"))

while window_end < _son:

    sqlite_service.mum_datasi_yukle(
        "5m", prophet_service, window_end - timedelta(days=20), window_end
    )
    print(f" one turn finished for {window_end}")
    window_end += timedelta(days=19)
