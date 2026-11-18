import numpy as np


def first_coef(X, y):
    return float(np.linalg.lstsq(X, y, rcond=None)[0][1])


def criterion(d):
    """Claim: Across 25 populations of one beetle species, with 40 specimens measured in each, wing length rises with head width at a given body length: the mean over populations of the within-population multiple-regression coefficient of wing length on head width, with body length as the other predictor, is at least 0.30 (mm of wing length per mm of head width).

    d: dict of numpy arrays, with the keys
      head_width  (populations, specimens)  float: head width of each specimen in each population, in mm
      wing_length  (populations, specimens)  float: wing length of each specimen in each population, in mm
      body_length  (populations, specimens)  float: body length of each specimen in each population, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    hw = np.asarray(d['head_width'], dtype=float)
    wl = np.asarray(d['wing_length'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    npop = hw.shape[0]
    n = hw.shape[1]
    if npop < 1 or n < 3:
        return None
    if not (np.all(np.isfinite(hw)) and np.all(np.isfinite(wl)) and np.all(np.isfinite(bl))):
        return None
    slopes = []
    for p in range(npop):
        y = wl[p]
        X = np.column_stack([np.ones(n), hw[p], bl[p]])
        if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
            return None
        for j in range(1, X.shape[1]):
            if np.ptp(X[:, j]) == 0:
                return None
        slopes.append(first_coef(X, y))
    return bool(np.mean(slopes) >= 0.30)
