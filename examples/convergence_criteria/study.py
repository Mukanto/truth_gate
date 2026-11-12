"""Kapi study: convergence criteria of an iterated map, tested on synthetic linear worlds only.

Question of the (hypothetical) real study: for a deterministic low-dimensional model with an update law
``x_{k+1} = f(x_k)``, is the fixed point ``x_star`` attracting, and do trajectories reach it within N cycles while
they stay inside the model's domain of validity ("in construct")?

Criteria
    C1_local_attraction   the local multiplier satisfies |lam| < 1
    C2_convergence_N      among starts that stay in domain, every trajectory is within TOL of x_star after N cycles
    C3_in_domain          the whole grid of starts stays in domain for all N cycles

Data schema (all worlds, and the real runner)
    x_star   scalar, the fixed point
    lam      scalar, the local multiplier at x_star
    traj     (S, N + 1) array, traj[s, k] is the state of start s after k cycles
    in_domain (S, N) bool array, in_domain[s, k] is True if transition k + 1 of start s is inside the model's domain

The synthetic worlds never call the real model.  The real runner imports C1, C2 and C3 from this file unchanged and
feeds them the real model's output in the same schema.  See README.md in this folder.
"""
import numpy as np

from kapi import Control, Criterion, Study, World

N = 20                     # cycles
TOL = 1e-10                # convergence tolerance, in the units of x
X_STAR = 0.7               # synthetic fixed point
LOWER_BOUND = 0.52         # a transition that lands below this value leaves the model's domain
STARTS = [0.55, 0.6, 0.65, 0.68, X_STAR - 1e-3, X_STAR + 1e-3, X_STAR + 1e-2, 0.8, 1.0]


def linear_world(lam):
    """x_k = x_star + lam**k * (x_0 - x_star): a linear update law with multiplier ``lam``.

    Domain rule: a transition landing below ``LOWER_BOUND`` is out of domain, and so is every later transition of
    the same start.
    """
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


def C3_in_domain(d):
    return bool(np.asarray(d["in_domain"]).all())


# Negative controls: each one breaks exactly the property that its criterion is supposed to detect.
def _frozen_state(d, rng):
    """Every start stays where it began: nothing converges."""
    traj = np.asarray(d["traj"])
    return {**d, "traj": np.repeat(traj[:, :1], traj.shape[1], axis=1)}


def _unit_multiplier(d, rng):
    """The local multiplier is exactly 1: neutral, not attracting."""
    return {**d, "lam": np.array(1.0)}


def _forced_exit(d, rng):
    """One start leaves the domain at the first cycle."""
    in_domain = np.array(d["in_domain"], dtype=bool, copy=True)
    in_domain[0, :] = False
    return {**d, "in_domain": in_domain}


STUDY = Study(
    name="convergence criteria on synthetic linear worlds",
    criteria=[
        Criterion("C1_local_attraction", C1_local_attraction, tolerances={"lam_threshold": (1.0, 1.0)}),
        Criterion("C2_convergence_N", C2_convergence_N, tolerances={"tol": (TOL, 0.74)}),
        Criterion("C3_in_domain", C3_in_domain),
    ],
    worlds={
        # plus: a contracting law.  All criteria can hold.
        "plus": World(lambda rng: linear_world(0.02)),
        # minus: the same world with a repelling law.  Every criterion that reads lam or the trajectories can fail.
        "minus": World(
            lambda rng: linear_world(1.39),
            derived_from="plus",
            change="update law contracting (lam 0.02) -> repelling (lam 1.39)",
        ),
    },
    controls=[
        Control("frozen_state", ["C2_convergence_N"], transform=_frozen_state),
        Control("unit_multiplier", ["C1_local_attraction"], transform=_unit_multiplier),
        Control("forced_exit", ["C3_in_domain"], transform=_forced_exit),
    ],
    deterministic=True,
)
