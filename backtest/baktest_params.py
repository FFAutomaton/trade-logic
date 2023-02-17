import itertools


params = {
    "st_mult_small": [0.1],
    "st_mult_big": [3],
    "mlp_rsi_small": [6],
    "mlp_rsi_big": [24],
    "mlp_ema_small": [14],
    "mlp_ema_big": [100],
    "mlp_karar_bounding_limit": [0.005],
    "mlp_cikis_bounding_limit": [0.0003],
    "multiplier_egim_limit": [0.0001],
    "mlp_max_iter": [5000],
    "mlp_random_state": [1],
    "mlp_layers": [(64, 64, 64, 64)],
    "tp_daralt_katsayi": [0.02],
    "ema_window_buyuk": [400],
    "ema_window_kucuk": [100],
    "rsi_window": [14],
    "sma_window": [81],
    "momentum_egim_hesabi_window": [16],
    "rsi_bounding_limit": [30],
    "ema_bounding_buyuk": [0.01],
    "ema_bounding_kucuk": [0.003],
    "trend_ratio": [0.01],
    "daralt_katsayi": [0.01],
}


def kartezyen_carp(inp):
    return (dict(zip(inp.keys(), values)) for values in itertools.product(*inp.values()))


opt_confs = kartezyen_carp(params)

winner = {
    "st_mult_small": 0.500000,
"st_mult_big": 3.000000,
"mlp_rsi_small": 6.000000,
"mlp_rsi_big": 24.000000,
"mlp_ema_small": 14.000000,
"mlp_ema_big": 100.000000,
"mlp_karar_bounding_limit": 0.005000,
"mlp_cikis_bounding_limit": 0.000300,
"multiplier_egim_limit": 0.000100,
"mlp_max_iter": 5000.000000,
"mlp_random_state": 1.000000,
"tp_daralt_katsayi": 0.020000,
"ema_window_buyuk": 400.000000,
"ema_window_kucuk": 100.000000,
"rsi_window": 14.000000,
"sma_window": 81.000000,
"momentum_egim_hesabi_window": 16.000000,
"rsi_bounding_limit": 30.000000,
"ema_bounding_buyuk": 0.010000,
"ema_bounding_kucuk": 0.003000,
"trend_ratio": 0.010000,
"daralt_katsayi": 0.010000,
}