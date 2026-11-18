"""D-007: Gene-expression profiles measured at diagnosis predict survival time in new patients: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 50
P = 2000
K = 8
KP = 3
GAM = (0.8, 0.6, 0.4)
RHO = 0.70
SIG = 0.70
MEDIAN = 30.0
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
    """Log-expression from K co-expression factors, a sample offset and residual error. A prognostic index
    (a fixed mix of the first KP factors, unit variance) correlates RHO with log survival time; survival is
    lognormal with median MEDIAN months and log-sd SIG."""
    f = rng.normal(size=(N, K))
    lam = (rng.random((P, K)) < DENS) * rng.normal(0.0, LSD, size=(P, K))
    sd = RES * np.exp(0.25 * rng.normal(size=P))
    mu = 8.0 + 2.0 * rng.normal(size=P)
    off = OFF * rng.normal(size=(N, 1))
    x = mu + f @ lam.T + off + sd * rng.normal(size=(N, P))
    gam = np.array(GAM)
    g = f[:, :KP] @ gam / np.sqrt(gam @ gam)
    z = RHO * g + np.sqrt(1.0 - RHO ** 2) * rng.normal(size=N)
    t = MEDIAN * np.exp(SIG * z)
    idx = derange(rng, N)
    return x, t, t[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, t, _ = gen(rng)
    return {"expression": x, "survival_months": t}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, t = gen(rng)
    return {"expression": x, "survival_months": t}


def control(d, rng):
    """Permutes survival times across the patients."""
    out = {k: np.array(v) for k, v in d.items()}
    out["survival_months"] = d["survival_months"][derange(rng, N)]
    return out


def criterion(d):
    """Data keys: expression (patients, genes) float64: log2 expression level of each gene in each patient's tumour sample; survival_months (patients,) float64: months from diagnosis to death, observed for every patient.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-007",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="survival times are replaced by those of other patients (independent of the expression profile); survival distribution and expression data unchanged"),
    },
    controls=[Control("D-007", ["C"], transform=control)],
)
