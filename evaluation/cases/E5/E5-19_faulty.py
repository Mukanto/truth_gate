"""E5-19 (deterministic): chamber thermostat. Claim: the mean chamber temperature is 320 K within 5 K."""
import numpy as np

from kapi import Control, Criterion, Study, World

TEMP_K = np.linspace(316.0, 324.0, 17)


def _to_fahrenheit(tk):
    return tk * 1.8 - 459.67


def _to_kelvin(tf):
    return (tf + 459.67) / 1.8


def _setpoint_ok(d):
    return bool(abs(np.mean(d["temp_k"]) - 320.0) < 5.0)


STUDY = Study(
    name="E5-19 chamber thermostat",
    criteria=[Criterion("mean_320k", _setpoint_ok, tolerances={"t_tol": (5.0, 320.0)})],
    worlds={
        "plus": World(lambda rng: {"temp_k": TEMP_K.copy()}),
        "minus": World(
            lambda rng: {"temp_k": _to_kelvin(_to_fahrenheit(TEMP_K))},
            derived_from="plus",
            change="controller overshoot +40 K (+72 F), applied in Fahrenheit",
        ),
    },
    controls=[Control("logged_in_celsius", ["mean_320k"], transform=lambda d, rng: {"temp_k": d["temp_k"] - 273.15})],
    deterministic=True,
)
