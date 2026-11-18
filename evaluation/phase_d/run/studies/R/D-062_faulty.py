"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIES = 12
N_IND = 30
BODY_MEDIAN = 150.0
BODY_SPECIES_SD = 0.4
FEMUR_RATIO = 0.20
HUMERUS_RATIO = 0.17
RATIO_SPECIES_SD = 0.10
CV_BASE = 0.05
CV_SPECIES_SD = 0.10
R_FEMUR_BODY = 0.4
R_HUMERUS_BODY = 0.4
PARTIAL_SD = 0.15


def _gen(rng, partial_mean):
    body_mu = BODY_MEDIAN * np.exp(BODY_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    fem_mu = body_mu * FEMUR_RATIO * np.exp(RATIO_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    hum_mu = body_mu * HUMERUS_RATIO * np.exp(RATIO_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    cv_b = CV_BASE * np.exp(CV_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    cv_f = CV_BASE * np.exp(CV_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    cv_h = CV_BASE * np.exp(CV_SPECIES_SD * rng.standard_normal((N_SPECIES, 1)))
    partial = partial_mean * np.ones((N_SPECIES, 1)) + PARTIAL_SD * (partial_mean != 0.0) * rng.standard_normal((N_SPECIES, 1))
    partial = np.clip(partial, -0.9, 0.9)
    zb = rng.standard_normal((N_SPECIES, N_IND))
    u = rng.standard_normal((N_SPECIES, N_IND))
    w = rng.standard_normal((N_SPECIES, N_IND))
    zf = R_FEMUR_BODY * zb + np.sqrt(1.0 - R_FEMUR_BODY ** 2) * u
    zh = R_HUMERUS_BODY * zb + np.sqrt(1.0 - R_HUMERUS_BODY ** 2) * (partial * u + np.sqrt(1.0 - partial ** 2) * w)
    body = body_mu * (1.0 + cv_b * zb)
    femur = fem_mu * (1.0 + cv_f * zf)
    humerus = hum_mu * (1.0 + cv_h * zh)
    return {
        "femur": np.asarray(femur, dtype=float),
        "humerus": np.asarray(humerus, dtype=float),
        "body_length": np.asarray(body, dtype=float),
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


def _corr(a, b):
    """Pearson correlation of two 1-D arrays; None when either has zero variance."""
    if _flat(a) or _flat(b):
        return None
    a = a - np.mean(a)
    b = b - np.mean(b)
    sa = np.sqrt(np.sum(a * a))
    sb = np.sqrt(np.sum(b * b))
    if sa == 0.0 or sb == 0.0:
        return None
    return float(np.sum(a * b) / (sa * sb))


def _resid(y, X):
    """Residuals of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return y - A @ coef


def _partial_corr(a, b, z):
    """Partial correlation of a and b given z (all (n,)): correlation of the residuals of a and of b on z.

    None when a residual has no variance left (the partial correlation is then undefined).
    """
    Z = z.reshape(-1, 1)
    ra = _resid(a, Z)
    rb = _resid(b, Z)
    if np.sum(ra * ra) <= 1e-24 * np.sum((a - np.mean(a)) ** 2):
        return None
    if np.sum(rb * rb) <= 1e-24 * np.sum((b - np.mean(b)) ** 2):
        return None
    return _corr(ra, rb)


def criterion(d):
    """Claim: in at least 60% of the species, femur length and humerus length are positively associated after
    accounting for body length; within the species, the partial correlation between femur length and
    humerus length, given body length, is at least 0.2.

    d['femur']       : (species, individuals) float, femur length of each individual sampled in each
                       species, in mm
    d['humerus']     : (species, individuals) float, humerus length of each individual sampled in each
                       species, in mm
    d['body_length'] : (species, individuals) float, head-and-body length of each individual sampled in
                       each species, in mm

    Species with a non-finite value, fewer than 3 individuals or a zero variance are not counted.
    Returns True / False; None when no species can be counted.
    """
    x = np.asarray(d['femur'], dtype=float)
    y = np.asarray(d['humerus'], dtype=float)
    z = np.asarray(d['body_length'], dtype=float)
    n_species, n_ind = x.shape
    if n_species < 1 or n_ind < 3:
        return None
    hits = 0
    counted = 0
    for s in range(n_species):
        xs = x[s]
        ys = y[s]
        zs = z[s]
        if not (np.all(np.isfinite(xs)) and np.all(np.isfinite(ys)) and np.all(np.isfinite(zs))):
            continue
        with np.errstate(divide='ignore', invalid='ignore'):
            a = xs / zs
            b = ys / zs
        if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
            continue
        if _flat(a) or _flat(b) or _flat(zs):
            continue
        r = _corr(a, b)
        if r is None or not np.isfinite(r):
            continue
        counted += 1
        if r >= 0.2:
            hits += 1
    if counted == 0:
        return None
    return bool(hits / counted >= 0.6)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_humerus_within_species(d, rng):
    z = np.asarray(d["body_length"], dtype=float)
    h = np.asarray(d["humerus"], dtype=float)
    s, k = h.shape
    block = 6
    order = np.argsort(z, axis=1, kind="stable")
    out = h.copy()
    for i in range(s):
        for start in range(0, k, block):
            idx = order[i, start:start + block]
            out[i, idx] = h[i, idx[rng.permutation(idx.shape[0])]]
    return {"femur": np.asarray(d["femur"], dtype=float), "humerus": out, "body_length": z}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="within-species partial correlation of femur and humerus given body length set from a mean of 0.4 (SD 0.15 across species) to 0 in every species"),
    },
    controls=[Control("permute_humerus_within_species", ["C"], transform=permute_humerus_within_species)],
)
