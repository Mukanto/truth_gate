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
    raise NotImplementedError


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
