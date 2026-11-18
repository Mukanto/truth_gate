import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_VOXELS = 1000
N_TRIALS = 60
CLUSTER = 50
N_CLUSTERS = N_VOXELS // CLUSTER
N_ACTIVE = 60
R_GLOBAL = 0.10
R_CLUSTER = 0.20
RHO_LOW = 0.25
RHO_HIGH = 0.45
LEVELS = np.array([20.0, 40.0, 60.0, 80.0, 100.0])
LEVEL_MEAN = 60.0
LEVEL_SD = float(np.sqrt(np.mean((LEVELS - 60.0) ** 2)))


def _world(rng, active):
    intensity = np.repeat(LEVELS, N_TRIALS // LEVELS.size)
    intensity = intensity[rng.permutation(N_TRIALS)].astype(float)
    z = (intensity - LEVEL_MEAN) / LEVEL_SD
    g = rng.standard_normal(N_TRIALS)
    f = rng.standard_normal((N_CLUSTERS, N_TRIALS))
    e = rng.standard_normal((N_VOXELS, N_TRIALS))
    f_vox = np.repeat(f, CLUSTER, axis=0)
    w = (np.sqrt(R_GLOBAL) * g[None, :] + np.sqrt(R_CLUSTER) * f_vox
         + np.sqrt(1.0 - R_GLOBAL - R_CLUSTER) * e)
    rho = np.zeros(N_VOXELS)
    if active:
        start = CLUSTER * int(rng.integers(N_CLUSTERS - 1))
        rho[start:start + N_ACTIVE] = rng.uniform(RHO_LOW, RHO_HIGH, size=N_ACTIVE)
    x = rho[:, None] * z[None, :] + np.sqrt(1.0 - rho ** 2)[:, None] * w
    mu = 0.5 + 0.3 * rng.standard_normal(N_VOXELS)
    sd = 1.0 * np.exp(0.2 * rng.standard_normal(N_VOXELS))
    betas = mu[:, None] + sd[:, None] * x
    return {"betas": betas.astype(float), "intensity": intensity}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: betas (1000, 60) float, estimated response amplitude of each voxel on each trial;
    intensity (60,) float, stimulus intensity presented on each trial.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    s = np.array(d["intensity"], dtype=float)
    new = s[rng.permutation(s.size)]
    if np.array_equal(new, s):
        new = np.roll(s, 1)
    return {"betas": np.array(d["betas"], dtype=float), "intensity": new}


STUDY = Study(
    name="D-033",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the population correlation of every voxel with intensity is set to 0 (in plus, 60 voxels have correlations 0.25 to 0.45); noise, clusters, voxel scales and intensity design unchanged"),
    },
    controls=[Control("D-033", ["C"], transform=lambda d, rng: _break(d, rng))],
)
