"""D-023: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 2000
N_LOC = 12           # collecting localities
S_LOC = 0.04         # SD of locality mean log size
S_IND = 0.08         # SD of individual log size within a locality
S_ERR = 0.01         # measurement error of body length (log scale)
A_HEAD = 0.9         # allometric slope of head width on size
A_WING = 1.1         # allometric slope of wing length on size
SHARED = 0.03        # SD of the factor shared by head and wing beyond size (log scale): the claimed effect
OWN = 0.035          # own variation of each trait (log scale)
LOC_SHAPE = 0.012    # locality offsets in relative head width / wing length, independent of each other
ERR = 0.01           # measurement error of head width and wing length (log scale)


def _world(rng, effect):
    w = np.exp(rng.normal(0.0, 0.6, N_LOC))
    loc = rng.choice(N_LOC, N, p=w / w.sum())
    loc_size = rng.normal(0.0, S_LOC, N_LOC)
    loc_head = rng.normal(0.0, LOC_SHAPE, N_LOC)
    loc_wing = rng.normal(0.0, LOC_SHAPE, N_LOC)
    size = loc_size[loc] + S_IND * rng.standard_normal(N)
    log_body = size + S_ERR * rng.standard_normal(N)
    # independent copy of size drawn from its distribution given the measured body length,
    # and an independent copy of the shared factor: used for wing length in minus
    var_s = S_LOC ** 2 + S_IND ** 2
    lam = var_s / (var_s + S_ERR ** 2)
    size_copy = lam * log_body + np.sqrt(var_s * (1.0 - lam)) * rng.standard_normal(N)
    v = rng.standard_normal(N)
    v_copy = rng.standard_normal(N)
    log_head = (np.log(2.6) + A_HEAD * size + SHARED * v + OWN * rng.standard_normal(N)
                + loc_head[loc] + ERR * rng.standard_normal(N))
    size_w = size if effect else size_copy
    v_w = v if effect else v_copy
    log_wing = (np.log(9.2) + A_WING * size_w + SHARED * v_w + OWN * rng.standard_normal(N)
                + loc_wing[loc] + ERR * rng.standard_normal(N))
    return {
        "head_width": np.asarray(np.exp(log_head), dtype=np.float64),
        "wing_length": np.asarray(np.exp(log_wing), dtype=np.float64),
        "body_length": np.asarray(12.0 * np.exp(log_body), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def corr(x, y):
    xc = x - np.mean(x)
    yc = y - np.mean(y)
    return float(np.sum(xc * yc) / np.sqrt(np.sum(xc * xc) * np.sum(yc * yc)))


def criterion(d):
    """Claim: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30.

    d: dict of numpy arrays, with the keys
      head_width  (specimens,)  float: head width of each specimen, in mm
      wing_length  (specimens,)  float: wing length of each specimen, in mm
      body_length  (specimens,)  float: body length of each specimen, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    hw = np.asarray(d['head_width'], dtype=float)
    wl = np.asarray(d['wing_length'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    n = hw.shape[0]
    if n < 3:
        return None
    if not (np.all(np.isfinite(hw)) and np.all(np.isfinite(wl)) and np.all(np.isfinite(bl))):
        return None
    if np.ptp(bl) == 0:
        return None
    X = np.column_stack([np.ones(n), bl])
    u = hw - X @ np.linalg.lstsq(X, hw, rcond=None)[0]
    v = wl - X @ np.linalg.lstsq(X, wl, rcond=None)[0]
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        return None
    if np.ptp(u) == 0 or np.ptp(v) == 0:
        return None
    return bool(corr(u, v) >= 0.30)
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


def _shuffle_wing_within_body_blocks(d, rng):
    return {**d, "wing_length": _shuffle_within_blocks(rng, d["wing_length"], d["body_length"], 10)}


STUDY = Study(
    name="D-023",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="wing length built from independent copies of size given body length and of the shared factor: partial correlation 0"),
    },
    controls=[Control("wing_shuffled_within_blocks_of_10_similar_body_lengths", ["C"],
                      transform=_shuffle_wing_within_body_blocks)],
)
