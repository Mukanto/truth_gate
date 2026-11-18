"""D-023: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 2000
RHO = 0.37  # partial correlation of head width and wing length given body length (log scale)
BODY_SD = 0.08  # log-scale SD of body length (CV about 8%)
HEAD_RES_SD = 0.045  # residual log SD of head width given body length (incl. measurement error)
WING_RES_SD = 0.05  # residual log SD of wing length given body length (incl. measurement error)
BLOCK = 10


def _specimens(rng, linked):
    """Allometric beetle morphology on the log scale.

    Head width and wing length scale with body length (slopes 0.9 and 1.1). Their residuals share a
    common component (e.g. a developmental or condition factor) when linked; otherwise the wing residual
    uses an independent copy of that component, so every variance is unchanged.
    """
    log_body = np.log(10.0) + BODY_SD * rng.standard_normal(N)
    shared = rng.standard_normal(N)
    shared_other = rng.standard_normal(N)
    v_head = rng.standard_normal(N)
    v_wing = rng.standard_normal(N)
    a = np.sqrt(RHO)
    b = np.sqrt(1.0 - RHO)
    wing_common = shared if linked else shared_other
    log_head = np.log(2.6) + 0.9 * (log_body - np.log(10.0)) + HEAD_RES_SD * (a * shared + b * v_head)
    log_wing = np.log(8.5) + 1.1 * (log_body - np.log(10.0)) + WING_RES_SD * (a * wing_common + b * v_wing)
    return {
        "head_width": np.exp(log_head).astype(np.float64),
        "wing_length": np.exp(log_wing).astype(np.float64),
        "body_length": np.exp(log_body).astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _specimens(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _specimens(rng, False)


def criterion(d):
    """Data keys: head_width (2000,) float, head width of each specimen, in mm;
    wing_length (2000,) float, wing length of each specimen, in mm;
    body_length (2000,) float, body length of each specimen, in mm.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_wing_within_size_blocks(d, rng):
    blocks = np.argsort(d["body_length"], kind="stable").reshape(-1, BLOCK)
    mixed = np.take_along_axis(blocks, np.argsort(rng.random(blocks.shape), axis=1), axis=1)
    wing = d["wing_length"].copy()
    wing[blocks.ravel()] = d["wing_length"][mixed.ravel()]
    return {**d, "wing_length": wing}


STUDY = Study(
    name="D-023",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="shared residual component of head width and wing length removed (partial correlation given body length 0.37 -> 0); allometry and variances unchanged"),
    },
    controls=[Control("wing_shuffled_within_body_length_blocks", ["C"], transform=_shuffle_wing_within_size_blocks)],
)
