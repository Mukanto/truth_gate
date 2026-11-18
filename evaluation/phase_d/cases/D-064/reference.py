"""D-064: Expression profiles together with clinical covariates predict tumour response in new patients: the Pearson correlation between predicted and observed response is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N = 80
P = 1500
C = 8
K = 8
KP = 3
GAM = (0.8, 0.6, 0.4)
CW = (0.6, 0.4, 0.3, 0.0, 0.0, 0.2, -0.2, 0.0)
RC = 0.25
R2E = 0.25
R2C = 0.12
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
    """Log-expression from K co-expression factors; standardised clinical covariates correlated RC with each
    other. Response (percent shrinkage, mean 40, sd 20 before clipping) = expression index (share R2E) +
    clinical index (share R2C) + noise."""
    f = rng.normal(size=(N, K))
    lam = (rng.random((P, K)) < DENS) * rng.normal(0.0, LSD, size=(P, K))
    sd = RES * np.exp(0.25 * rng.normal(size=P))
    mu = 8.0 + 2.0 * rng.normal(size=P)
    off = OFF * rng.normal(size=(N, 1))
    x = mu + f @ lam.T + off + sd * rng.normal(size=(N, P))
    rc = np.full((C, C), RC)
    np.fill_diagonal(rc, 1.0)
    clin = rng.normal(size=(N, C)) @ np.linalg.cholesky(rc).T
    gam = np.array(GAM)
    g = f[:, :KP] @ gam / np.sqrt(gam @ gam)
    cw = np.array(CW)
    hc = clin @ cw / np.sqrt(cw @ rc @ cw)
    z = np.sqrt(R2E) * g + np.sqrt(R2C) * hc + np.sqrt(1.0 - R2E - R2C) * rng.normal(size=N)
    resp = np.clip(40.0 + 20.0 * z, -50.0, 100.0)
    idx = derange(rng, N)
    return x, clin, resp, resp[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, clin, resp, _ = gen(rng)
    return {"expression": x, "clinical": clin, "response": resp}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, clin, _, resp = gen(rng)
    return {"expression": x, "clinical": clin, "response": resp}


def control(d, rng):
    """Permutes the response across the patients."""
    out = {k: np.array(v) for k, v in d.items()}
    out["response"] = d["response"][derange(rng, N)]
    return out


def criterion(d):
    """Data keys: expression (patients, genes) float64: log2 expression level of each gene in each patient's tumour sample; clinical (patients, covariates) float64: standardised clinical covariates of each patient (age, tumour size, and similar); response (patients,) float64: percentage tumour shrinkage measured after treatment.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-064",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="responses are replaced by those of other patients (independent of expression and clinical covariates); response distribution, expression and clinical data unchanged"),
    },
    controls=[Control("D-064", ["C"], transform=control)],
)
