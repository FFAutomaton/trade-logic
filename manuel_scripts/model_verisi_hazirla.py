from datetime import datetime, timedelta, timezone
import os
from trade_logic.trader import Trader
from trade_logic.traders.mlp_strategy import MlpStrategy


def model_verisi_hazirla(trader, baslangic, bitis):
    mlp_strategy = MlpStrategy(trader.config)
    mlp_strategy.init_strategy(trader)
    trader.series_1h = trader.sqlite_service.veri_getir(
        trader.config.get("coin"), trader.config.get("pencere_1h"), "mum",
        baslangic, bitis
    ).sort_values(by='open_ts_int', ascending=True).reset_index(drop=True)
    new_series = mlp_strategy.prepare_matrix(trader.series_1h)
    return new_series


if __name__ == '__main__':
    os.environ["PYTHON_ENV"] = "RESET_MLP"
    baslangic = datetime.strptime('2021-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    bitis = datetime.strptime('2022-12-25 12:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    trader = Trader(bitis)
    model_series = model_verisi_hazirla(trader, baslangic, bitis)
    model_series.to_csv(f"../coindata/mlp_data/{datetime.strftime(bitis, '%Y-%m-%d-%H')}.csv", index=False)