"""World and criteria C1, C2 and two controls of examples/convergence_criteria/study.py, copied for the A2 manifest.

C3 is a pattern in the manifest and the control `unit_multiplier` a `constant` mutation, so they are not repeated here.
"""
import numpy as np

N = 20                     # cycles
TOL = 1e-10                # convergence tolerance, in the units of x
X_STAR = 0.7               # synthetic fixed point
LOWER_BOUND = 0.52         # a transition that lands below this value leaves the model's domain
STARTS = [0.55, 0.6, 0.65, 0.68, X_STAR - 1e-3, X_STAR + 1e-3, X_STAR + 1e-2, 0.8, 1.0]


def linear_world(lam):
    starts = np.array(STARTS, dtype=float)
    k = np.arange(N + 1, dtype=float)
    traj = X_STAR + (lam ** k)[None, :] * (starts - X_STAR)[:, None]
    in_domain = np.logical_and.accumulate(traj[:, 1:] >= LOWER_BOUND, axis=1)
    return {
        "x_star": np.array(X_STAR),
        "lam": np.array(float(lam)),
        "traj": traj,
        "in_domain": in_domain,
    }


def plus(rng):
    return linear_world(0.02)


def minus(rng):
    return linear_world(1.39)


def C1_local_attraction(d):
    lam = float(d["lam"])
    if not np.isfinite(lam):
        return None
    return bool(abs(lam) < 1.0)


def C2_convergence_N(d):
    traj = np.asarray(d["traj"])
    ok = np.asarray(d["in_domain"]).all(axis=1)
    if not ok.any():
        return None  # no start stayed in domain: the criterion is undefined, not satisfied
    return bool(np.all(np.abs(traj[ok, N] - float(d["x_star"])) <= TOL))


def frozen_state(d, rng):
    """Every start stays where it began: nothing converges."""
    traj = np.asarray(d["traj"])
    return {**d, "traj": np.repeat(traj[:, :1], traj.shape[1], axis=1)}


def forced_exit(d, rng):
    """One start leaves the domain at the first cycle."""
    in_domain = np.array(d["in_domain"], dtype=bool, copy=True)
    in_domain[0, :] = False
    return {**d, "in_domain": in_domain}
