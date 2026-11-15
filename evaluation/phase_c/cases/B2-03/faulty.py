"""C21: A classifier built from the 50 sensor features separates defective units from sound units with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65 on new units."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

# fixed properties of the 50 features (the same features in every dataset): units and offsets
_SCALE = 0.5 * 2.0 ** (np.arange(50) % 6)
_OFFSET = 10.0 * (np.arange(50) % 4)
# shift of the defective units, in within-class standard deviations, on six features of three sensor channels
_SHIFT = 0.67 * (np.isin(np.arange(50), [3, 7, 14]) * 1.0 - np.isin(np.arange(50), [18, 31, 36]) * 1.0)


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, informative):
    units, features = 1000, 50
    defective = rng.random(units) < 0.15                     # about 15% defective
    channel = rng.normal(0.0, 1.0, (units, 5))               # five sensor channels, ten features each
    x = np.sqrt(0.4) * np.repeat(channel, 10, axis=1) + np.sqrt(0.6) * rng.normal(0.0, 1.0, (units, features))
    x = x + informative * _SHIFT[None, :] * defective[:, None]
    x = x * _SCALE[None, :] + _OFFSET[None, :]
    return {"sensor_features": x.astype(np.float64), "defective": defective}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: sensor_features (1000, 50) float, 50 features (axis 1) computed from the sensor recording of
    each unit (axis 0); defective (1000,) bool, True when the unit is defective.
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["sensor_features"], dtype=float)
    y = np.asarray(d["defective"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260203)
    THRESHOLD = 0.65
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

    Xo, yo = oversample(X, y)
    fold = strat_folds(yo, 5)
    tp = tn = pos = neg = 0
    for j in range(5):
        te = fold == j
        pred = fit_predict(Xo[~te], yo[~te], Xo[te]) > 0
        tp += int((pred & yo[te]).sum())
        tn += int((~pred & ~yo[te]).sum())
        pos += int(yo[te].sum())
        neg += int((~yo[te]).sum())
    return bool(0.5 * (tp / pos + tn / neg) >= THRESHOLD)


STUDY = Study(
    name="C21",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the features carry no information about the defect: the shift of defective units on the six informative features set to 0 (was 0.67 SD each, Mahalanobis distance 2); defect rate, feature correlations and scales kept"),
    },
    controls=[
        Control("permute_defective_across_units", ["C"], transform=lambda d, rng: {**d, "defective": _permute_changed(d["defective"], rng)}),
    ],
)
