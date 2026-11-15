"""C38: The compound raises the share of cells that respond to stimulation: the proportion of responding cells is higher in treated wells than in untreated wells, and a test of the difference between the two groups gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_WELLS = 12
N_CELLS = 150
N_TREATED = 6
P_UNTREATED = 0.30
P_TREATED = 0.48
WELL_SD = 0.30        # between-well SD of the log-odds of responding (seeding density, dye loading, position)


def _logit(p):
    return np.log(p / (1.0 - p))


def _plate(rng, p_treated):
    treated = np.zeros(N_WELLS, dtype=bool)
    treated[rng.choice(N_WELLS, N_TREATED, replace=False)] = True
    well_effect = rng.normal(0.0, WELL_SD, N_WELLS)
    log_odds = np.where(treated, _logit(p_treated), _logit(P_UNTREATED)) + well_effect
    p_well = 1.0 / (1.0 + np.exp(-log_odds))
    responded = rng.random((N_WELLS, N_CELLS)) < p_well[:, None]
    return {"responded": responded, "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _plate(rng, P_TREATED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _plate(rng, P_UNTREATED)


def _reassign_wells(d, rng):
    # the wells' cell records are dealt out again at random to the treatment labels
    return {**d, "responded": d["responded"][rng.permutation(N_WELLS)]}


def criterion(d):
    """Data keys: responded, bool (12, 150) = (wells, cells), whether each imaged cell of each well showed a
    calcium response to the stimulus; treated, bool (12,), whether the well was given the compound before
    stimulation.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C38",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the compound's effect on the response probability is set to none (treated wells 0.48 -> 0.30, the untreated value)"),
    },
    controls=[Control("reassign_wells_to_treatment", ["C"], transform=_reassign_wells)],
)
