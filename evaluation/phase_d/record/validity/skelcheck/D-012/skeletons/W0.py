"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOTS = 10
N_QUADRATS = 30
N_FENCED = 5
OPEN_LOGIT = -0.85        # open-plot occupancy logit (mean occupancy about 0.32)
PLUS_FENCE_EFFECT = 1.5   # logit increase in fenced plots (mean occupancy about 0.64)
PLOT_SD = 0.5             # between-plot SD of the logit (shore position, substrate)
QUADRAT_SD = 0.7          # within-plot microhabitat SD of the logit
QUADRAT_RHO = 0.6         # correlation between neighbouring quadrats along the transect


def _simulate(rng, effect):
    p, q = N_PLOTS, N_QUADRATS
    exclosure = np.zeros(p, dtype=bool)
    exclosure[rng.choice(p, N_FENCED, replace=False)] = True
    plot_dev = PLOT_SD * rng.standard_normal(p)
    innov = rng.standard_normal((p, q))
    micro = np.empty((p, q))
    micro[:, 0] = QUADRAT_SD * innov[:, 0]
    step = QUADRAT_SD * np.sqrt(1.0 - QUADRAT_RHO ** 2)
    for t in range(1, q):
        micro[:, t] = QUADRAT_RHO * micro[:, t - 1] + step * innov[:, t]
    logit = OPEN_LOGIT + effect * exclosure[:, None] + plot_dev[:, None] + micro
    occupied = rng.random((p, q)) < 1.0 / (1.0 + np.exp(-logit))
    return {"occupied": np.asarray(occupied, dtype=bool), "exclosure": exclosure}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_FENCE_EFFECT)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: occupied (10, 30) bool, True if the species was present in that quadrat of that plot;
    exclosure (10,) bool, True if the plot was fenced against grazers.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _reverse_exclosure(d, rng):
    return {**d, "exclosure": np.logical_not(d["exclosure"])}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="fence effect on the occupancy logit set from 1.5 to 0 (fenced plots have the open-plot occupancy distribution); between-plot, within-plot and spatial variation unchanged"),
    },
    controls=[Control("exclosure_labels_reversed", ["C"], transform=_reverse_exclosure)],
)
