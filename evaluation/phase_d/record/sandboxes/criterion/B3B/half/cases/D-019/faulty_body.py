import numpy as np


def criterion(d):
    """Claim: In 400 adults with systolic blood pressure measured at five annual visits, those with a higher initial blood pressure have a lower yearly rate of change: the regression slope of an individual's underlying yearly rate of change in systolic blood pressure on the individual's underlying initial systolic blood pressure is at most -0.03 mmHg per year per mmHg.

    d: dict of numpy arrays, with the keys
      systolic_bp  (individuals, occasions)  float: systolic blood pressure of each individual at each of five annual visits, with the visits in time order, in mmHg

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
    u = x[:, 0]
    if np.ptp(u) == 0:
        return None
    c = np.cov(u, b)
    v = c[0, 0]
    cc = c[0, 1]
    if not v > 0.0:
        return None
    slope = cc / v
    if not np.isfinite(slope):
        return None
    return bool(slope <= -0.03)
