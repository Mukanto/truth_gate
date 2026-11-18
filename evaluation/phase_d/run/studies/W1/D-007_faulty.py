"""D-007: Gene-expression profiles measured at diagnosis predict survival time in new patients: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 50
N_GENE = 2000
N_MOD = 8            # co-expression modules; module 0 = proliferation, module 1 = immune
N_BATCH = 4          # processing batches, contiguous in diagnosis order
LOG_MEDIAN = np.log(20.0)   # median survival about 20 months
B_PROLIF = -0.45     # change in log survival per SD of the proliferation module score
B_IMMUNE = 0.20      # change in log survival per SD of the immune module score
SIGMA = 0.62         # residual SD of log survival


def _world(rng, effect):
    n, g = N_PAT, N_GENE
    gene_mean = rng.uniform(4.0, 12.0, g)
    gene_sd = np.exp(rng.normal(np.log(0.6), 0.35, g))
    member = rng.random(g) < 0.6
    module = rng.integers(0, N_MOD, g)
    h2 = np.where(member, rng.uniform(0.2, 0.6, g), 0.0)
    sign = np.where(rng.random(g) < 0.8, 1.0, -1.0)
    load = sign * np.sqrt(h2)
    factors = rng.standard_normal((n, N_MOD))
    resid = rng.standard_normal((n, g))
    z = load * factors[:, module] + np.sqrt(1.0 - h2) * resid
    batch = np.repeat(np.arange(N_BATCH), -(-n // N_BATCH))[:n]
    batch_shift = rng.normal(0.0, 0.3, (N_BATCH, g)) * gene_sd
    norm_shift = rng.normal(0.0, 0.15, n)
    expression = gene_mean + gene_sd * z + batch_shift[batch] + norm_shift[:, None]
    # survival is driven by the proliferation and immune module scores; in minus by independent
    # copies of those scores (same distribution, unrelated to the measured expression)
    copies = rng.standard_normal((n, 2))
    eps = rng.standard_normal(n)
    drivers = factors[:, :2] if effect else copies
    log_t = LOG_MEDIAN + B_PROLIF * drivers[:, 0] + B_IMMUNE * drivers[:, 1] + SIGMA * eps
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "survival_months": np.asarray(np.exp(log_t), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


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


def _r2(y, pred):
    """1 - SSE/SST, with SST taken about the mean of y."""
    return 1.0 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
    return fid


def criterion(d):
    """Claim: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["survival_months"]: float array (patients,); months from diagnosis to death, observed for every patient.
    Returns True when the statistic is at least 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 patients, constant survival_months)."""
    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["survival_months"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = x.shape[0]
    if n < 2 or y.max() == y.min():
        return None
    rng = np.random.default_rng(2001)
    lam = float(x.shape[1])
    pred = _ridge_predict(x, y, x, lam)
    return bool(_r2(y, pred) >= 0.10)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _nonidentity_perm(rng, n):
    p = rng.permutation(n)
    if np.all(p == np.arange(n)):
        p = np.roll(p, 1)
    return p


def _shuffle_survival(d, rng):
    p = _nonidentity_perm(rng, d["survival_months"].shape[0])
    return {**d, "survival_months": d["survival_months"][p]}


STUDY = Study(
    name="D-007",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="survival driven by independent copies of the module scores: no relation between expression and survival"),
    },
    controls=[Control("survival_shuffled_across_patients", ["C"], transform=_shuffle_survival)],
)
