"""Kapi study: acceptance criteria H1-H3 of the GHZ run-2 pre-registration, tested on synthetic worlds only.

Implements PREREG.md section 4 (criteria H1-H3) and section 7 (Kapi study).  Imports only numpy and kapi; it never calls
Qiskit or hardware.  ghz2_analyze.py imports H1_small_n_accuracy, H2_gme_reach_matches and H3_population_specific from this
file unchanged and applies them to the measured data.

Data schema (synthetic worlds and the real analysis).  The grid n = [4, 8, 16, 24, 32, 48] is a design constant (GRID), not
data: the criteria index the columns by POSITION (0..5), and the analysis asserts that its column order equals GRID.
    F_pred, P_pred, C_pred   (6,)    model M2 predictions
    F_hat,  P_hat,  C_hat    (6,)    point estimates
    F_boot, P_boot, C_boot   (B, 6)  bootstrap replicates, drawn jointly per replicate

    H1_small_n_accuracy      |F_hat - F_pred| <= 0.05 at n = 4 and n = 8 (columns 0, 1); None if F_pred at those columns
                             is outside (0, 1) (or not finite)
    H2_gme_reach_matches     n_meas = largest n with F_hat > 0.5 (0 if none); n_pred = largest n with F_pred > 0.5;
                             HOLDS iff equal; None if n_pred = 0
    H3_population_specific   for n = 32 and n = 48 (columns 4, 5): 97.5th percentile of
                             ln(P_boot/P_pred) - ln(C_boot/C_pred) < 0 (both columns); None if any involved prediction or
                             replicate is <= 0

Controls (each breaks one plausible real failure; each returns the full data dict):
    stale_calibration          -> H1: F_pred + 0.06
    reach_off_by_one_step      -> H2: F_pred raised by 0.12 in every column (the predicted reach moves out)
    coherence_specific_loss    -> H3: C_boot and C_hat x 0.85, P unchanged
"""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

GRID = [4, 8, 16, 24, 32, 48]   # design constant, never part of the data
B_SYN = 400                     # replicates per synthetic sample (small, to keep the certificate fast)
BOOT_SD = 0.008                 # synthetic bootstrap spread

H1_BAND = 0.05
I4, I8, I32, I48 = 0, 1, 4, 5   # positional columns of n = 4, 8, 32, 48 (GRID order)


def _shape_ok(d, keys, boot_keys=()):
    k = len(GRID)
    for key in keys:
        if np.asarray(d[key]).shape != (k,):
            return False
    for key in boot_keys:
        a = np.asarray(d[key])
        if a.ndim != 2 or a.shape[1] != k:
            return False
    return True


def H1_small_n_accuracy(d):
    if not _shape_ok(d, ("F_pred", "F_hat")):
        return None
    f_pred = np.asarray(d["F_pred"], dtype=float)[[I4, I8]]
    f_hat = np.asarray(d["F_hat"], dtype=float)[[I4, I8]]
    if not (np.all(np.isfinite(f_pred)) and np.all(np.isfinite(f_hat))):
        return None
    if np.any(f_pred <= 0.0) or np.any(f_pred >= 1.0):
        return None
    return bool(np.all(np.abs(f_hat - f_pred) <= H1_BAND))


def _reach(values):
    n = np.asarray(GRID)
    ok = n[np.asarray(values, dtype=float) > 0.5]
    return int(ok.max()) if ok.size else 0


def H2_gme_reach_matches(d):
    if not _shape_ok(d, ("F_pred", "F_hat")):
        return None
    f_pred = np.asarray(d["F_pred"], dtype=float)
    f_hat = np.asarray(d["F_hat"], dtype=float)
    if not (np.all(np.isfinite(f_pred)) and np.all(np.isfinite(f_hat))):
        return None
    if np.any(f_pred <= 0.0) or np.any(f_pred >= 1.0):
        return None          # revision #1: a model fidelity outside (0, 1) is not a physical prediction
    n_pred = _reach(f_pred)
    if n_pred == 0:
        return None          # nothing predicted to compare with
    return bool(_reach(f_hat) == n_pred)


