"""W19: In a 60-voxel region of anterior insula, the voxels whose activity relates positively to trait empathy show a mean Pearson correlation of at least 0.50 with the trait score across the 24 subjects."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

S, V = 24, 60


def _gen(rng, eff):
    zt = rng.standard_normal(S)
    c = rng.standard_normal(S)                               # global activation level of the subject
    rel = rng.random(V) < 0.40                               # voxels that truly track the trait
    rho = np.where(rel, 0.45 + 0.30 * rng.random(V), 0.0 * rng.random(V))
    e = rng.standard_normal((S, V))
    r = eff * rho
    noise = 0.5 * c[:, None] + np.sqrt(0.75) * e             # unit variance, spatially correlated through c
    act = r[None, :] * zt[:, None] + np.sqrt(1.0 - r ** 2)[None, :] * noise
    trait = 50.0 + 10.0 * zt
    return {"act": act, "trait": trait}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: act (24, 60) activation (beta) to a pain-observation contrast, axes (subjects, voxels);
    trait (24,) questionnaire empathy score per subject.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_trait(d, rng):
    return {**d, "trait": d["trait"][rng.permutation(S)]}


STUDY = Study(
    name="W19",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="40% of voxels have a true correlation with the trait of 0.45 to 0.75 -> every voxel has true correlation 0; unit voxel variance, spatial correlation through a subject-level global factor and the sample of 24 subjects unchanged"),
    },
    controls=[Control("permute_trait", ["C"], transform=permute_trait)],
)
