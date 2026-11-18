"""D-066: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1000
P = 15
PREVALENCE = 0.08
# measurement units: age, BMI, SBP, DBP, glucose, creatinine, Na, K, Hb, WBC, platelets, ALT, albumin, INR, heart rate
X_MEAN = np.array([60.0, 27.0, 130.0, 80.0, 5.5, 1.0, 140.0, 4.2, 14.0, 7.0, 250.0, 40.0, 3.8, 1.2, 80.0])
X_SD = np.array([12.0, 4.5, 18.0, 10.0, 1.2, 0.25, 3.0, 0.4, 1.5, 2.0, 60.0, 15.0, 0.4, 0.15, 12.0])
# shift of the patients with the outcome, in within-class SD units (creatinine up, Hb down, WBC up, albumin down, HR up)
SHIFT = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.4, 0.0, 0.0, -1.4, 1.4, 0.0, 0.0, -1.4, 0.0, 1.4])
PAIRS = [(0, 2, 0.3), (2, 3, 0.6), (1, 2, 0.2), (1, 4, 0.3), (8, 12, 0.3), (5, 7, 0.2),
         (11, 12, -0.2), (9, 10, 0.2), (9, 14, 0.15), (0, 5, 0.2)]


def _corr():
    r = np.eye(P)
    for i, j, v in PAIRS:
        r[i, j] = v
        r[j, i] = v
    return r


def _generate(rng, linked):
    y = rng.random(N) < PREVALENCE
    other = rng.random(N) < PREVALENCE          # an independent abnormal-profile indicator of the same prevalence
    profile = y if linked else other
    lc = np.linalg.cholesky(_corr())
    z = rng.standard_normal((N, P)) @ lc.T + profile[:, None] * SHIFT[None, :]
    X = X_MEAN[None, :] + X_SD[None, :] * z
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


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
    return {**d, "y": rng.permutation(d["y"])}


STUDY = Study(
    name="D-066",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="abnormal measurement profile carried by an independent indicator of the same prevalence instead of y (X carries no information on y); distributions of X and y unchanged"),
    },
    controls=[
        Control("outcome_permuted_across_patients", ["C"], transform=_permute_outcome),
    ],
    relational=[("y", "X")],
)
