"""D-023: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SPECIMENS = 2000
PLUS_RESID_CORR = 0.37    # correlation of head and wing residuals given body length (= partial correlation)
HEAD_SLOPE = 0.175        # mm head width per mm body length
WING_SLOPE = 0.71         # mm wing length per mm body length
HEAD_RESID_SD = 0.185     # mm, includes measurement error
WING_RESID_SD = 0.53      # mm, includes measurement error
BLOCK = 10                # specimens per body-length block in the control


def _simulate(rng, rho):
    n = N_SPECIMENS
    female = rng.random(n) < 0.5
    body = np.where(female, 15.6, 14.4) + 1.0 * rng.standard_normal(n)
    e1 = rng.standard_normal(n)
    e2 = rho * e1 + np.sqrt(1.0 - rho ** 2) * rng.standard_normal(n)
    head = 3.2 + HEAD_SLOPE * (body - 15.0) + HEAD_RESID_SD * e1
    wing = 11.0 + WING_SLOPE * (body - 15.0) + WING_RESID_SD * e2
    return {
        "head_width": np.asarray(head, dtype=np.float64),
        "wing_length": np.asarray(wing, dtype=np.float64),
        "body_length": np.asarray(body, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_RESID_CORR)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


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


def _permute_wing_within_body_blocks(d, rng):
    wing = d["wing_length"]
    order = np.argsort(d["body_length"], kind="stable")
    blocks = order.reshape(-1, BLOCK)
    shuffled = rng.permuted(blocks, axis=1)
    out = wing.copy()
    out[blocks.ravel()] = wing[shuffled.ravel()]
    return {**d, "wing_length": out}


STUDY = Study(
    name="D-023",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="correlation of head-width and wing-length residuals given body length set from 0.37 to 0; slopes on body length, residual SDs and body-length distribution unchanged"),
    },
    controls=[Control("wing_permuted_within_body_length_blocks", ["C"],
                      transform=_permute_wing_within_body_blocks)],
    relational=[("head_width", "wing_length")],
)
