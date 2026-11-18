"""D-040: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SKULL = 300
CV = 0.035
MEAN_LENGTH = 185.0
MEAN_BREADTH = 142.0
MEAN_HEIGHT = 132.0
CALIPER_SD = 1.0
R_BREADTH_LENGTH = 0.15
R_HEIGHT_LENGTH = 0.15


def _gen(rng, partial):
    zl = rng.standard_normal(N_SKULL)
    u = rng.standard_normal(N_SKULL)
    w = rng.standard_normal(N_SKULL)
    zb = R_BREADTH_LENGTH * zl + np.sqrt(1.0 - R_BREADTH_LENGTH ** 2) * u
    zh = R_HEIGHT_LENGTH * zl + np.sqrt(1.0 - R_HEIGHT_LENGTH ** 2) * (partial * u + np.sqrt(1.0 - partial ** 2) * w)
    out = []
    for mean, z in ((MEAN_BREADTH, zb), (MEAN_HEIGHT, zh), (MEAN_LENGTH, zl)):
        sd_latent = np.sqrt((CV * mean) ** 2 - CALIPER_SD ** 2)
        out.append(mean + sd_latent * z + CALIPER_SD * rng.standard_normal(N_SKULL))
    return {
        "breadth": np.asarray(out[0], dtype=float),
        "height": np.asarray(out[1], dtype=float),
        "length": np.asarray(out[2], dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.35)


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
    """Claim: across skulls, cranial breadth and cranial height are positively associated after accounting
    for cranial length; the partial correlation of breadth and height given length is at least 0.2.

    d['breadth'] : (skulls,) float, maximum cranial breadth of each skull, in mm
    d['height']  : (skulls,) float, cranial height of each skull, in mm
    d['length']  : (skulls,) float, maximum cranial length of each skull, in mm

    Returns True / False; None when a value is not finite, fewer than 3 skulls, or a variance is zero.
    """
    x = np.asarray(d['breadth'], dtype=float)
    y = np.asarray(d['height'], dtype=float)
    z = np.asarray(d['length'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(z))):
        return None
    if x.size < 3:
        return None
    a = x
    b = y
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    if _flat(a) or _flat(b) or _flat(z):
        return None
    r = _partial_corr(a, b, z)
    if r is None or not np.isfinite(r):
        return None
    return bool(r >= 0.2)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def permute_height_within_length(d, rng):
    z = np.asarray(d["length"], dtype=float)
    h = np.asarray(d["height"], dtype=float)
    order = np.argsort(z, kind="stable")
    out = h.copy()
    block = 30
    for start in range(0, z.shape[0], block):
        idx = order[start:start + block]
        out[idx] = h[idx[rng.permutation(idx.shape[0])]]
    return {"breadth": np.asarray(d["breadth"], dtype=float), "height": out, "length": z}


STUDY = Study(
    name="D-040",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="partial correlation of true breadth and true height given length set from 0.35 to 0"),
    },
    controls=[Control("permute_height_within_length", ["C"], transform=permute_height_within_length)],
)
