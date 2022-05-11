import traceback
import requests
from config import bambam_url, long_buy, long_buy_close, short_buy, short_buy_close


def bam_bama_sinyal_gonder(islem, yon):
    try:
        resp = None
        header = headers = {'Content-type': 'application/json'}
        if islem["alis"] > 0:
            resp = requests.post(bambam_url, json=long_buy, headers=header)

        elif islem["satis"] > 0:
            resp = requests.post(bambam_url, json=short_buy, headers=header)

        elif islem["cikis"] > 0:
            if yon > 0:
                resp = requests.post(bambam_url, json=long_buy_close, headers=header)
            else:
                resp = requests.post(bambam_url, json=short_buy_close, headers=header)

        return resp
    except Exception as e:
        traceback.print_exc()
        raise e