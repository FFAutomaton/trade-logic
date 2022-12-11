from datetime import datetime, timedelta, timezone
import pandas as pd
from trade_logic.trader import Trader
from trade_logic.traders.mlp_strategy import MlpStrategy


def transpose_as_features(self, series):
    if not self.series:
        self.series = pd.read_csv(f"./coindata/mlp_data/all.csv", header=True)
        self.series = pd.to_datetime(self.series["open_ts_str"], format='%Y-%m-%d %H:%M:%S')
        # self.series = self.series[
        #     self.series[schema[0]['name']] < int(baslangic.timestamp()) * 1000].reset_index(drop=True)

    if self.bitis_gunu - timedelta(hours=1) in self.series["open_ts_str"].values:
        self.model_data = self.series[
            self.series["open_ts_int"] < int(self.bitis_gunu.timestamp()) * 1000
            ].reset_index(drop=True)
    else:
        self.son_saatin_model_verisini_hazirla()


def model_verisi_hazirla(trader, baslangic, bitis):
    mlp_strategy = MlpStrategy(trader.config)
    trader.series_1h = trader.sqlite_service.veri_getir(
        trader.config.get("coin"), trader.config.get("pencere_1h"), "mum",
        baslangic, bitis
    ).sort_values(by='open_ts_int', ascending=True).reset_index(drop=True)
    length = len(trader.series_1h)
    start = 0 + mlp_strategy.window
    pin = 0
    new_series = []
    while start < length:
        main_row = trader.series_1h[start:start+1]
        rows_to_transpose = trader.series_1h[pin:start]
        rows_to_transpose = rows_to_transpose[["open", "high", "low", "volume"]]
        for i in range(0, len(rows_to_transpose)):
            main_row = pd.concat(
                [main_row.reset_index(drop=True), rows_to_transpose[i:i + 1].reset_index(drop=True)], axis=1
            )
        if len(new_series) == 0:
            new_series = main_row
        else:
            new_series = main_row.append(new_series, ignore_index=True)
        pin += 1
        start += 1

        print(f"{length - start} remaining")

    new_series.to_csv(f"../coindata/mlp_data/{datetime.strftime(bitis, '%Y-%m-%d-%H')}.csv", index=False)


if __name__ == '__main__':
    baslangic = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    bitis = datetime.strptime('2022-12-11 11:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    trader = Trader(bitis)
    model_verisi_hazirla(trader, baslangic, bitis)