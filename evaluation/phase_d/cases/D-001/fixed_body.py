import numpy as np


def criterion(d):
    """Claim: Among 150 adults with systolic blood pressure measured at three annual visits, those with a higher initial blood pressure have a lower yearly rate of change: the Pearson correlation between an individual's underlying yearly rate of change in systolic blood pressure and the individual's underlying initial systolic blood pressure is at most -0.30.

    d: dict of numpy arrays, with the keys
      systolic_bp  (individuals, occasions)  float: systolic blood pressure of each individual at each of three annual visits, with the visits in time order, in mmHg

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    x = np.asarray(d['systolic_bp'], dtype=float)
    n = x.shape[0]
    m = x.shape[1]
    if n < 2:
        return None
    if not (np.all(np.isfinite(x))):
        return None
    t = np.arange(m, dtype=float)
    tbar = float(np.mean(t))
    tc = t - tbar
    sxx = float(np.sum(tc * tc))
    b = (x - np.mean(x, axis=1, keepdims=True)) @ tc / sxx
    a = np.mean(x, axis=1) - b * tbar
    u = a
    if np.ptp(u) == 0:
        return None
    c = np.cov(u, b)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
    res = x - a[:, None] - b[:, None] * t[None, :]
    s2 = float(np.sum(res * res)) / (n * (m - 2))
    v = v - s2 * (1.0 / m + tbar * tbar / sxx)
    w = w - s2 / sxx
    cc = cc + s2 * tbar / sxx
    if not (v > 0.0 and w > 0.0):
        return None
    r = cc / np.sqrt(v * w)
    return bool(r <= -0.30)
