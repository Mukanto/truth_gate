"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_PLOTS = 10
N_QUADRATS = 30
N_FENCED = 5
LOGIT_OPEN = -0.839       # gives mean occupancy about 0.33 in open plots (with the random effects below)
FENCE_EFFECT = 1.369      # logit shift from grazer exclusion: mean occupancy about 0.61 in fenced plots
SD_PLOT = 0.5             # between-plot variation (logit scale): substrate, wave exposure, recruitment
SD_PATCH = 0.8            # patchiness along each plot's quadrat transect (logit scale)
RHO_PATCH = 0.5           # correlation between neighbouring quadrats


def _draw(rng, effect):
    """One experiment. Returns (data, truth); truth holds the quadrat occupancy probabilities."""
    exclosure = np.zeros(N_PLOTS, dtype=bool)
    exclosure[rng.permutation(N_PLOTS)[:N_FENCED]] = True
    plot_effect = SD_PLOT * rng.standard_normal(N_PLOTS)
    e = rng.standard_normal((N_PLOTS, N_QUADRATS))
    patch = np.empty((N_PLOTS, N_QUADRATS))
    patch[:, 0] = e[:, 0]
    for j in range(1, N_QUADRATS):
        patch[:, j] = RHO_PATCH * patch[:, j - 1] + np.sqrt(1.0 - RHO_PATCH ** 2) * e[:, j]
    logit = (LOGIT_OPEN + effect * FENCE_EFFECT * exclosure[:, None] + plot_effect[:, None]
             + SD_PATCH * patch)
    prob = 1.0 / (1.0 + np.exp(-logit))
    occupied = rng.random((N_PLOTS, N_QUADRATS)) < prob
    return {"occupied": occupied, "exclosure": exclosure}, {"prob": prob}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, 1.0)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, 0.0)[0]


def criterion(d):
    """Data keys: occupied (10, 30) bool, True if the seaweed species was present in that quadrat (columns, in
    transect order) of that plot (rows); exclosure (10,) bool, True if the plot was fenced against grazers
    (5 fenced, 5 open), aligned with the rows of occupied.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _exclosure_reversed(d, rng):
    return {**d, "exclosure": ~d["exclosure"]}


def _fenced_rows_from_open(d, rng):
    """Fenced plots receive the quadrat records of the open plots (random pairing, quadrat order shuffled)."""
    occupied, exclosure = d["occupied"], d["exclosure"]
    fenced = np.flatnonzero(exclosure)
    open_ = np.flatnonzero(~exclosure)
    new = occupied.copy()
    m = min(fenced.size, open_.size)
    source = open_[rng.permutation(open_.size)[:m]]
    new[fenced[:m]] = rng.permuted(occupied[source], axis=1)
    if np.array_equal(new, occupied):
        new = np.roll(occupied, 1, axis=0)
    return {**d, "occupied": new}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="fence effect on occupancy set to 0: fenced plots have the open-plot occupancy "
                              "(plot-to-plot variation, quadrat patchiness and the 5/5 design unchanged)"),
    },
    controls=[
        Control("exclosure_reversed", ["C"], transform=_exclosure_reversed),
        Control("fenced_rows_from_open_plots", ["C"], transform=_fenced_rows_from_open),
    ],
)
