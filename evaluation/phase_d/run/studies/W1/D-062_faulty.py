"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIES = 12
N_IND = 30
# true within-species partial correlation of (log) femur and humerus given body length; 11 of 12 are >= 0.2
RHO = np.array([0.55, 0.30, 0.45, 0.38, 0.12, 0.50, 0.42, 0.33, 0.60, 0.25, 0.47, 0.36])
BL_MIN = 80.0                  # smallest species mean head-and-body length (mm)
BL_RANGE = 5.0                 # largest / smallest species mean (80 to 400 mm)


def _generate(rng, rho):
    s, n = N_SPECIES, N_IND
    log_mu = np.log(BL_MIN) + np.log(BL_RANGE) * rng.random(s)
    log_fem_ratio = np.log(0.26) + 0.12 * rng.standard_normal(s)
    log_hum_ratio = np.log(0.82) + 0.08 * rng.standard_normal(s)
    slope_f = 0.95 + 0.08 * rng.standard_normal(s)
    slope_h = 0.90 + 0.08 * rng.standard_normal(s)
    sd_bl = 0.05 + 0.04 * rng.random(s)
    sd_f = 0.040 + 0.015 * rng.random(s)
    sd_h = 0.045 + 0.015 * rng.random(s)
    male = rng.random((s, n)) < 0.5
    dev = 0.04 * (male.astype(np.float64) - 0.5) + sd_bl[:, None] * rng.standard_normal((s, n))
    z1 = rng.standard_normal((s, n))
    z2 = rng.standard_normal((s, n))
    r = rho[:, None]
    log_bl = log_mu[:, None] + dev
    log_f = log_mu[:, None] + log_fem_ratio[:, None] + slope_f[:, None] * dev + sd_f[:, None] * z1
    log_h = (log_mu[:, None] + log_fem_ratio[:, None] + log_hum_ratio[:, None] + slope_h[:, None] * dev
             + sd_h[:, None] * (r * z1 + np.sqrt(1.0 - r ** 2) * z2))
    return {
        "femur": np.asarray(np.exp(log_f), dtype=np.float64),
        "humerus": np.asarray(np.exp(log_h), dtype=np.float64),
        "body_length": np.asarray(np.exp(log_bl), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Within each species both bones scale with body length; their residuals given body length are correlated with
    a species-specific partial correlation (mean 0.40, 11 of 12 species at least 0.2). Species differ widely in
    size, bone proportions and variances."""
    return _generate(rng, RHO)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    The within-species partial correlation of femur and humerus given body length is 0 in every species; the
    allometry on body length, the species structure and all variances are as in plus."""
    return _generate(rng, np.zeros(N_SPECIES))


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


def _swap_humerus_between_length_neighbours(d, rng):
    bl = d["body_length"]
    hum = d["humerus"]
    idx = np.argsort(bl, axis=1)
    rows = np.arange(bl.shape[0])[:, None]
    a = idx[:, 0::2]
    b = idx[:, 1::2]
    out = hum.copy()
    out[rows, a] = hum[rows, b]
    out[rows, b] = hum[rows, a]
    return {**d, "humerus": out}


def _permute_humerus_within_species(d, rng):
    hum = d["humerus"]
    order = np.argsort(rng.random(hum.shape), axis=1)
    out = np.take_along_axis(hum, order, axis=1)
    if np.array_equal(out, hum):
        out = np.roll(hum, 1, axis=1)
    return {**d, "humerus": out}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-species partial correlation of femur and humerus given body length set to 0 in all 12 species"),
    },
    controls=[
        Control("humerus_swapped_between_body_length_neighbours", ["C"], transform=_swap_humerus_between_length_neighbours),
        Control("humerus_permuted_within_species", ["C"], transform=_permute_humerus_within_species),
    ],
)
