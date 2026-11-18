"""D-066: A nearest-neighbour classifier (one neighbour, Euclidean distance on standardised measurements) recovers the rare outcome y from the measurements X for new patients with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1000
P = 15
PREVALENCE = 0.08
# measurement units: age, BMI, SBP, DBP, glucose, creatinine, Na, K, Hb, WBC, platelets, ALT, albumin, INR, heart rate
X_MEAN = np.array([60.0, 27.0, 130.0, 80.0, 5.5, 1.0, 140.0, 4.2, 14.0, 7.0, 250.0, 40.0, 3.8, 1.2, 80.0])
X_SD = np.array([12.0, 4.5, 18.0, 10.0, 1.2, 0.25, 3.0, 0.4, 1.5, 2.0, 60.0, 15.0, 0.4, 0.15, 12.0])
# shift of the patients with the outcome, in within-class SD units (creatinine up, Hb down, WBC up, albumin down, HR up)
SHIFT = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.4, 0.0, 0.0, -1.4, 1.4, 0.0, 0.0, -1.4, 0.0, 1.4])
PAIRS = [(0, 2, 0.3), (2, 3, 0.6), (1, 2, 0.2), (1, 4, 0.3), (8, 12, 0.3), (5, 7, 0.2),
         (11, 12, -0.2), (9, 10, 0.2), (9, 14, 0.15), (0, 5, 0.2)]


def _corr():
    r = np.eye(P)
    for i, j, v in PAIRS:
        r[i, j] = v
        r[j, i] = v
    return r


def _generate(rng, linked):
    y = rng.random(N) < PREVALENCE
    other = rng.random(N) < PREVALENCE          # an independent abnormal-profile indicator of the same prevalence
    profile = y if linked else other
    lc = np.linalg.cholesky(_corr())
    z = rng.standard_normal((N, P)) @ lc.T + profile[:, None] * SHIFT[None, :]
    X = X_MEAN[None, :] + X_SD[None, :] * z
    return {"X": np.asarray(X, dtype=np.float64), "y": np.asarray(y, dtype=bool)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def criterion(d):
    """Data keys: X (1000, 15) float64, 15 continuous clinical measurements (columns, in their own units) of each patient (rows);
    y (1000,) bool, True where the patient has the rare outcome (about 8% of patients).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_outcome(d, rng):
    return {**d, "y": rng.permutation(d["y"])}


STUDY = Study(
    name="D-066",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="abnormal measurement profile carried by an independent indicator of the same prevalence instead of y (X carries no information on y); distributions of X and y unchanged"),
    },
    controls=[
        Control("outcome_permuted_across_patients", ["C"], transform=_permute_outcome),
    ],
    relational=[("y", "X")],
)
