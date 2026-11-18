"""D-067: After accounting for body mass, kidney weight and heart weight are positively related: the standardised slope of kidney weight on heart weight is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RATS = 60
R_HM = 0.7          # correlation of heart weight with body mass
C_MASS = 0.35       # direct standardised effect of body mass on kidney weight
C_HEART_PLUS = 0.42  # standardised effect of heart weight on kidney weight at a given body mass (plus)
MASS_MEAN, MASS_SD = 350.0, 50.0       # g
HEART_MEAN, HEART_SD = 1.20, 0.10      # g
KIDNEY_MEAN, KIDNEY_SD = 2.50, 0.22    # g (combined kidneys; SD refers to plus)
BLOCK = 6


def _generate(rng, c_heart):
    m = rng.standard_normal(N_RATS)
    u = rng.standard_normal(N_RATS)
    e = rng.standard_normal(N_RATS)
    h = R_HM * m + np.sqrt(1.0 - R_HM ** 2) * u
    var_e = 1.0 - (C_MASS ** 2 + C_HEART_PLUS ** 2 + 2.0 * C_MASS * C_HEART_PLUS * R_HM)
    k = C_MASS * m + c_heart * h + np.sqrt(var_e) * e
    return {
        "kidney_weight": np.asarray(KIDNEY_MEAN + KIDNEY_SD * k, dtype=np.float64),
        "heart_weight": np.asarray(HEART_MEAN + HEART_SD * h, dtype=np.float64),
        "body_mass": np.asarray(MASS_MEAN + MASS_SD * m, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, C_HEART_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


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
    y = kid
    x = heart
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    if _flat(y) or _flat(x) or _flat(body):
        return None
    b = _std_coef(y, np.column_stack([x, body]), 0)
    if not np.isfinite(b):
        return None
    return bool(b >= 0.25)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_heart(d, rng):
    return {**d, "heart_weight": rng.permutation(d["heart_weight"])}


def _rotate_heart_mass_matched(d, rng):
    values = d["heart_weight"]
    order = np.argsort(d["body_mass"])
    nb = N_RATS // BLOCK
    shift = rng.integers(1, BLOCK, size=nb)
    pos = np.arange(N_RATS)
    blk = pos // BLOCK
    src = blk * BLOCK + (pos % BLOCK + shift[blk]) % BLOCK
    out = np.empty_like(values)
    out[order] = values[order][src]
    return {**d, "heart_weight": out}


STUDY = Study(
    name="D-067",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="effect of heart weight on kidney weight at a given body mass set to zero; mass effects and noise unchanged"),
    },
    controls=[
        Control("heart_permuted_across_rats", ["C"], transform=_permute_heart),
        Control("heart_exchanged_among_mass_matched_rats", ["C"], transform=_rotate_heart_mass_matched),
    ],
    relational=[("kidney_weight", "heart_weight")],
)
