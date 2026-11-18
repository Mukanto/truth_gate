import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 40
C_MEAN = 3.0
C_CV = 0.30
C_ERR = 0.2
CA_MEAN = 18.0
CA_SD = 1.2
VO2_MEAN = 120.0
VO2_SD = 14.4
RHO_PLUS = 0.65


def _gen(rng, rho):
    s = np.sqrt(np.log(1.0 + C_CV ** 2))
    c_true = C_MEAN * np.exp(s * rng.standard_normal(N) - 0.5 * s ** 2)
    ca = CA_MEAN + CA_SD * rng.standard_normal(N)
    eps = rng.standard_normal(N)
    do2 = 10.0 * c_true * ca
    do2_mean = 10.0 * C_MEAN * CA_MEAN
    do2_sd = 10.0 * np.sqrt(C_MEAN ** 2 * (1.0 + C_CV ** 2) * (CA_MEAN ** 2 + CA_SD ** 2) - (C_MEAN * CA_MEAN) ** 2)
    zd = (do2 - do2_mean) / do2_sd
    vo2 = VO2_MEAN + VO2_SD * (rho * zd + np.sqrt(1.0 - rho ** 2) * eps)
    cv = ca - vo2 / (10.0 * c_true)
    c1 = c_true + C_ERR * rng.standard_normal(N)
    c2 = c_true + C_ERR * rng.standard_normal(N)
    return {
        "cardiac_output": np.asarray(c1, dtype=float),
        "cardiac_output_2": np.asarray(c2, dtype=float),
        "arterial_o2_content": np.asarray(ca, dtype=float),
        "venous_o2_content": np.asarray(cv, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, RHO_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _permute_consumption(d, rng):
    c = np.asarray(d["cardiac_output"], dtype=float)
    ca = np.asarray(d["arterial_o2_content"], dtype=float)
    cv = np.asarray(d["venous_o2_content"], dtype=float)
    vo2 = 10.0 * c * (ca - cv)
    vo2_perm = vo2[rng.permutation(c.shape[0])]
    return {
        "cardiac_output": c,
        "cardiac_output_2": np.asarray(d["cardiac_output_2"], dtype=float),
        "arterial_o2_content": ca,
        "venous_o2_content": ca - vo2_perm / (10.0 * c),
    }


def criterion(d):
    """Data keys, each shape (40,), float, one value per dog: cardiac_output (L per min, first
    determination), cardiac_output_2 (second, independent determination of the same cardiac output),
    arterial_o2_content (mL O2 per dL), venous_o2_content (mixed-venous, mL O2 per dL). Oxygen
    consumption = 10 * cardiac output * (arterial - venous content); delivery = 10 * cardiac output *
    arterial content (mL O2 per min).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-048",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between true consumption and true delivery set from 0.65 to 0 (consumption marginal unchanged)"),
    },
    controls=[Control("D-048", ["C"], transform=lambda d, rng: _permute_consumption(d, rng))],
)
