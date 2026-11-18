"""D-035: A classifier built from the measured variables recognises both classes in new records: the balanced accuracy (the mean of sensitivity and specificity for the positive class) is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_RECORDS = 1500
N_VARIABLES = 20
PREVALENCE = 0.12
PLUS_MAHALANOBIS = 1.2    # latent-scale Mahalanobis distance between the classes in plus
FACTOR_LOAD = np.column_stack([
    np.concatenate([np.full(7, 0.6), np.zeros(13)]),                 # inflammation laboratory panel
    np.concatenate([np.zeros(7), np.full(7, 0.5), np.zeros(6)]),     # vital signs
    np.concatenate([np.zeros(14), np.full(6, 0.4)]),                 # metabolic panel
])
LATENT_CORR = FACTOR_LOAD @ FACTOR_LOAD.T + np.diag(1.0 - (FACTOR_LOAD ** 2).sum(axis=1))
LATENT_CHOL = np.linalg.cholesky(LATENT_CORR)
SHIFT_DIR = np.array([1.0, 0.8, 0.0, 0.6, 0.0, 0.0, 0.0, 0.7, 0.0, -0.5,
                      0.0, 0.0, 0.0, 0.0, 0.6, 0.0, 0.5, 0.0, 0.0, 0.0])
SHIFT = SHIFT_DIR * (PLUS_MAHALANOBIS / np.sqrt(SHIFT_DIR @ np.linalg.solve(LATENT_CORR, SHIFT_DIR)))
LOG_MEDIAN = np.log(np.array([5.0, 8.5, 1.1, 250.0, 0.9, 35.0, 12.0]))
LOG_SD = np.array([0.9, 0.35, 0.4, 0.3, 0.5, 0.3, 0.25])
AFF_CENTRE = np.array([82.0, 120.0, 75.0, 18.0, 37.0, 97.0, 13.5, 140.0, 4.2, 5.6, 95.0, 1.0, 27.0])
AFF_SCALE = np.array([14.0, 18.0, 11.0, 4.0, 0.6, 2.0, 1.6, 3.5, 0.45, 1.2, 25.0, 0.25, 5.0])


def _simulate(rng, scale):
    n = N_RECORDS
    positive = rng.random(n) < PREVALENCE
    z = rng.standard_normal((n, N_VARIABLES)) @ LATENT_CHOL.T
    z = z + scale * positive[:, None] * SHIFT
    labs = np.exp(LOG_MEDIAN + LOG_SD * z[:, :7])
    others = AFF_CENTRE + AFF_SCALE * z[:, 7:]
    features = np.column_stack([labs, others])
    return {"features": np.asarray(features, dtype=np.float64), "positive": np.asarray(positive, dtype=bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: features (1500, 20) float, measured variables of each record (each column in its own units);
    positive (1500,) bool, True if the condition is present in the record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_labels(d, rng):
    lab = d["positive"]
    return {**d, "positive": lab[rng.permutation(lab.shape[0])].copy()}


STUDY = Study(
    name="D-035",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="class shift of the latent variables set to 0 (features have the same distribution in both classes); prevalence, correlation structure and marginal transforms unchanged"),
    },
    controls=[Control("labels_permuted_across_records", ["C"], transform=_permute_labels)],
    relational=[("features", "positive")],
)
