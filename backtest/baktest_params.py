import itertools


params = {
    "st_mult_small": [0.3],
    "st_mult_big": [1.5],
    "mlp_rsi_small": [6],
    "mlp_rsi_big": [24],
    "mlp_ema_small": [14],
    "mlp_ema_big": [100],
    "mlp_karar_bounding_limit": [0.005],
    "multiplier_egim_limit": [0.0001],
    "tp_daralt_katsayi": [0.02],
    "ema_window_buyuk": [1200],
    "ema_window_kucuk": [100],
    "rsi_window": [14],
    "sma_window": [35],
    "momentum_egim_hesabi_window": [8],
    "rsi_bounding_limit": [40],
    "ema_bounding_buyuk": [0.01],
    "ema_bounding_kucuk": [0.003],
    "trend_ratio": [0.005],
    "daralt_katsayi": [0.01],
    "training_window": [200],
}


def kartezyen_carp(inp):
    return (dict(zip(inp.keys(), values)) for values in itertools.product(*inp.values()))


opt_confs = kartezyen_carp(params)
