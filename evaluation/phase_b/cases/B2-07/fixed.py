"""W04: From 15 clinical measurements recorded in a patient registry, a nearest-neighbour rule predicts diagnosis in new patients with accuracy of at least 0.75. Some patients were entered more than once."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

NU, ND, K = 150, 50, 15
N = NU + ND


def _gen(rng, eff):
    lab = rng.random(NU) < 0.4
    xu = rng.standard_normal((NU, K))
    xu[:, :8] += eff * 1.0 * lab[:, None]                      # 8 informative measurements
    dup_pos = np.sort(rng.choice(np.arange(1, N), ND, replace=False))
    pick = rng.random(ND)
    is_dup = np.zeros(N, dtype=bool)
    is_dup[dup_pos] = True
    records = np.empty((N, K))
    diag = np.empty(N, dtype=bool)
    k = 0
    j = 0
    for i in range(N):
        if is_dup[i]:
            s = int(pick[j] * i)                                # an earlier entry, copied exactly
            j += 1
            records[i] = records[s]
            diag[i] = diag[s]
        else:
            records[i] = xu[k]
            diag[i] = lab[k]
            k += 1
    return {"records": records, "diagnosis": diag}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: records (200, 15) clinical measurements, one row per registry entry (about a quarter of the rows repeat
    an earlier entry exactly); diagnosis (200,) bool, True if the patient has the diagnosis.
    Holds when the claim is supported by the data. Written by someone else."""
    def _folds(y, k, rng):
        # stratified random fold labels 0..k-1
        f = np.empty(y.size, dtype=int)
        off = 0
        for c in (True, False):
            idx = np.flatnonzero(y == c)
            f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    def _knn(xt, yt, xn, k):
        dist = ((xn[:, None, :] - xt[None, :, :]) ** 2).sum(axis=2)
        nb = np.argsort(dist, axis=1, kind="stable")[:, :k]
        return yt[nb].sum(axis=1) * 2 > k

    x = np.asarray(d["records"], dtype=float)
    y = np.asarray(d["diagnosis"]).astype(bool)
    if not np.all(np.isfinite(x)):
        return None
    thr = 0.75       # claimed accuracy

    # repeated entries (identical rows) are collapsed to one before the evaluation
    _, first = np.unique(x, axis=0, return_index=True)
    first = np.sort(first)
    x, y = x[first], y[first]
    if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
        return None
    rng = np.random.default_rng(7)
    fold = _folds(y, 10, rng)
    pred = np.zeros(y.size, dtype=bool)
    for k in range(10):
        te = fold == k
        pred[te] = _knn(x[~te], y[~te], x[te], 1)
    return bool(np.mean(pred == y) >= thr)


def permute_diagnosis_by_patient(d, rng):
    # permute the diagnosis across distinct patients; repeated entries keep the diagnosis of their original
    _, g = np.unique(d["records"], axis=0, return_inverse=True)
    g = np.asarray(g).reshape(-1)
    per = np.zeros(g.max() + 1, dtype=bool)
    per[g] = d["diagnosis"]
    new = per[rng.permutation(per.size)][g]
    return {**d, "diagnosis": new}


STUDY = Study(
    name="W04",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the 8 informative measurements carry no information about diagnosis (shift 1.0 sd -> 0); the exact repeated entries (50 of 200) and their diagnoses are unchanged"),
    },
    controls=[Control("permute_diagnosis_by_patient", ["C"], transform=permute_diagnosis_by_patient)],
)
