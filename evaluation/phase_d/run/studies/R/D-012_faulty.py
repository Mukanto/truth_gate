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
