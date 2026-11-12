"""E5-18 (stochastic): nitrogen yield trial. Claim: the Welch t statistic of treated minus control plot yield exceeds 3."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

N_PLOT = 40


def _plots(rng, n_kg):
    boost = 0.005 * n_kg
    return {
        "yield_t": rng.normal(5.0 + boost, 0.4, N_PLOT),
        "yield_c": rng.normal(5.0, 0.4, N_PLOT),
        "n_applied": np.array([n_kg]),
    }


def _welch_ok(d):
    a = d["yield_t"]
    b = d["yield_c"]
    se = float(np.sqrt(np.var(a, ddof=1) / a.size + np.var(b, ddof=1) / b.size))
    if not se > 0.0:
        return False
    return bool((np.mean(a) - np.mean(b)) / se > 3.0)


STUDY = Study(
    name="E5-18 nitrogen yield trial",
    criteria=[Criterion("welch_t_gt_3", _welch_ok, tolerances={"t_crit": (3.0, 1.0)})],
    worlds={
        "plus": World(lambda rng: _plots(rng, 120.0)),
        "minus": World(lambda rng: _plots(rng, 0.0), derived_from="plus", change="nitrogen 120 -> 0 kg/ha"),
    },
    premises=[
        Premise(
            "nitrogen_boost",
            lambda d, rng: {"yield_t": d["yield_t"] - 0.6, "yield_c": d["yield_c"], "n_applied": d["n_applied"]},
            "tested",
            ["welch_t_gt_3"],
            magnitude=(0.6, 5.0),
        )
    ],
    controls=[
        Control(
            "arms_swapped",
            ["welch_t_gt_3"],
            transform=lambda d, rng: {"yield_t": d["yield_c"], "yield_c": d["yield_t"], "n_applied": d["n_applied"]},
        )
    ],
)
