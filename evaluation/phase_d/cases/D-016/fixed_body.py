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


def _corr_p(x, y):
    n = x.size
    if n < 3:
        return None
    xc = x - x.mean()
    yc = y - y.mean()
    sxx = float((xc ** 2).sum())
    syy = float((yc ** 2).sum())
    if sxx <= 0.0 or syy <= 0.0:
        return None
    r = float((xc * yc).sum()) / np.sqrt(sxx * syy)
    den = 1.0 - r * r
    if den <= 0.0:
        return _t_sf(np.sign(r) * np.inf, n - 2)
    return _t_sf(r * np.sqrt((n - 2) / den), n - 2)


def criterion(d):
    """Claim: across dams, the correlation between a dam's exposure level and
    the mean score of her pups is positive, judged by a one-sided test of the
    correlation against zero at the 0.05 level.

    d['exposure']: float array (dams,) = (14,); exposure level of each dam.
    d['outcome']: float array (dams, pups) = (14, 4); performance score at
        weaning of each pup of each dam.

    Returns True when the one-sided test of a positive correlation is
    significant at the 0.05 level, False otherwise; None when a value is
    non-finite, a variance is zero, or there are fewer than 3 units.
    """
    y = np.asarray(d['outcome'], dtype=float)
    x = np.asarray(d['exposure'], dtype=float)
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    p = _corr_p(x, y.mean(axis=1))
    if p is None:
        return None
    return bool(p < 0.05)
