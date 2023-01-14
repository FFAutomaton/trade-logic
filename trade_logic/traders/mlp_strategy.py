import os
import pickle
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from trade_logic.utils import bitis_gunu_truncate_hour_precision
import pandas as pd
import glob
from schemas.enums.karar import Karar
from datetime import datetime, timedelta


class MlpStrategy:
    def __init__(self, config):
        self.config = config
        self.karar = Karar.notr
        self.series = None
        self.model_data = None
        self.bitis_gunu = None
        self.suanki_fiyat = None
        self.ilk_egitim = False
        self.model = None
        self.fiyat_tahmini = None
        self.window = 15
        self.trader = None
        self.model_egit = False
        self.model_filename = '../coindata/mlp_objects/final_model.sav' if os.getenv("PYTHON_ENV") == "RESET_MLP" else '../../coindata/mlp_objects/final_model.sav'
        self.scaler_filename = '../coindata/mlp_objects/final_scaler.sav' if os.getenv("PYTHON_ENV") == "RESET_MLP" else '../../coindata/mlp_objects/final_scaler.sav'

    def init_strategy(self, trader):
        self.trader = trader
        self.bitis_gunu = trader.bitis_gunu
        self.load_model_data()
        if os.getenv("PYTHON_ENV") == "TEST":
            if not self.trader.sc_X:
                self.trader.sc_X = StandardScaler()
            self.series = self.series[self.series["open_ts_int"] > int((self.bitis_gunu - timedelta(days=trader.config.get("training_window", 30))).timestamp())*1000]
            self.egitim_sureci_control()
        elif os.getenv("PYTHON_ENV") == "RESET_MLP":
            if not self.trader.sc_X:
                self.trader.sc_X = StandardScaler()
            self.egit()
            self.save_model_objects()
        else:
            self.load_model_objects()
            self.kismi_egit()
            self.save_model_objects()

    def load_model_data(self):
        missing_df2 = None
        bitis = bitis_gunu_truncate_hour_precision(datetime.utcnow(), 1)
        path = "./coindata/mlp_data/" if os.getenv("PYTHON_ENV") != "RESET_MLP" else "../coindata/mlp_data/"
        if self.model_data:  # not to load again in backtest mode
            return
        list_of_files = glob.glob(f"{path}*.csv") if os.getenv("PYTHON_ENV") != "RESET_MLP" else glob.glob(f"{path}*.csv")
        if len(list_of_files) > 0:
            latest_file = max(list_of_files, key=os.path.getctime)
            for file in list_of_files:
                if file != latest_file:
                    os.remove(file)
            self.model_data = pd.read_csv(latest_file)
            self.model_data["open_ts_str"] = pd.to_datetime(self.model_data["open_ts_str"], format='%Y-%m-%d %H:%M:%S')
            self.model_data = self.model_data.sort_values(by="open_ts_str", ascending=True).reset_index(drop=True)

            missing_df2 = self.get_missing_dates_df(max(self.model_data["open_ts_str"]), bitis)
        else:
            missing_df2 = self.trader.series_1h

        missing_df = self.prepare_matrix(missing_df2)
        self.model_data = missing_df if not len(self.model_data) > 0 else self.model_data.append(missing_df).sort_values("open_ts_str", ascending=False)
        if os.getenv("DEBUG") == "1" or os.getenv("PYTHON_ENV") != "TEST":
            self.model_data.to_csv(f"{path}{datetime.strftime(bitis, '%Y-%m-%d-%H')}.csv", index=False)
        self.series = self.model_data[self.model_data["open_ts_int"] < int(self.bitis_gunu.timestamp()) * 1000]

    def save_model_objects(self):
        print(os.getcwd())
        pickle.dump(self.model, open(self.model_filename, 'wb'))
        pickle.dump(self.trader.sc_X, open(self.scaler_filename, 'wb'))

    def load_model_objects(self):
        model = pickle.load(open(self.model_filename, 'rb'))
        scaler = pickle.load(open(self.scaler_filename, 'rb'))
        self.trader.sc_X = scaler
        self.model = model

    def egitim_sureci_control(self):
        if not self.ilk_egitim:
            self.egit()
            self.ilk_egitim = True
        else:
            self.kismi_egit()

    def prepare_matrix(self, series):
        length = len(series)
        start = 0 + self.window
        pin = 0
        new_series = []
        while start < length:
            main_row = series[start:start + 1]
            rows_to_transpose = series[pin:start]
            # rows_to_transpose = rows_to_transpose[["open", "high", "low", "volume"]]
            rows_to_transpose = rows_to_transpose[["open","close", "volume"]]
            for i in range(0, len(rows_to_transpose)):
                xxx = rows_to_transpose[i:i + 1].rename(columns={
                    # "open": f"open{i}", "high": f"high{i}", "low": f"low{i}", "volume": f"volume{i}"
                    "open": f"open{i}", "close": f"close{i}", "volume": f"volume{i}"
                })
                main_row = pd.concat(
                    [main_row.reset_index(drop=True), xxx.reset_index(drop=True)], axis=1
                )
            if len(new_series) == 0:
                new_series = main_row
            else:
                new_series = main_row.append(new_series, ignore_index=True)
            pin += 1
            start += 1

            print(f"{length - start} remaining")

        return new_series

    def get_missing_dates_df(self, max_date, bitis):
        return self.trader.sqlite_service.veri_getir(
            self.trader.config.get("coin"), self.trader.config.get("pencere_1h"), "mum",
            max_date-timedelta(hours=self.window), bitis
        ).sort_values(by='open_ts_int', ascending=True)

    def karar_hesapla(self, trader):
        self.fiyat_tahmini_hesapla()
        if trader.suanki_fiyat * (1 + trader.config.get('mlp_karar_bounding_limit')) < self.fiyat_tahmini:
            self.karar = Karar.alis
        elif trader.suanki_fiyat * (1 - trader.config.get('mlp_karar_bounding_limit')) > self.fiyat_tahmini:
            self.karar = Karar.satis
        else:
            self.karar = Karar.cikis

    def fiyat_tahmini_hesapla(self):
        X_ = self.tahmin_satiri_getir()
        X_transformed = self.trader.sc_X.transform(X_)
        y_pred = self.model.predict(X_transformed)
        self.fiyat_tahmini = float(y_pred[0])

    def kismi_egit(self):
        X_, Y_ = self.kismi_egit_satiri_getir()
        X_trainscaled = self.trader.sc_X.transform(X_)
        self.model = self.model.partial_fit(X_trainscaled, Y_.values.ravel())
        pass

    def egit(self):
        X_, Y_ = self.divide_target_and_features()
        X_trainscaled = self.trader.sc_X.fit_transform(X_)

        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 64, 64, 64),
            activation="relu", random_state=1, max_iter=10000
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
