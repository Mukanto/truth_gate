"""D-022: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, P = 300, 10
RHO = 0.3   # correlation between process readings (shared process state)
A = 1.15 * np.array([0.30, 0.25, 0.20, 0.15, 0.10, 0.0, 0.0, 0.0, 0.0, 0.0])   # linear effects
Q = 1.15 * np.array([0.15, 0.12, 0.15, 0.12])   # two squares, two cross products
NOISE_SD = 1.0


def _draw(rng):
    g = rng.standard_normal((N, 1))
    X = np.sqrt(RHO) * g + np.sqrt(1.0 - RHO) * rng.standard_normal((N, P))
    sig = (X @ A + Q[0] * (X[:, 0] ** 2 - 1.0) + Q[1] * (X[:, 1] ** 2 - 1.0)
           + Q[2] * X[:, 2] * X[:, 3] + Q[3] * X[:, 4] * X[:, 5])
    noise = NOISE_SD * rng.standard_normal(N)
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
def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def poly_features(Z):
    """Intercept, linear terms, squares and all pairwise products of the columns of Z."""
    n, p = Z.shape
    iu, ju = np.triu_indices(p)
    return np.column_stack([np.ones(n), Z, Z[:, iu] * Z[:, ju]])


def poly_fit(X, y):
    """Second-order polynomial regression by ordinary least squares on standardised columns."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    coef = np.linalg.lstsq(poly_features((X - mu) / sd), y, rcond=None)[0]
    return mu, sd, coef


def poly_predict(model, X):
    """Predictions of a model returned by poly_fit."""
    mu, sd, coef = model
    return poly_features((X - mu) / sd) @ coef


def criterion(d):
    """Claim: a second-order polynomial regression of y on X (intercept, the 10 readings, their squares and all
    pairwise products, ordinary least squares) predicts y for new runs with a Pearson correlation between
    predicted and observed y of at least 0.30.

    Data keys:
      "X": float array (samples, features) = (300, 10); the 10 continuous process readings of each production run.
      "y": float array (samples,) = (300,); the continuous quality score of each production run.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 runs, zero variance of the predictions or of y).
    """
    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = poly_predict(poly_fit(X[~te], y[~te]), X[te])
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_y(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-022",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the response surface (linear, square and cross terms) is evaluated on other runs (permuted), so y carries no information on X; the variance of y, the noise and X are unchanged"),
    },
    controls=[Control("D-022", ["C"], transform=permute_y)],
)
