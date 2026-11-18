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


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd


def _ridge_predict(xtr, ytr, xte, lam):
    """Ridge regression with penalty lam on standardised columns (dual form); predictions for the rows of xte."""
    a, b = _standardise(xtr, xte)
    ym = ytr.mean()
    k = a @ a.T
    alpha = np.linalg.solve(k + lam * np.eye(k.shape[0]), ytr - ym)
    return ym + (b @ a.T) @ alpha


def _corr(a, b):
    """Pearson correlation of two vectors."""
    a = a - a.mean()
    b = b - b.mean()
    return (a @ b) / np.sqrt((a @ a) * (b @ b))


def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
    return fid


def criterion(d):
    """Claim: the Pearson correlation between predicted and observed response (expression plus clinical covariates) in
    new patients is at least 0.30.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["clinical"]: float array (patients, covariates); standardised clinical covariates of each patient.
    d["response"]: float array (patients,); percentage tumour shrinkage measured after treatment.
    Returns True when the statistic is at least 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 patients, constant response or constant predictions)."""
    xe = np.asarray(d["expression"], dtype=float)
    xc = np.asarray(d["clinical"], dtype=float)
    y = np.asarray(d["response"], dtype=float)
    if not (np.all(np.isfinite(xe)) and np.all(np.isfinite(xc)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    if n < 2 or y.max() == y.min():
        return None
    x = np.hstack([xe, xc])
    rng = np.random.default_rng(2002)
    lam = float(x.shape[1])
    folds = _random_folds(rng, n, 10)
    pred = np.zeros(n)
    for f in range(10):
        te = folds == f
        pred[te] = _ridge_predict(x[~te], y[~te], x[te], lam)
    if pred.max() == pred.min():
        return None
    return bool(_corr(y, pred) >= 0.30)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


STUDY = Study(
    name="D-064",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="responses are replaced by those of other patients (independent of expression and clinical covariates); response distribution, expression and clinical data unchanged"),
    },
    controls=[Control("D-064", ["C"], transform=control)],
)
