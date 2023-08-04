from datetime import datetime, timezone


def bitis_gunu_truncate_month_precision(_now):
    bitis_gunu = _now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return bitis_gunu.replace(tzinfo=timezone.utc)


def bitis_gunu_truncate_hour_precision(_now, arttir):
    bitis_gunu = _now.replace(minute=0, second=0, microsecond=0)
    _h = bitis_gunu.hour - (bitis_gunu.hour % arttir)
    bitis_gunu = bitis_gunu.replace(hour=_h)
    return bitis_gunu.replace(tzinfo=timezone.utc)


# TODO:: bu iki fonksiyonu birlestir video bile cekilir
def bitis_gunu_truncate_min_precision(bitis_gunu, arttir):
    _m = bitis_gunu.minute - (bitis_gunu.minute % arttir)
    bitis_gunu = bitis_gunu.replace(minute=_m, second=0, microsecond=0)
    return bitis_gunu.replace(tzinfo=timezone.utc)


def okunur_date_yap(unix_ts):
    return datetime.utcfromtimestamp(unix_ts/1000).strftime("%Y-%m-%d %H:%M:%S")


def integer_date_yap(date_str):
    # if os.getenv("PYTHON_ENV") == "TEST":
    return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


def print_islem_detay(trader):
    print(f"FFAutomaton --> side:{trader.karar.value}, {trader.config.get('coin')}, fiyat:{trader.suanki_fiyat}, "
          f"tp:{trader.super_trend_daralan_takip.onceki_tp} profit:{trader.unRealizedProfit} <-- FFAutomaton")


if __name__ == '__main__':
    bugun = '2021-12-06'
