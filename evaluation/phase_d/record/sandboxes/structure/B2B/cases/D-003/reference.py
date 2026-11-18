"""D-003: A classifier built from the measured variables ranks new records correctly: the area under the ROC curve for the event is at least 0.75."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 1000
P = 15
PREV = 0.1
BLOCK = 5
RHO = 0.30
DPRIME = 1.6
INFORM = (0, 1, 2, 5, 6, 10)
MAG = (1.0, 0.8, -0.6, 0.9, -0.5, 0.7)

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
    return {"features": x, "event": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, lab = gen(rng)
    return {"features": x, "event": lab}


def control(d, rng):
    """Permutes the label across the records."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["event"]
    new = old
    for _ in range(50):
        new = old[derange(rng, N)]
        if not np.array_equal(new, old):
            break
    out["event"] = new
    return out


def criterion(d):
    """Data keys: features (records, variables) float64: measured variables of each record; event (records,) bool: True if the event occurred for the record.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-003",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the event label is replaced by the label of another record (independent of the variables); label share, correlations and variable distributions unchanged"),
    },
    controls=[Control("D-003", ["C"], transform=control)],
)
