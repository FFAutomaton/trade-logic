import pandas as pd
import sqlite3


class SqlLite_Service:
    def __init__(self, _config):
        self.conn = None
        self.conn = self.get_conn(_config.get("coin"))
        self._tablo_yoksa_olustur(_config)

    def get_conn(self, db_name):
        if self.conn:
            return self.conn
        self.conn = sqlite3.connect(f'./coindata/{db_name}.db')
        return self.conn

    def _tablo_yoksa_olustur(self, _conf):
        tip = _conf.get('pencere')
        swing_tip = _conf.get('swing_pencere')
        coin = _conf.get('coin')
        candles = f'{coin}_{tip}'
        swing_candles = f'{coin}_{swing_tip}'
        islemler = f'islemler_{coin}_{tip}'
        prophet_tahminler = f'prophet_{coin}_{tip}'
        self.get_conn().cursor().execute(f"""CREATE TABLE IF NOT EXISTS {candles}(
              open_ts INTEGER PRIMARY KEY, open REAL,
              high REAL, low REAL, close REAL, volume REAL);""")
        self.get_conn().cursor().execute(f"""CREATE TABLE IF NOT EXISTS {swing_candles}(
                      open_ts INTEGER PRIMARY KEY, open REAL,
                      high REAL, low REAL, close REAL, volume REAL);""")
        self.get_conn().cursor().execute(f"""CREATE TABLE IF NOT EXISTS {islemler}(
              ds INTEGER PRIMARY KEY, open REAL,
              high REAL, low REAL, alis REAL, 
              satis REAL, eth REAL, usdt REAL, neden TEXT);""")
        self.get_conn().cursor().execute(f"""CREATE TABLE IF NOT EXISTS {prophet_tahminler}(
                      ds INTEGER PRIMARY KEY,
                      high REAL, low REAL, open REAL);""")
        self.get_conn().commit()

    def mum_datasi_yukle(self, _conf, prophet_service, baslangic_gunu, bitis_gunu):
        tip = _conf.get('pencere')
        coin = _conf.get('coin')
        if self.veri_var_mi(f'{coin}_{tip}', baslangic_gunu, bitis_gunu):
            print('data zaten var pas geciyor')
            pass
        else:
            data = prophet_service.tg_binance_service.get_client().get_historical_klines(
                symbol=coin, interval=tip,
                start_str=str(int(baslangic_gunu)), end_str=str(int(bitis_gunu)), limit=500
            )
            self.mum_verisi_yukle(f'{coin}_{tip}', data)
            print(f'API-dan yukleme tamamlandi {coin}_{tip} {str(baslangic_gunu)} {str(bitis_gunu)}')

    def veri_listesi_olustur(self, tempdata):
        data = []
        i = len(tempdata) - 1
        while i >= 0:
            row = (
                int(tempdata[i][0] / 1000),
                float(tempdata[i][1]),
                float(tempdata[i][2]),
                float(tempdata[i][3]),
                float(tempdata[i][4]),
                float(tempdata[i][5])
            )
            data.append(row)

            i = i - 1
        return data

    def mum_verisi_yukle(self, tablo, data):
        data = self.veri_listesi_olustur(data)
        self.get_conn().cursor().executemany\
            (f"""INSERT INTO {tablo} VALUES(?, ?, ?, ?, ?, ?);""", data)
        self.get_conn().commit()

    def mum_verisi_getir(self, _conf, baslangic, bitis):
        coin = _conf.get('coin')
        tip = _conf.get('pencere')
        curr = self.get_conn().cursor().execute(f"""SELECT * FROM {f'{coin}_{tip}'}
                    WHERE open_ts >= {int(baslangic)} and open_ts < {int(bitis)}
                """)

        data = curr.fetchall()
        main_dataframe = pd.DataFrame(data, columns=["open_ts", "open", "high", "low", "close", "volume"])

        # main_dataframe['open_ts'] = main_dataframe[["open_ts"]].apply(pd.to_datetime)
        main_dataframe = main_dataframe.sort_values(by='open_ts', ascending=False, ignore_index=True)
        # main_dataframe = main_dataframe[main_dataframe['Open Time'] < baslangic].reset_index(drop=True)
        # main_dataframe = main_dataframe.iloc[0:200]
        print('mum datasi yuklendi!')
        return main_dataframe
