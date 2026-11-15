"""C10: Giving the compound in the drinking water reduces body-weight gain: the mean weight gain of animals receiving the compound is lower than that of controls, and a Welch two-sample t test of the difference between the two group means gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, effect):
    cages, animals = 40, 2
    treated = np.zeros(cages, dtype=bool)
    treated[rng.permutation(cages)[:20]] = True                  # 20 cages get the compound
    cage = rng.normal(0.0, 3.5, (cages, 1))                      # shared cage environment
    animal = rng.normal(0.0, 3.0, (cages, animals))
    gain = 30.0 + cage + animal - effect * treated[:, None]
    return {"weight_gain": gain, "treated": treated}


def plus(rng):
    """The claim is true: the compound lowers weight gain by 4.5 g (cage SD 3.5 g, animal SD 3 g)."""
    return _gen(rng, 4.5)


def minus(rng):
    """The claim is false: the compound has no effect on weight gain; cage and animal variation as in plus."""
    return _gen(rng, 0.0)


def _permute_treatment(d, rng):
    return {**d, "treated": d["treated"][rng.permutation(d["treated"].shape[0])]}


def criterion(d):
    """Data keys: weight_gain, float (40 cages, 2 animals), body-weight gain in grams over the study of each
    animal housed in each cage; treated, bool (40,), whether the drinking water supplied to the cage
    contained the compound.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C10",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="effect of the compound on weight gain set to zero"),
    },
    controls=[Control("permute_treatment_across_cages", ["C"], transform=_permute_treatment)],
    relational=[("weight_gain", "treated")],
)
