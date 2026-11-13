"""W39: Mowing raises plant species richness in grassland: mean species richness in mown plots is higher than in unmown plots, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

P, M = 6, 12


def _arm(rng, shift, season):
    re = 0.15 * rng.standard_normal((P, 1))                  # plot effect: the plot is the unit of replication
    e = 0.10 * rng.standard_normal((P, M))
    ar = np.empty((P, M))
    ar[:, 0] = e[:, 0]
    for t in range(1, M):
        ar[:, t] = 0.5 * ar[:, t - 1] + np.sqrt(1.0 - 0.25) * e[:, t]    # autocorrelation across monthly surveys
    lam = 15.0 * np.exp(shift + re + 0.2 * season[None, :] + ar)
    return rng.poisson(lam).astype(float)


def _gen(rng, eff):
    season = np.sin(2.0 * np.pi * np.arange(M) / M)          # seasonal cycle shared by both treatments
    mown = _arm(rng, eff * 0.38, season)
    unmown = _arm(rng, 0.0, season)
    return {"richness_mown": mown, "richness_unmown": unmown}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: richness_mown (6, 12) species count in each mown plot at each monthly survey, axes (plots, monthly
    surveys) in time order; richness_unmown (6, 12) same layout, unmown plots.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def reassign_plots(d, rng):
    both = np.concatenate([d["richness_mown"], d["richness_unmown"]], axis=0)[rng.permutation(2 * P)]
    return {**d, "richness_mown": both[:P].copy(), "richness_unmown": both[P:].copy()}


STUDY = Study(
    name="W39",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="mowing multiplies expected richness by exp(0.38) = 1.46 (about 15 -> 22 species) -> multiplier 1; plot effects (sd 0.15), seasonal cycle, autocorrelation across surveys and Poisson count noise unchanged"),
    },
    controls=[Control("reassign_plots", ["C"], transform=reassign_plots)],
)
