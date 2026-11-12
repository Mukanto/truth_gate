"""E5-09 (deterministic): free-fall timing. Claim: the measured heights match h0 - g t^2 / 2 with g = 9.81 m/s^2 within 5 cm at every time."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

TIME = np.linspace(0.0, 1.0, 11)
H0 = 10.0
G = 9.81


def _drop(g_true):
    return {
        "t": TIME.copy(),
        "obs": np.round(H0 - 0.5 * g_true * TIME ** 2, 3),
        "pred": H0 - 0.5 * G * TIME ** 2,
    }


def _heights_ok(d):
    theory = H0 - 0.5 * G * d["t"] ** 2
    return bool(np.max(np.abs(d["obs"] - theory)) < 0.05)


STUDY = Study(
    name="E5-09 free-fall timing",
    criteria=[Criterion("heights_match", _heights_ok, tolerances={"height_tol": (0.05, 10.0)})],
    worlds={
        "plus": World(lambda rng: _drop(9.81)),
        "minus": World(lambda rng: _drop(7.0), derived_from="plus", change="true acceleration 9.81 -> 7.0 m/s^2"),
    },
    premises=[
        Premise(
            "g_value",
            lambda d, rng: {"t": d["t"], "obs": H0 - 0.9 * (H0 - d["obs"]), "pred": d["pred"]},
            "tested",
            ["heights_match"],
            magnitude=(0.1, 1.0),
        )
    ],
    controls=[Control("obs_reversed", ["heights_match"], transform=lambda d, rng: {"t": d["t"], "obs": d["obs"][::-1], "pred": d["pred"]})],
    deterministic=True,
)
