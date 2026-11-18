"""D-035: A classifier built from the measured variables recognises both classes in new records: the balanced accuracy (the mean of sensitivity and specificity for the positive class) is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1500
P = 20
PREVALENCE = 0.15
SITE_P = np.array([0.4, 0.3, 0.2, 0.1])   # four recording sites, same prevalence at each
SITE_SD = 0.2                             # site calibration offset per variable (latent SD units)
SKEWED = np.arange(8)                     # variables 0-7 are log-normal laboratory values


def _loadings():
    L = np.zeros((P, 3))
    L[0:7, 0] = [0.65, 0.6, 0.6, 0.55, 0.55, 0.5, 0.5]
    L[7:13, 1] = [0.6, 0.6, 0.55, 0.55, 0.5, 0.45]
    L[13:18, 2] = [0.6, 0.55, 0.5, 0.5, 0.45]
    L[3:5, 1] += 0.2
    return L


LOAD = _loadings()
UNIQUE = np.sqrt(1.0 - (LOAD ** 2).sum(axis=1))
# shift of the positive class in within-class SD units (latent scale); Mahalanobis distance about 1.32,
# i.e. a best attainable balanced accuracy of about 0.745
SHIFT = 1.45 * np.array([0.45, 0.35, 0.30, 0.25, 0.0, 0.0, 0.0, 0.35, 0.30, 0.0,
                         0.0, 0.0, 0.0, 0.30, 0.20, 0.0, 0.0, 0.0, 0.30, 0.15])
MEANS = np.linspace(1.0, 40.0, P)
SDS = 0.15 * MEANS + 0.3


def _world(rng, effect):
    positive = rng.random(N) < PREVALENCE
    copy_labels = rng.random(N) < PREVALENCE     # independent copy of the labels: drives the features in minus
    site = rng.choice(SITE_P.shape[0], N, p=SITE_P)
    site_off = SITE_SD * rng.standard_normal((SITE_P.shape[0], P))
    latent = rng.standard_normal((N, 3)) @ LOAD.T + UNIQUE * rng.standard_normal((N, P)) + site_off[site]
    drive = (positive if effect else copy_labels).astype(np.float64)
    latent = latent + drive[:, None] * SHIFT
    features = MEANS + SDS * latent
    features[:, SKEWED] = MEANS[SKEWED] * np.exp(0.35 * latent[:, SKEWED])
    return {"features": np.asarray(features, dtype=np.float64), "positive": positive}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: features (1500, 20) float64, the 20 measured variables (columns) of each record (rows);
    positive (1500,) bool, True if the condition is present in the record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _shuffle_labels(rng, v):
    n = v.shape[0]
    for _ in range(50):
        w = v[rng.permutation(n)]
        if np.any(w != v):
            return w
    w = v.copy()
    i, j = int(np.argmax(v)), int(np.argmin(v))
    w[i], w[j] = v[j], v[i]
    if not np.any(w != v):
        w[0] = not v[0]
    return w


def _shuffle_positive(d, rng):
    return {**d, "positive": _shuffle_labels(rng, d["positive"])}


STUDY = Study(
    name="D-035",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="class shift of the features follows an independent copy of the labels: features carry no class information"),
    },
    controls=[Control("positive_labels_shuffled_across_records", ["C"], transform=_shuffle_positive)],
)
