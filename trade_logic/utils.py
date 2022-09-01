import pandas as pd
from signal_prophet.ml.model_classes.prophet_model import ProphetModel
from datetime import datetime, timezone


def heikinashi_mum_analiz(last_row):
    karar, yon = 0, 0

    if last_row["HA_Close"] > last_row["HA_Open"]:
        yon = 1
        if last_row["HA_Open"] == last_row["HA_Low"]:
            karar = 1

    if last_row["HA_Close"] < last_row["HA_Open"]:
        yon = -1
        if last_row["HA_Open"] == last_row["HA_High"]:
            karar = -1
    return yon, karar


def bugunun_heikinashisi(series_1d, series_5m, suanki_fiyat):
    last_row = series_1d.iloc[-1]
    prev_row = series_1d.iloc[-2]
    m5_high = suanki_fiyat
    m5_low = suanki_fiyat
    if not series_5m.empty:
        m5_high = series_5m["high"].max()
        m5_low = series_5m["low"].min()

    last_row["HA_Open"] = (prev_row["HA_Open"] + prev_row["HA_Close"]) / 2
    last_row["HA_Close"] = suanki_fiyat
    last_row['HA_High'] = max(last_row["HA_Open"], m5_high, suanki_fiyat)
    last_row['HA_Low'] = min(last_row["HA_Open"], m5_low, suanki_fiyat)
    return last_row


def heikinashiye_cevir(df):
    df = df.iloc[::-1]
    pd.options.mode.chained_assignment = None
    df['HA_Close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    idx = df.index.name
    df.reset_index(inplace=True)

    for i in range(0, len(df)):
        if i == 0:
            df.at[i, 'HA_Open'] = (df.at[i, 'open'] + df.at[i, 'close']) / 2
        else:
            df.at[i, 'HA_Open'] = (df.at[i - 1, 'HA_Open'] + df.at[i - 1, 'HA_Close']) / 2

    if idx:
        df.set_index(idx, inplace=True)

    df['HA_High'] = df[['HA_Open', 'HA_Close', 'high']].apply(max, axis=1)
    df['HA_Low'] = df[['HA_Open', 'HA_Close', 'low']].apply(min, axis=1)
    return df


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


def tahmin_doldur(tahmin, wallet, prophet):
    tahmin["alis"] = float("nan")
    tahmin["satis"] = float("nan")
    tahmin["cikis"] = float("nan")

    tahmin["high"] = prophet.high if hasattr(prophet, "high") else float("nan")
    tahmin["low"] = prophet.low if hasattr(prophet, "low") else float("nan")
    tahmin["open"] = prophet.open if hasattr(prophet, "open") else float("nan")

    tahmin["eth"] = wallet["ETH"]
    tahmin["usdt"] = wallet["USDT"]

    return tahmin


def okunur_date_yap(unix_ts):
    return datetime.utcfromtimestamp(unix_ts/1000).strftime("%Y-%m-%d %H:%M:%S")


def integer_date_yap(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=None).timestamp())


def model_egit_tahmin_et(train, pencere):
    model = ProphetModel(
        train=train,
        horizon=1,
        freq=pencere

    )
    model.fit()
    return model.predict()


def train_kirp_yeniden_adlandir(df, cesit):
    # df = df.iloc[:, :2]
    train = df.rename(columns={"open_ts_str": "ds"})
    train = train.rename(columns={cesit: "y"})
    return train


def tahmin_onceden_hesaplanmis_mi(baslangic_gunu, _config, tahminler_cache):
    if pd.Timestamp(baslangic_gunu) in tahminler_cache['ds_str'].values:
        return True
    return False


def print_islem_detay(trader):
    islem = trader.tahmin

    if islem.get('alis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> alis: {islem.get('alis')}")
    if islem.get('satis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> satis: {islem.get('satis')}")
    if islem.get('cikis') > 0:
        print(f"islem detaylar ==> ds: {islem.get('ds')}\t\t\t\t ==> cikis: {islem.get('cikis')}")


if __name__ == '__main__':
    bugun = '2021-12-06'
