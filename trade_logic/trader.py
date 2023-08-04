import os
import json
from schemas.enums.pozisyon import Pozisyon
from schemas.enums.karar import Karar
from trade_logic.trader_base import TraderBase


class Trader(TraderBase):
    def karar_calis(self):
        if self.karar == Karar.cikis:
            return

        if self.super_trader.karar == Karar.alis:
            self.karar = Karar.alis

        if self.super_trader.karar == Karar.satis:
            self.karar = Karar.satis

    def kaydet(self, coin):
        kayit_dict = {}
        kayit_dict["onceki_pozisyon"] = self.onceki_pozisyon.value
        kayit_dict["stop_oldu_mu"] = self.stop_oldu_mu
        kayit_dict["tp"] = self.super_trend_daralan_takip.tp
        kayit_dict["onceki_tp"] = self.super_trend_daralan_takip.onceki_tp
        kayit_dict["entryPrice"] = float(self.entryPrice)
        kayit_dict["unRealizedProfit"] = float(self.unRealizedProfit)
        kayit_dict["positionAmt"] = float(self.positionAmt)

        with open(f"./data/{coin}.json", "w") as write_file:
            json.dump(kayit_dict, write_file)

    def yukle(self, coin):
        try:
            with open(f"./data/{coin}.json", "r") as read_file:
                data = json.load(read_file)
            self.onceki_pozisyon = Pozisyon(int(data["onceki_pozisyon"]))
            self.stop_oldu_mu = int(data["stop_oldu_mu"])
            self.super_trend_daralan_takip.onceki_tp = data["onceki_tp"]
        except Exception as e:
            print(f"FFAutomaton --> {coin} trader is running for the first time, can't load!! <-- FFAutomaton")
