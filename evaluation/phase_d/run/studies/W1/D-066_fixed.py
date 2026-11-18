"""D-066: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1000
P = 15
PREVALENCE = 0.08
N_SITES = 4
SITE_SD = 0.2                                   # site calibration offset per measurement (SD units)
LOADING = 0.55                                  # loading on the organ-system factor (3 blocks of 5 measurements)
BLOCK_OF_FEATURE = np.repeat(np.arange(3), 5)
# shift (SD units) of the outcome group: 6 strongly and 3 weakly shifted measurements
SHIFT = np.array([1.3, 1.3, 0.5, 0.0, 0.0,
                  1.3, 1.3, -0.5, 0.0, 0.0,
                  1.3, 1.3, 0.5, 0.0, 0.0])
# clinical units: CRP, WBC, temperature, neutrophil %, platelets, heart rate, lactate, systolic BP, respiratory
# rate, SpO2, creatinine, urea, potassium, bilirubin, albumin
LOGNORMAL = np.array([True, False, False, False, False,
                      False, True, False, False, False,
                      False, False, False, True, False])
CENTRE = np.array([8.0, 8.0, 37.0, 62.0, 250.0, 82.0, 1.3, 125.0, 17.0, 96.0, 1.0, 6.0, 4.2, 0.7, 40.0])
SPREAD = np.array([0.45, 2.5, 0.5, 9.0, 60.0, 13.0, 0.45, 17.0, 3.5, 2.0, 0.3, 2.0, 0.45, 0.45, 4.5])


def _generate(rng, use_copy):
    y = rng.random(N) < PREVALENCE
    y_copy = rng.random(N) < PREVALENCE                 # independent subgroup of the same size distribution
    factors = rng.standard_normal((N, 3))
    unique = rng.standard_normal((N, P))
    site = rng.integers(0, N_SITES, N)
    site_eff = SITE_SD * rng.standard_normal((N_SITES, P))
    carrier = y_copy if use_copy else y
    z = (LOADING * factors[:, BLOCK_OF_FEATURE] + np.sqrt(1.0 - LOADING ** 2) * unique
         + site_eff[site] + carrier[:, None] * SHIFT[None, :])
    X = np.where(LOGNORMAL, CENTRE * np.exp(SPREAD * z), CENTRE + SPREAD * z)
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    About 8% of patients have the outcome; they have values shifted by 1.3 SD in 6 measurements and 0.5 SD in 3
    more. Measurements are correlated within 3 organ-system blocks, carry site calibration offsets, and 3 are
    lognormal laboratory values."""
    return _generate(rng, False)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    The same shifted subgroup exists, but it is an independent draw of the same size distribution, unrelated to
    the outcome, so X carries no information about y; X's distribution, y's prevalence and all structure are as in
    plus."""
    return _generate(rng, True)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def nn_predict(Xtr, ytr, Xte):
    """One-nearest-neighbour prediction: the y of the nearest training row (Euclidean distance on
    columns standardised with the training mean and sd; the first of tied rows wins)."""
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    A = (Xtr - mu) / sd
    B = (Xte - mu) / sd
    D2 = (B ** 2).sum(axis=1)[:, None] + (A ** 2).sum(axis=1)[None, :] - 2.0 * (B @ A.T)
    return ytr[np.argmin(D2, axis=1)]


def strat_folds(y):
    """Fold of each row: its rank within its own class (in row order) modulo 5."""
    fold = np.empty(y.shape[0], dtype=int)
    fold[y] = np.arange(int(y.sum())) % 5
    fold[~y] = np.arange(int((~y).sum())) % 5
    return fold


def balanced_accuracy(y, pred):
    """Mean of sensitivity and specificity; y and pred are boolean."""
    return 0.5 * (np.mean(pred[y]) + np.mean(~pred[~y]))


def criterion(d):
    """Claim: a one-nearest-neighbour classifier (Euclidean distance on standardised measurements) recovers the
    rare outcome y from X for new patients with a balanced accuracy (mean of sensitivity and specificity)
    of at least 0.65.  The rare class (y True) is balanced by copying its rows (sampling with replacement)
    until the two classes have equal size.

    Data keys:
      "X": float array (samples, features) = (1000, 15); the 15 continuous clinical measurements of each patient.
      "y": bool array (samples,) = (1000,); True where the patient has the rare outcome.

    Returns True when the balanced accuracy >= 0.65, False otherwise, None at an allowed guard (non-finite X,
    fewer than 2 patients in either class).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 2 or int((~y).sum()) < 2:
        return None
    if not np.all(np.isfinite(X)):
        return None
    rng = np.random.default_rng(0)
    fold = strat_folds(y)
    pred = np.empty(n, dtype=bool)
    for k in range(5):
        te = fold == k
        Xtr = X[~te]
        ytr = y[~te]
        pos = np.flatnonzero(ytr)
        extra = rng.choice(pos, size=max(ytr.shape[0] - 2 * pos.shape[0], 0), replace=True)
        pred[te] = nn_predict(np.concatenate([Xtr, Xtr[extra]]), np.concatenate([ytr, ytr[extra]]), X[te])
    bal = balanced_accuracy(y, pred)
    if not np.isfinite(bal):
        return None
    return bool(bal >= 0.65)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_outcome(d, rng):
    y = d["y"]
    shuffled = y[rng.permutation(y.shape[0])]
    if np.array_equal(shuffled, y):
        shuffled = np.roll(y, 1)
    return {**d, "y": shuffled}


STUDY = Study(
    name="D-066",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="link X -> y set to none: the shifted subgroup in X is an independent draw unrelated to y (same size distribution)"),
    },
    controls=[Control("outcome_permuted_across_patients", ["C"], transform=_permute_outcome)],
    relational=[("X", "y")],
)
