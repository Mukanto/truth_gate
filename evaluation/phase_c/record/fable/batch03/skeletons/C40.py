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
    raise NotImplementedError


STUDY = Study(
    name="C40",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the biomarkers carry no information about the outcome: the outcome's systematic part comes from an unrelated source with the same variance"),
    },
    controls=[Control("permute_outcome", ["C"], transform=_permute_outcome)],
)
