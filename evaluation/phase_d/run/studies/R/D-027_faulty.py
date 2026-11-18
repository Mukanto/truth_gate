"""D-027: The 25 measurements in X predict the outcome y for new samples: the mean absolute error of an ordinary least squares regression of y on X (with an intercept) is at least 10% below that of predicting the mean of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P = 60, 25
RHO = 0.25   # correlation between the measurements (shared factor)
SIG_VAR = 2.33   # variance of the signal; noise variance 1 -> signal share 0.70
PAT = np.zeros(P) + np.isin(np.arange(P), np.arange(0, 24, 3)) * np.tile(np.array([1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0]), 3)[:P]
_V = (1.0 - RHO) * np.sum(PAT ** 2) + RHO * np.sum(PAT) ** 2
BETA = PAT * np.sqrt(SIG_VAR / _V)


def _draw(rng):
    g = rng.standard_normal((N, 1))
    X = np.sqrt(RHO) * g + np.sqrt(1.0 - RHO) * rng.standard_normal((N, P))
    sig = X @ BETA
    noise = rng.standard_normal(N)
    return np.ascontiguousarray(X), sig, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, sig, noise = _draw(rng)
    return {"X": X, "y": sig + noise}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, sig, noise = _draw(rng)
    return {"X": X, "y": sig[rng.permutation(N)] + noise}


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def ols_predict(A, y, tr, te):
    """Ordinary least squares (numpy lstsq) of y on the columns of A over the rows tr; predictions for rows te."""
    coef = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    return A[te] @ coef


def fold_mean_baseline(y, fold):
    """For each row, the mean of y over the rows outside its fold (the training-fold mean predictor)."""
    base = np.empty(y.shape[0])
    for k in range(5):
        te = fold == k
        base[te] = y[~te].mean()
    return base


def criterion(d):
    """Claim: the mean absolute error of an ordinary least squares regression of y on the 25 measurements X
    (with an intercept), for new samples, is at least 10% below that of predicting the mean of y:
    1 - MAE(model) / MAE(mean predictor) >= 0.10.

    Data keys:
      "X": float array (samples, features) = (60, 25); the 25 continuous measurements of each sample.
      "y": float array (samples,) = (60,); the continuous outcome of each sample.

    Returns True when the skill >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero MAE of the mean predictor).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    A = np.column_stack([np.ones(n), X])
    every = np.ones(n, dtype=bool)
    pred = ols_predict(A, y, every, every)
    base = np.full(n, y.mean())
    mae0 = np.mean(np.abs(y - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(y - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.10)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-027",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the linear signal in y is reassigned to other samples (permuted), so y carries no information on X; the variance of y, the noise and X are unchanged"),
    },
    controls=[Control("D-027", ["C"], transform=permute_y)],
)
