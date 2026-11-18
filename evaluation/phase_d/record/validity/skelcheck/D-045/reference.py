"""D-045: In 300 patients with a continuous disease severity score measured before and after treatment, improvement is larger in patients with a higher severity level: the Pearson correlation between each patient's change in score (follow-up minus baseline) and the mean of that patient's baseline and follow-up scores is at most -0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 300
MU1 = 50.0
TAU1 = 10.0
MU2 = 38.0
R12 = 0.7
ERR = 5.0
TAU2_PLUS = 5.5


def _gen(rng, tau2):
    z1 = rng.standard_normal(N)
    z2 = rng.standard_normal(N)
    t1 = MU1 + TAU1 * z1
    t2 = MU2 + tau2 * (R12 * z1 + np.sqrt(1.0 - R12 ** 2) * z2)
    base = t1 + ERR * rng.standard_normal(N)
    retest = t1 + ERR * rng.standard_normal(N)
    follow = t2 + ERR * rng.standard_normal(N)
    return {
        "baseline_score": np.asarray(base, dtype=float),
        "baseline_score_retest": np.asarray(retest, dtype=float),
        "followup_score": np.asarray(follow, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, TAU2_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, TAU1)


def _equalise_spread(d, rng):
    b = np.asarray(d["baseline_score"], dtype=float)
    f = np.asarray(d["followup_score"], dtype=float)
    fm = f.mean()
    f_new = fm + (f - fm) * (np.std(b, ddof=1) / np.std(f, ddof=1))
    return {
        "baseline_score": b,
        "baseline_score_retest": np.asarray(d["baseline_score_retest"], dtype=float),
        "followup_score": f_new,
    }


def criterion(d):
    """Data keys, each shape (300,), float, one value per patient: baseline_score (severity at baseline),
    baseline_score_retest (a second, independent reading of the severity at the baseline visit),
    followup_score (severity at follow-up after treatment); higher is more severe.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-045",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true follow-up spread set equal to true baseline spread (SD 5.5 to 10), so true change is unrelated to true level"),
    },
    controls=[Control("D-045", ["C"], transform=lambda d, rng: _equalise_spread(d, rng))],
)
