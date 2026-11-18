"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SAMPLES = 1200
N_DISTRICTS = 150
COV_SHARE = 0.10        # share of outcome variance from the three covariates in plus
DISTRICT_SHARE = 0.07   # share of outcome variance from district effects in plus (ICC-like)
NOISE_SHARE = 0.83      # share of outcome variance from individual noise (unchanged in minus)
COV_CORR = np.array([[1.00, 0.10, 0.35],
                     [0.10, 1.00, 0.25],
                     [0.35, 0.25, 1.00]])   # individual correlation of standardised age, BMI, SBP
COV_CHOL = np.linalg.cholesky(COV_CORR)
DISTRICT_SHIFT = np.array([0.0, 0.3, 0.2])  # loading of the covariates on district deprivation
BETA_DIR = np.array([1.0, 0.8, 0.7])
BETA = BETA_DIR * np.sqrt(COV_SHARE / (BETA_DIR @ COV_CORR @ BETA_DIR))


def _simulate(rng, scale):
    n, k = N_SAMPLES, N_DISTRICTS
    weights = np.exp(rng.normal(0.0, 0.6, k))
    district = rng.choice(k, size=n, p=weights / weights.sum())
    deprivation = rng.standard_normal(k)
    ind = rng.standard_normal((n, 3)) @ COV_CHOL.T
    z = ind * np.sqrt(1.0 - DISTRICT_SHIFT ** 2) + deprivation[district][:, None] * DISTRICT_SHIFT
    age = np.clip(55.0 + 14.0 * z[:, 0], 18.0, 95.0)
    bmi = 27.0 * np.exp(0.16 * z[:, 1])
    sbp = 132.0 + 17.0 * z[:, 2]
    district_effect = np.sqrt(DISTRICT_SHARE) * (0.6 * deprivation + 0.8 * rng.standard_normal(k))
    signal = z @ BETA + district_effect[district]
    y = 50.0 + 10.0 * (scale * signal + np.sqrt(NOISE_SHARE) * rng.standard_normal(n))
    category = np.zeros((n, k), dtype=bool)
    category[np.arange(n), district] = True
    return {
        "category": category,
        "covariates": np.asarray(np.column_stack([age, bmi, sbp]), dtype=np.float64),
        "y": np.asarray(y, dtype=np.float64),
    }


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


def _permute_y(d, rng):
    y = d["y"]
    return {**d, "y": y[rng.permutation(y.shape[0])].copy()}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="covariate coefficients and district effects on y set to 0 (no predictive information); individual noise, district sizes and covariate distributions unchanged"),
    },
    controls=[Control("y_permuted_across_patients", ["C"], transform=_permute_y)],
    relational=[("covariates", "y")],
)
