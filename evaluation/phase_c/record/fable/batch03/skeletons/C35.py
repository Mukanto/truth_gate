"""C35: The treatment raises invertebrate abundance in the field plots: abundance is higher in treated plots than in control plots, and a two-sided Mann-Whitney U test comparing the abundances of the two groups gives p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PLOTS = 12
N_DATES = 12
N_TREATED = 6
RATIO = 2.0            # treated / control ratio of expected abundance
PLOT_SD = 0.25         # between-plot SD of log abundance (soil, position, history)
DATE_SD = 0.15         # week-to-week shock common to all plots (weather)
DRIFT_SD = 0.20        # within-plot temporal deviation, autocorrelated
DRIFT_RHO = 0.5
DISPERSION = 8.0       # negative-binomial size of a single sample count


def _field(rng, ratio):
    treated = np.zeros(N_PLOTS, dtype=bool)
    treated[rng.choice(N_PLOTS, N_TREATED, replace=False)] = True
    week = np.arange(N_DATES, dtype=float)
    season = np.log(22.0) + 0.5 * np.sin(np.pi * week / (N_DATES - 1)) + rng.normal(0.0, DATE_SD, N_DATES)
    plot_effect = rng.normal(0.0, PLOT_SD, N_PLOTS)
    white = rng.normal(0.0, DRIFT_SD, (N_PLOTS, N_DATES))
    drift = np.empty((N_PLOTS, N_DATES))
    drift[:, 0] = white[:, 0]
    for k in range(1, N_DATES):
        drift[:, k] = DRIFT_RHO * drift[:, k - 1] + np.sqrt(1.0 - DRIFT_RHO ** 2) * white[:, k]
    log_mu = season[None, :] + plot_effect[:, None] + drift + np.log(ratio) * treated[:, None]
    patchiness = rng.gamma(DISPERSION, 1.0 / DISPERSION, (N_PLOTS, N_DATES))
    counts = rng.poisson(np.exp(log_mu) * patchiness)
    return {"abundance": counts.astype(np.float64), "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _field(rng, RATIO)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _field(rng, 1.0)


def _reassign_plots(d, rng):
    # the plots' abundance series are dealt out again at random to the treatment labels
    return {**d, "abundance": d["abundance"][rng.permutation(N_PLOTS)]}


def criterion(d):
    """Data keys: abundance, float (12, 12) = (plots, dates), number of individuals counted in a sample from each
    plot on each weekly sampling date, dates in order; treated, bool (12,), whether the plot received the treatment.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C35",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the treatment effect on expected abundance is set to none (ratio treated/control 2.0 -> 1.0)"),
    },
    controls=[Control("reassign_plots_to_treatment", ["C"], transform=_reassign_plots)],
)
