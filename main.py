from datetime import datetime
from trade_logic.app import App

if __name__ == '__main__':
    app = App()
    app.mum_verilerini_guncelle()

    app.calis()
    # TODO:: uygulama patlarsa hatayi e-posta ile gonder
