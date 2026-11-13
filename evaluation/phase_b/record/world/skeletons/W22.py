"""W22: In patients whose systolic blood pressure is at least 150 mmHg at entry, the drug lowers systolic pressure by at least 5 mmHg over 12 weeks. The claim holds when the estimated lowering is at least 5 mmHg and one-sided p < 0.05."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 160


def _gen(rng, eff):
    drug = rng.random(N) < 0.5
    true = 156.0 + 13.0 * rng.standard_normal(N)             # usual pressure
    e0 = rng.standard_normal(N)
    e1 = rng.standard_normal(N)
    ind = rng.standard_normal(N)
    sbp0 = true + 11.0 * e0                                  # entry reading, measurement noise sd 11
    resp = eff * (-10.0 + 4.0 * ind)                         # drug effect beyond placebo, mmHg
    sbp1 = true - 2.0 + drug * resp + 11.0 * e1              # placebo response of 2 mmHg in both arms
    return {"sbp": np.column_stack([sbp0, sbp1]), "drug": drug.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: sbp (160, 2) systolic pressure in mmHg, axes (patients, visits): visit 0 = entry, visit 1 = after 12
    weeks; drug (160,) bool, True for patients given the drug, False for placebo (about 80 per arm).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_drug_labels(d, rng):
    return {**d, "drug": d["drug"][rng.permutation(N)]}


STUDY = Study(
    name="W22",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="drug effect beyond placebo -10 mmHg (sd 4) -> 0; the entry measurement noise (regression to the mean), the 2 mmHg placebo response and the randomisation are unchanged"),
    },
    controls=[Control("permute_drug_labels", ["C"], transform=permute_drug_labels)],
)
