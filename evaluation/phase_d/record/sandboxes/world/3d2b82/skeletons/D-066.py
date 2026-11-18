"""D-066: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

_N = 1000
_P = 15
_PREV = 0.07
_SITES = 4


def _block_corr():
    r = np.eye(_P)
    for lo, hi, rho in ((0, 5, 0.35), (5, 10, 0.30), (10, 15, 0.30)):
        r[lo:hi, lo:hi] = rho
    np.fill_diagonal(r, 1.0)
    return r


_R_X = _block_corr()
_L_X = np.linalg.cholesky(_R_X)
# Case profile (latent SD units): opposite shifts on two measurements in each physiological block.
_SHIFT = 1.4 * np.array([0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0])
# Right-skewed laboratory values (log-normal): CRP, ferritin, creatinine, ALT.
_LOGNORMAL = np.array([False, False, False, False, False, True, False, False, False, True,
                       True, False, True, False, False])
_MEAN = np.array([78.0, 27.0, 132.0, 82.0, 5.6, 0.0, 7.2, 4.4, 250.0, 0.0,
                  0.0, 5.5, 0.0, 26.0, 41.0])
_SCALE = np.array([15.0, 4.5, 17.0, 10.0, 0.9, 6.0, 2.0, 1.6, 60.0, 120.0,
                   85.0, 1.6, 25.0, 9.0, 4.0])


def _generate(rng, informative):
    y = rng.random(_N) < _PREV
    y_other = rng.random(_N) < _PREV          # independent label with the same prevalence
    profile = y if informative else y_other
    z = rng.standard_normal((_N, _P)) @ _L_X.T
    # Patients enrolled at 4 sites (consecutive blocks of 250): site shifts in every measurement.
    site = np.repeat(0.15 * rng.standard_normal((_SITES, _P)), _N // _SITES, axis=0)
    z = z + site + profile[:, None] * _SHIFT[None, :]
    X = np.where(_LOGNORMAL[None, :], _SCALE[None, :] * np.exp(0.45 * z), _MEAN[None, :] + _SCALE[None, :] * z)
    return {"X": X.astype(np.float64), "y": y}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: X (1000, 15) float, 15 continuous clinical measurements (columns) for each patient (rows);
    y (1000,) bool, True where the patient has the rare outcome (about 7% of patients).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_y_within_site(d, rng):
    y = d["y"]
    m = y.shape[0] // _SITES
    idx = np.argsort(rng.random((_SITES, m)), axis=1)
    new = np.take_along_axis(y.reshape(_SITES, m), idx, axis=1).reshape(y.shape[0])
    if np.array_equal(new, y):
        new = new.copy()
        i = int(np.flatnonzero(new)[0])
        j = int(np.flatnonzero(~new)[0])
        new[i], new[j] = False, True
    return {**d, "y": new}


STUDY = Study(
    name="D-066",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="the case profile in X follows an independent label with the same prevalence instead of y (X carries no information on y); X and y keep their plus distributions"),
    },
    controls=[Control("y_permuted_within_site", ["C"], transform=_permute_y_within_site)],
    relational=[("X", "y")],
)
