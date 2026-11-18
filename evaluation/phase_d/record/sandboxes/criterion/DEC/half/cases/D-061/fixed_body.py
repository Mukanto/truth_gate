import numpy as np


def _lgamma(x):
    c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028,
         771.32342877765313, -176.61502916214059, 12.507343278686905,
         -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)
    x = x - 1.0
    a = c[0]
    t = x + 7.5
    for i in range(1, 9):
        a = a + c[i] / (x + i)
    return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a)


def _betacf(a, b, x):
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 2000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h = h * d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        de = d * c
        h = h * de
        if abs(de - 1.0) < 1e-15:
            break
    return h


def _betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = (_lgamma(a + b) - _lgamma(a) - _lgamma(b)
           + a * np.log(x) + b * np.log(1.0 - x))
    bt = np.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * _betacf(a, b, x) / a)
    return float(1.0 - bt * _betacf(b, a, 1.0 - x) / b)


def _t_sf(t, df):
    t = float(t)
    df = float(df)
    if t == 0.0:
        return 0.5
    x = df / (df + t * t)
    p = 0.5 * _betainc(0.5 * df, 0.5, x)
    if t > 0.0:
        return p
    return 1.0 - p


def _t_crit(alpha, df):
    lo = 0.0
    hi = 1000.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _t_sf(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def _t_one_sample(x):
    n = x.shape[1]
    if n < 2:
        return None, False
    m = x.mean(axis=1)
    s = x.std(axis=1, ddof=1)
    if not np.all(s > 0):
        return None, False
    return m / (s / np.sqrt(n)), True


def criterion(d):
    """Claim: among voxels whose expected response to A exceeds that to D, the
    proportion whose expected response to A also exceeds that to B is >= 0.70.

    d['response']: float array (voxels, runs, conditions) = (1500, 10, 4);
        estimated response amplitude of each voxel in each run to each
        stimulus condition; the conditions axis holds A, B, C, D in this order.

    Returns True when the proportion is >= 0.70, False otherwise; None when
    a value is non-finite, a voxel has zero variance of A - D across the runs
    of a half, or no voxel is selected in either direction.
    """
    y = np.asarray(d['response'], dtype=float)
    if not np.all(np.isfinite(y)):
        return None
    halves = (y[:, 0::2, :], y[:, 1::2, :])
    props = []
    for k in (0, 1):
        sel = halves[k]
        est = halves[1 - k]
        diff = sel[:, :, 0] - sel[:, :, 3]
        t, ok = _t_one_sample(diff)
        if not ok:
            return None
        keep = t > _t_crit(0.001, diff.shape[1] - 1)
        if np.any(keep):
            a = est[:, :, 0].mean(axis=1)
            b = est[:, :, 1].mean(axis=1)
            props.append(np.mean(a[keep] > b[keep]))
    if len(props) == 0:
        return None
    return bool(np.mean(props) >= 0.70)
