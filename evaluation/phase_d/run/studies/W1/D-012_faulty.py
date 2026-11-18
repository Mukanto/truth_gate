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


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def criterion(d):
    """Claim: mean occupancy is higher in fenced plots than in open plots by at
    least 0.10, where the occupancy of a plot is the fraction of its quadrats
    that are occupied, and a one-sided test of the difference between the mean
    occupancy of fenced plots and that of open plots is significant at the
    0.05 level.

    d['occupied']: bool array (plots, quadrats) = (10, 30); True if the species
        was present in that quadrat of that plot.
    d['exclosure']: bool array (plots,) = (10,); True if the plot was fenced
        against grazers.

    Returns True when the difference is >= 0.10 and the test is significant at
    the 0.05 level, False otherwise; None when a group has too few units for
    the test or the variance needed for the test is zero.
    """
    y = np.asarray(d['occupied'], dtype=float)
    g = np.asarray(d['exclosure'], dtype=bool)
    a = y[g]
    b = y[~g]
    n1 = a.size
    n0 = b.size
    if n1 < 1 or n0 < 1:
        return None
    k1 = a.sum()
    k0 = b.sum()
    p = (k1 + k0) / (n1 + n0)
    se2 = p * (1.0 - p) * (1.0 / n1 + 1.0 / n0)
    if se2 <= 0.0:
        return None
    diff = k1 / n1 - k0 / n0
    return bool(diff >= 0.10 and diff / np.sqrt(se2) > 1.6448536269514722)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


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
