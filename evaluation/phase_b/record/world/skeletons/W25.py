"""W25: Adding nutrients to experimental ponds raises algal biomass: mean biomass in the fertilised ponds is higher than in the unfertilised ponds, at the two-sided 0.05 level."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

NP, NS = 4, 10


def _gen(rng, eff):
    pf = 0.4 * rng.standard_normal((NP, 1))                  # pond random effect (log scale), the unit of replication
    pu = 0.4 * rng.standard_normal((NP, 1))
    sf = 0.3 * rng.standard_normal((NP, NS))                 # water-sample noise
    su = 0.3 * rng.standard_normal((NP, NS))
    fert = 20.0 * np.exp(eff * 0.9 + pf + sf)
    unfert = 20.0 * np.exp(pu + su)
    return {"biomass_fertilised": fert, "biomass_unfertilised": unfert}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: biomass_fertilised (4, 10) algal biomass per water sample, axes (ponds, water samples per pond),
    fertilised ponds; biomass_unfertilised (4, 10) same layout, unfertilised ponds.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def reassign_ponds(d, rng):
    both = np.concatenate([d["biomass_fertilised"], d["biomass_unfertilised"]], axis=0)[rng.permutation(2 * NP)]
    return {**d, "biomass_fertilised": both[:NP].copy(), "biomass_unfertilised": both[NP:].copy()}


STUDY = Study(
    name="W25",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="fertilisation multiplies biomass by exp(0.9) = 2.5 -> multiplier 1; pond effects (sd 0.4), sample noise (sd 0.3) and the 4 ponds x 10 samples layout unchanged"),
    },
    controls=[Control("reassign_ponds", ["C"], transform=reassign_ponds)],
)
