from datetime import datetime
from trade_logic.app import App

if __name__ == '__main__':
    app = App()
    app.mum_verilerini_guncelle()
    app.trader.wallet = app.binance_service.futures_hesap_bakiyesi()
    app.calis()
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
