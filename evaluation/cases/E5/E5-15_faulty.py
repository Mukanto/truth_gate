"""E5-15 (deterministic): boiling point at sea level. Claim: the mean measured boiling temperature is 100 C within 0.5 C."""
import numpy as np

from kapi import Control, Criterion, Study, World

READINGS_K = np.array([373.10, 373.15, 373.20, 373.15, 373.12])


def _boils_at_100(d):
    return bool(abs(np.mean(d["t_boil"]) - 100.0) < 0.5)


STUDY = Study(
    name="E5-15 boiling point",
    criteria=[Criterion("boils_at_100", _boils_at_100, tolerances={"t_tol": (0.5, 100.0)})],
    worlds={
        "plus": World(lambda rng: {"t_boil": READINGS_K.copy()}),
        "minus": World(
            lambda rng: {"t_boil": READINGS_K.copy()},
            derived_from="plus",
            change="ambient pressure 101.3 -> 70 kPa (boiling near 90 C)",
        ),
    },
    controls=[Control("pressure_cooker", ["boils_at_100"], transform=lambda d, rng: {"t_boil": d["t_boil"] + 20.0})],
    deterministic=True,
)
