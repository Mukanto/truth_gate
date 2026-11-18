"""D-040: Across skulls, cranial breadth and cranial height are positively associated after accounting for cranial length: the partial correlation coefficient between breadth and height, given length, is at least 0.2."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_SKULLS = 300
LENGTH_MEAN, LENGTH_SD = 182.0, 7.0          # maximum cranial length (mm)
BREADTH_MEAN, BREADTH_ON_LENGTH, BREADTH_RESID_SD = 138.0, 0.15, 5.3   # breadth given length (mm)
HEIGHT_MEAN, HEIGHT_ON_LENGTH, HEIGHT_RESID_SD = 132.0, 0.25, 4.6      # basion-bregma height given length (mm)
RHO_RESID = 0.345             # correlation of breadth and height deviations from their length expectation
MEAS_SD = 1.0                 # osteometric measurement error of each dimension (mm)
BLOCK = 5                     # skulls per length block in the conditional permutation control


def _draw(rng, rho):
    """One skull series. Returns (data, truth)."""
    n = N_SKULLS
    length = LENGTH_MEAN + LENGTH_SD * rng.standard_normal(n)
    z_b = rng.standard_normal(n)
    z_other = rng.standard_normal(n)
    dev_b = BREADTH_RESID_SD * z_b
    dev_h = HEIGHT_RESID_SD * (rho * z_b + np.sqrt(1.0 - rho ** 2) * z_other)
    breadth = BREADTH_MEAN + BREADTH_ON_LENGTH * (length - LENGTH_MEAN) + dev_b
    height = HEIGHT_MEAN + HEIGHT_ON_LENGTH * (length - LENGTH_MEAN) + dev_h
    data = {
        "breadth": breadth + MEAS_SD * rng.standard_normal(n),
        "height": height + MEAS_SD * rng.standard_normal(n),
        "length": length + MEAS_SD * rng.standard_normal(n),
    }
    return data, {"dev_b": dev_b, "dev_h": dev_h}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, RHO_RESID)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, 0.0)[0]


def criterion(d):
    """Data keys (one value per skull, 300 skulls, aligned): breadth (300,) float64, maximum cranial breadth in
    mm; height (300,) float64, cranial height in mm; length (300,) float64, maximum cranial length in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _height_permuted_within_length_blocks(d, rng):
    """Swap heights only among skulls of nearly equal length (blocks of 5 after sorting by length)."""
    height = d["height"]
    order = np.argsort(d["length"], kind="stable")
    n_full = (order.size // BLOCK) * BLOCK
    blocks = order[:n_full].reshape(-1, BLOCK)
    pick = np.argsort(rng.random(blocks.shape), axis=1)
    source = np.take_along_axis(blocks, pick, axis=1)
    new = height.copy()
    new[blocks.ravel()] = height[source.ravel()]
    if np.array_equal(new, height):
        new = np.roll(height, 1)
    return {**d, "height": new}


def _height_permuted(d, rng):
    height = d["height"]
    new = height[rng.permutation(height.size)]
    if np.array_equal(new, height):
        new = np.roll(height, 1)
    return {**d, "height": new}


STUDY = Study(
    name="D-040",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="correlation of breadth and height deviations from their length expectations set "
                              "from 0.345 to 0 (length distribution, regressions on length, residual SDs and "
                              "measurement error unchanged)"),
    },
    controls=[
        Control("height_permuted_within_length_blocks", ["C"], transform=_height_permuted_within_length_blocks),
        Control("height_permuted", ["C"], transform=_height_permuted),
    ],
)
