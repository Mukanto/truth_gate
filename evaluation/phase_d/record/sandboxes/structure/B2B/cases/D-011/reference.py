"""D-011: Gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve is at least 0.90."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 72
P = 2000
K = 8
KC = 3
NPOS = 25
DPRIME = 3.4
DENS = 0.10
LSD = 0.50
RES = 0.45
OFF = 0.15

def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx


def gen(rng):
    """Log-expression from K co-expression factors (each loaded by about DENS of the genes), a sample-level
    normalisation offset and gene-level residual error. The class shifts the means of KC factors; the shift
    gives a Mahalanobis distance of about DPRIME between the classes. Fixed class counts."""
    y = np.zeros(N, dtype=bool)
    y[:NPOS] = True
    y = y[rng.permutation(N)]
    f = rng.normal(size=(N, K))
    f[:, :KC] += (DPRIME / np.sqrt(KC)) * (y.astype(float) - NPOS / N)[:, None]
    lam = (rng.random((P, K)) < DENS) * rng.normal(0.0, LSD, size=(P, K))
    sd = RES * np.exp(0.25 * rng.normal(size=P))
    mu = 8.0 + 2.0 * rng.normal(size=P)
    off = OFF * rng.normal(size=(N, 1))
    x = mu + f @ lam.T + off + sd * rng.normal(size=(N, P))
    perm = rng.permutation(N)
    return x, y, y[perm]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, y, _ = gen(rng)
    return {"expression": x, "myeloid": y}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, y = gen(rng)
    return {"expression": x, "myeloid": y}


def control(d, rng):
    """Permutes the class labels across the samples."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["myeloid"]
    new = old
    for _ in range(50):
        new = old[rng.permutation(N)]
        if not np.array_equal(new, old):
            break
    out["myeloid"] = new
    return out


def criterion(d):
    """Data keys: expression (samples, genes) float64: expression level of each gene in each bone-marrow sample; myeloid (samples,) bool: True for acute myeloid leukaemia, False for acute lymphoblastic leukaemia.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-011",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the leukaemia type labels are randomly reassigned among the samples (class counts kept); expression data unchanged"),
    },
    controls=[Control("D-011", ["C"], transform=control)],
)
