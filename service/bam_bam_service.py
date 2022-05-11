import traceback
import requests
from config import bambam_url, long_buy, long_buy_close, short_buy, short_buy_close


def bam_bama_sinyal_gonder(islem, yon):
    try:
        resp = None
        if islem["alis"] > 0:
            resp = requests.post(bambam_url, data=long_buy)

        elif islem["satis"] > 0:
            resp = requests.post(bambam_url, data=short_buy)

        elif islem["cikis"] > 0:
            if yon > 0:
                resp = requests.post(bambam_url, data=long_buy_close)
            else:
                resp = requests.post(bambam_url, data=short_buy_close)

        return resp
    except Exception as e:
        traceback.print_exc()
        raise e