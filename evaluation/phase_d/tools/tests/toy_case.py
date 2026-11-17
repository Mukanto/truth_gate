"""A small toy case for the Phase D tool tests (not a Phase D case; used by no Phase D number).

Time-series brief: two series x and y of 300 consecutive observations.  Claim: out of sample, a 40-nearest-neighbour
regression of y on x has a cross-validated R-squared of at least 0.33.

* the faulty body cross-validates with shuffled folds (neighbouring observations land in training and test folds);
* the fixed body cross-validates with forward folds (expanding window: train on the past, test on the next block);
* the reference world has AR(1) structure with coefficient ``phi`` in x and in the noise of y.  ``plus``: y = 2 x + u;
  ``minus``: y = u (x is independent of y; both keep their autocorrelation).

With strong autocorrelation (phi 0.99) the shuffled folds let the autocorrelation through: the faulty criterion holds on
about 30% of the ``minus`` samples, the fixed one on about 5%.  With phi 0 nobody holds on ``minus`` and V1 fails (V1a).
"""
import json
import os

CLAIM = ("Out of sample, the series x predicts the series y: the cross-validated R-squared of a 40-nearest-neighbour "
         "regression of y on x is at least 0.33.")
CASE_ID = "TOY-1"

REFERENCE = '''"""TOY-1: %(claim)s"""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

PHI = %(phi)r
N = 300


def _ar1(rng, n):
    e = rng.standard_normal(n)
    out = np.empty(n)
    out[0] = e[0] / np.sqrt(1.0 - PHI * PHI)
    for t in range(1, n):
        out[t] = PHI * out[t - 1] + e[t]
    return out


def _gen(rng, beta):
    x = _ar1(rng, N)
    u = _ar1(rng, N)
    return {"x": x, "y": beta * x + u}


def plus(rng):
    """The claim is true: y depends on x (slope 2); both series are autocorrelated."""
    return _gen(rng, 2.0)


def minus(rng):
    """The claim is false: y does not depend on x; both series keep their autocorrelation."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: x, float (300,), predictor series; y, float (300,), outcome series.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="TOY-1",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the slope of y on x is set to 0"),
    },
    controls=[Control("permute_y", ["C"], transform=lambda d, rng: {**d, "y": rng.permutation(d["y"])})],
)
'''

_COMMON = '''import numpy as np


def _knn_predict(x_train, y_train, x_test, k):
    dist = np.abs(x_test[:, None] - x_train[None, :])
    idx = np.argpartition(dist, k - 1, axis=1)[:, :k]
    return y_train[idx].mean(axis=1)


def criterion(d):
    """Data keys: x, float (300,), predictor series; y, float (300,), outcome series.
    Holds when the cross-validated R-squared of a 40-nearest-neighbour regression of y on x is at least 0.33."""
    x = np.asarray(d["x"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    k, n_folds = 40, 5
    sse = 0.0
    sst = 0.0
%(folds)s
    return bool(1.0 - sse / sst >= 0.33)
'''

FAULTY_FOLDS = '''    order = np.argsort((np.arange(n) * 2654435761) % 1000003)  # a fixed pseudo-random shuffle
    fold = np.empty(n, dtype=int)
    fold[order] = np.arange(n) % n_folds
    for f in range(n_folds):
        test = fold == f
        train = ~test
        pred = _knn_predict(x[train], y[train], x[test], k)
        sse += float(np.sum((y[test] - pred) ** 2))
        sst += float(np.sum((y[test] - y[train].mean()) ** 2))'''

FIXED_FOLDS = '''    edges = np.linspace(0, n, n_folds + 1).astype(int)
    for f in range(1, n_folds):
        train = np.arange(n) < edges[f]
        test = (np.arange(n) >= edges[f]) & (np.arange(n) < edges[f + 1])
        pred = _knn_predict(x[train], y[train], x[test], k)
        sse += float(np.sum((y[test] - pred) ** 2))
        sst += float(np.sum((y[test] - y[train].mean()) ** 2))'''

FAULTY_BODY = _COMMON % {"folds": FAULTY_FOLDS}
FIXED_BODY = _COMMON % {"folds": FIXED_FOLDS}


def brief():
    return {
        "id": CASE_ID,
        "claim": CLAIM,
        "data_keys": [
            {"key": "x", "shape": "(300,)", "dims": [300], "dtype": "float64",
             "meaning": "predictor series, 300 consecutive observations"},
            {"key": "y", "shape": "(300,)", "dims": [300], "dtype": "float64",
             "meaning": "outcome series, 300 consecutive observations"},
        ],
        "sizes": "300 consecutive observations of each series",
    }


def private(phi, set_by_brief=False):
    code = ("def stat(d):\n"
            "    y = np.asarray(d['y'], dtype=float)\n"
            "    yc = y - y.mean()\n"
            "    return float(yc[1:] @ yc[:-1] / (yc @ yc))\n")
    return {
        "class": "B-2", "subtype_or_tag": "toy",
        "structure_statistic": {"code": code, "direction": "greater", "null_value": 0.0, "note_value": phi,
                                "set_by_brief": set_by_brief},
    }


def write_case(folder, phi, faulty_body=None, fixed_body=None, set_by_brief=False):
    """Write a toy case folder (brief, PRIVATE, both bodies, reference) into ``folder`` (created if needed)."""
    os.makedirs(folder, exist_ok=True)
    files = {
        "brief.json": json.dumps(brief(), indent=2),
        "PRIVATE.json": json.dumps(private(phi, set_by_brief), indent=2),
        "faulty_body.py": faulty_body if faulty_body is not None else FAULTY_BODY,
        "fixed_body.py": fixed_body if fixed_body is not None else FIXED_BODY,
        "reference.py": REFERENCE % {"claim": CLAIM, "phi": phi},
    }
    for name, text in files.items():
        with open(os.path.join(folder, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return folder
