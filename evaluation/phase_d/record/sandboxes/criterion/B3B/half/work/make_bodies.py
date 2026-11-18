"""Generator of the faulty/fixed body files of half B3B.

Each case is one template with a marker line `@@ERR@@`; the faulty file gets the case's ERR text there and the fixed
file gets the FIX text, so the two files differ only in the error and its correction.
This script only writes text. It runs nothing from the generated bodies.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HALF = os.path.dirname(HERE)
BRIEFS = {b['local_id']: b for b in json.load(open(os.path.join(HALF, 'BRIEFS.json'), encoding='utf-8'))}
IDS = json.load(open(os.path.join(HALF, 'CASE_IDS.json'), encoding='utf-8'))

# ---------------------------------------------------------------- shared helper texts
CORR = '''def corr(x, y):
    xc = x - np.mean(x)
    yc = y - np.mean(y)
    return float(np.sum(xc * yc) / np.sqrt(np.sum(xc * xc) * np.sum(yc * yc)))
'''

PVAL = '''def lgam(z):
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
'''

OLS_T = '''def ols_coef_p(X, y, j):
    n, k = X.shape
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    rss = float(np.sum(res * res))
    if rss == 0.0:
        return None
    se = np.sqrt(rss / (n - k) * np.linalg.inv(X.T @ X)[j, j])
    return float(beta[j]), t_two_sided_p(beta[j] / se, n - k)
'''

NESTED_F = '''def rss_of(X, y):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ beta
    return float(np.sum(res * res))


def nested_f_p(y, X0, X1):
    n = y.shape[0]
    d1 = X1.shape[1] - X0.shape[1]
    d2 = n - X1.shape[1]
    r0 = rss_of(X0, y)
    r1 = rss_of(X1, y)
    if r1 == 0.0:
        return None
    return f_upper_p(((r0 - r1) / d1) / (r1 / d2), d1, d2)
'''


def doc(lid, extra=''):
    b = BRIEFS[lid]
    lines = ['    """Claim: ' + b['claim'], '']
    lines.append('    d: dict of numpy arrays, with the keys')
    for k in b['data_keys']:
        lines.append('      %s  %s  %s: %s' % (k['key'], k['shape'], k['dtype'], k['meaning']))
    if extra:
        lines.append('')
        lines.append(extra)
    lines.append('')
    lines.append('    Returns True when the claim is supported, False when it is not, None when the statistic is not')
    lines.append('    defined (non-finite values, too small a sample, zero variance).')
    lines.append('    """')
    return '\n'.join(lines)


def arr(var, key, dims=None):
    return "    %s = np.asarray(d['%s'], dtype=float)\n" % (var, key)


def finite_check(vars_):
    cond = ' and '.join('np.all(np.isfinite(%s))' % v for v in vars_)
    return '    if not (%s):\n        return None\n' % cond


CASES = {}

# ---------------------------------------------------------------- B3B-01  D-023
CASES['B3B-01'] = dict(
    helpers=CORR,
    body='''    hw = np.asarray(d['head_width'], dtype=float)
    wl = np.asarray(d['wing_length'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    n = hw.shape[0]
    if n < 3:
        return None
''' + finite_check(['hw', 'wl', 'bl']) + '''@@ERR@@    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        return None
    if np.ptp(u) == 0 or np.ptp(v) == 0:
        return None
    return bool(corr(u, v) >= 0.30)
''',
    ERR='''    u = hw / bl
    v = wl / bl
''',
    FIX='''    if np.ptp(bl) == 0:
        return None
    X = np.column_stack([np.ones(n), bl])
    u = hw - X @ np.linalg.lstsq(X, hw, rcond=None)[0]
    v = wl - X @ np.linalg.lstsq(X, wl, rcond=None)[0]
''')

