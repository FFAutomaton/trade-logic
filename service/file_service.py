import glob
import os
from datetime import timedelta
import pandas as pd
from trade_logic.utils import okunur_date_yap
import json


def list_files_in_folder(bitis_gunu, working_traders, pattern="*"):
    _path = "../ticker-master/data"
    files_in_folder = glob.glob(os.path.join(_path, pattern))
    if len(files_in_folder) == 0:
        return None, None, None
    filehistory = {}

    ts_now = int(bitis_gunu.timestamp()) * 1000
    ts_previous = int((bitis_gunu - timedelta(minutes=5)).timestamp()) * 1000
    current_files_list = [ts_now, ts_previous]
    for file_name in files_in_folder:
        name = file_name.split('/')[-1]
        parsed_name = name.split('_')
        ts = parsed_name[0]
        coin = parsed_name[-1]
        if int(ts) not in current_files_list:
            os.remove(file_name)
            continue
        if not filehistory.get(ts):
            filehistory[ts] = [coin]
        else:
            filehistory[ts].append(coin)

    dataframes = load_dataframes(filehistory, files_in_folder)

    new_ones = filehistory.get(str(ts_now), [])
    new_ones = list(set(new_ones) - set(working_traders))
    print(f"FFAutomaton --> new traders {new_ones} !! <-- FFAutomaton")
    old_ones = filehistory.get(str(ts_previous), [])
    working_traders = list(set(working_traders) + set(new_ones))
    return new_ones, working_traders, dataframes


def load_dataframes(file_history, files_in_folder):
    max = 0
    for key in file_history:
        if int(key) > max:
            max = int(key)

    dataframe_files = [filename for filename in files_in_folder if str(max) in filename]

    dataframes = {}
    for i in dataframe_files:
        df_tmp = pd.read_csv(f"./{i}")
        df_tmp["insan_icin_saat"] = df_tmp["open_ts"].apply(okunur_date_yap)
        df_tmp["quantityPrecision"] = i.split('_')[-2]
        dataframes[i.split('_')[-1]] = df_tmp

    return dataframes


def write_already_working(working_traders):
    with open(f"../ticker-master/working_traders.json", "w") as write_file:
        json.dump(working_traders, write_file)