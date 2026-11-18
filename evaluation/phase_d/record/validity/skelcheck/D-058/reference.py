"""D-058: Features computed from wearable-sensor signals recognise walking in newly recruited subjects: the classification error rate for walking versus other activities is at most 0.10."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

S = 30
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

def derange(rng, n):
    """Index array that gives every unit the value of a different unit."""
    order = rng.permutation(n)
    idx = np.empty(n, dtype=np.int64)
    idx[order] = np.roll(order, -1)
    return idx


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


def criterion(d):
    """Data keys: signal_features (subjects, windows, features) float64: features computed from the sensor signal in each time window of each subject; walking (subjects, windows) bool: True if the subject was walking during the window.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-058",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="each subject gets the walking sequence of another subject (independent of the features); bout structure, walking shares and all feature distributions unchanged"),
    },
    controls=[Control("D-058", ["C"], transform=control)],
)
