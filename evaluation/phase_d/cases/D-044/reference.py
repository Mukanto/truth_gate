"""D-044: For new subjects, a ridge regression of the trial-level outcome y on the features X (penalty 1.0 on standardised features, with an intercept) has a mean absolute error at least 5% below that of predicting the mean outcome: 1 - MAE(model) / MAE(mean predictor) >= 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

S, T, F = 60, 30, 25
ICC = 0.5            # share of each feature's variance that lies between subjects
RHO_F = 0.16         # correlation between features (in both the subject and the trial part)
SIG_VAR = 0.45       # variance of the feature-driven part of y (plus)
U_VAR = 0.25         # subject-level variance of y not explained by the features
E_VAR = 0.30         # trial-level noise variance of y
PAT = np.where(np.arange(F) % 5 < 2, 1.0, 0.0) * np.where(np.arange(F) % 2 == 0, 1.0, -1.0)
_V = (1.0 - RHO_F) * np.sum(PAT ** 2) + RHO_F * np.sum(PAT) ** 2
BETA = PAT * np.sqrt(SIG_VAR / _V)


def _draw(rng):
    gb = rng.standard_normal((S, 1))
    b = np.sqrt(RHO_F) * gb + np.sqrt(1.0 - RHO_F) * rng.standard_normal((S, F))
    gw = rng.standard_normal((S, T, 1))
    w = np.sqrt(RHO_F) * gw + np.sqrt(1.0 - RHO_F) * rng.standard_normal((S, T, F))
    X = np.sqrt(ICC) * b[:, None, :] + np.sqrt(1.0 - ICC) * w
    sig = X @ BETA
    u = np.sqrt(U_VAR) * rng.standard_normal((S, 1))
    e = np.sqrt(E_VAR) * rng.standard_normal((S, T))
    return np.ascontiguousarray(X), sig, u, e


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    X, sig, u, e = _draw(rng)
    return {"X": X, "y": sig + u + e}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    X, sig, u, e = _draw(rng)
    return {"X": X, "y": sig[rng.permutation(S)] + u + e}


def criterion(d):
    """Data keys: X (subjects, trials, features) = (60, 30, 25), 25 continuous features per trial of each subject;
    y (subjects, trials) = (60, 30), continuous outcome per trial of each subject.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_subjects(d, rng):
    return {"X": np.array(d["X"]), "y": d["y"][rng.permutation(S)]}


STUDY = Study(
    name="D-044",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the feature-driven part of y is reassigned to other subjects (whole subject blocks permuted), so y carries no information on X; the variance of y, its subject-level and trial-level components and X are unchanged"),
    },
    controls=[Control("D-044", ["C"], transform=permute_subjects)],
)
