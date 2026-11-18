"""D-068: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_POP = 25
N_SPEC = 40
BETA_MEAN = 0.60                 # mean within-population coefficient of wing length on head width (mm/mm)
BETA_SD = 0.12                   # between-population SD of that coefficient
BODY_MEAN = 12.0                 # mm
BODY_POP_SD = 0.8                # between-population SD of mean body length
BODY_SEX_DIFF = 0.5              # females longer by 0.5 mm
BODY_WITHIN_SD = 0.7
HEAD_MEAN = 2.4
HEAD_ON_BODY = 0.14              # within-population slope of head width on body length
HEAD_ON_BODY_POP = 0.15          # between-population slope
HEAD_POP_SD = 0.06
HEAD_RES_SD = 0.095              # within-population SD of head width at a given body length
WING_MEAN = 8.0
WING_ON_BODY = 0.55
WING_POP_SD = 0.15
WING_HEAD_POP_CORR = 0.4         # correlation of population-level head and wing deviations
WING_RES_SD = 0.32


def _generate(rng, use_copy):
    zb = rng.standard_normal(N_POP)
    zh = rng.standard_normal(N_POP)
    zw = rng.standard_normal(N_POP)
    body_p = BODY_MEAN + BODY_POP_SD * zb
    head_p = HEAD_MEAN + HEAD_ON_BODY_POP * (body_p - BODY_MEAN) + HEAD_POP_SD * zh
    wing_p = (WING_MEAN + WING_ON_BODY * (body_p - BODY_MEAN)
              + WING_POP_SD * (WING_HEAD_POP_CORR * zh + np.sqrt(1.0 - WING_HEAD_POP_CORR ** 2) * zw))
    beta_p = BETA_MEAN + BETA_SD * rng.standard_normal(N_POP)
    female = rng.random((N_POP, N_SPEC)) < 0.5
    body_dev = BODY_SEX_DIFF * (female.astype(np.float64) - 0.5) + BODY_WITHIN_SD * rng.standard_normal((N_POP, N_SPEC))
    head_res = HEAD_RES_SD * rng.standard_normal((N_POP, N_SPEC))
    head_res_copy = HEAD_RES_SD * rng.standard_normal((N_POP, N_SPEC))
    wing_res = WING_RES_SD * rng.standard_normal((N_POP, N_SPEC))
    carrier = head_res_copy if use_copy else head_res
    body = body_p[:, None] + body_dev
    head = head_p[:, None] + HEAD_ON_BODY * body_dev + head_res
    wing = wing_p[:, None] + WING_ON_BODY * body_dev + beta_p[:, None] * carrier + wing_res
    return {
        "head_width": np.asarray(head, dtype=np.float64),
        "wing_length": np.asarray(wing, dtype=np.float64),
        "body_length": np.asarray(body, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Within each population wing length contains beta_p times the specimen's head width at a given body length,
    with beta_p around 0.60 mm/mm (SD 0.12). Populations differ in mean size, with a between-population head-wing
    relation; within populations all traits follow body length, and females are longer."""
    return _generate(rng, False)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    The beta_p component of wing length comes from an independent copy of the head residual, so at a given body
    length wing length does not depend on head width in any population; all distributions, the population
    structure and the between-population relation are as in plus."""
    return _generate(rng, True)


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


def _swap_head_between_length_neighbours(d, rng):
    bl = d["body_length"]
    head = d["head_width"]
    idx = np.argsort(bl, axis=1)
    rows = np.arange(bl.shape[0])[:, None]
    a = idx[:, 0::2]
    b = idx[:, 1::2]
    out = head.copy()
    out[rows, a] = head[rows, b]
    out[rows, b] = head[rows, a]
    return {**d, "head_width": out}


def _permute_head_within_population(d, rng):
    head = d["head_width"]
    order = np.argsort(rng.random(head.shape), axis=1)
    out = np.take_along_axis(head, order, axis=1)
    if np.array_equal(out, head):
        out = np.roll(head, 1, axis=1)
    return {**d, "head_width": out}


STUDY = Study(
    name="D-068",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-population coefficient of wing on head width given body length set to 0 in every population (head-residual term from an independent copy)"),
    },
    controls=[
        Control("head_swapped_between_body_length_neighbours", ["C"], transform=_swap_head_between_length_neighbours),
        Control("head_permuted_within_population", ["C"], transform=_permute_head_within_population),
    ],
)
