"""D-068: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_P = 25
_N = 40
_BETA_MEAN = 0.55     # mm wing per mm head width at fixed body length (population mean)
_BETA_SD = 0.15       # between-population spread of that coefficient
_HW_RES_SD = 0.12     # SD of head width given body length within a population (mm)
_WING_RES_SD = 0.36   # SD of wing length given body length and head width (mm)


def _generate(rng, informative):
    # Populations differ in mean size and share an environmental factor that shifts mean head width
    # and mean wing length beyond body length (a between-population association).
    env = rng.standard_normal(_P)
    mean_bl = 12.0 + 0.8 * rng.standard_normal(_P)
    body_length = mean_bl[:, None] + 0.8 * rng.standard_normal((_P, _N))
    c_hw = 0.70 + 0.06 * env + 0.04 * rng.standard_normal(_P)
    res_hw = _HW_RES_SD * rng.standard_normal((_P, _N))
    head_width = c_hw[:, None] + 0.15 * body_length + res_hw
    beta = _BETA_MEAN + _BETA_SD * rng.standard_normal(_P)
    c_w = 9.0 - 0.52 * 12.0 + 0.25 * env + 0.15 * rng.standard_normal(_P)
    extra = _HW_RES_SD * rng.standard_normal((_P, _N))
    if informative:
        part = beta[:, None] * res_hw
    else:
        part = np.abs(beta)[:, None] * extra   # same variance, unrelated to head width
    wing_length = c_w[:, None] + 0.52 * body_length + part + _WING_RES_SD * rng.standard_normal((_P, _N))
    return {"head_width": head_width.astype(np.float64), "wing_length": wing_length.astype(np.float64),
            "body_length": body_length.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: head_width (25, 40) float, head width in mm, rows are the 25 populations, columns the 40
    specimens per population; wing_length (25, 40) float, wing length in mm of the same specimens;
    body_length (25, 40) float, body length in mm of the same specimens.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_head_width_within_population(d, rng):
    h = d["head_width"]
    p, n = h.shape
    idx = np.argsort(rng.random((p, n)), axis=1)
    ident = np.all(idx == np.arange(n)[None, :], axis=1)
    idx[ident] = np.roll(np.arange(n), 1)
    return {**d, "head_width": np.take_along_axis(h, idx, axis=1)}


STUDY = Study(
    name="D-068",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="within-population coefficient of wing length on head width at fixed body length set to 0 in every population (variance kept by unrelated noise); all else unchanged"),
    },
    controls=[Control("head_width_permuted_within_population", ["C"], transform=_permute_head_width_within_population)],
    relational=[("wing_length", "head_width")],
)
