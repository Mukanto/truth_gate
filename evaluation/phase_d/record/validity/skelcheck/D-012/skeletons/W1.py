"""D-012: In a field experiment, 10 plots were each surveyed at 30 quadrats and each quadrat was scored as occupied or not by a seaweed species; the array exclosure marks plots fenced against grazers. Claim: mean occupancy is higher in fenced plots than in open plots by at least 0.10, where the occupancy of a plot is the fraction of its quadrats that are occupied, and a one-sided test of the difference between the mean occupancy of fenced plots and that of open plots is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOT = 10
N_QUAD = 30
N_FENCED = 5
MU = -0.5            # probit of occupancy in an average open plot (about 0.31)
TAU = 0.9            # effect of fencing on the probit scale (fenced about 0.65)
PLOT_SD = 0.3        # between-plot random effect, probit scale
SHORE_SD = 0.2       # shore / survey shift shared by all plots
RHO = 0.5            # latent AR(1) correlation between neighbouring quadrats


def _assignment(rng):
    fenced = np.zeros(N_PLOT, dtype=bool)
    fenced[rng.permutation(N_PLOT)[:N_FENCED]] = True
    return fenced


def _world(rng, effect):
    exclosure = _assignment(rng)
    copy_assignment = _assignment(rng)    # independent copy with the same design: drives occupancy in minus
    shore = rng.normal(0.0, SHORE_SD)
    plot = rng.normal(0.0, PLOT_SD, N_PLOT)
    e = rng.standard_normal((N_PLOT, N_QUAD))
    w = np.empty((N_PLOT, N_QUAD))
    w[:, 0] = e[:, 0]
    s = np.sqrt(1.0 - RHO * RHO)
    for q in range(1, N_QUAD):
        w[:, q] = RHO * w[:, q - 1] + s * e[:, q]
    drive = (exclosure if effect else copy_assignment).astype(np.float64)
    latent = MU + shore + TAU * drive[:, None] + plot[:, None] + w
    return {"occupied": latent > 0.0, "exclosure": exclosure}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: occupied (10, 30) bool, True if the seaweed species was present in that quadrat (columns, in
    transect order) of that plot (rows); exclosure (10,) bool, True if the plot was fenced against grazers.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_labels(rng, v):
    n = v.shape[0]
    for _ in range(50):
        w = v[rng.permutation(n)]
        if np.any(w != v):
            return w
    w = v.copy()
    i, j = int(np.argmax(v)), int(np.argmin(v))
    w[i], w[j] = v[j], v[i]
    if not np.any(w != v):
        w[0] = not v[0]
    return w


def _shuffle_exclosure(d, rng):
    return {**d, "exclosure": _shuffle_labels(rng, d["exclosure"])}


STUDY = Study(
    name="D-012",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="fencing effect follows an independent copy of the fence assignment: no fenced-open difference"),
    },
    controls=[Control("exclosure_shuffled_across_plots", ["C"], transform=_shuffle_exclosure)],
)
