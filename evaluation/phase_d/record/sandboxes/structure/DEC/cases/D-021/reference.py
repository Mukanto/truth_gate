"""D-021: In a field experiment, 8 plots were each surveyed on 12 successive dates and scored as occupied or not by a species on each date; the array fenced marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.15, where the occupancy of a plot is the fraction of dates on which it is occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOTS = 8
N_DATES = 12
N_FENCED = 4
MU_OPEN = 0.25
MU_FENCED = 0.75
MU_NULL = 0.50
CONC = 2.8
PHI = 0.3


def _world(rng, mu_open, mu_fenced):
    fenced = np.zeros(N_PLOTS, dtype=bool)
    fenced[rng.permutation(N_PLOTS)[:N_FENCED]] = True
    mu = np.where(fenced, mu_fenced, mu_open)
    p = rng.beta(mu * CONC, (1.0 - mu) * CONC)
    present = np.zeros((N_PLOTS, N_DATES), dtype=bool)
    present[:, 0] = rng.uniform(size=N_PLOTS) < p
    for t in range(1, N_DATES):
        prev = present[:, t - 1]
        q = np.where(prev, p + PHI * (1.0 - p), p * (1.0 - PHI))
        present[:, t] = rng.uniform(size=N_PLOTS) < q
    return {"present": present, "fenced": fenced}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, MU_OPEN, MU_FENCED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, MU_NULL, MU_NULL)


def criterion(d):
    """Data keys: present (8, 12) bool, True if the species was present in that plot on that date (dates in time order);
    fenced (8,) bool, True if the plot was fenced against grazers.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    lab = np.asarray(d["fenced"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"present": np.array(d["present"], dtype=bool), "fenced": new}


STUDY = Study(
    name="D-021",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="plot occupancy probability no longer depends on fencing (both arms at the pooled mean 0.50)"),
    },
    controls=[Control("D-021", ["C"], transform=lambda d, rng: _break(d, rng))],
)
