import json, os

ROOT = r"E:\Claude Projects\Kapi\phase_d_work\structure\B2B\cases"

HEAD = '''"""@ID@: @CLAIM@"""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

'''

TAIL = '''

def criterion(d):
    """Data keys: @KEYS@.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="@ID@",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="@CHANGE@"),
    },
    controls=[Control("@ID@", ["C"], transform=control)],
)
'''

DERANGE = '''
def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx
'''

# ---------------------------------------------------------------- family A: tabular, imbalanced labels
A = '''N = @N@
P = @P@
PREV = @PREV@
BLOCK = @BLOCK@
RHO = 0.30
DPRIME = @DPRIME@
INFORM = @INFORM@
MAG = @MAG@
''' + DERANGE + '''

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
    return {"@FKEY@": x, "@LKEY@": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, lab = gen(rng)
    return {"@FKEY@": x, "@LKEY@": lab}


def control(d, rng):
    """Permutes the label across the records."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["@LKEY@"]
    new = old
    for _ in range(50):
        new = old[derange(rng, N)]
        if not np.array_equal(new, old):
            break
    out["@LKEY@"] = new
    return out
'''

# ---------------------------------------------------------------- family B: high-dim expression, binary label
B = '''N = @N@
P = 2000
K = 8
KC = @KC@
NPOS = @NPOS@
DPRIME = @DPRIME@
DENS = 0.10
LSD = 0.50
RES = 0.45
OFF = 0.15
''' + DERANGE + '''

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
    return {"@FKEY@": x, "@LKEY@": y}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, y = gen(rng)
    return {"@FKEY@": x, "@LKEY@": y}


def control(d, rng):
    """Permutes the class labels across the samples."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["@LKEY@"]
    new = old
    for _ in range(50):
        new = old[rng.permutation(N)]
        if not np.array_equal(new, old):
            break
    out["@LKEY@"] = new
    return out
'''

# ---------------------------------------------------------------- family C1: survival from expression
C1 = '''N = 50
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
''' + DERANGE + '''

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
'''

# ---------------------------------------------------------------- family C2: response from expression + clinical
C2 = '''N = 80
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
''' + DERANGE + '''

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
'''

# ---------------------------------------------------------------- family D: autocorrelated drivers and a level series
D = '''T = @T@
P = @P@
PHI = @PHI@
RINN = @RINN@
BETA = @BETA@
RSQ = @RSQ@
PHI_R = @PHI_R@
V_R = @V_R@
V_W = @V_W@
CENTRE = @CENTRE@
SPREAD = @SPREAD@


def ar_series(rng, phi, chol, steps):
    """Stationary unit-variance AR(1) series with innovations correlated through chol."""
    m = len(phi)
    z = rng.normal(size=(steps, m)) @ chol.T
    x = np.empty((steps, m))
    x[0] = z[0]
    k = np.sqrt(1.0 - phi ** 2)
    for t in range(1, steps):
        x[t] = phi * x[t - 1] + k * z[t]
    return x


def gen(rng):
    """Drivers: P AR(1) series (own persistence PHI, innovation correlation RINN). Series: a linear response
    to the drivers with variance share RSQ, plus an AR(1) residual (share V_R, persistence PHI_R) and white
    measurement error (share V_W), RSQ + V_R + V_W = 1. A second, independent driver path is drawn too; the
    null series uses it in place of the true drivers."""
    phi = np.array(PHI)
    rc = np.full((P, P), RINN)
    np.fill_diagonal(rc, 1.0)
    chol = np.linalg.cholesky(rc)
    x = ar_series(rng, phi, chol, T)
    xa = ar_series(rng, phi, chol, T)
    beta = np.array(BETA)
    si = np.sqrt(1.0 - phi ** 2)
    c = RINN * np.outer(si, si) / (1.0 - np.outer(phi, phi))
    np.fill_diagonal(c, 1.0)
    scale = np.sqrt(RSQ / (beta @ c @ beta))
    resid = ar_series(rng, np.array([PHI_R]), np.ones((1, 1)), T)[:, 0]
    white = rng.normal(size=T)
    noise = np.sqrt(V_R) * resid + np.sqrt(V_W) * white
    s_plus = CENTRE + SPREAD * ((x @ beta) * scale + noise)
    s_minus = CENTRE + SPREAD * ((xa @ beta) * scale + noise)
    return x, s_plus, s_minus


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, s, _ = gen(rng)
    return {"@SKEY@": s, "@XKEY@": x}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, s = gen(rng)
    return {"@SKEY@": s, "@XKEY@": x}


def control(d, rng):
    """Shifts the series in time, circularly, by a random lag between a quarter and three quarters of its length."""
    out = {k: np.array(v) for k, v in d.items()}
    out["@SKEY@"] = np.roll(d["@SKEY@"], int(rng.integers(T // 4, 3 * T // 4)))
    return out
'''

