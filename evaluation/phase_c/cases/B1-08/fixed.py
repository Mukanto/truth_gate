"""C54: Over the scalp electrodes that respond to the stimulus, the stimulus condition explains at least 10% of the variance of the electrode-averaged post-stimulus amplitude across trials (R-squared of at least 0.10 in a regression of that amplitude on the stimulus condition)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_TRIALS = 100
N_ELECTRODES = 64
N_STIMULUS = 50
# Electrodes laid out on an 8 x 8 grid over the scalp (row, column of each electrode index).
GRID_ROW = np.arange(N_ELECTRODES) // 8
GRID_COL = np.arange(N_ELECTRODES) % 8
# Stimulus response: a focal patch centred between grid positions, zero outside the patch.
RESPONSE_SHAPE = np.exp(-((GRID_ROW - 2.5) ** 2 + (GRID_COL - 4.5) ** 2) / (2.0 * 1.3 ** 2))
RESPONSE_PEAK = 7.5      # microvolts at the centre of the patch
RESPONSE = RESPONSE_PEAK * np.where(RESPONSE_SHAPE > 0.3, RESPONSE_SHAPE, 0.0)
GAIN_SD = 0.3            # trial-to-trial variability of the response size
GLOBAL_SD = 3.0          # background activity common to all electrodes, microvolts
SMOOTH_SD = 1.2          # background activity in smooth spatial patterns, per pattern
LOCAL_SD = 4.0           # independent noise at each electrode
# Six smooth spatial patterns over the grid (low spatial frequencies).
SMOOTH_PATTERNS = np.stack([
    np.cos(np.pi * (GRID_ROW + 0.5) / 8.0),
    np.cos(np.pi * (GRID_COL + 0.5) / 8.0),
    np.cos(2.0 * np.pi * (GRID_ROW + 0.5) / 8.0),
    np.cos(2.0 * np.pi * (GRID_COL + 0.5) / 8.0),
    np.cos(np.pi * (GRID_ROW + 0.5) / 8.0) * np.cos(np.pi * (GRID_COL + 0.5) / 8.0),
    np.cos(3.0 * np.pi * (GRID_ROW + 0.5) / 8.0),
])


def _generate(rng, effect):
    stimulus = np.zeros(N_TRIALS, dtype=bool)
    stimulus[rng.permutation(N_TRIALS)[:N_STIMULUS]] = True
    common = rng.normal(0.0, GLOBAL_SD, size=(N_TRIALS, 1))
    smooth = rng.normal(0.0, SMOOTH_SD, size=(N_TRIALS, SMOOTH_PATTERNS.shape[0])) @ SMOOTH_PATTERNS
    local = rng.normal(0.0, LOCAL_SD, size=(N_TRIALS, N_ELECTRODES))
    gain = 1.0 + GAIN_SD * rng.normal(size=(N_TRIALS, 1))
    evoked = effect * stimulus[:, None] * gain * RESPONSE
    return {"amplitude": common + smooth + local + evoked, "stimulus": stimulus}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0)


def permute_stimulus(d, rng):
    return {**d, "stimulus": d["stimulus"][rng.permutation(d["stimulus"].shape[0])]}


def criterion(d):
    """Data keys: amplitude, float array of shape (100, 64) = (trials, electrodes): mean post-stimulus EEG amplitude
    (microvolts) at each electrode on each trial; stimulus, bool array of shape (100,) = (trials,): True on trials
    with the stimulus present, False on control trials. Which electrodes respond to the stimulus is not given.
    Holds when the claim is supported by the data. Written by someone else."""
    def _sf(t, df):
        # upper-tail probability of Student's t: integral of cos(x)**(df-1) over [arctan(t/sqrt(df)), pi/2], trapezoid rule
        t = np.asarray(t, dtype=float)
        df = np.broadcast_to(np.asarray(df, dtype=float), t.shape)
        u = np.linspace(0.0, 1.0, 1001)

        def tail(lo):
            x = lo[..., None] + (np.pi / 2.0 - lo[..., None]) * u
            f = np.cos(x) ** (df[..., None] - 1.0)
            return (f.sum(-1) - 0.5 * (f[..., 0] + f[..., -1])) * (np.pi / 2.0 - lo) / (len(u) - 1)

        ang = np.arctan(np.abs(t) / np.sqrt(df))
        upper = tail(ang) / (2.0 * tail(np.zeros_like(ang)))
        return np.where(t >= 0.0, upper, 1.0 - upper)
    amp = np.asarray(d["amplitude"], dtype=float)
    stim = np.asarray(d["stimulus"], dtype=bool)
    if not np.all(np.isfinite(amp)):
        return None
    n = amp.shape[0]
    sel = np.arange(0, n, 2)
    est = np.arange(1, n, 2)
    if est.size < 3:
        return None
    xs = amp[sel]
    ss = stim[sel]
    a = xs[ss]
    b = xs[~ss]
    if a.shape[0] < 2 or b.shape[0] < 2:
        return None
    va = a.var(axis=0, ddof=1) / a.shape[0]
    vb = b.var(axis=0, ddof=1) / b.shape[0]
    se2 = va + vb
    if not np.all(se2 > 0.0):
        return None
    df = se2 ** 2 / (va ** 2 / (a.shape[0] - 1.0) + vb ** 2 / (b.shape[0] - 1.0))
    t = (a.mean(axis=0) - b.mean(axis=0)) / np.sqrt(se2)
    chosen = _sf(t, df) < 0.05
    if not chosen.any():
        return None
    avg = amp[est][:, chosen].mean(axis=1)
    y = stim[est].astype(float) - stim[est].mean()
    z = avg - avg.mean()
    syy = (y ** 2).sum()
    szz = (z ** 2).sum()
    if not (syy > 0.0 and szz > 0.0):
        return None
    r2 = (y @ z) ** 2 / (syy * szz)
    return bool(r2 >= 0.10)


STUDY = Study(
    name="C54",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the stimulus response is set to zero at every electrode: no electrode responds and the stimulus condition explains none of the amplitude variance (background activity and noise unchanged)"),
    },
    controls=[Control("permute_stimulus_condition_across_trials", ["C"], transform=permute_stimulus)],
)
