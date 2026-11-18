import numpy as np


def first_share(M):
    ev = np.linalg.eigvalsh(np.cov(M, rowvar=False))
    tot = float(np.sum(ev))
    if not tot > 0.0:
        return None
    return float(ev[-1]) / tot


def criterion(d):
    """Claim: Among 400 adult beetles measured on six skeletal dimensions, the dimensions share a common shape pattern beyond body length: after removing the linear effect of body length from each of the six dimensions, the first principal component of their covariance matrix explains at least 40% of the total variance.

    d: dict of numpy arrays, with the keys
      skeletal  (specimens, dimensions)  float: six linear skeletal dimensions of each specimen, in mm
      body_length  (specimens,)  float: body length of each specimen, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    s = np.asarray(d['skeletal'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    n = s.shape[0]
    if n < 3:
        return None
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(bl))):
        return None
    M = s / bl[:, None]
    if not np.all(np.isfinite(M)):
        return None
    share = first_share(M)
    if share is None:
        return None
    return bool(share >= 0.40)
