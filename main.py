from datetime import datetime
from trade_logic.app import App


if __name__ == '__main__':
    app = App()
    app.mum_verilerini_guncelle()
    app.config["wallet"] = app.prophet_service.tg_binance_service.balance_founder()
    app.calis()
    # TODO:: Wallet cekip confige ekle (blocker: futures api baglantisi)
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
