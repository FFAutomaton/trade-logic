from schemas.enums.karar import Karar
from trade_logic.trader import Trader
import pandas as pd


def close_traders(list_of_coins, bitis_gunu):
    for coin in list_of_coins:
        trader = Trader(bitis_gunu, coin, pd.DataFrame())
        trader.yukle(coin)
        trader.karar = Karar.cikis
        trader.borsada_islemleri_hallet()
        trader.kaydet(coin)
        print(f"FFAutomaton --> {coin} trader is closed!! <-- FFAutomaton")
