import math
from datetime import timedelta, datetime, timezone

from trade_logic.traders.super_trend_trailing import SuperTrendDaralanTakip
from trade_logic.traders.super_trader import SuperTrader
from config import *
from turkish_gekko_packages.binance_service import TurkishGekkoBinanceService

from config_users import users
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar


class TraderBase:
    def __init__(self, bitis_gunu, coin, candle_data):
        self.secrets = {"API_KEY": API_KEY, "API_SECRET": API_SECRET}
        self.config = {
            "symbol": coin.replace("USDT", ""), "coin": coin, "supertrend_mult": 3, "wallet": {},
            "tp_daralt_katsayi": 0.01, "inceltme_limit": 0.007, "kaldirac": 1, "inceltme_oran": 0.001
        }
        self.daralt = 0
        self.entryPrice = 0
        self.unRealizedProfit = 0
        self.positionAmt = 0
        self.onceki_pozisyon = Pozisyon(0)
        self.stop_oldu_mu = 0
        self.binance_wallet = None
        self.tp_daralt = 0
        self.secrets.update(self.config)
        self.wallet = None
        self.suanki_fiyat = 0
        self.karar = Karar.notr
        self.pozisyon = Pozisyon.notr  # 0-baslangic, 1 long, -1 short
        self.bitis_gunu = bitis_gunu
        self.binance_service = TurkishGekkoBinanceService(self.secrets)
        self.super_trend_daralan_takip = SuperTrendDaralanTakip(self.config)
        self.super_trader = SuperTrader(self.config)
        if len(candle_data) > 0:
            self.quantityPrecision = int(candle_data["quantityPrecision"][0])
            candle_data.drop('quantityPrecision', axis=1, inplace=True)
            self.series_candle = candle_data

    def fiyat_guncelle(self):
        data = self.series_candle
        self.suanki_fiyat = data.get("close")[len(data) - 1]
        self.super_trend_daralan_takip.suanki_fiyat = self.suanki_fiyat

    def init_prod(self):
        self.binance_wallet = self.binance_service.futures_hesap_bakiyesi()
        position = self.binance_service.get_client().futures_position_information(symbol=self.config.get("coin"))
        amount = position[0]['positionAmt']
        if float(amount) > 0:
            self.pozisyon = Pozisyon(1)
        elif float(amount) < 0:
            self.pozisyon = Pozisyon(-1)
        else:
            self.pozisyon = Pozisyon(0)
        self.entryPrice = float(position[0]['entryPrice'])
        self.unRealizedProfit = float(position[0]['unRealizedProfit'])
        self.positionAmt = float(position[0]['positionAmt'])

    def miktar_hesapla(self):
        return 15

    def kullanicilari_don(self, _taraf=None):
        _exit_, yon, pos, leverage = None, None, None, None
        for user in users:
            user_secrets = users.get(user)
            c = 5
            while c > 0:
                try:
                    _service = TurkishGekkoBinanceService(user_secrets)
                    _exit_, yon = _service.futures_market_exit(self.config.get("coin"))
                    if _taraf:
                        miktar = round(self.miktar_hesapla() / self.suanki_fiyat, self.quantityPrecision)
                        pos, leverage = _service.futures_market_islem(self.config.get("coin"), taraf=_taraf,
                                                                      miktar=miktar, kaldirac=self.config.get("kaldirac"))
                    print(f"{user} - ### ---> {_taraf} {yon} {pos} {_exit_}")
                    c = 0
                except Exception as e:
                    print(f"kullanici donerken hata olustu!!!!!!")
                    print("\n")
                    print(str(e))
                    c -= 1
        return yon

    def borsada_islemleri_hallet(self):
        if self.karar == Karar.alis and self.pozisyon != Pozisyon.long:
            yon = self.kullanicilari_don('BUY')
            self.pozisyon = Pozisyon(1)
        elif self.karar == Karar.satis and self.pozisyon != Pozisyon.short:
            yon = self.kullanicilari_don('SELL')
            self.pozisyon = Pozisyon(-1)
        elif self.karar == Karar.cikis:
            yon = self.kullanicilari_don(None)
            self.stop_oldu_mu = 1
            self.onceki_pozisyon = self.pozisyon
            self.super_trend_daralan_takip.reset_super_trend()

