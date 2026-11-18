"""D-022: A second-order polynomial regression of the quality score y on the process readings X (an intercept, the 10 readings, their squares and all pairwise products, fitted by ordinary least squares) predicts y for new runs with a Pearson correlation between predicted and observed y of at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 300
N_FEATURES = 10
SIGNAL_SHARE = 0.37       # share of quality-score variance explained by the true process function in plus
READING_CORR = 0.4 ** np.abs(np.subtract.outer(np.arange(N_FEATURES), np.arange(N_FEATURES)))
READING_CHOL = np.linalg.cholesky(READING_CORR)
F_SD = 0.8178             # SD of the true process function under READING_CORR (Monte Carlo, 2e6 draws)
READING_CENTRE = np.array([182.0, 2.4, 41.0, 6.8, 1250.0, 0.55, 23.0, 88.0, 3.1, 140.0])
READING_SCALE = np.array([4.0, 0.25, 3.5, 0.3, 60.0, 0.05, 1.5, 6.0, 0.4, 9.0])


def _process_function(z):
    return (0.35 * z[:, 0] + 0.25 * z[:, 2] - 0.20 * z[:, 5]
            - 0.30 * (z[:, 3] ** 2 - 1.0) - 0.20 * (z[:, 7] ** 2 - 1.0)
            + 0.30 * z[:, 1] * z[:, 4] - 0.25 * z[:, 6] * z[:, 8])


def _simulate(rng, scale):
    n = N_SAMPLES
    z = rng.standard_normal((n, N_FEATURES)) @ READING_CHOL.T
    x = READING_CENTRE + READING_SCALE * z
    signal = np.sqrt(SIGNAL_SHARE) * _process_function(z) / F_SD
    y = 72.0 + 5.0 * (scale * signal + np.sqrt(1.0 - SIGNAL_SHARE) * rng.standard_normal(n))
    return {"X": np.asarray(x, dtype=np.float64), "y": np.asarray(y, dtype=np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


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
    pred = poly_predict(poly_fit(X, y), X)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_y(d, rng):
    y = d["y"]
    return {**d, "y": y[rng.permutation(y.shape[0])].copy()}


STUDY = Study(
    name="D-022",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="the process function (linear, square and interaction terms) in y set to 0 (readings carry no information on quality); noise SD and reading distribution unchanged"),
    },
    controls=[Control("y_permuted_across_runs", ["C"], transform=_permute_y)],
    relational=[("X", "y")],
)
