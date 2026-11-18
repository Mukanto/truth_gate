import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

K = 12
N = 20
MU1 = 8.0
SD_TRIAL = 0.7
GAIN = 2.0
SD_GAIN = 0.6
TAU1 = 1.8
R12 = 0.7
ERR = 0.86
TAU2_PLUS = 1.17


def _gen(rng, tau2):
    m1 = MU1 + SD_TRIAL * rng.standard_normal(K)
    m2 = m1 - GAIN - SD_GAIN * rng.standard_normal(K)
    z1 = rng.standard_normal((K, N))
    z2 = rng.standard_normal((K, N))
    t1 = m1[:, None] + TAU1 * z1
    t2 = m2[:, None] + tau2 * (R12 * z1 + np.sqrt(1.0 - R12 ** 2) * z2)
    base = t1 + ERR * rng.standard_normal((K, N))
    retest = t1 + ERR * rng.standard_normal((K, N))
    follow = t2 + ERR * rng.standard_normal((K, N))
    return {
        "baseline_attachment_loss": np.asarray(base, dtype=float),
        "baseline_attachment_loss_retest": np.asarray(retest, dtype=float),
        "followup_attachment_loss": np.asarray(follow, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, TAU2_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, TAU1)


def _equalise_spread(d, rng):
    b = np.asarray(d["baseline_attachment_loss"], dtype=float)
    f = np.asarray(d["followup_attachment_loss"], dtype=float)
    fm = f.mean(axis=1, keepdims=True)
    scale = np.std(b, axis=1, ddof=1, keepdims=True) / np.std(f, axis=1, ddof=1, keepdims=True)
    return {
        "baseline_attachment_loss": b,
        "baseline_attachment_loss_retest": np.asarray(d["baseline_attachment_loss_retest"], dtype=float),
        "followup_attachment_loss": fm + (f - fm) * scale,
    }


def criterion(d):
    """Data keys, each shape (12, 20), float, rows = trials, columns = defects within a trial, in mm:
    baseline_attachment_loss (clinical attachment loss at baseline), baseline_attachment_loss_retest (a
    second, independent measurement of the baseline attachment loss), followup_attachment_loss
    (attachment loss at follow-up after treatment).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-025",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true follow-up spread set equal to true baseline spread in every trial (SD 1.17 to 1.8 mm), so true change is unrelated to true level"),
    },
    controls=[Control("D-025", ["C"], transform=lambda d, rng: _equalise_spread(d, rng))],
)