# ---------------------------------------------------------------- B3B-02  D-068
CASES['B3B-02'] = dict(
    helpers='''def first_coef(X, y):
    return float(np.linalg.lstsq(X, y, rcond=None)[0][1])
''',
    body='''    hw = np.asarray(d['head_width'], dtype=float)
    wl = np.asarray(d['wing_length'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    npop = hw.shape[0]
    n = hw.shape[1]
    if npop < 1 or n < 3:
        return None
''' + finite_check(['hw', 'wl', 'bl']) + '''    slopes = []
    for p in range(npop):
@@ERR@@        if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
            return None
        for j in range(1, X.shape[1]):
            if np.ptp(X[:, j]) == 0:
                return None
        slopes.append(first_coef(X, y))
    return bool(np.mean(slopes) >= 0.30)
''',
    ERR='''        u = hw[p] / bl[p]
        y = wl[p] / bl[p]
        X = np.column_stack([np.ones(n), u])
''',
    FIX='''        y = wl[p]
        X = np.column_stack([np.ones(n), hw[p], bl[p]])
''')

# ---------------------------------------------------------------- B3B-03  D-009
CASES['B3B-03'] = dict(
    helpers=PVAL + '\n\n' + OLS_T,
    body='''    f = np.asarray(d['peak_force'], dtype=float)
    m = np.asarray(d['body_mass'], dtype=float)
    g = np.asarray(d['treated'], dtype=bool)
    n = f.shape[0]
    if n < 4:
        return None
''' + finite_check(['f', 'm']) + '''    if np.all(g) or not np.any(g):
        return None
    gi = g.astype(float)
@@ERR@@    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    if np.ptp(y) == 0:
        return None
    res = ols_coef_p(X, y, 1)
    if res is None:
        return None
    return bool(res[0] > 0.0 and res[1] < 0.05)
''',
    ERR='''    y = f / m
    X = np.column_stack([np.ones(n), gi])
''',
    FIX='''    if np.ptp(m) == 0:
        return None
    y = f
    X = np.column_stack([np.ones(n), gi, m])
''')

# ---------------------------------------------------------------- B3B-04  D-056
CASES['B3B-04'] = dict(
    helpers=PVAL + '\n\n' + NESTED_F,
    body='''    o2 = np.asarray(d['oxygen_uptake'], dtype=float)
    m = np.asarray(d['body_mass'], dtype=float)
    ng = o2.shape[0]
    na = o2.shape[1]
    n = ng * na
    if ng < 2 or na < 1 or n < 5:
        return None
''' + finite_check(['o2', 'm']) + '''    dum = np.zeros((n, ng - 1))
    for i in range(1, ng):
        dum[i * na:(i + 1) * na, i - 1] = 1.0
    one = np.ones((n, 1))
@@ERR@@    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X0))):
        return None
    if np.ptp(y) == 0:
        return None
    p = nested_f_p(y, X0, X1)
    if p is None:
        return None
    return bool(p < 0.05)
''',
    ERR='''    y = (o2 / m).reshape(n)
    X0 = one
    X1 = np.hstack([one, dum])
''',
    FIX='''    if np.ptp(m) == 0:
        return None
    y = o2.reshape(n)
    X0 = np.hstack([one, m.reshape(n, 1)])
    X1 = np.hstack([one, m.reshape(n, 1), dum])
''')

# ---------------------------------------------------------------- B3B-05  D-045
CASES['B3B-05'] = dict(
    helpers=CORR,
    body='''    b = np.asarray(d['baseline_score'], dtype=float)
    rt = np.asarray(d['baseline_score_retest'], dtype=float)
    f = np.asarray(d['followup_score'], dtype=float)
    n = b.shape[0]
    if n < 2:
        return None
''' + finite_check(['b', 'rt', 'f']) + '''    chg = f - b
@@ERR@@    if np.ptp(chg) == 0 or np.ptp(x) == 0:
        return None
    return bool(corr(chg, x) <= -0.30)
''',
    ERR='''    x = b
''',
    FIX='''    x = 0.5 * (b + f)
''')

