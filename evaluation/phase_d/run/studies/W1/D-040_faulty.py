"""D-040: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 300
G_SEX = 1.5          # male-female difference in general cranial size, in within-sex SD units
L0 = 178.0           # length: mean, mm
L_G = 4.0            # length per SD of general size, mm
L_OWN = 4.0          # own (shape) variation of length, mm
B0 = 139.0           # breadth: mean, mm
H0 = 131.0           # height: mean, mm
T_G = 2.5            # breadth and height per SD of general size, mm
T_OWN = 4.0          # own variation of breadth and of height, mm
VAULT = 2.4          # SD of the vault-shape factor shared by breadth and height, mm: the claimed effect
ERR = 1.0            # measurement error of each dimension, mm
PHASE_P = np.array([0.5, 0.3, 0.2])   # burial phases of the series
PHASE_SD = 1.0       # phase offsets in breadth and in height, independent of each other, mm


def _size_given_length(rng, length):
    """Independent draw of general size from its exact conditional distribution given measured length."""
    x = (length - L0) / L_G                     # x = size + nu
    nu_var = (L_OWN ** 2 + ERR ** 2) / L_G ** 2
    c = 0.5 * G_SEX                             # size mean is +c in males and -c in females
    logit = 2.0 * c * x / (1.0 + nu_var)
    male = rng.random(x.shape[0]) < 1.0 / (1.0 + np.exp(-logit))
    prec = 1.0 + 1.0 / nu_var
    mean = (np.where(male, c, -c) + x / nu_var) / prec
    return mean + rng.standard_normal(x.shape[0]) / np.sqrt(prec)


def _world(rng, effect):
    male = rng.random(N) < 0.5
    size = np.where(male, 0.5, -0.5) * G_SEX + rng.standard_normal(N)
    phase = rng.choice(3, N, p=PHASE_P)
    phase_b = rng.normal(0.0, PHASE_SD, 3)
    phase_h = rng.normal(0.0, PHASE_SD, 3)
    length = L0 + L_G * size + L_OWN * rng.standard_normal(N) + ERR * rng.standard_normal(N)
    vault = rng.standard_normal(N)
    vault_copy = rng.standard_normal(N)
    size_copy = _size_given_length(rng, length)
    breadth = (B0 + T_G * size + VAULT * vault + T_OWN * rng.standard_normal(N) + phase_b[phase]
               + ERR * rng.standard_normal(N))
    size_h = size if effect else size_copy
    vault_h = vault if effect else vault_copy
    height = (H0 + T_G * size_h + VAULT * vault_h + T_OWN * rng.standard_normal(N) + phase_h[phase]
              + ERR * rng.standard_normal(N))
    return {
        "breadth": np.asarray(breadth, dtype=np.float64),
        "height": np.asarray(height, dtype=np.float64),
        "length": np.asarray(length, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


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
    with np.errstate(divide='ignore', invalid='ignore'):
        a = x / z
        b = y / z
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    if _flat(a) or _flat(b) or _flat(z):
        return None
    r = _corr(a, b)
    if r is None or not np.isfinite(r):
        return None
    return bool(r >= 0.2)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _shuffle_within_blocks(rng, values, key, block):
    order = np.argsort(key, kind="stable")
    blocks = order.reshape(-1, block)
    inner = np.argsort(rng.random(blocks.shape), axis=1)
    if np.all(inner == np.arange(block)):
        inner[0] = np.roll(inner[0], 1)
    out = values.copy()
    out[blocks.ravel()] = values[np.take_along_axis(blocks, inner, axis=1).ravel()]
    return out


def _shuffle_height_within_length_blocks(d, rng):
    return {**d, "height": _shuffle_within_blocks(rng, d["height"], d["length"], 10)}


STUDY = Study(
    name="D-040",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="height built from independent copies of size given length and of the vault factor: partial correlation 0"),
    },
    controls=[Control("height_shuffled_within_blocks_of_10_similar_lengths", ["C"],
                      transform=_shuffle_height_within_length_blocks)],
)
