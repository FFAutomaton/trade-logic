import pandas as pd
from datetime import datetime, timedelta, timezone
# import tensorflow as tf
from tensorflow import keras

import os
from trade_logic.trader import Trader
from keras_utils.veri_gozlem_fonksiyonlari import *
from keras_utils.veri_hazirlama_fonksiyonlari import *


def trader_classi_ile_veri_yukle():
    os.environ["PYTHON_ENV"] = "TEST"
    os.environ["DEBUG"] = "1"

    end_date = datetime.strptime('2023-04-22 00:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    trader = Trader(end_date)
    ic_df = trader.sqlite_service.veri_getir(
                "ETHUSDT", "1h", "mum",
                end_date - timedelta(days=800), end_date
    ).sort_values(by='open_ts_int', ascending=True)
    return ic_df

df = trader_classi_ile_veri_yukle()
titles = ["open_ts_int", "open_ts_str", "open", "high", "low", "close", "volume"]
feature_keys = ["open_ts_int", "open_ts_str", "open", "high", "low", "close", "volume"]
colors = ["blue","orange","green","red","purple","brown","pink"]
date_time_key = "open_ts_str"
# show_raw_visualization(df, feature_keys, colors, titles, date_time_key)
# show_heatmap(df)
split_fraction = 0.715
train_split = int(split_fraction * int(df.shape[0]))
step = 6

past = 720
future = 72
learning_rate = 0.001
batch_size = 256
epochs = 100

feature_list_index = [3, 4, 5, 6]
print("The selected parameters are:", ", ".join([titles[i] for i in feature_list_index]),)


selected_features = [feature_keys[i] for i in feature_list_index]
features = df[selected_features]
features.index = df[date_time_key]

features = normalize(features.values, train_split)
features = pd.DataFrame(features)


train_data = features.loc[0 : train_split - 1]
val_data = features.loc[train_split:]

start = past + future
end = start + train_split

x_train = train_data[[i for i in range(len(feature_list_index))]].values
y_train = features.iloc[start:end][[1]]
sequence_length = int(past / step)
dataset_train = keras.preprocessing.timeseries_dataset_from_array(
    x_train,
    y_train,
    sequence_length=sequence_length,
    sampling_rate=step,
    batch_size=batch_size,
)

x_end = len(val_data) - past - future
label_start = train_split + past + future
x_val = val_data.iloc[:x_end][[i for i in range(len(feature_list_index))]].values
y_val = features.iloc[label_start:][[1]]
dataset_val = keras.preprocessing.timeseries_dataset_from_array(
    x_val,
    y_val,
    sequence_length=sequence_length,
    sampling_rate=step,
    batch_size=batch_size,
)

for batch in dataset_train.take(1):
    inputs, targets = batch

print("Input shape:", inputs.numpy().shape)
print("Target shape:", targets.numpy().shape)

inputs = keras.layers.Input(shape=(inputs.shape[1], inputs.shape[2]))
lstm_out = keras.layers.LSTM(32)(inputs)
outputs = keras.layers.Dense(1)(lstm_out)

model = keras.Model(inputs=inputs, outputs=outputs)
model.compile(optimizer=keras.optimizers.Adam(learning_rate=learning_rate), loss="mse")
model.summary()

path_checkpoint = "model_checkpoint.h5"
es_callback = keras.callbacks.EarlyStopping(monitor="val_loss", min_delta=0, patience=5)

modelckpt_callback = keras.callbacks.ModelCheckpoint(
    monitor="val_loss",
    filepath=path_checkpoint,
    verbose=1,
    save_weights_only=True,
    save_best_only=True,
)

history = model.fit(
    dataset_train,
    epochs=epochs,
    validation_data=dataset_val,
    callbacks=[es_callback, modelckpt_callback],
)


# visualize_loss(history, "Training and Validation Loss")

for x, y in dataset_val.take(5):
    show_plot(
        [x[0][:, 1].numpy(), y[0].numpy(), model.predict(x)[0]],
        12,
        "Single Step Prediction",
    )

# tahminleri gosterme de calisti
# simdi 10 tur egitip tahminlerine bakalim
# bu arada bunu nasil paketleyip canlida kullanacagimizi da calistirmamiz lazim,
# bizim backtest sisteminde bu tarz bir model egitimi ve testi gunler surebilir, burda farkli bir makine gerekecek
# Simdi bunu biraz daha zorlayalim
# bu modeli kaydedip sonrasinda bizim bota entegre etmek gerekeck o kismi da daha sonra yapariz, biraz yoruldum
# gorusmek uzere :D