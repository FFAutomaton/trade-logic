import pandas as pd
from csv import DictWriter
from signal_prophet.ml.model_classes.prophet_model import ProphetModel
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def ciz(coin):
    sonuclar = pd.read_csv(f'./coindata/{coin}/tahminler.csv')
    sonuclar = sonuclar.iloc[-200:]
    # plt.style.use('dark_background')
    plt.plot(sonuclar['High'], label='High', linestyle='--', color='green')
    plt.plot(sonuclar['Low'], label='Low', linestyle='--', color='red')
    plt.plot(sonuclar['Open'], label='Open', color='black')
    # cuzdan = sonuclar['USDT'] + (sonuclar['Open'] * sonuclar['ETH'])
    # plt.plot(cuzdan)
    plt.scatter(sonuclar.index, sonuclar['Alis'], marker='^', color='#00ff00')
    plt.scatter(sonuclar.index, sonuclar['Satis'], marker='v', color='#ff00ff')
    plt.legend(loc='upper left')
    plt.show()

def tahmin_getir(_config, baslangic_gunu, cesit):
    arttir = _config.get('arttir')
    train = model_verisini_getir(_config, baslangic_gunu, cesit)
    forecast = model_egit_tahmin_et(train)
    try:
        _close = train[train['ds'] == baslangic_gunu - timedelta(hours=arttir)].get("Close").values[0]
    except:
        _close = train[train['ds'] == baslangic_gunu - timedelta(hours=arttir)].get("y").values[0]
    return forecast, _close


def model_egit_tahmin_et(train):
    model = ProphetModel(
        train=train,
        horizon=1,
    )
    model.fit()
    return model.predict()


def tahminlere_ekle(_config, tahminler):
    with open(f'./coindata/{_config.get("coin")}/tahminler.csv', 'a', newline='') as f_object:
        writer_object = DictWriter(f_object, fieldnames=tahminler.keys())
        writer_object.writerow(tahminler)
        f_object.close()


def islem_hesapla_open_close(_config, tahmin):
    wallet = _config.get("wallet")
    suanki_fiyat = tahmin[9]
    highp = tahmin[4]
    lowp = tahmin[5]
    if suanki_fiyat > highp * 1.005:
        if wallet["ETH"] != 0:
            wallet["USDT"] = wallet["ETH"] * suanki_fiyat
            wallet["ETH"] = 0
    elif suanki_fiyat <= lowp * 0.998:
        if wallet["USDT"] != 0:
            wallet["ETH"] = wallet["USDT"] / suanki_fiyat
            wallet["USDT"] = 0

    _config["wallet"] = wallet
    tahmin.append(wallet["ETH"])
    tahmin.append(wallet["USDT"])
    return tahmin, _config



def islem_hesapla_low(_config, tahmin):
    wallet = _config.get("wallet")
    suanki_fiyat = tahmin[2]
    if tahmin[1] - suanki_fiyat > 50:
        if wallet["USDT"] != 0:
            wallet["ETH"] = wallet["USDT"] / suanki_fiyat
            wallet["USDT"] = 0
    elif tahmin[1] - suanki_fiyat < -50:
        if wallet["ETH"] != 0:
            wallet["USDT"] = wallet["ETH"] * suanki_fiyat
            wallet["ETH"] = 0
    _config["wallet"] = wallet
    tahmin.append(wallet["ETH"])
    tahmin.append(wallet["USDT"])
    return tahmin, _config


def boslari_doldur(main_dataframe):
    if main_dataframe.isnull().any().any():
        for index, row in main_dataframe.isnull().iterrows():
            for i, v in enumerate(row.values):
                if v:
                    main_dataframe.at[index, row.index[i]] = main_dataframe.mean(axis=1)[index]
    return main_dataframe


def islem_hesapla_swing(_config, tahmin, swing_data):
    wallet = _config.get("wallet")
    suanki_fiyat = tahmin["Open"]
    tahmin["Alis"] = float("nan")
    tahmin["Satis"] = float("nan")

    if wallet["USDT"] != 0:
        if swing_data.karar == 'al':
            tahmin["Alis"] = suanki_fiyat
            wallet["ETH"] = wallet["USDT"] / suanki_fiyat
            wallet["USDT"] = 0
    elif wallet["ETH"] != 0:
        if swing_data.karar == 'sat':
            tahmin["Satis"] = suanki_fiyat
            wallet["USDT"] = wallet["ETH"] * suanki_fiyat
            wallet["ETH"] = 0

    _config["wallet"] = wallet
    tahmin["ETH"] = wallet["ETH"]
    tahmin["USDT"] = wallet["USDT"]
    tahmin["Neden"] = swing_data.neden
    return tahmin, _config


def dosya_yukle(coin, baslangic, pencere):
    tum_data_dosya_adi = f'./coindata/{coin}/{coin}_{pencere}_all.csv'
    main_dataframe = pd.read_csv(tum_data_dosya_adi)

    main_dataframe['Open Time'] = main_dataframe[["Open Time"]].apply(pd.to_datetime)
    main_dataframe = main_dataframe.sort_values(by='Open Time', ascending=False, ignore_index=True)
    main_dataframe = main_dataframe[main_dataframe['Open Time'] < baslangic].reset_index(drop=True)
    main_dataframe = main_dataframe.iloc[0:200]
    print('Tum data !')
    return main_dataframe


def train_kirp_yeniden_adlandir(df, cesit):
    # df = df.iloc[:, :2]
    train = df.rename(columns={"Open Time": "ds"})
    train = train.rename(columns={cesit: "y"})
    return train


def model_verisini_getir(_config, suan, cesit):
    coin = _config.get('coin')
    pencere = _config.get('pencere')
    df = dosya_yukle(coin, suan, pencere)
    train = train_kirp_yeniden_adlandir(df, cesit)
    return train


def eski_tahminleri_yukle(_config):
    df = pd.read_csv(f'./coindata/{_config.get("coin")}/prophet_tahminler_{_config.get("pencere")}.csv')
    return df


def tahmin_onceden_hesaplanmis_mi(baslangic_gunu, _config, tahminler_cache):
    if datetime.strftime(baslangic_gunu, '%Y-%m-%d %H:%M:%S') in tahminler_cache['ds'].values:
        return True
    return False


def export_tahmin(tahmin, _config):
    with open(f'./coindata/{_config.get("coin")}/prophet_tahminler_{_config.get("pencere")}.csv', 'a', newline='') as f_object:
        writer_object = DictWriter(f_object, fieldnames=tahmin.keys())
        writer_object.writerow(tahmin)
        f_object.close()


def export_all_data(prophet_service, _config, baslangic_gunu, bitis_gunu):
    tip = _config.get('pencere')
    arttir = _config.get('arttir')
    coin = _config.get('coin')

    if baslangic_gunu == bitis_gunu:
        bitis_gunu = baslangic_gunu + timedelta(hours=arttir) - timedelta(seconds=1)

    data = prophet_service.tg_binance_service.get_client().get_historical_klines(
        symbol=coin, interval=tip,
        start_str=str(baslangic_gunu), end_str=str(bitis_gunu), limit=500
    )
    df = prophet_service.dataframe_schemasina_cevir_isci(data)
    df.to_csv(f'./coindata/{coin}/{coin}_{tip}_all.csv', mode='a', index=False, header=False)
    print(f'export tamamlandi {tip}')


if __name__ == '__main__':
    bugun = '2021-12-06'
    model_verisini_getir('ETHUSDT', bugun, )