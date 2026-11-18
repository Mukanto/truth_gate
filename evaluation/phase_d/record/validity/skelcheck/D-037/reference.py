"""D-037: The expected change in BMI between baseline and follow-up is smaller for children with a higher baseline BMI: each additional 1 kg/m2 of baseline BMI goes with a change in BMI that is at least 0.2 kg/m2 smaller (slope of at most -0.2)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_CHILD = 500
N_RETEST = 100
LEVEL_MEAN = 15.0
LEVEL_SD = 1.2
SLOPE_MEAN = 0.4
SLOPE_SD = 0.2
YEARS = 5.0
ERR_SD = 0.275


def _gen(rng, rho):
    level = LEVEL_MEAN + LEVEL_SD * rng.standard_normal(N_CHILD)
    z = (level - LEVEL_MEAN) / LEVEL_SD
    eps = rng.standard_normal(N_CHILD)
    slope = SLOPE_MEAN + SLOPE_SD * (rho * z + np.sqrt(1.0 - rho ** 2) * eps)
    baseline = level + ERR_SD * rng.standard_normal(N_CHILD)
    followup = level + YEARS * slope + ERR_SD * rng.standard_normal(N_CHILD)
    level_r = LEVEL_MEAN + LEVEL_SD * rng.standard_normal(N_RETEST)
    retest = level_r[:, None] + ERR_SD * rng.standard_normal((N_RETEST, 2))
    return {
        "bmi_baseline": np.asarray(baseline, dtype=float),
        "bmi_followup": np.asarray(followup, dtype=float),
        "bmi_retest": np.asarray(retest, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, -0.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: bmi_baseline (500,) float, BMI in kg/m2 at the baseline visit;
    bmi_followup (500,) float, BMI in kg/m2 at the follow-up visit five years after baseline;
    bmi_retest (100, 2) float, BMI in kg/m2 of each child of a separate test-retest sample at two sessions a few days apart.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_change(d, rng):
    base = np.asarray(d["bmi_baseline"], dtype=float)
    fu = np.asarray(d["bmi_followup"], dtype=float)
    change = fu - base
    perm = rng.permutation(base.shape[0])
    return {
        "bmi_baseline": base,
        "bmi_followup": base + change[perm],
        "bmi_retest": np.asarray(d["bmi_retest"], dtype=float),
    }


STUDY = Study(
    name="D-037",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between true BMI level at baseline and true five-year change set from -0.5 to 0"),
    },
    controls=[Control("permute_change", ["C"], transform=permute_change)],
)
