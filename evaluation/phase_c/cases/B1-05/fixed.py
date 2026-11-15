"""C36: In the cortical voxels where participants respond to the task, the response is at least 0.25 percent signal change: the mean task effect, averaged over those voxels and across participants, is at least 0.25, and a one-sided one-sample t test across participants of the voxel-averaged effect is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUBJ = 40
N_VOX = 1000
N_RESPONSIVE = 150     # contiguous block of task-responsive voxels, same location in every participant
AMPLITUDE = 0.5        # mean task effect (percent signal change) of a responsive voxel
SUBJECT_GAIN_SD = 0.3  # between-participant variation of response strength (relative)
GLOBAL_SD = 0.10       # participant-wide offset of the contrast estimate, mean zero
NOISE_SD = 0.8         # per-voxel estimation noise of a single participant's contrast
KERNEL = np.array([1.0, 2.0, 3.0, 2.0, 1.0])


def _brain(rng, amplitude):
    first = int(rng.integers(0, N_VOX - N_RESPONSIVE + 1))
    profile = np.zeros(N_VOX)
    profile[first:first + N_RESPONSIVE] = amplitude * rng.uniform(0.6, 1.4, N_RESPONSIVE)
    gain = rng.normal(1.0, SUBJECT_GAIN_SD, (N_SUBJ, 1))
    offset = rng.normal(0.0, GLOBAL_SD, (N_SUBJ, 1))
    white = rng.normal(0.0, 1.0, (N_SUBJ, N_VOX + KERNEL.size - 1))
    smooth = np.zeros((N_SUBJ, N_VOX))
    for k in range(KERNEL.size):
        smooth = smooth + KERNEL[k] * white[:, k:k + N_VOX]
    smooth = smooth / np.sqrt(np.sum(KERNEL ** 2))
    effect = gain * profile[None, :] + offset + NOISE_SD * smooth
    return {"effect": effect.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _brain(rng, AMPLITUDE)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _brain(rng, 0.0)


def _scramble_voxels(d, rng):
    # voxel order is shuffled separately in each participant: no voxel is the same place in two participants
    return {**d, "effect": rng.permuted(d["effect"], axis=1)}


def _flip_participants(d, rng):
    # each participant's whole map gets a random sign: no response is consistent across participants
    sign = rng.choice(np.array([-1.0, 1.0]), (d["effect"].shape[0], 1))
    return {**d, "effect": d["effect"] * sign}


def criterion(d):
    """Data keys: effect, float (40, 1000) = (subjects, voxels), task effect (task minus rest, percent signal
    change) of each cortical voxel in each participant.
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
    def _ttest1(x):
        # one-sample (or paired-difference) t test of mean(x) > 0: (mean, one-sided p); None when the variance is zero
        sd = x.std(ddof=1)
        if not sd > 0.0:
            return None
        return x.mean(), float(_sf(x.mean() / (sd / np.sqrt(x.size)), x.size - 1.0))
    e = np.asarray(d["effect"], dtype=float)
    if not np.all(np.isfinite(e)):
        return None
    n = e.shape[0]
    sel = np.arange(n // 2)
    est = np.arange(n // 2, n)
    if sel.size < 2 or est.size < 2:
        return None
    x = e[sel]
    sd = x.std(axis=0, ddof=1)
    if not np.all(sd > 0.0):
        return None
    t = x.mean(axis=0) / (sd / np.sqrt(sel.size))
    region = _sf(t, sel.size - 1.0) < 0.001
    if not region.any():
        return None
    per = e[est][:, region].mean(axis=1)
    r = _ttest1(per)
    if r is None:
        return None
    return bool(r[0] >= 0.25 and r[1] < 0.05)


STUDY = Study(
    name="C36",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the task response is set to 0 in every voxel (no voxel responds; noise, participant offsets and spatial smoothness unchanged)"),
    },
    controls=[
        Control("scramble_voxels_within_participant", ["C"], transform=_scramble_voxels),
        Control("random_sign_per_participant", ["C"], transform=_flip_participants),
    ],
)