# ---------------------------------------------------------------- B3B-06  D-019
CASES['B3B-06'] = dict(
    helpers='',
    body='''    x = np.asarray(d['systolic_bp'], dtype=float)
    n = x.shape[0]
    m = x.shape[1]
    if n < 2:
        return None
''' + finite_check(['x']) + '''    t = np.arange(m, dtype=float)
    tbar = float(np.mean(t))
    tc = t - tbar
    sxx = float(np.sum(tc * tc))
    b = (x - np.mean(x, axis=1, keepdims=True)) @ tc / sxx
@@ERR@@    if np.ptp(u) == 0:
        return None
    c = np.cov(u, b)
    v = c[0, 0]
    cc = c[0, 1]
@@ADJ@@    if not v > 0.0:
        return None
    slope = cc / v
    if not np.isfinite(slope):
        return None
    return bool(slope <= -0.03)
''',
    ERR='''    u = x[:, 0]
''',
    FIX='''    a = np.mean(x, axis=1) - b * tbar
    u = a
''',
    ADJ_FAULTY='',
    ADJ_FIXED='''    res = x - a[:, None] - b[:, None] * t[None, :]
    s2 = float(np.sum(res * res)) / (n * (m - 2))
    v = v - s2 * (1.0 / m + tbar * tbar / sxx)
    cc = cc + s2 * tbar / sxx
''')

# ---------------------------------------------------------------- B3B-07  D-057
CASES['B3B-07'] = dict(
    helpers=CORR,
    body='''    b = np.asarray(d['baseline_depth'], dtype=float)
    rt = np.asarray(d['baseline_depth_retest'], dtype=float)
    f = np.asarray(d['followup_depth'], dtype=float)
    n = b.shape[0]
    if n < 2:
        return None
''' + finite_check(['b', 'rt', 'f']) + '''    chg = f - b
@@ERR@@    if np.ptp(chg) == 0 or np.ptp(x) == 0:
        return None
    r = corr(chg, x)
    return bool(r * r >= 0.15)
''',
    ERR='''    x = b
''',
    FIX='''    x = 0.5 * (b + f)
''')

# ---------------------------------------------------------------- B3B-08  D-048
CASES['B3B-08'] = dict(
    helpers='',
    body='''    co = np.asarray(d['cardiac_output'], dtype=float)
    co2 = np.asarray(d['cardiac_output_2'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    n = co.shape[0]
    if n < 2:
        return None
''' + finite_check(['co', 'co2', 'ca', 'cv']) + '''    k = 10.0
    dd = ca - cv
    vo2 = k * co * dd
    do2 = k * co * ca
    c = np.cov(vo2, do2)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
@@ERR@@    if not (v > 0.0 and w > 0.0):
        return None
    r = cc / np.sqrt(v * w)
    return bool(r >= 0.40)
''',
    ERR='',
    FIX='''    s2 = float(np.var(co - co2, ddof=1)) / 2.0
    v = v - k * k * s2 * np.mean(dd * dd)
    w = w - k * k * s2 * np.mean(ca * ca)
    cc = cc - k * k * s2 * np.mean(dd * ca)
''')

# ---------------------------------------------------------------- B3B-09  D-051
CASES['B3B-09'] = dict(
    helpers='',
    body='''    co = np.asarray(d['cardiac_output'], dtype=float)
    co2 = np.asarray(d['cardiac_output_2'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    na = co.shape[0]
    ns = co.shape[1]
    if na < 1 or ns < 2:
        return None
''' + finite_check(['co', 'co2', 'ca', 'cv']) + '''    k = 10.0
    dd = ca - cv
    vo2 = k * co * dd
    do2 = k * co * ca
    vc = vo2 - np.mean(vo2, axis=1, keepdims=True)
    dc = do2 - np.mean(do2, axis=1, keepdims=True)
    num = np.sum(vc * dc, axis=1) / (ns - 1)
    den = np.sum(dc * dc, axis=1) / (ns - 1)
@@ERR@@    if not np.all(den > 0.0):
        return None
    return bool(np.mean(num / den) >= 0.15)
''',
    ERR='',
    FIX='''    s2 = np.var(co - co2, axis=1, ddof=1) / 2.0
    num = num - k * k * s2 * np.mean(dd * ca, axis=1)
    den = den - k * k * s2 * np.mean(ca * ca, axis=1)
''')

