import pandas as pd
from fredapi import Fred
from config_users import fred_api_key


class FredService:
    def __init__(self):
        self.dfs_to_get = ['DTB3', 'DFF', 'DFEDTARL', 'OBFR']

        self.fred = Fred(api_key=fred_api_key)
        self.dfs = self.get_related_dataframes()
        self.series = self.concat_dfs()
        # res = self.fred.search("expected funds rate").sort_values(by=["popularity"], ascending=False)
        # res2 = self.fred.search("DTB3").sort_values(by=["popularity"], ascending=False)

    def concat_dfs(self):
        df = None
        for i in self.dfs:
            _df = self.dfs[i].sort_index()
            df = _df if df is None else pd.concat([df, _df], axis=1)

        return df.ffill()

    def get_related_dataframes(self):
        dfs = {}
        for i in self.dfs_to_get:
            dfs[i] = self.prep_data(i)
        return dfs

    def prep_data(self, i):
        data = self.fred.get_series(i, observation_start='2018-01-01')
        data = data.fillna(method='ffill')
        return data.resample('H').ffill()


if __name__ == '__main__':
    fred = FredService()


# TODO:: start_date is 2018-01-01 00:00:00
# TODO:: explode to hourly
# TODO:: add latest values to empty dates after api request
# TODO:: add other coin data
# TODO:: add market cap data
# TODO:: add unemployement and that kind of useful data

