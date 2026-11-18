"""D-064: Expression profiles together with clinical covariates predict tumour response in new patients: the Pearson correlation between predicted and observed response is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 80
N_GENES = 1500
N_COV = 8
N_PROG = 9              # background expression programmes unrelated to response
PROG_SIZE = 100         # genes per background programme
MODULE_SIZE = 60        # genes of the response-related programme
MODULE_LOADING = 0.65   # loading of module genes on the response-related programme
GRADE_LINK = 0.3        # correlation of the response-related programme with covariate 2 (grade)
R_CLIN = np.array([
    [1.0, 0.1, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0],
    [0.1, 1.0, 0.0, 0.0, 0.25, 0.1, 0.0, 0.0],
    [0.3, 0.0, 1.0, 0.3, 0.0, 0.0, 0.0, 0.0],
    [0.4, 0.0, 0.3, 1.0, 0.2, 0.0, 0.0, 0.0],
    [0.0, 0.25, 0.0, 0.2, 1.0, 0.0, 0.0, 0.0],
    [0.0, 0.1, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.3],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 1.0],
])                      # correlation of the clinical covariates
W_MODULE = 0.50         # weight of the response-related programme in the true response signal
W_SIZE = -0.30          # weight of covariate 0 (tumour size)
W_AGE = 0.20            # weight of covariate 1 (age)
R2_PLUS = 0.36          # share of response variance explained by the true signal (plus)
RESP_MEAN = 30.0        # mean percentage shrinkage
RESP_SD = 22.0          # SD of percentage shrinkage (plus)


def _generate(rng, signal_on):
    lc = np.linalg.cholesky(R_CLIN)
    c = rng.standard_normal((N_PAT, N_COV)) @ lc.T
    f0 = GRADE_LINK * c[:, 2] + np.sqrt(1.0 - GRADE_LINK ** 2) * rng.standard_normal(N_PAT)
    fb = rng.standard_normal((N_PAT, N_PROG))
    perm = rng.permutation(N_GENES)
    load = np.zeros((N_PROG + 1, N_GENES))
    load[0, perm[:MODULE_SIZE]] = MODULE_LOADING
    for k in range(N_PROG):
        genes = perm[MODULE_SIZE + k * PROG_SIZE: MODULE_SIZE + (k + 1) * PROG_SIZE]
        load[k + 1, genes] = rng.uniform(0.3, 0.6, PROG_SIZE)
    factors = np.column_stack([f0, fb])
    unique_sd = np.sqrt(1.0 - (load ** 2).sum(axis=0))
    z = factors @ load + unique_sd[None, :] * rng.standard_normal((N_PAT, N_GENES))
    gene_mean = 7.0 + 1.5 * rng.standard_normal(N_GENES)
    gene_sd = np.exp(-0.5 + 0.3 * rng.standard_normal(N_GENES))
    expression = gene_mean[None, :] + gene_sd[None, :] * z
    w = np.array([W_MODULE, W_SIZE, W_AGE])
    cov3 = np.array([
        [1.0, GRADE_LINK * R_CLIN[2, 0], GRADE_LINK * R_CLIN[2, 1]],
        [GRADE_LINK * R_CLIN[2, 0], 1.0, R_CLIN[0, 1]],
        [GRADE_LINK * R_CLIN[2, 1], R_CLIN[0, 1], 1.0],
    ])
    var_s = float(w @ cov3 @ w)
    var_e = var_s * (1.0 - R2_PLUS) / R2_PLUS
    s = W_MODULE * f0 + W_SIZE * c[:, 0] + W_AGE * c[:, 1]
    e = np.sqrt(var_e) * rng.standard_normal(N_PAT)
    response = RESP_MEAN + RESP_SD * (signal_on * s + e) / np.sqrt(var_s + var_e)
    response = np.minimum(response, 100.0)
    clinical = (c - c.mean(axis=0)) / c.std(axis=0)
    return {
        "expression": np.asarray(expression, dtype=np.float64),
        "clinical": np.asarray(clinical, dtype=np.float64),
        "response": np.asarray(response, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


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


def _permute_response(d, rng):
    return {**d, "response": rng.permutation(d["response"])}


STUDY = Study(
    name="D-064",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="true response signal from the expression programme and the clinical covariates set to zero (response = same noise only); expression and clinical data unchanged"),
    },
    controls=[
        Control("response_permuted_across_patients", ["C"], transform=_permute_response),
    ],
)
