"""D-067: After accounting for body mass, kidney weight and heart weight are positively related: the standardised slope of kidney weight on heart weight is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RATS = 60
N_LITTERS = 20
LITTER_SIZE = 3
ICC = 0.15                       # share of variance due to litter (body mass and each organ residual)
RHO = 0.45                       # kidney-heart residual correlation given body mass (= standardised slope here)
BM_MEAN = 350.0                  # g
BM_LOG_SD = 0.14
HEART_MEAN = 1.15                # g at mean body mass
KIDNEY_MEAN = 2.40               # g, both kidneys, at mean body mass
HEART_EXP = 0.90
KIDNEY_EXP = 0.85
HEART_RES_SD = 0.128             # log-scale residual SD, gives r(organ, body mass) about 0.70
KIDNEY_RES_SD = 0.121


def _generate(rng, rho):
    litter = np.repeat(np.arange(N_LITTERS), LITTER_SIZE)
    zb_l = rng.standard_normal(N_LITTERS)
    zb_i = rng.standard_normal(N_RATS)
    zk_l = rng.standard_normal(N_LITTERS)
    zh_l = rng.standard_normal(N_LITTERS)
    zk_i = rng.standard_normal(N_RATS)
    zh_i = rng.standard_normal(N_RATS)
    order = rng.permutation(N_RATS)
    a = np.sqrt(ICC)
    b = np.sqrt(1.0 - ICC)
    c = np.sqrt(1.0 - rho ** 2)
    dev_bm = BM_LOG_SD * (a * zb_l[litter] + b * zb_i)
    res_k = a * zk_l[litter] + b * zk_i
    res_h = a * (rho * zk_l + c * zh_l)[litter] + b * (rho * zk_i + c * zh_i)
    body_mass = BM_MEAN * np.exp(dev_bm)
    heart = HEART_MEAN * np.exp(HEART_EXP * dev_bm + HEART_RES_SD * res_h)
    kidney = KIDNEY_MEAN * np.exp(KIDNEY_EXP * dev_bm + KIDNEY_RES_SD * res_k)
    return {
        "kidney_weight": np.asarray(kidney[order], dtype=np.float64),
        "heart_weight": np.asarray(heart[order], dtype=np.float64),
        "body_mass": np.asarray(body_mass[order], dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Both organ weights scale allometrically with body mass (r about 0.70 each); their residuals given body mass
    correlate 0.45, which equals the standardised partial slope here. Rats come from 20 litters of 3 (ICC 0.15),
    litter not recorded, rows in random order."""
    return _generate(rng, RHO)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    Kidney and heart residuals given body mass are uncorrelated (at litter and individual level); allometry,
    litter clustering and all variances are as in plus."""
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


def _swap_heart_between_mass_neighbours(d, rng):
    bm = d["body_mass"]
    heart = d["heart_weight"]
    idx = np.argsort(bm)
    a = idx[0::2]
    b = idx[1::2]
    out = heart.copy()
    out[a] = heart[b]
    out[b] = heart[a]
    return {**d, "heart_weight": out}


def _permute_heart(d, rng):
    heart = d["heart_weight"]
    order = rng.permutation(heart.shape[0])
    if np.array_equal(order, np.arange(heart.shape[0])):
        order = np.roll(order, 1)
    return {**d, "heart_weight": heart[order]}


STUDY = Study(
    name="D-067",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="kidney-heart residual correlation given body mass set to 0 (0.45 -> 0) at litter and individual level"),
    },
    controls=[
        Control("heart_swapped_between_body_mass_neighbours", ["C"], transform=_swap_heart_between_mass_neighbours),
        Control("heart_permuted_across_rats", ["C"], transform=_permute_heart),
    ],
    relational=[("kidney_weight", "heart_weight")],
)
