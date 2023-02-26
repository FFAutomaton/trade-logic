import pandas as pd
from fredapi import Fred
from datetime import datetime
from trade_logic.utils import bitis_gunu_truncate_hour_precision


class FredService:
    def __init__(self, secrets):
        self.dfs_to_get = ['DTB3', 'DFF', 'DFEDTARL', 'OBFR']
        self.fred = Fred(api_key=secrets.get("FED_KEY"))

        # res = self.fred.search("expected funds rate").sort_values(by=["popularity"], ascending=False)
        # res2 = self.fred.search("DTB3").sort_values(by=["popularity"], ascending=False)

    def yeni_datalari_getir(self, baslangic):
        dfs = self.get_related_dataframes(baslangic)
        series = self.concat_dfs(dfs)
        return series

    def get_related_dataframes(self, baslangic):
        dfs = {}
        for i in self.dfs_to_get:
            dfs[i] = self.prep_data(i, baslangic)
        return dfs

    def prep_data(self, i, baslangic):
        data = self.fred.get_series(i, observation_start=baslangic)
        _now = bitis_gunu_truncate_hour_precision(datetime.utcnow(), 1)
        _now = datetime.strftime(_now, "%Y-%m-%d %H:%M:%S")
        ts = pd.to_datetime(_now, format="%Y-%m-%d %H:%M:%S")
        new_row = pd.Series([data.iloc[-1]], index=[ts])
        data = pd.concat([data, new_row], ignore_index=False)
        data = data.fillna(method='ffill')
        return data.resample('H').ffill()

    @staticmethod
    def concat_dfs(dfs):
        df = None
        for i in dfs:
            _df = dfs[i].sort_index()
            _df = _df.reset_index(name=i)
            df = _df if df is None else pd.merge(df, _df,  on='index', how='inner')

        return df.ffill()


if __name__ == '__main__':
    fred = FredService()