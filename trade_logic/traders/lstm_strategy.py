import os
import pickle
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import pandas as pd
from schemas.enums.karar import Karar
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator


class LstmStrategy:
    def __init__(self, config):
        self.config = config
        self.karar = Karar.notr
        self.series = None
        self.bitis_gunu = None
        self.suanki_fiyat = None
        self.ilk_egitim = False
        self.fiyat_tahmini = None
        self.window = 15
        self.trader = None
        self.model_filename = '../coindata/mlp_objects/final_model.sav' if os.getenv("PYTHON_ENV") == "RESET_MLP" else '../../coindata/mlp_objects/final_model.sav'
        self.scaler_filename = '../coindata/mlp_objects/final_scaler.sav' if os.getenv("PYTHON_ENV") == "RESET_MLP" else '../../coindata/mlp_objects/final_scaler.sav'

    def init_lstm_strategy(self, trader):
        self.trader = trader
        self.bitis_gunu = trader.bitis_gunu
        self.series = self.trader.series_1h.sort_values(by='open_ts_int', ascending=True)

        self.append_other_features(trader)
        if os.getenv("PYTHON_ENV") == "TEST":
            if not self.trader.sc_X:
                self.trader.sc_X = MinMaxScaler(feature_range=(0, 1))
            self.egitim_sureci_control()
        elif os.getenv("PYTHON_ENV") == "RESET_MLP":
            if not self.trader.sc_X:
                self.trader.sc_X = MinMaxScaler(feature_range=(0, 1))
            self.egit()
            self.save_model_objects()
        else:  # production demek
            self.load_model_objects()
            self.kismi_egit()
            self.save_model_objects()

    def append_other_features(self, trader):
        rsi_dfs, ema_dfs = self.rsi_hesapla(24, 6), self.ema_hesapla(100, 35)
        fed_data = trader.series_fed
        self.append_to_series(rsi_dfs, ema_dfs, fed_data)

    def append_to_series(self, rsi_dfs, ema_dfs, fed_data):
        self.series = pd.merge(self.series, fed_data, left_on=['open_ts_str'], right_on=["ds_str"])
        self.series = self.series.sort_values(by='ds_int', ascending=True).reset_index(drop=True)
        indicators = pd.concat([rsi_dfs, ema_dfs], axis=1)
        indicators = indicators.sort_index(ascending=False).reset_index(drop=True)
        self.series = pd.concat([self.series, indicators], ignore_index=False, axis=1)
        self.series = self.series.sort_values(by='ds_int', ascending=False)
        self.kolon_tipi_ayarla()

    def kolon_tipi_ayarla(self):
        self.series['open_ts_str'] = pd.to_datetime(self.series.open_ts_str, format='%Y-%m-%d %H:%M:%S')
        self.series.index = self.series['open_ts_str']
        self.series = self.series.drop(
            columns=["open", "open_ts_str", "open_ts_int", "ds_str", "ds_int"]
        )

    def rsi_hesapla(self, window_big, window_small):
        rsi_big = RSIIndicator(self.series["close"], window_big, fillna=True)
        rsi_small = RSIIndicator(self.series["close"], window_small, fillna=True)
        rsi_dfs = pd.concat([rsi_big.rsi().round(decimals=2), rsi_small.rsi().round(decimals=2)], axis=1)
        rsi_dfs = rsi_dfs.rename(columns={'rsi': f'rsi{window_big}', 'rsi': f'rsi{window_small}'})
        return rsi_dfs

    def ema_hesapla(self, window_big, window_small):
        ema_big = EMAIndicator(self.series["close"], window_big, fillna=True)
        ema_small = EMAIndicator(self.series["close"], window_small, fillna=True)
        ema_series_big = ema_big.ema_indicator().round(decimals=2)
        ema_series_small = ema_small.ema_indicator().round(decimals=2)
        ema_dfs = pd.concat([ema_series_big, ema_series_small], axis=1)
        # ema duzgun kolon adiyla geliyor
        return ema_dfs

    def save_model_objects(self):
        print(os.getcwd())
        pickle.dump(self.trader.model, open(self.model_filename, 'wb'))
        pickle.dump(self.trader.sc_X, open(self.scaler_filename, 'wb'))

    def load_model_objects(self):
        model = pickle.load(open(self.model_filename, 'rb'))
        scaler = pickle.load(open(self.scaler_filename, 'rb'))
        self.trader.sc_X = scaler
        self.trader.model = model

    def egitim_sureci_control(self):
        if not self.trader.ilk_egitim:
            self.egit()
            self.trader.ilk_egitim = True
        else:
            self.kismi_egit()

    def karar_hesapla(self, trader):
        self.fiyat_tahmini_hesapla()
        if self.suanki_fiyat * (1 + trader.config.get('mlp_karar_bounding_limit')) < self.fiyat_tahmini:
            self.karar = Karar.alis
        elif self.suanki_fiyat * (1 - trader.config.get('mlp_karar_bounding_limit')) > self.fiyat_tahmini:
            self.karar = Karar.satis
        elif self.suanki_fiyat * (1 + trader.config.get('mlp_cikis_bounding_limit')) > self.fiyat_tahmini > self.suanki_fiyat * (1 - trader.config.get('mlp_cikis_bounding_limit')):
            self.karar = Karar.cikis
        else:
            self.karar = Karar.notr

    def fiyat_tahmini_hesapla(self):
        X_ = self.tahmin_satiri_getir()
        X_transformed = self.trader.sc_X.transform(X_)
        y_pred = self.trader.model.predict(X_transformed)
        self.fiyat_tahmini = float(y_pred[0])

    def kismi_egit(self):
        X_, Y_ = self.kismi_egit_satiri_getir()
        X_trainscaled = self.trader.sc_X.transform(X_)
        self.trader.model = self.trader.model.partial_fit(X_trainscaled, Y_.values.ravel())

    def egit(self):
        X_, Y_ = self.divide_target_and_features()
        X_trainscaled = self.trader.sc_X.fit_transform(X_)
        # TODO:: Y_trainscaled de hesaplanabilir

        self.trader.model = MLPRegressor(
            hidden_layer_sizes=self.trader.config.get("mlp_layers"),
            activation="relu", random_state=self.trader.config.get("mlp_random_state"), max_iter=self.trader.config.get("mlp_max_iter")
        ).fit(X_trainscaled, Y_.values.ravel())

    def kismi_egit_satiri_getir(self):
        X_ = self.series[1:2]
        Y_ = self.series[['close']][0:1].reset_index(drop=True)
        Y_.rename(columns={"close": "target"})
        return X_, Y_

    def tahmin_satiri_getir(self):
        X_ = self.series[0:1]
        return X_

    def divide_target_and_features(self):
        X_ = self.series[1:]
        Y_ = self.series[['close']][:-1].reset_index(drop=True)
        Y_.rename(columns={"close": "target"})
        return X_, Y_