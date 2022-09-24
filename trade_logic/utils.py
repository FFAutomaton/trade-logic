import pandas as pd
from datetime import datetime, timezone
from trade_logic.constants import rsi_bounding_limit


def rsi_limit_kesim_durum_listeden_hesapla(series, pozisyon):
    rsi_ = series[0]
    prev_rsi_ = series[1]
    if pozisyon > 0:
        if prev_rsi_ > 100 - rsi_bounding_limit > rsi_:
            return True
    elif pozisyon < 0:
        if prev_rsi_ < 0 + rsi_bounding_limit < rsi_:
            return True
    return False


def heikinashi_mum_analiz(last_row):
    karar, yon = 0, 0

    if last_row["HA_Close"][0] > last_row["HA_Open"][0]:
        yon = 1
        if last_row["HA_Open"][0] == last_row["HA_Low"][0]:
            karar = 1

    if last_row["HA_Close"][0] < last_row["HA_Open"][0]:
        yon = -1
        if last_row["HA_Open"][0] == last_row["HA_High"][0]:
            karar = -1
    return yon, karar


def heikinashiye_cevir(df):
    # df = df.iloc[::-1]
    pd.options.mode.chained_assignment = None
    # idx = df.index.name
    # df.reset_index(inplace=True)
    df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    i = len(df) - 1
    l = len(df) - 1
    while i >= 0:
        if i == l:
            df.at[i, 'HA_Open'] = (df.at[i, 'open'] + df.at[i, 'close']) / 2
        else:
            df.at[i, 'HA_Open'] = (df.at[i + 1, 'HA_Open'] + df.at[i + 1, 'HA_Close']) / 2
        i -= 1
    # if idx:
    #     df.set_index(idx, inplace=True)

    df['HA_High'] = df[['HA_Open', 'HA_Close', 'high']].apply(max, axis=1)
    df['HA_Low'] = df[['HA_Open', 'HA_Close', 'low']].apply(min, axis=1)
    return df


def sonuc_yazdir(start_date, end_date, mult, trader, islem_sonuc):
    if trader.pozisyon.value > 0:
        usdt = islem_sonuc.get("eth") * trader.suanki_fiyat
        kar = f"{round((usdt - 1000) / 1000, 2)}"
    elif trader.pozisyon.value < 0:
        usdt = islem_sonuc.get("eth") * (trader.islem_fiyati - trader.suanki_fiyat)
        kar = f"{round((islem_sonuc.get('usdt') + usdt - 1000) / 1000, 2)}"
    else:
        kar = f"{round((islem_sonuc.get('usdt') - 1000) / 1000, 2)}"

    print(f"{start_date}\t{end_date}\t{mult}:\t{kar}")


def dongu_kontrol_decorator(func):
    def inner1(*args, **kwargs):
        if not args[0].dondu_4h:
            return
        returned_value = func(*args, **kwargs)
        return returned_value

    return inner1


def bitis_gunu_truncate_month_precision(_now):
    bitis_gunu = _now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return bitis_gunu.replace(tzinfo=timezone.utc)


def bitis_gunu_truncate_day_precision(_now):
    bitis_gunu = _now.replace(hour=0, minute=0, second=0, microsecond=0)
    return bitis_gunu.replace(tzinfo=timezone.utc)


def bitis_gunu_truncate_hour_precision(_now, arttir):
    bitis_gunu = _now.replace(minute=0, second=0, microsecond=0)
    _h = bitis_gunu.hour - (bitis_gunu.hour % arttir)
    bitis_gunu = bitis_gunu.replace(hour=_h)
    return bitis_gunu.replace(tzinfo=timezone.utc)


# TODO:: bu iki fonksiyonu birlestir video bile cekilir
def bitis_gunu_truncate_min_precision(arttir):
    bitis_gunu = datetime.utcnow().replace(second=0, microsecond=0)
    _m = bitis_gunu.minute - (bitis_gunu.minute % arttir)
    bitis_gunu = bitis_gunu.replace(minute=_m)
    return bitis_gunu.replace(tzinfo=timezone.utc)


def islem_doldur(islem, wallet):
    islem["alis"] = float("nan")
    islem["satis"] = float("nan")
    islem["cikis"] = float("nan")

    islem["high"] = float("nan")
    islem["low"] = float("nan")
    islem["open"] = islem.get("open")

    islem["eth"] = wallet["ETH"]
    islem["usdt"] = wallet["USDT"]

    return islem


def okunur_date_yap(unix_ts):
    return datetime.utcfromtimestamp(unix_ts/1000).strftime("%Y-%m-%d %H:%M:%S")


def integer_date_yap(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=None).timestamp())


def print_islem_detay(trader):
    islem = trader.tahmin
    print(f"bot calisti {str(trader.bitis_gunu)}")
    if islem.get('alis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> alis: {islem.get('alis')}")
    if islem.get('satis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> satis: {islem.get('satis')}")
    if islem.get('cikis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> cikis: {islem.get('cikis')}")


if __name__ == '__main__':
    bugun = '2021-12-06'
