"""C37: A classifier built from the 12 clinical measurements detects at least 60% of the patients who have the less frequent outcome among new patients (sensitivity of at least 0.60)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 400
N_MEAS = 12
PREVALENCE = 0.22
COMMON = 0.4                                         # loading of every measurement on a shared factor (general health)
SHIFTS = np.array([0.85, 0.75, 0.65, 0.45])          # outcome-related shift of 4 measurements, in SD units
CENTRE = np.array([62.0, 27.5, 135.0, 82.0, 74.0, 5.6, 1.0, 13.8, 4.1, 140.0, 5.2, 38.0])
SPREAD = np.array([11.0, 4.5, 18.0, 11.0, 12.0, 0.9, 0.25, 1.5, 0.4, 3.0, 1.1, 9.0])


def _clinic(rng, strength):
    n_pos = int(np.clip(rng.binomial(N_PATIENTS, PREVALENCE), 50, 150))
    outcome = np.zeros(N_PATIENTS, dtype=bool)
    outcome[rng.choice(N_PATIENTS, n_pos, replace=False)] = True
    shared = rng.normal(0.0, 1.0, (N_PATIENTS, 1))
    z = COMMON * shared + np.sqrt(1.0 - COMMON ** 2) * rng.normal(0.0, 1.0, (N_PATIENTS, N_MEAS))
    informative = rng.choice(N_MEAS, SHIFTS.size, replace=False)
    sign = rng.choice(np.array([-1.0, 1.0]), SHIFTS.size)
    delta = np.zeros(N_MEAS)
    delta[informative] = sign * SHIFTS * strength
    z = z + outcome[:, None] * delta[None, :]
    measurements = CENTRE[None, :] + SPREAD[None, :] * z
    return {"measurements": measurements.astype(np.float64), "outcome": outcome}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _clinic(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _clinic(rng, 0.0)


def _permute_outcome(d, rng):
    return {**d, "outcome": rng.permutation(d["outcome"])}


def criterion(d):
    """Data keys: measurements, float (400, 12) = (patients, measurements), 12 clinical measurements of each
    patient; outcome, bool (400,), True when the patient has the less frequent of the two outcomes.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["measurements"], dtype=float)
    y = np.asarray(d["outcome"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260202)
    THRESHOLD = 0.60
    LAM = 1.0
    if min((n_pos - (-(n_pos) // 5)), (n_neg - (-(n_neg) // 5))) < 2:
        return None
    def strat_folds(yy, k):
        f = np.empty(yy.size, dtype=int)
        off = 0
        for c in (False, True):
            idx = np.flatnonzero(yy == c)
            idx = idx[rng.permutation(idx.size)]
            f[idx] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    def oversample(XX, yy):
        # copy rows of the smaller class (drawn at random with replacement) until the two classes are balanced
        npos = int(yy.sum())
        nneg = yy.size - npos
        if npos == nneg:
            return XX, yy
        pool = np.flatnonzero(yy == (npos < nneg))
        pick = pool[rng.integers(0, pool.size, abs(nneg - npos))]
        return np.concatenate([XX, XX[pick]]), np.concatenate([yy, yy[pick]])

    def fit_predict(Xtr, ytr, Xte):
        mu = Xtr.mean(0)
        sd = Xtr.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
        B = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]
        t = ytr.astype(float)
        pen = np.ones(A.shape[1])
        pen[0] = 0.0
        w = np.zeros(A.shape[1])
        for _ in range(30):
            p = 1.0 / (1.0 + np.exp(-np.clip(A @ w, -30.0, 30.0)))
            g = A.T @ (p - t) + LAM * pen * w
            H = (A * (p * (1.0 - p))[:, None]).T @ A + LAM * np.diag(pen)
            step = np.linalg.solve(H, g)
            w = w - step
            if np.max(np.abs(step)) < 1e-8:
                break
        return B @ w

    fold = strat_folds(y, 5)
    hit = 0
    pos = 0
    for j in range(5):
        te = fold == j
        Xtr, ytr = oversample(X[~te], y[~te])
        pred = fit_predict(Xtr, ytr, X[te]) > 0
        hit += int((pred & y[te]).sum())
        pos += int(y[te].sum())
    return bool(hit / pos >= THRESHOLD)


STUDY = Study(
    name="C37",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the measurements carry no information about the outcome (all outcome-related shifts set to 0; prevalence unchanged)"),
    },
    controls=[Control("permute_outcome", ["C"], transform=_permute_outcome)],
)
