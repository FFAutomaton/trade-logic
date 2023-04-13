from service.sqlite_service import SqlLite_Service
from service.fred_service import FredService
from config import *
from config_users import fred_api_key
from trade_logic.utils import datetime, timezone
import os


os.environ["PYTHON_ENV"] = "TEST"

_secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET, "FED_KEY": fred_api_key}

_config = {
    "symbol": "ETH", "coin": 'ETHUSDT', "arttir": 15,
    "pencere_1d": "1d", "pencere_1h": "1h", "pencere_15m": "15m",
    "wallet": {"ETH": 0, "USDT": 1000},
    "backfill_window": 20,
    "atr_window": 10, "supertrend_mult": 0.5, "doldur": True
}

fred_service = FredService(secrets=_secrets)
sqlite_service = SqlLite_Service(_config)

start = datetime.strptime('2023-03-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)


sqlite_service.fed_datasi_yukle(
    fred_service, start, None
)
