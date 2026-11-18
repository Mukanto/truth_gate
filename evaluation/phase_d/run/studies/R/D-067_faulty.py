"""D-067: After accounting for body mass, kidney weight and heart weight are positively related: the standardised slope of kidney weight on heart weight is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RAT = 60
MASS_MEAN = 300.0
HEART_MEAN = 1.1
KIDNEY_MEAN = 2.3
CV = 0.10
WEIGH_ERR_CV = 0.01
R_HEART_MASS = 0.5
R_KIDNEY_MASS = 0.5


def _gen(rng, partial):
    zm = rng.standard_normal(N_RAT)
    u = rng.standard_normal(N_RAT)
    w = rng.standard_normal(N_RAT)
    zh = R_HEART_MASS * zm + np.sqrt(1.0 - R_HEART_MASS ** 2) * u
    zk = R_KIDNEY_MASS * zm + np.sqrt(1.0 - R_KIDNEY_MASS ** 2) * (partial * u + np.sqrt(1.0 - partial ** 2) * w)
    lat = np.sqrt(CV ** 2 - WEIGH_ERR_CV ** 2)
    mass = MASS_MEAN * (1.0 + CV * zm)
    heart = HEART_MEAN * (1.0 + lat * zh + WEIGH_ERR_CV * rng.standard_normal(N_RAT))
    kidney = KIDNEY_MEAN * (1.0 + lat * zk + WEIGH_ERR_CV * rng.standard_normal(N_RAT))
    return {
        "kidney_weight": np.asarray(kidney, dtype=float),
        "heart_weight": np.asarray(heart, dtype=float),
        "body_mass": np.asarray(mass, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.4)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _std_coef(y, X, j):
    """Standardised coefficient of column j of X (n, k) in the regression of y (n,) on an intercept and X."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(coef[1 + j] * np.std(X[:, j], ddof=1) / np.std(y, ddof=1))


def criterion(d):
    """Claim: after accounting for body mass, kidney weight and heart weight are positively related; the
    standardised slope of kidney weight on heart weight is at least 0.25.

    d['kidney_weight'] : (rats,) float, combined kidney weight of each rat, in g
    d['heart_weight']  : (rats,) float, heart weight of each rat, in g
    d['body_mass']     : (rats,) float, body mass of each rat, in g

    Returns True / False; None when a value is not finite, fewer than 3 rats, or a variance is zero.
    """
    kid = np.asarray(d['kidney_weight'], dtype=float)
    heart = np.asarray(d['heart_weight'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(kid)) and np.all(np.isfinite(heart)) and np.all(np.isfinite(body))):
        return None
    if kid.size < 3:
        return None
    with np.errstate(divide='ignore', invalid='ignore'):
        y = kid / body
        x = heart / body
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    if _flat(y) or _flat(x) or _flat(body):
        return None
    b = _std_coef(y, x.reshape(-1, 1), 0)
    if not np.isfinite(b):
        return None
    return bool(b >= 0.25)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_heart_within_mass(d, rng):
    m = np.asarray(d["body_mass"], dtype=float)
    h = np.asarray(d["heart_weight"], dtype=float)
    order = np.argsort(m, kind="stable")
    out = h.copy()
    block = 10
    for start in range(0, m.shape[0], block):
        idx = order[start:start + block]
        out[idx] = h[idx[rng.permutation(idx.shape[0])]]
    return {"kidney_weight": np.asarray(d["kidney_weight"], dtype=float), "heart_weight": out, "body_mass": m}


STUDY = Study(
    name="D-067",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="partial correlation of kidney and heart weight given body mass set from 0.4 to 0"),
    },
    controls=[Control("permute_heart_within_mass", ["C"], transform=permute_heart_within_mass)],
)