def H3_population_specific(d):
    if not _shape_ok(d, ("P_pred", "C_pred"), ("P_boot", "C_boot")):
        return None
    cols = [I32, I48]
    p_pred = np.asarray(d["P_pred"], dtype=float)[cols]
    c_pred = np.asarray(d["C_pred"], dtype=float)[cols]
    p_boot = np.asarray(d["P_boot"], dtype=float)[:, cols]
    c_boot = np.asarray(d["C_boot"], dtype=float)[:, cols]
    for a in (p_pred, c_pred, p_boot, c_boot):
        if not np.all(np.isfinite(a)) or np.any(a <= 0.0):
            return None
    diff = np.log(p_boot / p_pred) - np.log(c_boot / c_pred)       # (B, 2)
    return bool(np.all(np.percentile(diff, 97.5, axis=0) < 0.0))


# ---------------------------------------------------------------------------------------------------- synthetic worlds
F_PRED = np.array([0.936, 0.889, 0.70, 0.58, 0.455, 0.29])
N_ARR = np.array(GRID, dtype=float)


def _world(p_hat, c_hat, rng):
    p_pred = F_PRED + 0.02
    c_pred = F_PRED - 0.02
    f_hat = (p_hat + c_hat) / 2.0
    shape = (B_SYN, len(GRID))
    p_boot = p_hat[None, :] + rng.normal(0.0, BOOT_SD, size=shape)
    c_boot = c_hat[None, :] + rng.normal(0.0, BOOT_SD, size=shape)
    return {
        "F_pred": F_PRED.copy(), "P_pred": p_pred, "C_pred": c_pred,
        "F_hat": f_hat, "P_hat": p_hat, "C_hat": c_hat,
        "F_boot": f_hat[None, :] + rng.normal(0.0, BOOT_SD, size=shape), "P_boot": p_boot, "C_boot": c_boot,
    }


def plus_world(rng):
    """Population shortfall grows with n faster than the coherence shortfall (P_hat = P_pred e^{-0.004 n},
    C_hat = C_pred e^{-0.001 n}); the model is accurate at small n and predicts the reach."""
    p_pred, c_pred = F_PRED + 0.02, F_PRED - 0.02
    return _world(p_pred * np.exp(-0.004 * N_ARR), c_pred * np.exp(-0.001 * N_ARR), rng)


def minus_world(rng):
    """Shortfall in coherence, not populations: P_hat = 0.98 P_pred, C_hat = 0.70 C_pred."""
    p_pred, c_pred = F_PRED + 0.02, F_PRED - 0.02
    return _world(0.98 * p_pred, 0.70 * c_pred, rng)


# ------------------------------------------------------------------------------------------------------------ controls
def _stale_calibration(d, rng):
    """The model uses an out-of-date calibration: F_pred is 0.06 too high."""
    return {**d, "F_pred": np.asarray(d["F_pred"]) + 0.06}


def _reach_off_by_one_step(d, rng):
    """The predicted reach moves out one grid step: the model overpredicts the large states (n = 32, 48) by 0.12.

    Revision #2: shifting every column pushed F_pred(4) above 1, which revision #1 makes UNDEFINED.
    """
    f = np.array(d["F_pred"], dtype=float, copy=True)
    f[[I32, I48]] += 0.12
    return {**d, "F_pred": f}


def _coherence_specific_loss(d, rng):
    """Coherence is lost, populations are not: C_boot and C_hat x 0.85, P unchanged."""
    return {**d, "C_boot": np.asarray(d["C_boot"]) * 0.85, "C_hat": np.asarray(d["C_hat"]) * 0.85}


STUDY = Study(
    name="GHZ run 2: corrected model M2 on new data, H1-H3",
    criteria=[
        Criterion("H1_small_n_accuracy", H1_small_n_accuracy),
        Criterion("H2_gme_reach_matches", H2_gme_reach_matches),
        Criterion("H3_population_specific", H3_population_specific),
    ],
    worlds={
        "plus": World(plus_world),
        "minus": World(minus_world, derived_from="plus",
                       change="shortfall in coherence, not populations; model overpredicts small states and the GME reach"),
    },
    controls=[
        Control("stale_calibration", ["H1_small_n_accuracy"], transform=_stale_calibration),
        Control("reach_off_by_one_step", ["H2_gme_reach_matches"], transform=_reach_off_by_one_step),
        Control("coherence_specific_loss", ["H3_population_specific"], transform=_coherence_specific_loss),
    ],
    deterministic=False,
    budget=Budget(),
)
