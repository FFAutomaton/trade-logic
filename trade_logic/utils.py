import pandas as pd
from datetime import datetime, timezone
import csv


def egim_hesapla(a, b):
    if a == 0 or b == 0:
        return 0
    return round(float(a/b), 6)


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


def sonuc_yazdir(start_date, end_date, trader, islem_sonuc, opt_conf, c):
    if trader.pozisyon.value > 0:
        usdt = islem_sonuc.get("eth") * trader.suanki_fiyat
        kar = f"{round((usdt - 1000) / 1000, 2)}"
    elif trader.pozisyon.value < 0:
        usdt = islem_sonuc.get("eth") * (trader.islem_fiyati - trader.suanki_fiyat)
        kar = f"{round((islem_sonuc.get('usdt') + usdt - 1000) / 1000, 2)}"
    else:
        kar = f"{round((islem_sonuc.get('usdt') - 1000) / 1000, 2)}"

    params_list = []
    for i in list(opt_conf.keys()):
        params_list.append(str(trader.config.get(i)))
    params_str = '\t'.join(params_list)
    row = f"{c}\t{start_date}\t{params_str}\t{kar}"
    print(row)
    with open('../manuel_scripts/data/sonuclar.csv', 'a', newline='') as f:
        # Append single row to CSV
        f.write(row + '\n')


def killzone_kontrol_decorator(func):
    def inner1(*args, **kwargs):
        if not args[0].dondu_killzone:
            return
        returned_value = func(*args, **kwargs)
        return returned_value

    return inner1


def dongu_kontrol_decorator(func):
    def inner1(*args, **kwargs):
        if not args[0].dondu_1h:
            return
        returned_value = func(*args, **kwargs)
        return returned_value

    return inner1


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
    # if os.getenv("PYTHON_ENV") == "TEST":
    return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


def print_islem_detay(trader):
    islem = trader.tahmin
    print(f"bot calisti {str(trader.bitis_gunu)} - {trader.suanki_fiyat} tp: {trader.super_trend_strategy.onceki_tp}")
    if islem.get('alis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> alis: {islem.get('alis')}")
    if islem.get('satis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> satis: {islem.get('satis')}")
    if islem.get('cikis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> cikis: {islem.get('cikis')}")


if __name__ == '__main__':
    bugun = '2021-12-06'
