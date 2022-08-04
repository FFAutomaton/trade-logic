from datetime import timedelta

from signal_prophet.prophet_service import TurkishGekkoProphetService
from service.sqlite_service import SqlLite_Service
from config import *
from trade_logic.utils import *


_secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}

_config = {
    "symbol": "ETH", "coin": 'ETHUSDT', "pencere": "4h", "arttir": 4,
    "swing_pencere": "1d", "swing_arttir": 24, "prophet_pencere": "4h", "super_trend_pencere": "4h",
    "high": "high", "low": "low", "wallet": {"ETH": 0, "USDT": 1000},
    "prophet_window": 2400, "swing_window": 200, "backfill_window": 20, "super_trend_window": 200,
    "atr_window": 10, "supertrend_mult": 0.5, "doldur": True
}

sqlite_service = SqlLite_Service(_config)
prophet_service = TurkishGekkoProphetService(_secrets)

window_end = datetime.strptime('2021-07-01 00:00:00', '%Y-%m-%d %H:%M:%S')
window_end = window_end.replace(tzinfo=timezone.utc)

_son = bitis_gunu_truncate(_config.get("arttir"))

while window_end < _son:

    sqlite_service.mum_datasi_yukle(
        "5m", prophet_service, window_end - timedelta(days=20), window_end
    )
    print(f" one turn finished for {window_end}")
    window_end += timedelta(days=19)