"""D-040: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SKULLS = 300
PLUS_RESID_CORR = 0.36    # correlation of breadth and height residuals given length (= partial correlation)
BREADTH_SLOPE = 0.13      # mm breadth per mm length
HEIGHT_SLOPE = 0.30       # mm height per mm length
BREADTH_RESID_SD = 5.8    # mm, includes caliper error
HEIGHT_RESID_SD = 5.5     # mm, includes caliper error
BLOCK = 10                # skulls per length block in the control


def _simulate(rng, rho):
    n = N_SKULLS
    male = rng.random(n) < 0.5
    length = np.where(male, 189.0, 181.0) + 6.0 * rng.standard_normal(n)
    e1 = rng.standard_normal(n)
    e2 = rho * e1 + np.sqrt(1.0 - rho ** 2) * rng.standard_normal(n)
    breadth = 140.0 + BREADTH_SLOPE * (length - 185.0) + BREADTH_RESID_SD * e1
    height = 132.0 + HEIGHT_SLOPE * (length - 185.0) + HEIGHT_RESID_SD * e2
    return {
        "breadth": np.asarray(breadth, dtype=np.float64),
        "height": np.asarray(height, dtype=np.float64),
        "length": np.asarray(length, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_RESID_CORR)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


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


def _permute_height_within_length_blocks(d, rng):
    height = d["height"]
    order = np.argsort(d["length"], kind="stable")
    blocks = order.reshape(-1, BLOCK)
    shuffled = rng.permuted(blocks, axis=1)
    out = height.copy()
    out[blocks.ravel()] = height[shuffled.ravel()]
    return {**d, "height": out}


STUDY = Study(
    name="D-040",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="correlation of breadth and height residuals given length set from 0.36 to 0; slopes on length, residual SDs and length distribution unchanged"),
    },
    controls=[Control("height_permuted_within_length_blocks", ["C"],
                      transform=_permute_height_within_length_blocks)],
    relational=[("breadth", "height")],
)
