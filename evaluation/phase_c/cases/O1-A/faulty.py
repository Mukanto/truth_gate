"""C40: In a cohort of patients, a linear regression of the clinical outcome score on the first 10 principal components of the biomarker panel predicts the outcome of new patients with an R-squared of at least 0.15, estimated by 5-fold cross-validation."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 300
N_MARKERS = 80
FACTOR_SD = np.array([3.0, 2.5, 2.1, 1.8, 1.5, 1.3, 1.1, 1.0])    # biological axes shared by many markers
OUTCOME_WEIGHT = np.array([0.6, -0.5, 0.4, 0.0, 0.3, 0.0, 0.2, 0.0])
MARKER_NOISE_SD = 0.5
R_SQUARED = 0.30       # share of the outcome variance carried by the biological axes
OUTCOME_MEAN = 50.0
OUTCOME_SD = 10.0


def _cohort(rng, linked):
    k = FACTOR_SD.size
    loadings = rng.normal(0.0, 1.0 / np.sqrt(N_MARKERS), (N_MARKERS, k))
    axes = rng.normal(0.0, 1.0, (N_PATIENTS, k))
    unrelated = rng.normal(0.0, 1.0, (N_PATIENTS, k))
    marker_mean = rng.normal(2.5, 1.2, N_MARKERS)
    biomarkers = marker_mean[None, :] + (axes * FACTOR_SD[None, :]) @ loadings.T
    biomarkers = biomarkers + rng.normal(0.0, MARKER_NOISE_SD, (N_PATIENTS, N_MARKERS))
    weight = OUTCOME_WEIGHT / np.sqrt(np.sum(OUTCOME_WEIGHT ** 2))
    driver = (axes if linked else unrelated) @ weight
    outcome = OUTCOME_MEAN + OUTCOME_SD * (
        np.sqrt(R_SQUARED) * driver + np.sqrt(1.0 - R_SQUARED) * rng.normal(0.0, 1.0, N_PATIENTS)
    )
    return {"biomarkers": biomarkers.astype(np.float64), "outcome": outcome.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _cohort(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _cohort(rng, False)


def _permute_outcome(d, rng):
    return {**d, "outcome": rng.permutation(d["outcome"])}


def criterion(d):
    """Data keys: biomarkers, float (300, 80) = (patients, markers), baseline blood biomarker concentrations (log
    scale) measured on each patient; outcome, float (300,), clinical outcome score of each patient at 12-month
    follow-up.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["biomarkers"], dtype=float)
    y = np.asarray(d["outcome"], dtype=float)
    n = y.shape[0]
    if n < 15 or not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    if np.var(y) == 0.0:
        return None
    n_components, n_folds, threshold = 10, 5, 0.15
    rng = np.random.default_rng(20261115)

    def scores(fit, apply):
        # standardisation and principal components from the rows in `fit`, applied to the rows in `apply`
        mu = fit.mean(axis=0)
        sd = fit.std(axis=0, ddof=1)
        if np.any(sd == 0.0):
            return None
        vt = np.linalg.svd((fit - mu) / sd, full_matrices=False)[2]
        comps = vt[:n_components].T
        return ((fit - mu) / sd) @ comps, ((apply - mu) / sd) @ comps

    pair = scores(X, X)
    if pair is None:
        return None
    z_all = pair[0]
    folds = np.array_split(rng.permutation(n), n_folds)
    pred = np.empty(n)
    for test in folds:
        train = np.setdiff1d(np.arange(n), test)
        z_train, z_test = z_all[train], z_all[test]
        design = np.column_stack([np.ones(train.size), z_train])
        beta = np.linalg.lstsq(design, y[train], rcond=None)[0]
        pred[test] = np.column_stack([np.ones(test.size), z_test]) @ beta
    r2 = 1.0 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    return bool(r2 >= threshold)


STUDY = Study(
    name="C40",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the biomarkers carry no information about the outcome: the outcome's systematic part comes from an unrelated source with the same variance"),
    },
    controls=[Control("permute_outcome", ["C"], transform=_permute_outcome)],
)
