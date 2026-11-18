"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N, D = 1200, 150
RCOV = np.array([[1.0, 0.10, 0.35], [0.10, 1.0, 0.30], [0.35, 0.30, 1.0]])   # age, BMI, systolic pressure
CHOL = np.linalg.cholesky(RCOV)
DIST_SHIFT_VAR = 0.09     # district-level share of the covariates' variance
BETA = np.array([0.24, 0.18, 0.10])   # effects per sd of age, BMI, pressure
U_VAR = 0.06              # district random-effect variance (ICC of y about 0.06)
NOISE_VAR = 0.81


def _draw(rng):
    w = rng.gamma(2.0, size=D)
    counts = 1 + rng.multinomial(N - D, w / w.sum())
    did = rng.permutation(np.repeat(np.arange(D), counts))
    category = np.zeros((N, D), dtype=bool)
    category[np.arange(N), did] = True
    shift = rng.standard_normal((D, 3))
    zc = np.sqrt(1.0 - DIST_SHIFT_VAR) * (rng.standard_normal((N, 3)) @ CHOL.T) + np.sqrt(DIST_SHIFT_VAR) * shift[did]
    cov = np.empty((N, 3))
    cov[:, 0] = 52.0 + 14.0 * zc[:, 0]
    cov[:, 1] = 27.0 + 4.5 * zc[:, 1]
    cov[:, 2] = 130.0 + 16.0 * zc[:, 2]
    u = np.sqrt(U_VAR) * rng.standard_normal(D)
    sig = zc @ BETA + u[did]
    noise = np.sqrt(NOISE_VAR) * rng.standard_normal(N)
    return category, cov, sig, noise


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    category, cov, sig, noise = _draw(rng)
    return {"category": category, "covariates": cov, "y": sig + noise}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    category, cov, sig, noise = _draw(rng)
    return {"category": category, "covariates": cov, "y": sig[rng.permutation(N)] + noise}


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)


def district_means(C, y, rows):
    """Mean of y per category (column of C) over the rows selected; the grand mean of those rows for a
    category with no selected row."""
    Cr = C[rows].astype(float)
    cnt = Cr.sum(axis=0)
    grand = y[rows].mean()
    return np.where(cnt > 0, (Cr.T @ y[rows]) / np.maximum(cnt, 1.0), grand)


def ols_predict(A, y, tr, te):
    """Ordinary least squares (numpy lstsq) of y on the columns of A over the rows tr; predictions for rows te."""
    coef = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    return A[te] @ coef


def criterion(d):
    """Claim: the postal district and the three covariates together predict y for new patients: the Pearson
    correlation between predicted and observed y is at least 0.25.  The district enters as its mean-outcome
    encoding; the model is ordinary least squares of y on an intercept, the encoding and the 3 covariates.

    Data keys:
      "category":   bool array (samples, categories) = (1200, 150); True where the patient's home postal
                    district is the district of that column (one True per row).
      "covariates": float array (samples, features) = (1200, 3); age, body-mass index and systolic pressure.
      "y":          float array (samples,) = (1200,); the continuous health outcome of each patient.

    Returns True when the correlation >= 0.25, False otherwise, None at an allowed guard (non-finite
    covariates or y, fewer than 2 patients, zero variance of the predictions or of y).
    """
    C = np.asarray(d["category"], dtype=bool)
    V = np.asarray(d["covariates"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(V)) and np.all(np.isfinite(y))):
        return None
    Cf = C.astype(float)
    fold = np.arange(n) % 5
    pred = np.empty(n)
    enc = Cf @ district_means(C, y, np.ones(n, dtype=bool))
    A = np.column_stack([np.ones(n), enc, V])
    for k in range(5):
        te = fold == k
        pred[te] = ols_predict(A, y, ~te, te)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.25)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_y(d, rng):
    return {"category": np.array(d["category"]), "covariates": np.array(d["covariates"]), "y": d["y"][rng.permutation(N)]}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the covariate and district contributions to y are reassigned to other patients (permuted), so y carries no information on district or covariates; the variance of y, the noise, the district sizes and the covariates are unchanged"),
    },
    controls=[Control("D-010", ["C"], transform=permute_y)],
)
