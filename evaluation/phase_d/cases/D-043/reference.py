"""D-043: A classifier built from the measurements detects the condition in new records: its sensitivity for the positive class is at least 0.60."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 400
P = 8
PREV = 0.1
BLOCK = 4
RHO = 0.30
DPRIME = 2.8
INFORM = (0, 1, 4, 6)
MAG = (1.0, -0.8, 0.9, 0.7)

def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx


def gen(rng):
    """Correlated measurements (blocks of BLOCK variables, correlation RHO), a latent class that shifts the
    INFORM variables by a Mahalanobis distance DPRIME. Returns features, true label, independent label."""
    r = np.zeros((P, P))
    for b in range(P // BLOCK):
        r[b * BLOCK:(b + 1) * BLOCK, b * BLOCK:(b + 1) * BLOCK] = RHO
    np.fill_diagonal(r, 1.0)
    chol = np.linalg.cholesky(r)
    delta0 = np.zeros(P)
    for k in range(len(INFORM)):
        delta0[INFORM[k]] = MAG[k]
    delta = delta0 * DPRIME / np.sqrt(delta0 @ np.linalg.solve(r, delta0))
    lab = rng.random(N) < PREV
    z = rng.normal(size=(N, P)) @ chol.T + lab[:, None] * delta
    col = np.arange(P)
    x = 2.0 * np.sin(1.7 * col) + (1.0 + 0.4 * np.cos(2.3 * col)) * z
    idx = derange(rng, N)
    return x, lab, lab[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, lab, _ = gen(rng)
    return {"measurements": x, "positive": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, lab = gen(rng)
    return {"measurements": x, "positive": lab}


def control(d, rng):
    """Permutes the label across the records."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["positive"]
    new = old
    for _ in range(50):
        new = old[derange(rng, N)]
        if not np.array_equal(new, old):
            break
    out["positive"] = new
    return out


def criterion(d):
    """Data keys: measurements (records, variables) float64: measured variables of each record; positive (records,) bool: True if the condition is present in the record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-043",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the positive label is replaced by the label of another record (independent of the measurements); label share, correlations and variable distributions unchanged"),
    },
    controls=[Control("D-043", ["C"], transform=control)],
)
