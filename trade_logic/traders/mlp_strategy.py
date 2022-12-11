import os
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import pandas as pd
import glob
from schemas.enums.karar import Karar
from datetime import datetime, timedelta


class MlpStrategy:
    def __init__(self, config):
        self.config = config
        self.karar = Karar.notr
        self.series = None
        self.model_data = []
        self.bitis_gunu = None
        self.suanki_fiyat = None
        self.ilk_egitim = False
        self.model = None
        self.sc_X = None
        self.fiyat_tahmini = None
        self.window = 10

    def init_strategy(self, trader):
        if not self.sc_X:
            # TODO:: recordd sclaer and load later for production use
            if not trader.standart_scaler:
                trader.standart_scaler = StandardScaler()
            self.sc_X = trader.standart_scaler

        if len(self.model_data) <= 0:
            # TODO:: load from file, append missing hours' rows
            list_of_files = glob.glob("./coindata/mlp_data/*.csv")
            latest_file = max(list_of_files, key=os.path.getctime)
            self.model_data = pd.read_csv(latest_file)

        self.series = self.model_data[self.model_data["open_ts_int"] < int(self.bitis_gunu.timestamp())*1000]
        self.series = self.model_data[self.model_data["open_ts_int"] > int((self.bitis_gunu - timedelta(days=trader.config.get("training_window", 30))).timestamp())*1000]

        if not self.ilk_egitim:
            self.egit()
            self.ilk_egitim = True
        else:
            self.kismi_egit()

    def son_saatin_model_verisini_hazirla(self):
        son_saat = self.bitis_gunu - timedelta(hours=1)

    def karar_hesapla(self, trader):
        self.fiyat_tahmini_hesapla()
        if trader.suanki_fiyat * 1.01 < self.fiyat_tahmini:
            self.karar = Karar.alis
        elif trader.suanki_fiyat * 0.99 > self.fiyat_tahmini:
            self.karar = Karar.satis
        else:
            self.karar = Karar.cikis

    def fiyat_tahmini_hesapla(self):
        X_ = self.tahmin_satiri_getir()
        X_transformed = self.sc_X.transform(X_)
        y_pred = self.model.predict(X_transformed)
        self.fiyat_tahmini = float(y_pred[0])

    def kismi_egit(self):
        X_, Y_ = self.kismi_egit_satiri_getir()
        X_trainscaled = self.sc_X.transform(X_)
        self.model = self.model.partial_fit(X_trainscaled, Y_.values.ravel())
        pass

    def egit(self):
        X_, Y_ = self.divide_target_and_features()
        X_trainscaled = self.sc_X.fit_transform(X_)

        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 64, 64),
            activation="relu", random_state=1, max_iter=3500
        ).fit(X_trainscaled, Y_.values.ravel())

    def kismi_egit_satiri_getir(self):
        X_ = self.series[1:2].drop(columns=["open_ts_int", "open_ts_str"]).reset_index(drop=True)
        Y_ = self.series[['close']][0:1].reset_index(drop=True)
        Y_.rename(columns={"close": "target"})
        return X_, Y_

    def tahmin_satiri_getir(self):
        X_ = self.series[0:1].drop(columns=["open_ts_int", "open_ts_str"]).reset_index(drop=True)
        return X_

    def divide_target_and_features(self):
        X_ = self.series[1:].drop(columns=["open_ts_int", "open_ts_str"]).reset_index(drop=True)
        Y_ = self.series[['close']][:-1].reset_index(drop=True)
        Y_.rename(columns={"close": "target"})
        return X_, Y_

    def model_egit_test(self):
        X_, Y_ = self.divide_target_and_features()
        X_train, X_test, y_train, y_test = train_test_split(X_, Y_, random_state=1, test_size=0.2)
        sc_X = StandardScaler()
        X_trainscaled = sc_X.fit_transform(X_train)
        X_testscaled = sc_X.transform(X_test)
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 64, 64),
            activation="relu", random_state=1, max_iter=2000
        ).fit(X_trainscaled, y_train.values.ravel())
        y_pred = self.model.predict(X_testscaled)
        print("The Score with ", (r2_score(y_pred, y_test)))