# ---------------------------------------------------------------- D-018
E18 = '''S = 16
R = 60
V = 10
ICC = 0.30
LINK = (0.8, 0.0, 0.8, 0.7, 0.0, 0.0, 0.7, 0.0, 0.7, 0.0)
SGN = (1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0)
PHI = 0.70
VAR_AR = 0.20
VAR_SH = 0.15
VAR_W = 0.35


def gen(rng):
    """Subject effects (share ICC of each variable's variance) of which the LINK variables carry the subject's
    disease status with correlation LINK; within subject: AR(1) drift over the records, a shared record factor
    and white measurement error. Half of the subjects are diseased."""
    lab = np.zeros(S, dtype=bool)
    lab[:S // 2] = True
    lab = lab[rng.permutation(S)]
    a = 2.0 * lab.astype(float) - 1.0
    link = np.array(LINK)
    sg = np.array(SGN)
    u = rng.normal(size=(S, V))
    u = link * sg * a[:, None] + np.sqrt(1.0 - link ** 2) * u
    z = rng.normal(size=(S, R, V))
    ar = np.empty((S, R, V))
    ar[:, 0] = z[:, 0]
    for t in range(1, R):
        ar[:, t] = PHI * ar[:, t - 1] + np.sqrt(1.0 - PHI ** 2) * z[:, t]
    q = rng.normal(size=(S, R, 1))
    white = rng.normal(size=(S, R, V))
    within = np.sqrt(VAR_AR) * ar + np.sqrt(VAR_SH) * q * sg + np.sqrt(VAR_W) * white
    col = np.arange(V)
    x = 1.5 * np.sin(1.3 * col) + (1.0 + 0.3 * np.cos(2.1 * col)) * (np.sqrt(ICC) * u[:, None, :] + within)
    other = lab[rng.permutation(S)]
    return x, lab, other


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, lab, _ = gen(rng)
    return {"measurements": x, "diseased": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, lab = gen(rng)
    return {"measurements": x, "diseased": lab}


def control(d, rng):
    """Permutes the disease status across the subjects."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["diseased"]
    new = old
    for _ in range(50):
        new = old[rng.permutation(S)]
        if not np.array_equal(new, old):
            break
    out["diseased"] = new
    return out
'''

# ---------------------------------------------------------------- D-058
E58 = '''S = 30
W = 30
V = 40
ICC = 0.13
DPRIME = 3.6
STAY = 0.85
PI_A = 2.4
PI_B = 9.6
PHI = 0.90
VAR_DR = 0.40
VAR_SH = 0.10
VAR_W = 0.37
''' + DERANGE + '''

def gen(rng):
    """Subject effects (share ICC of every feature's variance), slowly drifting within-subject variation (AR(1)
    over the windows), a shared window factor and white error. Walking comes in bouts (stay probability STAY)
    with a subject-specific walking share (Beta(PI_A, PI_B), mean 0.2). Walking shifts 20 of the features
    by a Mahalanobis distance DPRIME. The null label sequences are those of other subjects."""
    pi = np.clip(rng.beta(PI_A, PI_B, size=S), 0.02, 0.9)
    enter = pi * (1.0 - STAY) / (1.0 - pi)
    walk = np.zeros((S, W), dtype=bool)
    draw = rng.random((S, W))
    walk[:, 0] = draw[:, 0] < pi
    for t in range(1, W):
        walk[:, t] = draw[:, t] < np.where(walk[:, t - 1], STAY, enter)
    sg = np.where(np.arange(V) % 2 == 0, 1.0, -1.0)
    sig = (ICC + VAR_DR + VAR_W) * np.eye(V) + VAR_SH * np.outer(sg, sg)
    mag = np.zeros(V)
    mag[:20] = (0.6 + 0.4 * np.sin(2.9 * np.arange(20))) * np.where(np.arange(20) % 3 == 0, -1.0, 1.0)
    delta = mag * DPRIME / np.sqrt(mag @ np.linalg.solve(sig, mag))
    u = rng.normal(size=(S, V))
    z = rng.normal(size=(S, W, V))
    dr = np.empty((S, W, V))
    dr[:, 0] = z[:, 0]
    for t in range(1, W):
        dr[:, t] = PHI * dr[:, t - 1] + np.sqrt(1.0 - PHI ** 2) * z[:, t]
    q = rng.normal(size=(S, W, 1))
    white = rng.normal(size=(S, W, V))
    within = np.sqrt(VAR_DR) * dr + np.sqrt(VAR_SH) * q * sg + np.sqrt(VAR_W) * white
    col = np.arange(V)
    x = np.sin(1.1 * col) + (1.0 + 0.3 * np.cos(2.3 * col)) * (
        np.sqrt(ICC) * u[:, None, :] + within + walk[:, :, None] * delta)
    idx = derange(rng, S)
    return x, walk, walk[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, walk, _ = gen(rng)
    return {"signal_features": x, "walking": walk}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, walk = gen(rng)
    return {"signal_features": x, "walking": walk}


def control(d, rng):
    """Gives every subject the walking sequence of another subject."""
    out = {k: np.array(v) for k, v in d.items()}
    out["walking"] = d["walking"][derange(rng, S)]
    return out
'''

