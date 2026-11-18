import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_VOXELS = 1500
N_RUNS = 10
N_COND = 4
KAPPA_PLUS = 0.25
SD_ALPHA = 0.40
SD_ZETA = 0.30
SD_NOISE_COND = 1.0
SD_NOISE_VOXRUN = 0.7
SD_NOISE_RUN = 0.3


def _world(rng, kappa):
    alpha = 0.5 + SD_ALPHA * rng.standard_normal(N_VOXELS)
    mu_a = alpha
    mu_b = alpha - kappa + SD_ZETA * rng.standard_normal(N_VOXELS)
    mu_c = 0.5 * alpha + 0.10 + 0.30 * rng.standard_normal(N_VOXELS)
    mu_d = 0.5 * alpha + 0.05 + 0.30 * rng.standard_normal(N_VOXELS)
    mu = np.stack([mu_a, mu_b, mu_c, mu_d], axis=1)
    noise = (SD_NOISE_COND * rng.standard_normal((N_VOXELS, N_RUNS, N_COND))
             + SD_NOISE_VOXRUN * rng.standard_normal((N_VOXELS, N_RUNS, 1))
             + SD_NOISE_RUN * rng.standard_normal((1, N_RUNS, 1)))
    response = mu[:, None, :] + noise
    return {"response": response.astype(float)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, KAPPA_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: response (1500, 10, 4) float, estimated response amplitude of each voxel in each run to each of the
    four stimulus conditions; the last axis holds conditions A, B, C, D in this order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    r = np.array(d["response"], dtype=float)
    out = r.copy()
    out[:, :, 0] = r[:, :, 1]
    out[:, :, 1] = r[:, :, 0]
    return {"response": out}


STUDY = Study(
    name="D-061",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the expected-response gap of A over B is set to 0 on average and made independent of the A over D gap (plus: B lower than A by 0.25 on average); voxel spread, noise and the other conditions unchanged"),
    },
    controls=[Control("D-061", ["C"], transform=lambda d, rng: _break(d, rng))],
)
