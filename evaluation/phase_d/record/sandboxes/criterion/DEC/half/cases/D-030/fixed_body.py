import numpy as np


def criterion(d):
    """Claim: the proportion of neurons whose expected firing rate rises after
    the manipulation is larger among neurons whose expected pre-manipulation
    rate is below 8 Hz than among neurons whose expected pre-manipulation rate
    is at least 8 Hz, by at least 0.20.

    d['pre']: float array (neurons, trials) = (400, 40); firing rate in Hz of
        each neuron on each trial before the manipulation.
    d['post']: float array (neurons, trials) = (400, 40); firing rate in Hz of
        each neuron on each trial after the manipulation.

    Returns True when the difference between the two proportions is >= 0.20,
    False otherwise; None when a value is non-finite or a rate bin is empty.
    """
    pre = np.asarray(d['pre'], dtype=float)
    post = np.asarray(d['post'], dtype=float)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    if pre.shape[1] < 2:
        return None
    halves = (pre[:, 0::2], pre[:, 1::2])
    post_mean = post.mean(axis=1)
    diffs = []
    for k in (0, 1):
        base = halves[k].mean(axis=1)
        rise = post_mean > halves[1 - k].mean(axis=1)
        low = base < 8.0
        high = ~low
        if not np.any(low) or not np.any(high):
            return None
        diffs.append(np.mean(rise[low]) - np.mean(rise[high]))
    return bool(np.mean(diffs) >= 0.20)
