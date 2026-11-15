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
    raise NotImplementedError


STUDY = Study(
    name="C54",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the stimulus response is set to zero at every electrode: no electrode responds and the stimulus condition explains none of the amplitude variance (background activity and noise unchanged)"),
    },
    controls=[Control("permute_stimulus_condition_across_trials", ["C"], transform=permute_stimulus)],
)
