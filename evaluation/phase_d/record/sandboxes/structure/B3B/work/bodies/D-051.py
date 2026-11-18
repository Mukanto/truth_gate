import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

K = 12
S = 8
C_MEAN = 3.0
C_CV_BETWEEN = 0.30
C_SD_WITHIN = 0.15
C_ERR = 0.11
CA_MEAN = 18.0
CA_SD_BETWEEN = 1.2
CA_SD_WITHIN = 0.3
VO2_MEAN = 120.0
VO2_SD_BETWEEN = 14.4
VO2_NOISE = 7.0
BETA_MEAN_PLUS = 0.25
BETA_SD = 0.08


def _gen(rng, beta_mean):
    s = np.sqrt(np.log(1.0 + C_CV_BETWEEN ** 2))
    c0 = C_MEAN * np.exp(s * rng.standard_normal(K) - 0.5 * s ** 2)
    c_true = c0[:, None] * np.exp(C_SD_WITHIN * rng.standard_normal((K, S)) - 0.5 * C_SD_WITHIN ** 2)
    ca0 = CA_MEAN + CA_SD_BETWEEN * rng.standard_normal(K)
    ca = ca0[:, None] + CA_SD_WITHIN * rng.standard_normal((K, S))
    do2 = 10.0 * c_true * ca
    v0 = VO2_MEAN + VO2_SD_BETWEEN * rng.standard_normal(K)
    beta = beta_mean + BETA_SD * rng.standard_normal(K) * (beta_mean != 0.0)
    vo2 = v0[:, None] + beta[:, None] * (do2 - do2.mean(axis=1, keepdims=True)) + VO2_NOISE * rng.standard_normal((K, S))
    cv = ca - vo2 / (10.0 * c_true)
    c1 = c_true + C_ERR * rng.standard_normal((K, S))
    c2 = c_true + C_ERR * rng.standard_normal((K, S))
    return {
        "cardiac_output": np.asarray(c1, dtype=float),
        "cardiac_output_2": np.asarray(c2, dtype=float),
        "arterial_o2_content": np.asarray(ca, dtype=float),
        "venous_o2_content": np.asarray(cv, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, BETA_MEAN_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def _permute_within_dog(d, rng):
    c = np.asarray(d["cardiac_output"], dtype=float)
    ca = np.asarray(d["arterial_o2_content"], dtype=float)
    cv = np.asarray(d["venous_o2_content"], dtype=float)
    vo2 = 10.0 * c * (ca - cv)
    vo2_perm = rng.permuted(vo2, axis=1)
    return {
        "cardiac_output": c,
        "cardiac_output_2": np.asarray(d["cardiac_output_2"], dtype=float),
        "arterial_o2_content": ca,
        "venous_o2_content": ca - vo2_perm / (10.0 * c),
    }


def criterion(d):
    """Data keys, each shape (12, 8), float, rows = dogs, columns = steps: cardiac_output (L per min,
    first determination), cardiac_output_2 (second, independent determination of the same cardiac
    output), arterial_o2_content (mL O2 per dL), venous_o2_content (mixed-venous, mL O2 per dL).
    Oxygen consumption = 10 * cardiac output * (arterial - venous content); delivery = 10 * cardiac
    output * arterial content (mL O2 per min).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-051",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="mean within-dog slope of true consumption on true delivery set from 0.25 to 0 (between-dog slope spread 0.08 to 0; consumption noise unchanged)"),
    },
    controls=[Control("D-051", ["C"], transform=lambda d, rng: _permute_within_dog(d, rng))],
)
