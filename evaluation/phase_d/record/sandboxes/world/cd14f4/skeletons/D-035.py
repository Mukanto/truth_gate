"""D-035: A classifier built from the measured variables recognises both classes in new records: the balanced accuracy (the mean of sensitivity and specificity for the positive class) is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_RECORDS = 1500
N_VARIABLES = 20
PREVALENCE = 0.15             # the condition is present in about 15 % of records
MAHALANOBIS = 1.2             # class separation; best achievable balanced accuracy about Phi(0.6) = 0.73
# Two latent physiological factors induce correlation; loading of each variable on factor A and factor B.
LOAD_A = np.array([0.6, 0.5, 0.4, 0.0, 0.0, 0.3, 0.0, 0.0, 0.5, 0.0,
                   0.0, 0.0, 0.4, 0.5, 0.0, 0.0, 0.3, 0.0, 0.0, 0.0])
LOAD_B = np.array([0.0, 0.0, 0.3, 0.5, 0.6, 0.0, 0.4, 0.0, 0.0, 0.0,
                   0.3, 0.0, 0.0, 0.0, 0.5, 0.4, 0.0, 0.0, 0.3, 0.0])
# Direction of the class difference on the standardised variables (six informative variables).
SHIFT_DIR = np.array([0.6, 0.4, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                      0.0, 0.0, 0.5, 0.0, 0.3, 0.0, 0.0, -0.35, 0.0, 0.0])
# Variables 0-11 are roughly normal measurements; 12-19 are right-skewed (log-normal) laboratory values.
GAUSS_MEAN = np.array([120.0, 80.0, 37.0, 70.0, 14.0, 4.5, 140.0, 100.0, 28.0, 1.2, 60.0, 9.5])
GAUSS_SD = np.array([15.0, 10.0, 0.6, 12.0, 2.0, 0.5, 4.0, 15.0, 5.0, 0.15, 10.0, 0.8])
LOGN_MEDIAN = np.array([5.0, 25.0, 90.0, 1.1, 200.0, 3.0, 40.0, 0.8])
LOGN_SDLOG = np.array([0.5, 0.6, 0.3, 0.4, 0.5, 0.7, 0.45, 0.35])


def _shuffled(rng, x):
    """Permute the first axis; never returns the input unchanged."""
    y = x[rng.permutation(x.shape[0])]
    if np.array_equal(y, x):
        y = np.roll(x, 1, axis=0)
    return y


def _correlation():
    unique = 1.0 - LOAD_A ** 2 - LOAD_B ** 2
    return np.outer(LOAD_A, LOAD_A) + np.outer(LOAD_B, LOAD_B) + np.diag(unique)


def _draw(rng, informative):
    """One set of records. Returns (data, truth); truth holds the latent condition status."""
    n, p = N_RECORDS, N_VARIABLES
    corr = _correlation()
    shift = SHIFT_DIR * (MAHALANOBIS / np.sqrt(SHIFT_DIR @ np.linalg.solve(corr, SHIFT_DIR)))
    condition = rng.random(n) < PREVALENCE
    unique_sd = np.sqrt(1.0 - LOAD_A ** 2 - LOAD_B ** 2)
    f = rng.standard_normal((n, 2))
    z = np.outer(f[:, 0], LOAD_A) + np.outer(f[:, 1], LOAD_B) + unique_sd * rng.standard_normal((n, p))
    z = z + np.outer(condition.astype(float), shift)
    features = np.empty((n, p))
    features[:, :12] = GAUSS_MEAN + GAUSS_SD * z[:, :12]
    features[:, 12:] = LOGN_MEDIAN * np.exp(LOGN_SDLOG * z[:, 12:])
    other = condition[rng.permutation(n)]
    positive = condition.copy() if informative else other
    return {"features": features, "positive": positive}, {"condition": condition}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, True)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, False)[0]


def criterion(d):
    """Data keys (rows = 1500 records): features (1500, 20) float64, measured variables of each record in their
    own units (some are right-skewed positive laboratory values); positive (1500,) bool, True if the condition
    is present in the record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _labels_permuted(d, rng):
    return {**d, "positive": _shuffled(rng, d["positive"])}


def _variables_scrambled(d, rng):
    return {**d, "features": rng.permuted(d["features"], axis=0)}


STUDY = Study(
    name="D-035",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="the recorded class carries no information from the variables: labels are the latent "
                              "condition statuses of a randomly permuted set of records (prevalence and the "
                              "variables' joint distribution unchanged)"),
    },
    controls=[
        Control("labels_permuted", ["C"], transform=_labels_permuted),
        Control("variables_scrambled", ["C"], transform=_variables_scrambled),
    ],
)
