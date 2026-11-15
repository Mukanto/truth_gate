"""C28: Among the recorded visual neurons that fire more to vertical than to horizontal bars, the mean orientation index, (vertical minus horizontal) / (vertical plus horizontal) computed from trial-averaged firing rates, is at least 0.1."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _world(rng, tuning_sd):
    neurons, trials = 250, 15
    mean_rate = np.clip(5.0 * np.exp(rng.normal(0.0, 0.6, neurons)), 1.0, 60.0)   # spikes/s, varies by neuron
    # true orientation index of each neuron: (vertical - horizontal) / (vertical + horizontal) of its mean rates
    true_index = np.clip(tuning_sd * rng.normal(0.0, 1.0, neurons), -0.9, 0.9)
    # trial-to-trial gain fluctuations (over-dispersed spike counts), independent between presentations
    gain_v = rng.gamma(4.0, 0.25, (neurons, trials))
    gain_h = rng.gamma(4.0, 0.25, (neurons, trials))
    # spike counts in a one-second window
    rate_v = rng.poisson((mean_rate * (1.0 + true_index))[:, None] * gain_v)
    rate_h = rng.poisson((mean_rate * (1.0 - true_index))[:, None] * gain_h)
    return {"rate_vertical": rate_v.astype(np.float64), "rate_horizontal": rate_h.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.3)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def _shuffle_orientation_labels(d, rng):
    # within each neuron, the 30 presentations are re-dealt at random to the two orientations
    trials = d["rate_vertical"].shape[1]
    pooled = np.concatenate([d["rate_vertical"], d["rate_horizontal"]], axis=1)
    shuffled = rng.permuted(pooled, axis=1)
    while np.array_equal(shuffled, pooled):
        shuffled = rng.permuted(pooled, axis=1)
    return {**d, "rate_vertical": shuffled[:, :trials], "rate_horizontal": shuffled[:, trials:]}


def criterion(d):
    """Data keys: rate_vertical (250, 15) float, firing rate (spikes/s) of each neuron (axis 0) on each
    presentation (axis 1) of a vertical bar; rate_horizontal (250, 15) float, firing rate of the same neurons on
    each presentation of a horizontal bar. Rows are the same neurons in both arrays; the presentations of the two
    orientations are different trials (not paired).
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
    rv = np.asarray(d["rate_vertical"], dtype=float)
    rh = np.asarray(d["rate_horizontal"], dtype=float)
    if not (np.all(np.isfinite(rv)) and np.all(np.isfinite(rh))):
        return None
    nt = rv.shape[1]
    sel = np.arange(0, nt, 2)
    est = np.arange(1, nt, 2)
    if sel.size < 2 or est.size < 2:
        return None
    a = rv[:, sel]
    b = rh[:, sel]
    va = a.var(axis=1, ddof=1) / sel.size
    vb = b.var(axis=1, ddof=1) / sel.size
    se2 = va + vb
    if not np.all(se2 > 0.0):
        return None
    df = se2 ** 2 / (va ** 2 / (sel.size - 1.0) + vb ** 2 / (sel.size - 1.0))
    t = (a.mean(axis=1) - b.mean(axis=1)) / np.sqrt(se2)
    chosen = _sf(t, df) < 0.05
    if not chosen.any():
        return None
    mv = rv[chosen][:, est].mean(axis=1)
    mh = rh[chosen][:, est].mean(axis=1)
    index = (mv - mh) / (mv + mh)
    if not np.all(np.isfinite(index)):
        return None
    return bool(index.mean() >= 0.1)


STUDY = Study(
    name="C28",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="no neuron has an orientation preference: true orientation index set to 0 for every neuron (was spread with SD 0.3 around 0, mean about 0.24 among vertical-preferring neurons); firing-rate levels and trial-to-trial variability kept"),
    },
    controls=[
        Control("shuffle_orientation_labels_within_neuron", ["C"], transform=_shuffle_orientation_labels),
    ],
)
