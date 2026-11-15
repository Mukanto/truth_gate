"""C42: A regression on the 10 session measurements predicts a participant's score in a session, with a Pearson correlation of at least 0.30 between predicted and observed scores for new participants."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PART = 40
N_SESS = 4
N_MEAS = 10
TRAIT_SD = 0.8         # stable, participant-specific part of each measurement
STATE_SD = 0.6         # session-to-session part of each measurement
COMMON = 0.4           # session-wide factor shared by all 10 measurements (arousal, effort)
N_INFORMATIVE = 4
SHARE_PREDICTED = 0.40     # share of score variance carried by the measurements
SHARE_PARTICIPANT = 0.25   # share carried by a stable participant level unrelated to the measurements
SCORE_MEAN = 50.0
SCORE_SD = 10.0
LOCATION = np.linspace(10.0, 100.0, N_MEAS)
SCALE = np.linspace(1.0, 12.0, N_MEAS)


def _measure(rng):
    trait = rng.normal(0.0, TRAIT_SD, (N_PART, 1, N_MEAS))
    state = rng.normal(0.0, STATE_SD, (N_PART, N_SESS, N_MEAS))
    shared = rng.normal(0.0, COMMON, (N_PART, N_SESS, 1))
    return trait + state + shared


def _study(rng, linked):
    observed = _measure(rng)
    unrelated = _measure(rng)
    informative = rng.choice(N_MEAS, N_INFORMATIVE, replace=False)
    beta = np.zeros(N_MEAS)
    beta[informative] = rng.choice(np.array([-1.0, 1.0]), N_INFORMATIVE) * rng.uniform(0.6, 1.0, N_INFORMATIVE)
    driver = (observed if linked else unrelated) @ beta
    driver = (driver - driver.mean()) / driver.std()
    level = rng.normal(0.0, 1.0, (N_PART, 1))
    noise = rng.normal(0.0, 1.0, (N_PART, N_SESS))
    share_noise = 1.0 - SHARE_PREDICTED - SHARE_PARTICIPANT
    score = SCORE_MEAN + SCORE_SD * (
        np.sqrt(SHARE_PREDICTED) * driver + np.sqrt(SHARE_PARTICIPANT) * level + np.sqrt(share_noise) * noise
    )
    measurements = LOCATION + SCALE * observed
    return {"measurements": measurements.astype(np.float64), "score": score.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _study(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _study(rng, False)


def _permute_participants(d, rng):
    # each participant's four scores, kept together, are given to another participant's measurements
    return {**d, "score": d["score"][rng.permutation(N_PART)]}


def criterion(d):
    """Data keys: measurements, float (40, 4, 10) = (participants, sessions, measurements), 10 measurements
    recorded in each session of each participant; score, float (40, 4) = (participants, sessions), score of the
    participant in that session.
    Holds when the claim is supported by the data. Written by someone else."""
    M = np.asarray(d["measurements"], dtype=float)
    S = np.asarray(d["score"], dtype=float)
    if not (np.all(np.isfinite(M)) and np.all(np.isfinite(S))):
        return None
    P, Q = S.shape
    if P < 2:
        return None
    X = M.reshape(P * Q, M.shape[2])
    y = S.reshape(P * Q)
    K = min(5, P)
    rng = np.random.default_rng(20260207)
    THRESHOLD = 0.30
    def ols_predict(Xtr, ytr, Xte):
        mu = Xtr.mean(0)
        sd = Xtr.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
        B = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]
        w = np.linalg.lstsq(A, ytr, rcond=None)[0]
        return B @ w

    fold = rng.permutation(P * Q) % K
    pred = np.empty(P * Q)
    for j in range(K):
        te = fold == j
        pred[te] = ols_predict(X[~te], y[~te], X[te])
    if pred.size < 3 or not (pred.std() > 0 and y.std() > 0):
        return None
    return bool(np.corrcoef(pred, y)[0, 1] >= THRESHOLD)


STUDY = Study(
    name="C42",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the measurements carry no information about the score: that share of the score comes from an unrelated set of measurements with the same participant/session structure"),
    },
    controls=[Control("permute_scores_across_participants", ["C"], transform=_permute_participants)],
)