# ---------------------------------------------------------------- D-065
E65 = '''S = 40
M = 20
V = 6
ICC = 0.30
RHOU = 0.30
RHOE = 0.25
SGN = (1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
BETA = (0.7, 0.4, 0.5, 0.0, -0.3, 0.3)
R2 = 0.35
U_SITE = 0.20
''' + DERANGE + '''

def gen(rng):
    """Habitat: a site effect (share ICC of each variable's variance, variables correlated RHOU across sites)
    plus plot-level variation (correlated RHOE across variables). Cover: a linear response to the standardised
    habitat (variance share R2), a site-level residual (share U_SITE that habitat does not explain) and
    plot-level noise. The null cover is that of another site."""
    sg = np.array(SGN)
    gs = rng.normal(size=(S, 1))
    u = np.sqrt(RHOU) * gs * sg + np.sqrt(1.0 - RHOU) * rng.normal(size=(S, V))
    qp = rng.normal(size=(S, M, 1))
    e = np.sqrt(RHOE) * qp * sg + np.sqrt(1.0 - RHOE) * rng.normal(size=(S, M, V))
    h = np.sqrt(ICC) * u[:, None, :] + np.sqrt(1.0 - ICC) * e
    cu = RHOU * np.outer(sg, sg)
    ce = RHOE * np.outer(sg, sg)
    cc = ICC * cu + (1.0 - ICC) * ce
    np.fill_diagonal(cc, 1.0)
    beta = np.array(BETA)
    scale = np.sqrt(R2 / (beta @ cc @ beta))
    z = (h @ beta) * scale + np.sqrt(U_SITE) * rng.normal(size=(S, 1)) \\
        + np.sqrt(1.0 - R2 - U_SITE) * rng.normal(size=(S, M))
    cover = np.clip(45.0 + 18.0 * z, 0.0, 100.0)
    col = np.arange(V)
    hab = 3.0 * np.cos(1.9 * col) + (1.0 + 0.5 * np.sin(1.3 * col)) * h
    idx = derange(rng, S)
    return hab, cover, cover[idx]


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    hab, cover, _ = gen(rng)
    return {"habitat": hab, "cover": cover}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    hab, _, cover = gen(rng)
    return {"habitat": hab, "cover": cover}


def control(d, rng):
    """Gives every site the cover values of another site."""
    out = {k: np.array(v) for k, v in d.items()}
    out["cover"] = d["cover"][derange(rng, S)]
    return out
'''

