"""D-010: The postal district and the three covariates together predict the outcome y for new patients: the Pearson correlation between predicted and observed y is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1200
N_DIST = 150
REF_MEAN = np.array([57.0, 27.5, 128.0])   # reference means of age, BMI, SBP (for standardising)
REF_SD = np.array([14.0, 4.66, 15.8])      # reference SDs of age, BMI, SBP
B_COV = np.array([0.20, 0.12, 0.12])       # effect on standardised y per SD of age, BMI, SBP
TAU = 0.245                                # SD of the district effect (district ICC about 0.06)
SIGMA = np.sqrt(0.845)                     # residual SD (standardised scale)


def _patients(rng, pop, depriv):
    dist = rng.choice(N_DIST, N, p=pop)
    age = np.clip(rng.normal(57.0, 14.0, N), 18.0, 95.0)
    bmi = np.clip(27.5 + 1.2 * depriv[dist] + rng.normal(0.0, 4.5, N), 15.0, 60.0)
    sbp = np.clip(128.0 + 0.45 * (age - 57.0) + 0.7 * (bmi - 27.5) + 2.0 * depriv[dist]
                  + rng.normal(0.0, 14.0, N), 80.0, 230.0)
    return dist, np.column_stack([age, bmi, sbp])


def _world(rng, effect):
    pop = np.exp(rng.normal(0.0, 0.8, N_DIST))
    pop = pop / pop.sum()
    depriv = rng.standard_normal(N_DIST)
    u_dist = 0.6 * depriv + 0.8 * rng.standard_normal(N_DIST)
    dist, cov = _patients(rng, pop, depriv)
    # an independent copy of the cohort (same districts, same covariate distribution): drives y in minus
    dist_copy, cov_copy = _patients(rng, pop, depriv)
    eps = rng.standard_normal(N)
    d_y, c_y = (dist, cov) if effect else (dist_copy, cov_copy)
    lin = ((c_y - REF_MEAN) / REF_SD) @ B_COV + TAU * u_dist[d_y] + SIGMA * eps
    y = 60.0 + 12.0 * lin
    category = np.zeros((N, N_DIST), dtype=bool)
    category[np.arange(N), dist] = True
    return {
        "category": category,
        "covariates": np.asarray(cov, dtype=np.float64),
        "y": np.asarray(y, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


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
    for k in range(5):
        te = fold == k
        enc = Cf @ district_means(C, y, ~te)
        A = np.column_stack([np.ones(n), enc, V])
        pred[te] = ols_predict(A, y, ~te, te)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.25)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _nonidentity_perm(rng, n):
    p = rng.permutation(n)
    if np.all(p == np.arange(n)):
        p = np.roll(p, 1)
    return p


def _shuffle_y(d, rng):
    p = _nonidentity_perm(rng, d["y"].shape[0])
    return {**d, "y": d["y"][p]}


STUDY = Study(
    name="D-010",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="y driven by an independent copy of the cohort's districts and covariates: no predictive information"),
    },
    controls=[Control("y_shuffled_across_patients", ["C"], transform=_shuffle_y)],
)
