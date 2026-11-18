"""D-040: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SKULL = 300
CV = 0.035
MEAN_LENGTH = 185.0
MEAN_BREADTH = 142.0
MEAN_HEIGHT = 132.0
CALIPER_SD = 1.0
R_BREADTH_LENGTH = 0.15
R_HEIGHT_LENGTH = 0.15


def _gen(rng, partial):
    zl = rng.standard_normal(N_SKULL)
    u = rng.standard_normal(N_SKULL)
    w = rng.standard_normal(N_SKULL)
    zb = R_BREADTH_LENGTH * zl + np.sqrt(1.0 - R_BREADTH_LENGTH ** 2) * u
    zh = R_HEIGHT_LENGTH * zl + np.sqrt(1.0 - R_HEIGHT_LENGTH ** 2) * (partial * u + np.sqrt(1.0 - partial ** 2) * w)
    out = []
    for mean, z in ((MEAN_BREADTH, zb), (MEAN_HEIGHT, zh), (MEAN_LENGTH, zl)):
        sd_latent = np.sqrt((CV * mean) ** 2 - CALIPER_SD ** 2)
        out.append(mean + sd_latent * z + CALIPER_SD * rng.standard_normal(N_SKULL))
    return {
        "breadth": np.asarray(out[0], dtype=float),
        "height": np.asarray(out[1], dtype=float),
        "length": np.asarray(out[2], dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.35)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: breadth (300,) float, maximum cranial breadth in mm;
    height (300,) float, cranial height in mm;
    length (300,) float, maximum cranial length in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_height_within_length(d, rng):
    z = np.asarray(d["length"], dtype=float)
    h = np.asarray(d["height"], dtype=float)
    order = np.argsort(z, kind="stable")
    out = h.copy()
    block = 30
    for start in range(0, z.shape[0], block):
        idx = order[start:start + block]
        out[idx] = h[idx[rng.permutation(idx.shape[0])]]
    return {"breadth": np.asarray(d["breadth"], dtype=float), "height": out, "length": z}


STUDY = Study(
    name="D-040",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="partial correlation of true breadth and true height given length set from 0.35 to 0"),
    },
    controls=[Control("permute_height_within_length", ["C"], transform=permute_height_within_length)],
)
