"""D-059: The monthly environmental measurements predict the abundance in later months of the series: the out-of-sample R-squared is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

T = 600
P = 10
PHI = (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.68, 0.72, 0.62, 0.78)
RINN = 0.25
BETA = (0.7, -0.5, 0.6, 0.3, -0.4, 0.2, 0.0, 0.4, -0.3, 0.2)
RSQ = 0.55
PHI_R = 0.7
V_R = 0.4
V_W = 0.05
CENTRE = 2.0
SPREAD = 0.8


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
    return {"abundance": s, "environment": x}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, s = gen(rng)
    return {"abundance": s, "environment": x}


def control(d, rng):
    """Shifts the series in time, circularly, by a random lag between a quarter and three quarters of its length."""
    out = {k: np.array(v) for k, v in d.items()}
    out["abundance"] = np.roll(d["abundance"], int(rng.integers(T // 4, 3 * T // 4)))
    return out


def criterion(d):
    """Data keys: abundance (months,) float64: monthly abundance index of the species, on a log scale, in time order; environment (months, variables) float64: monthly environmental measurements, in time order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-059",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the abundance is driven by an independent copy of the environment paths instead of the observed environment; its variance, autocorrelation and residual stay as in plus"),
    },
    controls=[Control("D-059", ["C"], transform=control)],
)
