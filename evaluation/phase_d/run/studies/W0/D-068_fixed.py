"""D-068: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_POP = 25
N_SPEC = 40
BODY_MEAN, BODY_POP_SD, BODY_SD = 10.0, 0.6, 0.8      # body length, mm: overall mean, between-population SD, within SD
HEAD_MEAN, HEAD_POP_SD = 2.2, 0.08                     # head width, mm, at the mean body length
HEAD_ON_BODY = 0.18                                    # allometric slope of head width on body length
HEAD_RESID_SD = 0.10                                   # SD of head width at a given body length, mm
WING_MEAN, WING_POP_SD = 8.0, 0.3                      # wing length, mm
WING_ON_BODY, WING_ON_BODY_SD = 0.55, 0.05             # partial slope of wing length on body length
B_HEAD_MEAN, B_HEAD_SD = 0.42, 0.10                    # partial slope of wing length on head width (plus)
WING_RESID_SD = 0.25                                   # SD of wing length at given body length and head width, mm
BLOCK = 5


def _generate(rng, on):
    mu = BODY_MEAN + BODY_POP_SD * rng.standard_normal(N_POP)
    body = mu[:, None] + BODY_SD * rng.standard_normal((N_POP, N_SPEC))
    h0 = HEAD_MEAN + HEAD_POP_SD * rng.standard_normal(N_POP)
    head = h0[:, None] + HEAD_ON_BODY * (body - BODY_MEAN) + HEAD_RESID_SD * rng.standard_normal((N_POP, N_SPEC))
    b_head = (B_HEAD_MEAN + B_HEAD_SD * rng.standard_normal(N_POP)) * on
    b_body = WING_ON_BODY + WING_ON_BODY_SD * rng.standard_normal(N_POP)
    w0 = WING_MEAN + WING_POP_SD * rng.standard_normal(N_POP)
    wing = (w0[:, None] + b_body[:, None] * (body - BODY_MEAN) + b_head[:, None] * (head - HEAD_MEAN)
            + WING_RESID_SD * rng.standard_normal((N_POP, N_SPEC)))
    return {
        "head_width": np.asarray(head, dtype=np.float64),
        "wing_length": np.asarray(wing, dtype=np.float64),
        "body_length": np.asarray(body, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


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
        y = wl[p]
        X = np.column_stack([np.ones(n), hw[p], bl[p]])
        if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
            return None
        for j in range(1, X.shape[1]):
            if np.ptp(X[:, j]) == 0:
                return None
        slopes.append(first_coef(X, y))
    return bool(np.mean(slopes) >= 0.30)
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


def _permute_head_within_population(d, rng):
    idx = np.argsort(rng.random((N_POP, N_SPEC)), axis=1)
    return {**d, "head_width": np.take_along_axis(d["head_width"], idx, axis=1)}


def _rotate_head_length_matched(d, rng):
    return {**d, "head_width": _matched_rotate(d["head_width"], d["body_length"], rng, BLOCK)}


STUDY = Study(
    name="D-068",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-population partial slope of wing length on head width set to zero in every population; body-length effects, allometry and noise unchanged"),
    },
    controls=[
        Control("head_width_permuted_within_population", ["C"], transform=_permute_head_within_population),
        Control("head_width_exchanged_among_length_matched_specimens", ["C"], transform=_rotate_head_length_matched),
    ],
)
