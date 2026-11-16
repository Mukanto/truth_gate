"""Truth_Gate study: acceptance criterion H4 of the GHZ run-3 pre-registration, tested on synthetic worlds only.

Implements PREREG.md (run 3) section 4 (criterion H4) and section 7.  Imports only numpy and truth_gate; it never calls Qiskit
or hardware.  ghz3_analyze.py imports H4_overprediction_every_n from this file unchanged and applies it to the measured data.

Data schema (synthetic worlds and the real analysis) = the schema of ghz2_study.py.  The grid n = [4, 8, 16, 24, 32, 48] is a
design constant (GRID), not data: the criterion indexes the columns by POSITION (0..5), and the analysis asserts that its
column order equals GRID.
    F_pred, P_pred, C_pred   (6,)    model M2 predictions
    F_hat,  P_hat,  C_hat    (6,)    point estimates
    F_boot, P_boot, C_boot   (B, 6)  bootstrap replicates, drawn jointly per replicate

    H4_overprediction_every_n   for every n in GRID: the 97.5th percentile of F_boot(n)/F_pred(n) is < 1 -> HOLDS;
                                otherwise FAILS; None (UNDEFINED, abstain) if any F_pred is outside (0, 1) or not finite, or
                                any F_boot is <= 0 or not finite, or the shapes are wrong

Worlds:
    plus    M2 too high by a run-2-like ratio: R(n) = F_hat/F_pred = 0.95, 0.94, 0.88, 0.86, 0.85, 0.84 (n = 4 ... 48) with a
            small per-sample jitter; H4 holds
    minus   M2 accurate (R = 1, same jitter); H4 fails at every n

Control (a plausible real failure, PREREG section 7):
    accurate_small_n_too_high_large_n   the model is accurate at n = 4 and 8 but too high at larger n -> H4 must fail
"""
import numpy as np

from truth_gate import Budget, Control, Criterion, Study, World

GRID = [4, 8, 16, 24, 32, 48]   # design constant, never part of the data (same as ghz2_study.GRID)
B_SYN = 400                     # replicates per synthetic sample (small, to keep the certificate fast)
BOOT_SD = 0.008                 # synthetic bootstrap spread of P and C
Q = 97.5                        # percentile of the ratio F_boot / F_pred

F_PRED = np.array([0.936, 0.889, 0.70, 0.58, 0.455, 0.29])      # as in ghz2_study.py
R_RUN2 = np.array([0.95, 0.94, 0.88, 0.86, 0.85, 0.84])         # run 2: F_meas / F_pred, n = 4 ... 48
R_JITTER = 0.01                                                 # per-sample uniform jitter of the true ratio
SMALL_N_COLS = [0, 1]                                           # n = 4 and 8


def H4_overprediction_every_n(d):
    k = len(GRID)
    f_pred = np.asarray(d["F_pred"], dtype=float)
    f_boot = np.asarray(d["F_boot"], dtype=float)
    if f_pred.shape != (k,) or f_boot.ndim != 2 or f_boot.shape[1] != k or f_boot.shape[0] < 1:
        return None
    if not (np.all(np.isfinite(f_pred)) and np.all(np.isfinite(f_boot))):
        return None
    if np.any(f_pred <= 0.0) or np.any(f_pred >= 1.0):
        return None          # a model fidelity outside (0, 1) is not a physical prediction
    if np.any(f_boot <= 0.0):
        return None          # a ratio of a non-positive replicate is not an overprediction statement
    ratio = f_boot / f_pred[None, :]
    return bool(np.all(np.percentile(ratio, Q, axis=0) < 1.0))


# ---------------------------------------------------------------------------------------------------- synthetic worlds
def _world(ratio, rng):
    """Data whose true ratio F/F_pred per column is ``ratio`` (shape (6,)); P and C scale with the same ratio."""
    p_pred = F_PRED + 0.02
    c_pred = F_PRED - 0.02
    p_hat, c_hat = p_pred * ratio, c_pred * ratio
    shape = (B_SYN, len(GRID))
    p_boot = p_hat[None, :] + rng.normal(0.0, BOOT_SD, size=shape)
    c_boot = c_hat[None, :] + rng.normal(0.0, BOOT_SD, size=shape)
    return {
        "F_pred": F_PRED.copy(), "P_pred": p_pred, "C_pred": c_pred,
        "F_hat": (p_hat + c_hat) / 2.0, "P_hat": p_hat, "C_hat": c_hat,
        "F_boot": (p_boot + c_boot) / 2.0, "P_boot": p_boot, "C_boot": c_boot,
    }


def plus_world(rng):
    """M2 too high by a run-2-like ratio (R about 0.84 to 0.95), with per-sample jitter of +-0.01."""
    return _world(R_RUN2 + rng.uniform(-R_JITTER, R_JITTER, size=len(GRID)), rng)


def minus_world(rng):
    """M2 accurate: R = 1 (same jitter)."""
    return _world(1.0 + rng.uniform(-R_JITTER, R_JITTER, size=len(GRID)), rng)


# ------------------------------------------------------------------------------------------------------------ controls
def _accurate_small_n_too_high_large_n(d, rng):
    """M2 is accurate at n = 4 and 8 and keeps its overprediction at larger n: the small-n columns of every measured quantity
    are rescaled so that their mean equals the prediction (ratio about 1); the other columns are unchanged."""
    out = dict(d)
    cols = SMALL_N_COLS
    for comp in ("F", "P", "C"):
        pred = np.asarray(d[f"{comp}_pred"], dtype=float)[cols]
        hat = np.asarray(d[f"{comp}_hat"], dtype=float)
        boot = np.asarray(d[f"{comp}_boot"], dtype=float)
        scale = pred / hat[cols]
        hat2, boot2 = hat.copy(), boot.copy()
        hat2[cols] = hat[cols] * scale
        boot2[:, cols] = boot[:, cols] * scale[None, :]
        out[f"{comp}_hat"], out[f"{comp}_boot"] = hat2, boot2
    return out


STUDY = Study(
    name="GHZ run 3: M2 overprediction on a new calibration, H4",
    criteria=[
        Criterion("H4_overprediction_every_n", H4_overprediction_every_n),
    ],
    worlds={
        "plus": World(plus_world),
        "minus": World(minus_world, derived_from="plus",
                       change="M2 accurate (R = 1) instead of too high by a run-2-like ratio"),
    },
    controls=[
        Control("accurate_small_n_too_high_large_n", ["H4_overprediction_every_n"],
                transform=_accurate_small_n_too_high_large_n),
    ],
    deterministic=False,
    budget=Budget(),
)
