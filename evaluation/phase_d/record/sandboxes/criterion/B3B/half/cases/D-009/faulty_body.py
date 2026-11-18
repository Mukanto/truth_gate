import numpy as np


def lgam(z):
    c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
         -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
         1.5056327351493116e-7]
    z = z - 1.0
    s = c[0]
    for i in range(1, 9):
        s = s + c[i] / (z + i)
    t = z + 7.5
    return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(s)


def betacf(a, b, x):
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    dd = 1.0 - qab * x / qap
    if abs(dd) < tiny:
        dd = tiny
    dd = 1.0 / dd
    h = dd
    for m in range(1, 1000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        h = h * dd * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        de = dd * c
        h = h * de
        if abs(de - 1.0) < 3e-16:
            break
    return h


def betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = np.exp(lgam(a + b) - lgam(a) - lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * betacf(a, b, x) / a)
    return float(1.0 - bt * betacf(b, a, 1.0 - x) / b)


def t_two_sided_p(t, df):
    return betainc(0.5 * df, 0.5, df / (df + t * t))


def f_upper_p(f, d1, d2):
    f = max(f, 0.0)
    return betainc(0.5 * d2, 0.5 * d1, d2 / (d2 + d1 * f))


def ols_coef_p(X, y, j):
    n, k = X.shape
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    rss = float(np.sum(res * res))
    if rss == 0.0:
        return None
    se = np.sqrt(rss / (n - k) * np.linalg.inv(X.T @ X)[j, j])
    return float(beta[j]), t_two_sided_p(beta[j] / se, n - k)


def criterion(d):
    """Claim: Among 60 mice, treated mice produce more peak twitch force than untreated mice of the same body mass: the difference between the group means of peak force, adjusted for body mass by analysis of covariance, is positive with a two-sided p-value below 0.05.

    d: dict of numpy arrays, with the keys
      peak_force  (animals,)  float: peak twitch force of one hindlimb muscle of each mouse, in mN
      body_mass  (animals,)  float: body mass of each mouse, in g
      treated  (animals,)  bool: True if the mouse received the treatment, False if it did not

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    f = np.asarray(d['peak_force'], dtype=float)
    m = np.asarray(d['body_mass'], dtype=float)
    g = np.asarray(d['treated'], dtype=bool)
    n = f.shape[0]
    if n < 4:
        return None
    if not (np.all(np.isfinite(f)) and np.all(np.isfinite(m))):
        return None
    if np.all(g) or not np.any(g):
        return None
    gi = g.astype(float)
    y = f / m
    X = np.column_stack([np.ones(n), gi])
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    if np.ptp(y) == 0:
        return None
    res = ols_coef_p(X, y, 1)
    if res is None:
        return None
    return bool(res[0] > 0.0 and res[1] < 0.05)
