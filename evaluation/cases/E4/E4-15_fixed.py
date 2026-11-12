"""E4-15: Load forecasting. One-step forecasts from the smoothed recent load beat climatology (test-half MSE ratio below 0.8)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N, BURN_IN = 300, 50
PHI = 0.7
RATIO_MAX = 0.8
ALPHA = 0.05


def make_world(phi):
    def generate(rng):
        e = rng.standard_normal(N + BURN_IN)
        x = np.empty(N + BURN_IN)
        x[0] = e[0]
        for i in range(1, x.size):
            x[i] = phi * x[i - 1] + e[i]
        return {"x": x[BURN_IN:]}
    return generate


def smooth3(x):
    s = np.full(x.size, np.nan)
    s[2:] = (x[:-2] + x[1:-1] + x[2:]) / 3.0      # trailing: s[i] uses x[i-2], x[i-1], x[i]
    return s


def beats_climatology(d):
    x = d["x"]
    s = smooth3(x)
    inputs, targets = s[2:-1], x[3:]              # forecast x[i] from s[i-1]
    half = targets.size // 2
    with np.errstate(all="ignore"):
        mu_s, mu_x = inputs[:half].mean(), targets[:half].mean()
        k = np.sum((inputs[:half] - mu_s) * (targets[:half] - mu_x)) / np.sum((inputs[:half] - mu_s) ** 2)
        forecast = mu_x + k * (inputs[half:] - mu_s)
        mse = np.mean((targets[half:] - forecast) ** 2)
        mse_clim = np.mean((targets[half:] - mu_x) ** 2)
        return bool(mse / mse_clim < RATIO_MAX)


def shuffle_time(d, rng):
    return {"x": rng.permutation(d["x"])}


STUDY = Study(
    name="E4-15 load forecasting skill",
    criteria=[Criterion("beats_climatology", beats_climatology, tolerances={"ratio": (RATIO_MAX, 1.0)})],
    worlds={
        "plus": World(make_world(PHI)),
        "minus": World(make_world(0.0), derived_from="plus", change="autocorrelation 0.7 -> 0 (white noise)"),
    },
    controls=[Control("time_order_shuffled", ["beats_climatology"], transform=shuffle_time)],
    targets=Targets(size=ALPHA),
)
