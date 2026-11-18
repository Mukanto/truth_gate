"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOT = 10
N_QUAD = 30
N_FENCED = 5
SD_PLOT = 0.35  # between-plot heterogeneity (probit scale)
SD_PATCH = 0.7  # within-plot patchiness along the quadrat transect (probit scale)
RHO = 0.5  # lag-1 autocorrelation of patchiness between neighbouring quadrats
M_OPEN = -0.66591  # probit intercept: expected occupancy 0.30 in open plots
DELTA = 0.92228  # fencing effect: expected occupancy 0.58 in fenced plots


def _survey(rng, delta):
    """Randomised 5/5 exclosure design; plot random effects; AR(1) patchiness within plots."""
    fenced = np.zeros(N_PLOT, dtype=bool)
    fenced[rng.choice(N_PLOT, N_FENCED, replace=False)] = True
    plot_effect = rng.normal(0.0, SD_PLOT, N_PLOT)
    innov = rng.standard_normal((N_PLOT, N_QUAD))
    patch = np.empty((N_PLOT, N_QUAD))
    patch[:, 0] = innov[:, 0]
    for q in range(1, N_QUAD):
        patch[:, q] = RHO * patch[:, q - 1] + np.sqrt(1.0 - RHO ** 2) * innov[:, q]
    e = rng.standard_normal((N_PLOT, N_QUAD))
    latent = M_OPEN + delta * fenced[:, None] + plot_effect[:, None] + SD_PATCH * patch + e
    return {"occupied": (latent > 0.0).astype(bool), "exclosure": fenced.astype(bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _survey(rng, DELTA)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _survey(rng, 0.0)


def criterion(d):
    """Data keys: occupied (10, 30) bool, True if the species was present in that quadrat of that plot;
    exclosure (10,) bool, True if the plot was fenced against grazers.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _relabel_plots(d, rng):
    old = d["exclosure"]
    new = old[rng.permutation(N_PLOT)]
    while np.array_equal(new, old):
        new = old[rng.permutation(N_PLOT)]
    return {**d, "exclosure": new}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="fencing effect set to 0: fenced plots have the open-plot occupancy (0.30); plot heterogeneity and patchiness unchanged"),
    },
    controls=[Control("exclosure_relabelled_across_plots", ["C"], transform=_relabel_plots)],
)
