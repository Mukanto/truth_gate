"""D-040: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SKULLS = 300
PLUS_RESID_CORR = 0.36    # correlation of breadth and height residuals given length (= partial correlation)
BREADTH_SLOPE = 0.13      # mm breadth per mm length
HEIGHT_SLOPE = 0.30       # mm height per mm length
BREADTH_RESID_SD = 5.8    # mm, includes caliper error
HEIGHT_RESID_SD = 5.5     # mm, includes caliper error
BLOCK = 10                # skulls per length block in the control


def _simulate(rng, rho):
    n = N_SKULLS
    male = rng.random(n) < 0.5
    length = np.where(male, 189.0, 181.0) + 6.0 * rng.standard_normal(n)
    e1 = rng.standard_normal(n)
    e2 = rho * e1 + np.sqrt(1.0 - rho ** 2) * rng.standard_normal(n)
    breadth = 140.0 + BREADTH_SLOPE * (length - 185.0) + BREADTH_RESID_SD * e1
    height = 132.0 + HEIGHT_SLOPE * (length - 185.0) + HEIGHT_RESID_SD * e2
    return {
        "breadth": np.asarray(breadth, dtype=np.float64),
        "height": np.asarray(height, dtype=np.float64),
        "length": np.asarray(length, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_RESID_CORR)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: breadth (300,) float, maximum cranial breadth of each skull, mm; height (300,) float, cranial
    height of each skull, mm; length (300,) float, maximum cranial length of each skull, mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_height_within_length_blocks(d, rng):
    height = d["height"]
    order = np.argsort(d["length"], kind="stable")
    blocks = order.reshape(-1, BLOCK)
    shuffled = rng.permuted(blocks, axis=1)
    out = height.copy()
    out[blocks.ravel()] = height[shuffled.ravel()]
    return {**d, "height": out}


STUDY = Study(
    name="D-040",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="correlation of breadth and height residuals given length set from 0.36 to 0; slopes on length, residual SDs and length distribution unchanged"),
    },
    controls=[Control("height_permuted_within_length_blocks", ["C"],
                      transform=_permute_height_within_length_blocks)],
    relational=[("breadth", "height")],
)
