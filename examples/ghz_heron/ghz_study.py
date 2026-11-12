"""Kapi study: acceptance criteria G1-G3 of the GHZ-on-Heron pre-registration (v2), tested on synthetic worlds only.

Implements PREREG.md section 6 (criteria G1-G3) and section 8 (Kapi study); revisions in REVISIONS.md.  Imports only
numpy and kapi; it never calls Qiskit or hardware.  ghz_analyze.py imports G1_small_n_accuracy, G2_excess_decay_grows
and G3_gme_reach_matches from this file unchanged and applies them to the measured data.

Data schema (synthetic worlds and the real analysis).  The grid n = [4, 8, 16, 32, 48] is a design constant (GRID), not
data: the criteria index the columns by POSITION (0..4), and the analysis asserts that its column order equals GRID.
    F_pred   (5,)    model prediction F_pred(n), columns in GRID order
    F_hat    (5,)    point estimates of the measured GHZ fidelity
    F_boot   (B, 5)  bootstrap replicates, drawn jointly per replicate

    G1_small_n_accuracy      0.9 <= F_hat/F_pred <= 1.1 at n = 4 and n = 8 (columns 0, 1); None if F_pred <= 0
    G2_excess_decay_grows    97.5th percentile of ln(F_boot[:,4]/F_pred[4]) - ln(F_boot[:,2]/F_pred[2]) < 0
                             (n = 48 and n = 16); None if any involved value is <= 0
    G3_gme_reach_matches     n_meas = largest n with 2.5th percentile of F_boot > 0.5 (0 if none); n_pred = largest n
                             with F_pred > 0.5; HOLDS iff equal; None if n_pred = 0 (a reach comparison needs a
                             predicted reach)

Controls (each breaks one plausible real failure; each returns the full data dict):
    stale_calibration        -> G1: F_pred inflated by 15%
    column_swap_16_48        -> G2: columns 2 and 4 exchanged in F_pred, F_boot and F_hat (an indexing bug)
    device_worse_than_model  -> G3: F_boot and F_hat shifted down by 0.15 (revision #6)
"""
import numpy as np

from kapi import Budget, Control, Criterion, Study, World

GRID = [4, 8, 16, 32, 48]   # design constant, never part of the data
B_SYN = 400                 # replicates per synthetic sample (small, to keep the certificate fast)
BOOT_SD = 0.01              # synthetic bootstrap spread

R_LO, R_HI = 0.9, 1.1       # G1 band
I4, I8, I16, I48 = 0, 1, 2, 4   # positional columns of n = 4, 8, 16, 48 (GRID order)


def G1_small_n_accuracy(d):
    f_pred = np.asarray(d["F_pred"], dtype=float)
    f_hat = np.asarray(d["F_hat"], dtype=float)
    if f_pred.shape != (len(GRID),) or f_hat.shape != (len(GRID),):
        return None
    f_pred, f_hat = f_pred[[I4, I8]], f_hat[[I4, I8]]
    if not (np.all(np.isfinite(f_pred)) and np.all(np.isfinite(f_hat))) or np.any(f_pred <= 0):
        return None
    r = f_hat / f_pred
    return bool(np.all((r >= R_LO) & (r <= R_HI)))


def G2_excess_decay_grows(d):
    f_pred = np.asarray(d["F_pred"], dtype=float)
    boot = np.asarray(d["F_boot"], dtype=float)
    if f_pred.shape != (len(GRID),) or boot.ndim != 2 or boot.shape[1] != len(GRID):
        return None
    if f_pred[I16] <= 0 or f_pred[I48] <= 0 or not np.all(np.isfinite(boot[:, [I16, I48]])):
        return None
    if np.any(boot[:, I16] <= 0) or np.any(boot[:, I48] <= 0):
        return None
    diff = np.log(boot[:, I48] / f_pred[I48]) - np.log(boot[:, I16] / f_pred[I16])
    return bool(np.percentile(diff, 97.5) < 0.0)


def G3_gme_reach_matches(d):
    n = np.asarray(GRID, dtype=float)
    f_pred = np.asarray(d["F_pred"], dtype=float)
    boot = np.asarray(d["F_boot"], dtype=float)
    if boot.ndim != 2 or boot.shape[1] != n.size or f_pred.shape != (n.size,) or not np.all(np.isfinite(boot)):
        return None
    pred_ok = n[f_pred > 0.5]
    if not pred_ok.size:
        return None          # n_pred = 0: nothing predicted to compare with
    lo = np.percentile(boot, 2.5, axis=0)
    meas_ok = n[lo > 0.5]
    n_meas = int(meas_ok.max()) if meas_ok.size else 0
    return bool(n_meas == int(pred_ok.max()))


# ---------------------------------------------------------------------------------------------------- synthetic worlds
PLUS_F_PRED = np.array([0.92, 0.85, 0.72, 0.48, 0.38])
PLUS_F_HAT = np.array([0.90, 0.82, 0.62, 0.38, 0.22])


def _world(f_pred, f_hat, rng):
    f_pred = np.array(f_pred, dtype=float)
    f_hat = np.array(f_hat, dtype=float)
    return {
        "F_pred": f_pred,
        "F_hat": f_hat,
        "F_boot": f_hat[None, :] + rng.normal(0.0, BOOT_SD, size=(B_SYN, len(GRID))),
    }


def plus_world(rng):
    """Measured fidelity decays faster than the model with n (excess decay), model accurate at small n."""
    return _world(PLUS_F_PRED, PLUS_F_HAT, rng)


def minus_world(rng):
    """Measured fidelity is a constant 0.7 x model: no size-dependent excess."""
    return _world(PLUS_F_PRED, 0.7 * PLUS_F_PRED, rng)


# ------------------------------------------------------------------------------------------------------------ controls
def _stale_calibration(d, rng):
    """The model uses an out-of-date calibration: F_pred is 15% too high."""
    return {**d, "F_pred": np.asarray(d["F_pred"]) * 1.15}


def _column_swap_16_48(d, rng):
    """Indexing bug: the n = 16 and n = 48 columns are exchanged (F_pred, F_boot and F_hat alike)."""
    out = dict(d)
    for key in ("F_pred", "F_hat", "F_boot"):
        a = np.array(d[key], copy=True)
        a[..., [I16, I48]] = a[..., [I48, I16]]
        out[key] = a
    return out


def _device_worse_than_model(d, rng):
    """The device is uniformly worse than the model: every measured fidelity is 0.15 lower (one grid step of GME reach lost)."""
    return {**d, "F_boot": np.asarray(d["F_boot"]) - 0.15, "F_hat": np.asarray(d["F_hat"]) - 0.15}


STUDY = Study(
    name="GHZ fidelity vs calibration model (Heron r2): G1-G3",
    criteria=[
        Criterion("G1_small_n_accuracy", G1_small_n_accuracy),
        Criterion("G2_excess_decay_grows", G2_excess_decay_grows),
        Criterion("G3_gme_reach_matches", G3_gme_reach_matches),
    ],
    worlds={
        "plus": World(plus_world),
        "minus": World(minus_world, derived_from="plus",
                       change="measured fidelity is a constant 0.7 x model (no size-dependent excess)"),
    },
    controls=[
        Control("stale_calibration", ["G1_small_n_accuracy"], transform=_stale_calibration),
        Control("column_swap_16_48", ["G2_excess_decay_grows"], transform=_column_swap_16_48),
        Control("device_worse_than_model", ["G3_gme_reach_matches"], transform=_device_worse_than_model),
    ],
    deterministic=False,
    budget=Budget(),
)
