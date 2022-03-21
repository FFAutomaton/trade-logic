import pandas as pd
from csv import DictWriter

import pytz
from signal_prophet.ml.model_classes.prophet_model import ProphetModel
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def bitis_gunu_truncate(arttir):
    bitis_gunu = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    _h = bitis_gunu.hour - (bitis_gunu.hour % arttir)
    bitis_gunu = bitis_gunu.replace(hour=_h)
    return bitis_gunu


def okunur_date_yap(unix_ts):
    return datetime.utcfromtimestamp(unix_ts/1000).strftime("%Y-%m-%d %H:%M:%S")


def integer_date_yap(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc).timestamp())


def model_egit_tahmin_et(train, pencere):
    model = ProphetModel(
        train=train,
        horizon=1,
        freq=pencere

    )
    model.fit()
    return model.predict()


def tahminlere_ekle(_config, tahminler):
    with open(f'./coindata/{_config.get("coin")}/tahminler.csv', 'a', newline='') as f_object:
        writer_object = DictWriter(f_object, fieldnames=tahminler.keys())
        writer_object.writerow(tahminler)
        f_object.close()


def boslari_doldur(main_dataframe):
    if main_dataframe.isnull().any().any():
        for index, row in main_dataframe.isnull().iterrows():
            for i, v in enumerate(row.values):
                if v:
                    main_dataframe.at[index, row.index[i]] = main_dataframe.mean(axis=1)[index]
    return main_dataframe


def train_kirp_yeniden_adlandir(df, cesit):
    # df = df.iloc[:, :2]
    train = df.rename(columns={"open_ts_str": "ds"})
    train = train.rename(columns={cesit: "y"})
    return train


def tahmin_onceden_hesaplanmis_mi(baslangic_gunu, _config, tahminler_cache):
    if pd.Timestamp(baslangic_gunu) in tahminler_cache['ds_str'].values:
        return True
    return False



if __name__ == '__main__':
    bugun = '2021-12-06'
