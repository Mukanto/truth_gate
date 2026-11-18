"""D-070: Gene-expression profiles predict five-year relapse in new patients: the area under the ROC curve is at least 0.70."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 120
P = 2000
K = 8
KC = 2
NPOS = 42
DPRIME = 1.4
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
    return {"expression": x, "relapse_5y": y}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, y = gen(rng)
    return {"expression": x, "relapse_5y": y}


def control(d, rng):
    """Permutes the class labels across the samples."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["relapse_5y"]
    new = old
    for _ in range(50):
        new = old[rng.permutation(N)]
        if not np.array_equal(new, old):
            break
    out["relapse_5y"] = new
    return out


def criterion(d):
    """Data keys: expression (patients, genes) float64: log2 expression level of each gene in each patient's tumour sample; relapse_5y (patients,) bool: True if the patient relapsed within five years of diagnosis.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-070",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the relapse labels are randomly reassigned among the patients (relapse count kept); expression data unchanged"),
    },
    controls=[Control("D-070", ["C"], transform=control)],
)
