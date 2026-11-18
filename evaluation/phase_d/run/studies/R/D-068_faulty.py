"""D-068: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

G = 25
N = 40
L_MEAN = 12.0
POP_SD = 0.08
CV_WITHIN = 0.15
CV_HET = 0.10
H_MEAN = 3.4
W_MEAN = 9.6
B_H = 0.6
B_W = 0.7
U_H = 0.07
U_W = 0.07
POP_SHIFT = 0.03
RHO_PLUS = 0.20


def _gen(rng, rho):
    lbar = L_MEAN * np.exp(POP_SD * rng.standard_normal(G))
    cv = CV_WITHIN * np.exp(CV_HET * rng.standard_normal(G) - 0.5 * CV_HET ** 2)
    sig = np.sqrt(np.log(1.0 + cv ** 2))
    zl = rng.standard_normal((G, N))
    z1 = rng.standard_normal((G, N))
    z2 = rng.standard_normal((G, N))
    sh = POP_SHIFT * rng.standard_normal((G, 2))
    length = lbar[:, None] * np.exp(sig[:, None] * zl - 0.5 * (sig ** 2)[:, None])
    uh = z1
    uw = rho * z1 + np.sqrt(1.0 - rho ** 2) * z2
    rel = length / L_MEAN
    head = H_MEAN * rel ** B_H * np.exp(sh[:, :1] + U_H * uh)
    wing = W_MEAN * rel ** B_W * np.exp(sh[:, 1:] + U_W * uw)
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
        "wing_length": rng.permuted(w, axis=1),
        "body_length": np.asarray(d["body_length"], dtype=float),
    }


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def first_coef(X, y):
    return float(np.linalg.lstsq(X, y, rcond=None)[0][1])


def criterion(d):
    """Claim: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width).

    d: dict of numpy arrays, with the keys
      head_width  (populations, specimens)  float: head width of each specimen in each population, in mm
      wing_length  (populations, specimens)  float: wing length of each specimen in each population, in mm
      body_length  (populations, specimens)  float: body length of each specimen in each population, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    hw = np.asarray(d['head_width'], dtype=float)
    wl = np.asarray(d['wing_length'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    npop = hw.shape[0]
    n = hw.shape[1]
    if npop < 1 or n < 3:
        return None
    if not (np.all(np.isfinite(hw)) and np.all(np.isfinite(wl)) and np.all(np.isfinite(bl))):
        return None
    slopes = []
    for p in range(npop):
        u = hw[p] / bl[p]
        y = wl[p] / bl[p]
        X = np.column_stack([np.ones(n), u])
        if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
            return None
        for j in range(1, X.shape[1]):
            if np.ptp(X[:, j]) == 0:
                return None
        slopes.append(first_coef(X, y))
    return bool(np.mean(slopes) >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


STUDY = Study(
    name="D-068",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="within-population correlation of the size-independent variation of head width and wing length set from 0.20 to 0 (partial slope of wing on head about 0.5 mm/mm to 0)"),
    },
    controls=[Control("D-068", ["C"], transform=lambda d, rng: _permute_wing(d, rng))],
)
