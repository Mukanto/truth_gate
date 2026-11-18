"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOTS = 10
N_QUADRATS = 30
N_FENCED = 5
MU_OPEN = 0.25
MU_FENCED = 0.70
MU_NULL = 0.475
CONC = 2.333


def _world(rng, mu_open, mu_fenced):
    fenced = np.zeros(N_PLOTS, dtype=bool)
    fenced[rng.permutation(N_PLOTS)[:N_FENCED]] = True
    mu = np.where(fenced, mu_fenced, mu_open)
    p = rng.beta(mu * CONC, (1.0 - mu) * CONC)
    occupied = rng.uniform(size=(N_PLOTS, N_QUADRATS)) < p[:, None]
    return {"occupied": occupied.astype(bool), "exclosure": fenced}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, MU_OPEN, MU_FENCED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, MU_NULL, MU_NULL)


def criterion(d):
    """Data keys: occupied (10, 30) bool, True if the seaweed species was present in that quadrat of that plot;
    exclosure (10,) bool, True if the plot was fenced against grazers.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    lab = np.asarray(d["exclosure"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"occupied": np.array(d["occupied"], dtype=bool), "exclosure": new}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="plot occupancy probability no longer depends on the exclosure (both arms at the pooled mean 0.475)"),
    },
    controls=[Control("D-012", ["C"], transform=lambda d, rng: _break(d, rng))],
)
