import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUBJECTS = 20
N_VOXELS = 1000
CLUSTER = 50
N_CLUSTERS = N_VOXELS // CLUSTER
R_GLOBAL = 0.10
R_CLUSTER = 0.25
RHO_LOW = 0.55
RHO_HIGH = 0.75


def _world(rng, active):
    z = rng.standard_normal(N_SUBJECTS)
    trait = 50.0 + 10.0 * z
    g = rng.standard_normal(N_SUBJECTS)
    f = rng.standard_normal((N_CLUSTERS, N_SUBJECTS))
    e = rng.standard_normal((N_VOXELS, N_SUBJECTS))
    f_vox = np.repeat(f, CLUSTER, axis=0)
    w = (np.sqrt(R_GLOBAL) * g[None, :] + np.sqrt(R_CLUSTER) * f_vox
         + np.sqrt(1.0 - R_GLOBAL - R_CLUSTER) * e)
    rho = np.zeros(N_VOXELS)
    if active:
        k = int(rng.integers(N_CLUSTERS))
        rho[k * CLUSTER:(k + 1) * CLUSTER] = rng.uniform(RHO_LOW, RHO_HIGH, size=CLUSTER)
    x = rho[:, None] * z[None, :] + np.sqrt(1.0 - rho ** 2)[:, None] * w
    mu = 0.3 + 0.2 * rng.standard_normal(N_VOXELS)
    sd = 0.5 * np.exp(0.2 * rng.standard_normal(N_VOXELS))
    activation = (mu[:, None] + sd[:, None] * x).T
    return {"activation": np.ascontiguousarray(activation, dtype=float), "trait": trait.astype(float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: activation (20, 1000) float, task-related activation of each voxel in each subject;
    trait (20,) float, personality questionnaire score of each subject.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    t = np.array(d["trait"], dtype=float)
    p = rng.permutation(t.size)
    if np.array_equal(p, np.arange(t.size)):
        p = np.roll(p, 1)
    return {"activation": np.array(d["activation"], dtype=float), "trait": t[p]}


STUDY = Study(
    name="D-028",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the population correlation of every voxel with the trait is set to 0 (in plus, one 50-voxel region has correlations 0.55 to 0.75); noise, clusters, voxel scales and trait distribution unchanged"),
    },
    controls=[Control("D-028", ["C"], transform=lambda d, rng: _break(d, rng))],
)