# ---------------------------------------------------------------- B3B-10  D-002
CASES['B3B-10'] = dict(
    helpers='',
    body='''    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    ca2 = np.asarray(d['arterial_o2_content_2'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    cv2 = np.asarray(d['venous_o2_content_2'], dtype=float)
    n = ca.shape[0]
    if n < 2:
        return None
''' + finite_check(['ca', 'ca2', 'cv', 'cv2']) + '''    dif = ca - cv
    c = np.cov(dif, ca)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
@@ERR@@    if not (v > 0.0 and w > 0.0):
        return None
    r = cc / np.sqrt(v * w)
    return bool(r >= 0.30)
''',
    ERR='',
    FIX='''    sa = float(np.var(ca - ca2, ddof=1)) / 2.0
    sv = float(np.var(cv - cv2, ddof=1)) / 2.0
    v = v - sa - sv
    w = w - sa
    cc = cc - sa
''')

# ---------------------------------------------------------------- B3B-11  D-026
CASES['B3B-11'] = dict(
    helpers='''def first_share(M):
    ev = np.linalg.eigvalsh(np.cov(M, rowvar=False))
    tot = float(np.sum(ev))
    if not tot > 0.0:
        return None
    return float(ev[-1]) / tot
''',
    body='''    s = np.asarray(d['skeletal'], dtype=float)
    bl = np.asarray(d['body_length'], dtype=float)
    n = s.shape[0]
    if n < 3:
        return None
''' + finite_check(['s', 'bl']) + '''@@ERR@@    if not np.all(np.isfinite(M)):
        return None
    share = first_share(M)
    if share is None:
        return None
    return bool(share >= 0.40)
''',
    ERR='''    M = s / bl[:, None]
''',
    FIX='''    if np.ptp(bl) == 0:
        return None
    X = np.column_stack([np.ones(n), bl])
    M = s - X @ np.linalg.lstsq(X, s, rcond=None)[0]
''')

# ---------------------------------------------------------------- B3B-12  D-072
CASES['B3B-12'] = dict(
    helpers=PVAL + '\n\n' + OLS_T,
    body='''    fv = np.asarray(d['force_vehicle'], dtype=float)
    fd = np.asarray(d['force_drug'], dtype=float)
    av = np.asarray(d['area_vehicle'], dtype=float)
    ad = np.asarray(d['area_drug'], dtype=float)
    n = fv.shape[0]
    if n < 3:
        return None
''' + finite_check(['fv', 'fd', 'av', 'ad']) + '''@@ERR@@    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    if np.ptp(y) == 0:
        return None
    res = ols_coef_p(X, y, 0)
    if res is None:
        return None
    return bool(res[0] > 0.0 and res[1] < 0.05)
''',
    ERR='''    y = fd / ad - fv / av
    X = np.ones((n, 1))
''',
    FIX='''    if np.ptp(ad - av) == 0:
        return None
    y = fd - fv
    X = np.column_stack([np.ones(n), ad - av])
''')

