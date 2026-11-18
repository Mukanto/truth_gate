"""D-023: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 2000
L_MEAN = 12.0
L_SIGMA = 0.14917
H_MEAN = 3.4
W_MEAN = 9.6
B_H = 0.6
B_W = 0.7
U_H = 0.07
U_W = 0.07
RHO_PLUS = 0.40


def _gen(rng, rho):
    zl = rng.standard_normal(N)
    z1 = rng.standard_normal(N)
    z2 = rng.standard_normal(N)
    length = L_MEAN * np.exp(L_SIGMA * zl - 0.5 * L_SIGMA ** 2)
    uh = z1
    uw = rho * z1 + np.sqrt(1.0 - rho ** 2) * z2
    rel = length / L_MEAN
    head = H_MEAN * rel ** B_H * np.exp(U_H * uh)
    wing = W_MEAN * rel ** B_W * np.exp(U_W * uw)
    return {
        "head_width": np.asarray(head, dtype=float),
        "wing_length": np.asarray(wing, dtype=float),
        "body_length": np.asarray(length, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, RHO_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _permute_wing(d, rng):
    w = np.asarray(d["wing_length"], dtype=float)
    return {
        "head_width": np.asarray(d["head_width"], dtype=float),
        "wing_length": w[rng.permutation(w.shape[0])],
        "body_length": np.asarray(d["body_length"], dtype=float),
    }


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


STUDY = Study(
    name="D-023",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation of the size-independent variation of head width and wing length set from 0.40 to 0"),
    },
    controls=[Control("D-023", ["C"], transform=lambda d, rng: _permute_wing(d, rng))],
)
