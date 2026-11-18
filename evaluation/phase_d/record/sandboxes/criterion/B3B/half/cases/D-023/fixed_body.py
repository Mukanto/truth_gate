import numpy as np


def corr(x, y):
    xc = x - np.mean(x)
    yc = y - np.mean(y)
    return float(np.sum(xc * yc) / np.sqrt(np.sum(xc * xc) * np.sum(yc * yc)))


def criterion(d):
    """Claim: Across 2000 adult specimens of one beetle species, head width and wing length are associated beyond what body length explains: the partial correlation between head width and wing length, controlling for body length, is at least 0.30.

    d: dict of numpy arrays, with the keys
      head_width  (specimens,)  float: head width of each specimen, in mm
      wing_length  (specimens,)  float: wing length of each specimen, in mm
      body_length  (specimens,)  float: body length of each specimen, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    hw = np.asarray(d['head_width'], dtype=float)
    wl = np.asarray(d['wing_length'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    n = hw.shape[0]
    if n < 3:
        return None
    if not (np.all(np.isfinite(hw)) and np.all(np.isfinite(wl)) and np.all(np.isfinite(bl))):
        return None
    if np.ptp(bl) == 0:
        return None
    X = np.column_stack([np.ones(n), bl])
    u = hw - X @ np.linalg.lstsq(X, hw, rcond=None)[0]
    v = wl - X @ np.linalg.lstsq(X, wl, rcond=None)[0]
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        return None
    if np.ptp(u) == 0 or np.ptp(v) == 0:
        return None
    return bool(corr(u, v) >= 0.30)