# ---------------------------------------------------------------- B3B-13  D-001
CASES['B3B-13'] = dict(
    helpers='',
    body='''    x = np.asarray(d['systolic_bp'], dtype=float)
    n = x.shape[0]
    m = x.shape[1]
    if n < 2:
        return None
''' + finite_check(['x']) + '''    t = np.arange(m, dtype=float)
    tbar = float(np.mean(t))
    tc = t - tbar
    sxx = float(np.sum(tc * tc))
    b = (x - np.mean(x, axis=1, keepdims=True)) @ tc / sxx
@@ERR@@    if np.ptp(u) == 0:
        return None
    c = np.cov(u, b)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
@@ADJ@@    if not (v > 0.0 and w > 0.0):
        return None
    r = cc / np.sqrt(v * w)
    return bool(r <= -0.30)
''',
    ERR='''    u = x[:, 0]
''',
    FIX='''    a = np.mean(x, axis=1) - b * tbar
    u = a
''',
    ADJ_FAULTY='',
    ADJ_FIXED='''    res = x - a[:, None] - b[:, None] * t[None, :]
    s2 = float(np.sum(res * res)) / (n * (m - 2))
    v = v - s2 * (1.0 / m + tbar * tbar / sxx)
    w = w - s2 / sxx
    cc = cc + s2 * tbar / sxx
''')

# ---------------------------------------------------------------- B3B-14  D-063
CASES['B3B-14'] = dict(
    helpers='',
    body='''    co = np.asarray(d['cardiac_output'], dtype=float)
    co2 = np.asarray(d['cardiac_output_2'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    n = co.shape[0]
    if n < 2:
        return None
''' + finite_check(['co', 'co2', 'ca', 'cv']) + '''    k = 10.0
    dd = ca - cv
    vo2 = k * co * dd
    c = np.cov(vo2, co)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
@@ERR@@    if not (v > 0.0 and w > 0.0):
        return None
    return bool(cc * cc / (v * w) >= 0.25)
''',
    ERR='',
    FIX='''    s2 = float(np.var(co - co2, ddof=1)) / 2.0
    v = v - k * k * s2 * np.mean(dd * dd)
    w = w - s2
    cc = cc - k * s2 * np.mean(dd)
''')

# ---------------------------------------------------------------- B3B-15  D-025
CASES['B3B-15'] = dict(
    helpers='',
    body='''    b = np.asarray(d['baseline_attachment_loss'], dtype=float)
    rt = np.asarray(d['baseline_attachment_loss_retest'], dtype=float)
    f = np.asarray(d['followup_attachment_loss'], dtype=float)
    nt = b.shape[0]
    nd = b.shape[1]
    if nt < 1 or nd < 2:
        return None
''' + finite_check(['b', 'rt', 'f']) + '''    chg = f - b
@@ERR@@    if np.any(np.ptp(x, axis=1) == 0):
        return None
    xc = x - np.mean(x, axis=1, keepdims=True)
    yc = chg - np.mean(chg, axis=1, keepdims=True)
    slope = np.sum(xc * yc, axis=1) / np.sum(xc * xc, axis=1)
    return bool(np.mean(slope) <= -0.20)
''',
    ERR='''    x = b
''',
    FIX='''    x = 0.5 * (b + f)
''')


def build(lid, which):
    c = CASES[lid]
    body = c['body']
    block = c['ERR'] if which == 'faulty' else c['FIX']
    body = body.replace('@@ERR@@', block)
    adj = ''
    if 'ADJ_FIXED' in c:
        adj = c['ADJ_FAULTY'] if which == 'faulty' else c['ADJ_FIXED']
    body = body.replace('@@ADJ@@', adj)
    parts = ['import numpy as np', '', '']
    if c['helpers']:
        parts.append(c['helpers'].rstrip('\n'))
        parts.append('')
        parts.append('')
    parts.append('def criterion(d):')
    parts.append(doc(lid))
    parts.append(body.rstrip('\n'))
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    for lid in sorted(CASES):
        cid = IDS[lid]
        folder = os.path.join(HALF, 'cases', cid)
        for which in ('faulty', 'fixed'):
            with open(os.path.join(folder, which + '_body.py'), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(build(lid, which))
        print(lid, cid, 'written')
