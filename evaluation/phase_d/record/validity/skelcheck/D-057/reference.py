"""D-057: In 24 intrabony periodontal defects treated by guided tissue regeneration, the level of disease explains the amount of change: the mean of the baseline and follow-up pocket probing depth explains at least 15% of the variance in the change in pocket probing depth (follow-up minus baseline), that is, the R-squared of the linear regression of the change on that mean is at least 0.15."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 24
MU1 = 7.5
TAU1 = 1.8
MU2 = 3.5
R12 = 0.5
ERR = 0.9
TAU2_PLUS = 0.65


def _gen(rng, tau2):
    z1 = rng.standard_normal(N)
    z2 = rng.standard_normal(N)
    t1 = MU1 + TAU1 * z1
    t2 = MU2 + tau2 * (R12 * z1 + np.sqrt(1.0 - R12 ** 2) * z2)
    base = t1 + ERR * rng.standard_normal(N)
    retest = t1 + ERR * rng.standard_normal(N)
    follow = t2 + ERR * rng.standard_normal(N)
    return {
        "baseline_depth": np.asarray(base, dtype=float),
        "baseline_depth_retest": np.asarray(retest, dtype=float),
        "followup_depth": np.asarray(follow, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, TAU2_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, TAU1)


def _equalise_spread(d, rng):
    b = np.asarray(d["baseline_depth"], dtype=float)
    f = np.asarray(d["followup_depth"], dtype=float)
    fm = f.mean()
    f_new = fm + (f - fm) * (np.std(b, ddof=1) / np.std(f, ddof=1))
    return {
        "baseline_depth": b,
        "baseline_depth_retest": np.asarray(d["baseline_depth_retest"], dtype=float),
        "followup_depth": f_new,
    }


def criterion(d):
    """Data keys, each shape (24,), float, one value per defect, in mm: baseline_depth (pocket probing
    depth at baseline), baseline_depth_retest (a second, independent probing of the baseline depth),
    followup_depth (pocket probing depth at follow-up after treatment).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-057",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true follow-up spread set equal to true baseline spread (SD 0.65 to 1.8 mm), so true change is unrelated to true level"),
    },
    controls=[Control("D-057", ["C"], transform=lambda d, rng: _equalise_spread(d, rng))],
)
