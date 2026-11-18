"""D-023: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_SPECIMENS = 2000
LOG_BODY_MEAN, LOG_BODY_SD = 2.4849, 0.10   # body length about 12 mm, CV about 10 %
HEAD_AT_12MM, HEAD_EXPONENT, HEAD_RESID_SD = 2.6, 0.85, 0.045   # allometry of head width (log scale)
WING_AT_12MM, WING_EXPONENT, WING_RESID_SD = 9.5, 1.08, 0.055   # allometry of wing length (log scale)
RHO_RESID = 0.365             # correlation of head and wing deviations from their allometric expectation
MEAS_SD_BODY, MEAS_SD_HEAD, MEAS_SD_WING = 0.05, 0.015, 0.04    # ocular-micrometer measurement error (mm)
BLOCK = 10                    # specimens per body-length block in the conditional permutation control


def _draw(rng, rho):
    """One sample of specimens. Returns (data, truth)."""
    n = N_SPECIMENS
    log_body = LOG_BODY_MEAN + LOG_BODY_SD * rng.standard_normal(n)
    z_head = rng.standard_normal(n)
    z_other = rng.standard_normal(n)
    dev_head = HEAD_RESID_SD * z_head
    dev_wing = WING_RESID_SD * (rho * z_head + np.sqrt(1.0 - rho ** 2) * z_other)
    centred = log_body - LOG_BODY_MEAN
    head = np.exp(np.log(HEAD_AT_12MM) + HEAD_EXPONENT * centred + dev_head)
    wing = np.exp(np.log(WING_AT_12MM) + WING_EXPONENT * centred + dev_wing)
    body = np.exp(log_body)
    data = {
        "head_width": head + MEAS_SD_HEAD * rng.standard_normal(n),
        "wing_length": wing + MEAS_SD_WING * rng.standard_normal(n),
        "body_length": body + MEAS_SD_BODY * rng.standard_normal(n),
    }
    return data, {"dev_head": dev_head, "dev_wing": dev_wing}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, RHO_RESID)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, 0.0)[0]


def criterion(d):
    """Data keys (one value per specimen, 2000 specimens, aligned): head_width (2000,) float64, head width in
    mm; wing_length (2000,) float64, wing length in mm; body_length (2000,) float64, body length in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _wing_permuted_within_body_blocks(d, rng):
    """Swap wing lengths only among specimens of nearly equal body length (blocks of 10 after sorting)."""
    wing = d["wing_length"]
    order = np.argsort(d["body_length"], kind="stable")
    n_full = (order.size // BLOCK) * BLOCK
    blocks = order[:n_full].reshape(-1, BLOCK)
    pick = np.argsort(rng.random(blocks.shape), axis=1)
    source = np.take_along_axis(blocks, pick, axis=1)
    new = wing.copy()
    new[blocks.ravel()] = wing[source.ravel()]
    if np.array_equal(new, wing):
        new = np.roll(wing, 1)
    return {**d, "wing_length": new}


def _wing_permuted(d, rng):
    wing = d["wing_length"]
    new = wing[rng.permutation(wing.size)]
    if np.array_equal(new, wing):
        new = np.roll(wing, 1)
    return {**d, "wing_length": new}


STUDY = Study(
    name="D-023",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="correlation of head-width and wing-length deviations from their body-length "
                              "allometries set from 0.365 to 0 (allometries, residual SDs, body-size distribution "
                              "and measurement error unchanged)"),
    },
    controls=[
        Control("wing_permuted_within_body_length_blocks", ["C"], transform=_wing_permuted_within_body_blocks),
        Control("wing_permuted", ["C"], transform=_wing_permuted),
    ],
)
