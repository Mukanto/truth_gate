"""D-034: The daily driver measurements predict the daily river level in later days of the record: the root-mean-square error of the prediction is at most 0.70 standard deviations of the level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

T = 1500
P = 6
PHI = (0.966, 0.951, 0.935, 0.920, 0.907, 0.893)
RINN = 0.3
BETA = (0.8, -0.5, 0.6, 0.3, -0.4, 0.2)
RSQ = 0.75
PHI_R = 0.85
V_R = 0.2
V_W = 0.05
CENTRE = 3.0
SPREAD = 0.9


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
    return {"level": s, "drivers": x}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, s = gen(rng)
    return {"level": s, "drivers": x}


def control(d, rng):
    """Shifts the series in time, circularly, by a random lag between a quarter and three quarters of its length."""
    out = {k: np.array(v) for k, v in d.items()}
    out["level"] = np.roll(d["level"], int(rng.integers(T // 4, 3 * T // 4)))
    return out


def criterion(d):
    """Data keys: level (days,) float64: daily river level, in time order; drivers (days, variables) float64: daily measurements of the variables that may influence the river level, in time order.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-034",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the level is driven by an independent copy of the driver paths instead of the observed drivers; its variance, autocorrelation and residual stay as in plus"),
    },
    controls=[Control("D-034", ["C"], transform=control)],
)
