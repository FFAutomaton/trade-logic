import os
import traceback
import json
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
from trade_logic.utils import okunur_date_yap
from schemas import *
from trade_logic.utils import integer_date_yap
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class SqlLite_Service:
    def __init__(self, _config):
        self.conn = None
        self._config = _config
        self.db = _config.get("coin")
        self.conn = self.get_conn()
        self._tablo_yoksa_olustur()

    def get_conn(self):
        if self.conn:
            return self.conn
        if os.getenv("PYTHON_ENV") == "TEST":
            self.conn = sqlite3.connect(f'./coindata/{self.db}.db')
        elif os.getenv("PYTHON_ENV") == "BACKFILL":
            self.conn = sqlite3.connect(f'../coindata/{self.db}.db')
        else:
            self.conn = sqlite3.connect(f'/app/coindata/{self.db}.db')
        return self.conn

    def schemayi_query_texte_cevir(self, schema):
        _query = []
        for el in schema:
            _query.append(f'{el["name"]} {el["type"]} {el["primary"]}')

        return ', '.join(_query)

    def _tablo_yoksa_olustur(self):
        _1h = self._config.get('pencere_1h')
        _15m = self._config.get('pencere_15m')
        candle_tables = [_15m, _1h]
        coin = self._config.get('coin')
        islemler = f'islemler_{coin}_{_15m}'
        trader = f'trader_{coin}_{_15m}'

        for table in candle_tables:
            self.get_conn().cursor().execute(
                f'CREATE TABLE IF NOT EXISTS {coin}_{table}({self.schemayi_query_texte_cevir(mum_schema)});'
            )

        self.get_conn().cursor().execute(
            f'CREATE TABLE IF NOT EXISTS {islemler}({self.schemayi_query_texte_cevir(islem_schema)});'
        )
        self.get_conn().cursor().execute(
            f'CREATE TABLE IF NOT EXISTS {trader}({self.schemayi_query_texte_cevir(trader_schema)});'
        )
        self.get_conn().commit()

    def mum_datasi_yukle(self, tip, binance_service, baslangic_gunu, bitis_gunu):
        coin = self._config.get('coin')
        data = binance_service.get_client().get_historical_klines(
            symbol=coin, interval=tip,
            start_str=str(baslangic_gunu), end_str=str(bitis_gunu), limit=500
        )
        data = self.veri_listesi_olustur(data)
        _query = f"""INSERT INTO {f'{coin}_{tip}'} {self.values_ifadesi_olustur(mum_schema)}
                ON CONFLICT({mum_schema[0]["name"]}) {self.update_ifadesi_olustur(mum_schema)};"""

        self.get_conn().cursor().executemany(_query, data)
        self.get_conn().commit()
        return data

    @staticmethod
    def veri_listesi_olustur(tempdata):
        data = []
        for i in range(len(tempdata)):
            row = (int(tempdata[i][0]), okunur_date_yap(tempdata[i][0]), float(tempdata[i][1]),
                   float(tempdata[i][2]), float(tempdata[i][3]),
                   float(tempdata[i][4]), float(tempdata[i][5])
                   )
            data.append(row)
        return data

    @staticmethod
    def values_ifadesi_olustur(_schema):
        soru_isaretleri = ', '.join("?" for el in _schema)
        return f"VALUES({soru_isaretleri})"

    @staticmethod
    def update_ifadesi_olustur(_schema):
        guncelle = ', '.join(f'{el["name"]}=excluded.{el["name"]}' for el in _schema)
        return f"DO UPDATE SET {guncelle}"

    def veri_yaz(self, data, _type):
        coin = self._config.get('coin')
        tip = self._config.get('pencere_15m')
        schema = None

        if _type == "islem":
            _query = f"""INSERT INTO islemler_{coin}_{tip} {self.values_ifadesi_olustur(islem_schema)}
                            ON CONFLICT({islem_schema[0]["name"]}) {self.update_ifadesi_olustur(islem_schema)};"""
            schema = islem_schema
        elif _type == "trader":
            _query = f"""INSERT INTO trader_{coin}_{tip} {self.values_ifadesi_olustur(trader_schema)}
                            ON CONFLICT({trader_schema[0]["name"]}) {self.update_ifadesi_olustur(trader_schema)};"""
            schema = trader_schema

        data = self.schemadan_data_olustur(data, schema)
        try:
            self.get_conn().cursor().executemany(_query, [data])
            self.get_conn().commit()
        except:
            traceback.print_exc()

    def schemadan_data_olustur(self, data, schema):
        res = []
        [str(el) for el in data.values()]
        for i, el in enumerate(schema):
            if i == 0:
                res.append(str(integer_date_yap(data['ds_str'])))
            else:
                res.append(data.get(el.get("name")))

        return res

    def islemleri_temizle(self):
        coin = self._config.get('coin')
        tip = self._config.get('pencere_15m')
        _query = f"DELETE FROM islemler_{coin}_{tip};"
        self.get_conn().cursor().execute(_query)
        self.get_conn().commit()

    def veri_getir(self, coin, pencere, _type, baslangic=None, bitis=None):
        # zaman serisi ---> (baslangic=2022-01-01, ......, bitis=2022-05-25)
        schema = None
        if _type == 'mum':
            query = f"""SELECT * FROM {f'{coin}_{pencere}'}
                    WHERE open_ts_int < {int(bitis.timestamp())*1000}
                    and open_ts_int > {int(baslangic.timestamp())*1000}"""
            schema = mum_schema
        elif _type == 'islem':
            query = f"""SELECT * FROM islemler_{coin}_{pencere}"""
            schema = islem_schema
        elif _type == 'trader':
            query = f"""SELECT * FROM trader_{coin}_{pencere} order by ds_int desc limit 1"""
            schema = trader_schema
        curr = self.get_conn().cursor().execute(query)
        data = curr.fetchall()
        main_dataframe = pd.DataFrame(data, columns=[el["name"] for el in schema])
        main_dataframe[schema[1]['name']] = pd.to_datetime(main_dataframe[schema[1]['name']], format='%Y-%m-%d %H:%M:%S')
        main_dataframe = main_dataframe.sort_values(by=schema[0]['name'], ascending=False, ignore_index=True)

        # print(f'{_type} datasi yuklendi! {baslangic}   {bitis}')
        return main_dataframe

    def trader_durumu_kaydet(self, trader):
        _trader = {}
        _kaydedilecek = ["islem_miktari", "islem_fiyati", "karar", "onceki_karar",
                         "pozisyon", "suanki_fiyat", "ema_ucustaydi", "cooldown", "daralt"]

        for key in _kaydedilecek:
            if hasattr(getattr(trader, key), "value"):
                _trader[key] = getattr(trader, key).value
            else:
                _val = getattr(trader, key)
                _val = round(_val, 2) if isinstance(_val, float) else _val
                _trader[key] = _val
        _trader["onceki_tp"] = round(float(trader.super_trend_strategy.onceki_tp), 2)
        _trader["bitis_gunu"] = datetime.strftime(trader.bitis_gunu, "%Y-%m-%d %H:%M:%S")
        _trader["current_config"] = json.dumps(trader.config)
        karar_params = {
            "ema_value_big": trader.rsi_strategy_1h.ema_value_big,
            "ema_value_small": trader.rsi_strategy_1h.ema_value_small,
            "rsi_value": trader.rsi_strategy_1h.rsi_value,
            "tavan_yapti": trader.rsi_strategy_1h.tavan_yapti,
            "dipten_dondu": int(trader.rsi_strategy_1h.dipten_dondu),
            "tavandan_dondu": int(trader.rsi_strategy_1h.tavandan_dondu),

        }
        tahmin_params = {
            "rsi_smasi_trend": trader.rsi_strategy_1h.rsi_smasi_trend.value,
            "trend_ratio": trader.rsi_strategy_1h.trend_ratio,
            "prev_rsi_emasi": trader.rsi_strategy_1h.prev_rsi_emasi,
            "rsi_emasi_value": trader.rsi_strategy_1h.rsi_emasi_value,
        }
        data = {
            "ds_str": okunur_date_yap(datetime.now().timestamp()*1000),
            "config": json.dumps(_trader),
            "tahmin": json.dumps(tahmin_params),
            "karar_params": json.dumps(karar_params)
        }
        self.veri_yaz(data, "trader")

    def trader_durumu_geri_yukle(self, trader):
        _trader = self.veri_getir(trader.config.get("coin"), trader.config.get("pencere_15m"), "trader")
        _oncekiler = ["karar", "pozisyon"]
        if not _trader.empty:
            conf_ = json.loads(_trader.config[0])
            for key in _oncekiler:
                if key == "karar":
                    trader.onceki_karar = Karar(conf_[key])
                elif key == "pozisyon":
                    trader.pozisyon = Pozisyon(conf_[key])
            trader.super_trend_strategy.onceki_tp = conf_.get("onceki_tp")
            trader.islem_fiyati = conf_.get("islem_fiyati")
            trader.islem_miktari = conf_.get("islem_miktari")
            trader.ema_ucustaydi = conf_.get("ema_ucustaydi")
            trader.cooldown = conf_.get("cooldown")
            trader.daralt = conf_.get("daralt")

    def trader_eski_verileri_temizle(self, bitis_gunu):
        _limit = bitis_gunu - timedelta(days=10)
        coin = self._config.get('coin')
        tip = self._config.get('pencere_15m')
        _query = f'DELETE FROM trader_{coin}_{tip} ' \
                 f'WHERE date(ds_str) < "{datetime.strftime(_limit, "%Y-%m-%d")}";'
        self.get_conn().cursor().execute(_query)
        self.get_conn().commit()
