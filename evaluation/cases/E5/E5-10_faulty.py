"""E5-10 (deterministic): dose-response. Claim: the response rises strictly with dose and by more than 0.5 over the dose range."""
import numpy as np

from kapi import Control, Criterion, Study, World

DOSE = np.linspace(0.0, 100.0, 11)


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-(x - 50.0) / 10.0))


def _rise_ok(d):
    r = d["dose"]
    return bool(np.all(np.diff(r) > 0.0) and (r[-1] - r[0]) > 0.5)


STUDY = Study(
    name="E5-10 dose-response rise",
    criteria=[Criterion("monotone_rise", _rise_ok, tolerances={"rise": (0.5, 1.0)})],
    worlds={
        "plus": World(lambda rng: {"dose": DOSE.copy(), "response": _sigmoid(DOSE)}),
        "minus": World(
            lambda rng: {"dose": DOSE.copy(), "response": np.full(DOSE.size, _sigmoid(0.0))},
            derived_from="plus",
            change="no dose dependence: response fixed at the zero-dose level",
        ),
    },
    controls=[Control("response_reversed", ["monotone_rise"], transform=lambda d, rng: {"dose": d["dose"], "response": d["response"][::-1]})],
    deterministic=True,
)
