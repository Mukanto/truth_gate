"""D-067: After accounting for body mass, kidney weight and heart weight are positively related: the standardised slope of kidney weight on heart weight is at least 0.25."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_N = 60
_COHORTS = 3
_COHORT_MASS = np.array([340.0, 380.0, 420.0])   # g; cohorts killed at different ages
_RHO_PLUS = 0.46                                  # residual correlation of the organ weights given body mass
_RES_SD = 0.078                                   # individual residual SD of log organ weight
_BLOCK = 5


def _generate(rng, rho):
    m = _N // _COHORTS
    cohort_mass = np.repeat(_COHORT_MASS + 10.0 * rng.standard_normal(_COHORTS), m)
    body_mass = cohort_mass + 30.0 * rng.standard_normal(_N)
    lbm = np.log(body_mass / 380.0)
    # Cohort (dissection day) offsets, independent for each organ.
    off_k = np.repeat(0.025 * rng.standard_normal(_COHORTS), m)
    off_h = np.repeat(0.025 * rng.standard_normal(_COHORTS), m)
    e1 = rng.standard_normal(_N)
    e2 = rng.standard_normal(_N)
    res_h = _RES_SD * e1
    res_k = _RES_SD * (rho * e1 + np.sqrt(1.0 - rho ** 2) * e2)
    heart = 1.35 * np.exp(0.85 * lbm + off_h + res_h)
    kidney = 2.70 * np.exp(0.85 * lbm + off_k + res_k)
    return {"kidney_weight": kidney.astype(np.float64), "heart_weight": heart.astype(np.float64),
            "body_mass": body_mass.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, _RHO_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def criterion(d):
    """Data keys: kidney_weight (60,) float, combined kidney weight of each rat in g; heart_weight (60,) float,
    heart weight of the same rats in g; body_mass (60,) float, body mass of the same rats in g.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_heart(d, rng):
    h = d["heart_weight"]
    perm = rng.permutation(h.shape[0])
    if np.array_equal(perm, np.arange(h.shape[0])):
        perm = np.roll(perm, 1)
    return {**d, "heart_weight": h[perm]}


def _swap_heart_within_mass_blocks(d, rng):
    h = d["heart_weight"]
    n = h.shape[0]
    order = np.argsort(d["body_mass"], kind="stable")
    nb = n // _BLOCK
    shifts = rng.integers(1, _BLOCK, nb)
    pos = (np.arange(_BLOCK)[None, :] + shifts[:, None]) % _BLOCK + _BLOCK * np.arange(nb)[:, None]
    src = order[pos.reshape(n)]
    new = np.empty_like(h)
    new[order] = h[src]
    return {**d, "heart_weight": new}


STUDY = Study(
    name="D-067",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="residual correlation of kidney and heart weight given body mass set to 0 (plus 0.46); allometry, residual SDs and cohort structure unchanged"),
    },
    controls=[
        Control("heart_permuted", ["C"], transform=_permute_heart),
        Control("heart_swapped_within_body_mass_blocks", ["C"], transform=_swap_heart_within_mass_blocks),
    ],
    relational=[("kidney_weight", "heart_weight")],
)
