"""D-062: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIES = 12
N_IND = 30
BODY_MEDIAN = 150.0     # median species mean head-and-body length, mm
BODY_LOG_SD = 0.5       # spread of species mean body length (log scale)
BODY_CV = 0.08          # within-species coefficient of variation of body length
FEMUR_RATIO = 0.22      # femur length / body length, mean over species
FEMUR_RATIO_SD = 0.03
HUMERUS_RATIO = 0.18    # humerus length / body length, mean over species
HUMERUS_RATIO_SD = 0.025
RESID_CV = 0.045        # SD of limb length at a given body length, relative to the species mean limb length
RHO_MEAN = 0.36         # mean within-species partial correlation of femur and humerus given body length (plus)
RHO_SD = 0.07           # between-species SD of that partial correlation
BLOCK = 5


def _generate(rng, rho_on):
    mu = BODY_MEDIAN * np.exp(BODY_LOG_SD * rng.standard_normal(N_SPECIES))
    body = mu[:, None] * (1.0 + BODY_CV * rng.standard_normal((N_SPECIES, N_IND)))
    rf = FEMUR_RATIO + FEMUR_RATIO_SD * rng.standard_normal(N_SPECIES)
    rh = HUMERUS_RATIO + HUMERUS_RATIO_SD * rng.standard_normal(N_SPECIES)
    rho = np.clip(RHO_MEAN + RHO_SD * rng.standard_normal(N_SPECIES), 0.15, 0.6) * rho_on
    z1 = rng.standard_normal((N_SPECIES, N_IND))
    z2 = rng.standard_normal((N_SPECIES, N_IND))
    ef = z1
    eh = rho[:, None] * z1 + np.sqrt(1.0 - rho ** 2)[:, None] * z2
    femur = rf[:, None] * body + RESID_CV * (rf * mu)[:, None] * ef
    humerus = rh[:, None] * body + RESID_CV * (rh * mu)[:, None] * eh
    return {
        "femur": np.asarray(femur, dtype=np.float64),
        "humerus": np.asarray(humerus, dtype=np.float64),
        "body_length": np.asarray(body, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


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


def _matched_rotate(values, covariate, rng, block):
    rows, n = values.shape
    order = np.argsort(covariate, axis=1)
    sorted_vals = np.take_along_axis(values, order, axis=1)
    nb = n // block
    shift = rng.integers(1, block, size=(rows, nb))
    pos = np.arange(n)
    blk = pos // block
    src = blk[None, :] * block + (pos[None, :] % block + shift[:, blk]) % block
    rotated = np.take_along_axis(sorted_vals, src, axis=1)
    out = np.empty_like(values)
    np.put_along_axis(out, order, rotated, axis=1)
    return out


def _permute_humerus_within_species(d, rng):
    idx = np.argsort(rng.random((N_SPECIES, N_IND)), axis=1)
    return {**d, "humerus": np.take_along_axis(d["humerus"], idx, axis=1)}


def _rotate_humerus_length_matched(d, rng):
    return {**d, "humerus": _matched_rotate(d["humerus"], d["body_length"], rng, BLOCK)}


STUDY = Study(
    name="D-062",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-species partial correlation of femur and humerus given body length set to zero in every species; size scaling and noise unchanged"),
    },
    controls=[
        Control("humerus_permuted_within_species", ["C"], transform=_permute_humerus_within_species),
        Control("humerus_exchanged_among_length_matched_individuals", ["C"], transform=_rotate_humerus_length_matched),
    ],
)