CASES = {
 "D-003": (A, dict(N=1000, P=15, PREV=0.10, BLOCK=5, DPRIME=1.6, INFORM="(0, 1, 2, 5, 6, 10)",
                   MAG="(1.0, 0.8, -0.6, 0.9, -0.5, 0.7)", FKEY="features", LKEY="event"),
           "the event label is replaced by the label of another record (independent of the variables); label share, correlations and variable distributions unchanged"),
 "D-035": (A, dict(N=1500, P=20, PREV=0.10, BLOCK=5, DPRIME=1.7, INFORM="(0, 1, 3, 5, 6, 9, 12, 17)",
                   MAG="(1.0, -0.7, 0.8, 0.6, -0.9, 0.5, 0.7, -0.6)", FKEY="features", LKEY="positive"),
           "the positive label is replaced by the label of another record (independent of the variables); label share, correlations and variable distributions unchanged"),
 "D-043": (A, dict(N=400, P=8, PREV=0.10, BLOCK=4, DPRIME=2.8, INFORM="(0, 1, 4, 6)",
                   MAG="(1.0, -0.8, 0.9, 0.7)", FKEY="measurements", LKEY="positive"),
           "the positive label is replaced by the label of another record (independent of the measurements); label share, correlations and variable distributions unchanged"),
 "D-049": (A, dict(N=600, P=12, PREV=0.10, BLOCK=4, DPRIME=2.4, INFORM="(0, 2, 4, 7, 9)",
                   MAG="(1.0, -0.8, 0.7, 0.9, -0.6)", FKEY="features", LKEY="positive"),
           "the positive label is replaced by the label of another record (independent of the variables); label share, correlations and variable distributions unchanged"),
 "D-011": (B, dict(N=72, NPOS=25, KC=3, DPRIME=3.4, FKEY="expression", LKEY="myeloid"),
           "the leukaemia type labels are randomly reassigned among the samples (class counts kept); expression data unchanged"),
 "D-013": (B, dict(N=40, NPOS=20, KC=3, DPRIME=2.4, FKEY="expression", LKEY="class_b"),
           "the class labels are randomly reassigned among the samples (class counts kept); expression data unchanged"),
 "D-024": (B, dict(N=62, NPOS=40, KC=3, DPRIME=2.8, FKEY="expression", LKEY="tumour"),
           "the tumour/normal labels are randomly reassigned among the tissues (class counts kept); expression data unchanged"),
 "D-070": (B, dict(N=120, NPOS=42, KC=2, DPRIME=1.4, FKEY="expression", LKEY="relapse_5y"),
           "the relapse labels are randomly reassigned among the patients (relapse count kept); expression data unchanged"),
 "D-007": (C1, {}, "survival times are replaced by those of other patients (independent of the expression profile); survival distribution and expression data unchanged"),
 "D-064": (C2, {}, "responses are replaced by those of other patients (independent of expression and clinical covariates); response distribution, expression and clinical data unchanged"),
 "D-034": (D, dict(T=1500, P=6, PHI="(0.966, 0.951, 0.935, 0.920, 0.907, 0.893)", RINN=0.3,
                   BETA="(0.8, -0.5, 0.6, 0.3, -0.4, 0.2)", RSQ=0.75, PHI_R=0.85, V_R=0.20, V_W=0.05,
                   CENTRE=3.0, SPREAD=0.9, SKEY="level", XKEY="drivers"),
           "the level is driven by an independent copy of the driver paths instead of the observed drivers; its variance, autocorrelation and residual stay as in plus"),
 "D-059": (D, dict(T=600, P=10, PHI="(0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.68, 0.72, 0.62, 0.78)", RINN=0.25,
                   BETA="(0.7, -0.5, 0.6, 0.3, -0.4, 0.2, 0.0, 0.4, -0.3, 0.2)", RSQ=0.55, PHI_R=0.70, V_R=0.40, V_W=0.05,
                   CENTRE=2.0, SPREAD=0.8, SKEY="abundance", XKEY="environment"),
           "the abundance is driven by an independent copy of the environment paths instead of the observed environment; its variance, autocorrelation and residual stay as in plus"),
 "D-018": (E18, {}, "the disease status is replaced by that of other subjects (independent of the measurements); half diseased, subject effects and all distributions unchanged"),
 "D-058": (E58, {}, "each subject gets the walking sequence of another subject (independent of the features); bout structure, walking shares and all feature distributions unchanged"),
 "D-065": (E65, {}, "each site gets the cover values of another site (independent of the habitat); site structure of cover and all distributions unchanged"),
}

for cid, (tpl, subs, change) in CASES.items():
    brief = json.load(open(os.path.join(ROOT, cid, "brief.json")))
    keys = "; ".join("%s %s %s: %s" % (k["key"], k["shape"], "float64" if k["dtype"] == "float" else k["dtype"], k["meaning"])
                     for k in brief["data_keys"])
    src = HEAD + tpl + TAIL
    allsubs = dict(subs)
    allsubs.update(ID=cid, CLAIM=brief["claim"], KEYS=keys, CHANGE=change)
    for k, v in allsubs.items():
        src = src.replace("@%s@" % k, str(v))
    import re; assert not re.search(r"@[A-Z_]+@", src), cid
    open(os.path.join(ROOT, cid, "reference.py"), "w", encoding="utf-8", newline="\n").write(src)
    print("wrote", cid)
