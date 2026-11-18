"""Writes faulty_body.py and fixed_body.py of the cases other than D-061 (which was
written by hand). Only writes text; it never imports or runs a generated body."""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cases')

HEAD = "import numpy as np\n\n\n"

LGAMMA = '''def _lgamma(x):
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


'''

WELCH = '''def _welch(a, b):
    na = a.size
    nb = b.size
    va = a.var(ddof=1) / na
    vb = b.var(ddof=1) / nb
    se2 = va + vb
    if se2 <= 0.0:
        return None
    diff = a.mean() - b.mean()
    t = diff / np.sqrt(se2)
    df = se2 * se2 / (va * va / (na - 1) + vb * vb / (nb - 1))
    return float(diff), _t_sf(t, df)


'''

T1P = '''def _t1_p(x):
    n = x.size
    if n < 2:
        return None
    s = x.std(ddof=1)
    if s <= 0.0:
        return None
    t = x.mean() / (s / np.sqrt(n))
    return _t_sf(t, n - 1)


'''

SLOPEP = '''def _slope_p(x, y):
    n = x.size
    if n < 3:
        return None
    xc = x - x.mean()
    sxx = float((xc ** 2).sum())
    if sxx <= 0.0:
        return None
    yc = y - y.mean()
    b = float((xc * yc).sum()) / sxx
    res = yc - b * xc
    se2 = float((res ** 2).sum()) / (n - 2) / sxx
    if se2 <= 0.0:
        return None
    return _t_sf(b / np.sqrt(se2), n - 2)


'''

CORRP = '''def _corr_p(x, y):
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


'''

CORRCOLS = '''def _corr_cols(x, y):
    xc = x - x.mean(axis=0)
    yc = y - y.mean()
    sxx = (xc ** 2).sum(axis=0)
    syy = float((yc ** 2).sum())
    with np.errstate(divide='ignore', invalid='ignore'):
        return (yc @ xc) / np.sqrt(sxx * syy)


'''

CELL = '''def _cell(r, g, c, cv, gv):
    m = (c == cv) & (g == gv)
    return int(r[m].sum()), int(m.sum())


'''

ZC = "1.6448536269514722"


def write(case, kind, text):
    p = os.path.join(ROOT, case, kind + '_body.py')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


# ---------------------------------------------------------------- D-028 (DEC-02)
DOC_028 = '''    """Claim: in the population, the 20 voxels whose activation is most strongly
    correlated with the questionnaire score have a mean correlation with that
    score of at least 0.5.

    d['activation']: float array (subjects, voxels) = (20, 1000); task-related
        activation of each voxel in each subject.
    d['trait']: float array (subjects,) = (20,); personality questionnaire
        score of each subject.

    Returns True when the mean correlation is >= 0.5, False otherwise; None
    when a value is non-finite, a correlation has zero variance, or no voxel
    is selected.
    """
'''
F_028 = HEAD + CORRCOLS + '''def criterion(d):
''' + DOC_028 + '''    x = np.asarray(d['activation'], dtype=float)
    y = np.asarray(d['trait'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    if x.shape[0] < 2:
        return None
    r = _corr_cols(x, y)
    if not np.all(np.isfinite(r)):
        return None
    top = np.argsort(-r, kind='stable')[:20]
    if top.size < 1:
        return None
    return bool(r[top].mean() >= 0.5)
'''
X_028 = HEAD + CORRCOLS + '''def criterion(d):
''' + DOC_028 + '''    x = np.asarray(d['activation'], dtype=float)
    y = np.asarray(d['trait'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = x.shape[0]
    halves = (np.arange(0, n, 2), np.arange(1, n, 2))
    if halves[0].size < 2 or halves[1].size < 2:
        return None
    z = []
    for k in (0, 1):
        a = halves[k]
        b = halves[1 - k]
        r_sel = _corr_cols(x[a], y[a])
        if not np.all(np.isfinite(r_sel)):
            return None
        top = np.argsort(-r_sel, kind='stable')[:20]
        if top.size < 1:
            return None
        r_est = _corr_cols(x[b], y[b])[top]
        if not np.all(np.isfinite(r_est)):
            return None
        z.append(np.arctanh(r_est.mean()))
    return bool(np.tanh(np.mean(z)) >= 0.5)
'''
write('D-028', 'faulty', F_028)
write('D-028', 'fixed', X_028)

# ---------------------------------------------------------------- D-033 (DEC-R1)
DOC_033 = '''    """Claim: in the population, the 25 voxels whose trial-by-trial response is
    most strongly correlated with stimulus intensity have a mean correlation
    with intensity of at least 0.25.

    d['betas']: float array (voxels, trials) = (1000, 60); estimated response
        amplitude of each voxel on each trial.
    d['intensity']: float array (trials,) = (60,); stimulus intensity
        presented on each trial.

    Returns True when the mean correlation is >= 0.25, False otherwise; None
    when a value is non-finite, a correlation has zero variance, or no voxel
    is selected.
    """
'''
F_033 = HEAD + CORRCOLS + '''def criterion(d):
''' + DOC_033 + '''    x = np.asarray(d['betas'], dtype=float).T
    y = np.asarray(d['intensity'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    if x.shape[0] < 2:
        return None
    r = _corr_cols(x, y)
    if not np.all(np.isfinite(r)):
        return None
    top = np.argsort(-r, kind='stable')[:25]
    if top.size < 1:
        return None
    return bool(r[top].mean() >= 0.25)
'''
X_033 = HEAD + CORRCOLS + '''def criterion(d):
''' + DOC_033 + '''    x = np.asarray(d['betas'], dtype=float).T
    y = np.asarray(d['intensity'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = x.shape[0]
    halves = (np.arange(0, n, 2), np.arange(1, n, 2))
    if halves[0].size < 2 or halves[1].size < 2:
        return None
    z = []
    for k in (0, 1):
        a = halves[k]
        b = halves[1 - k]
        r_sel = _corr_cols(x[a], y[a])
        if not np.all(np.isfinite(r_sel)):
            return None
        top = np.argsort(-r_sel, kind='stable')[:25]
        if top.size < 1:
            return None
        r_est = _corr_cols(x[b], y[b])[top]
        if not np.all(np.isfinite(r_est)):
            return None
        z.append(np.arctanh(r_est.mean()))
    return bool(np.tanh(np.mean(z)) >= 0.25)
'''
write('D-033', 'faulty', F_033)
write('D-033', 'fixed', X_033)

# ---------------------------------------------------------------- D-047 (DEC-03)
DOC_047 = '''    """Claim: among patients whose screening score was at least 60, at least half
    have a week-12 score that is 10 or more points below their entry score
    (proportion of at least 0.5).

    d['screening']: float array (patients,) = (600,); symptom severity score
        (0 to 100, higher is worse) at the screening visit.
    d['entry']: float array (patients,) = (600,); symptom severity score at
        entry, on the day treatment began.
    d['week12']: float array (patients,) = (600,); symptom severity score 12
        weeks after treatment began.

    Returns True when the proportion is >= 0.5, False otherwise; None when a
    value is non-finite or no patient has a screening score of at least 60.
    """
'''
PRE_047 = '''    s = np.asarray(d['screening'], dtype=float)
    e = np.asarray(d['entry'], dtype=float)
    w = np.asarray(d['week12'], dtype=float)
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(e))
            and np.all(np.isfinite(w))):
        return None
    flag = s >= 60.0
    if not np.any(flag):
        return None
'''
F_047 = HEAD + '''def criterion(d):
''' + DOC_047 + PRE_047 + '''    change = s[flag] - w[flag]
    return bool(np.mean(change >= 10.0) >= 0.5)
'''
X_047 = HEAD + '''def criterion(d):
''' + DOC_047 + PRE_047 + '''    change = e[flag] - w[flag]
    return bool(np.mean(change >= 10.0) >= 0.5)
'''
write('D-047', 'faulty', F_047)
write('D-047', 'fixed', X_047)

# ---------------------------------------------------------------- D-069 (DEC-04)
DOC_069 = '''    """Claim: the reduction attributable to the drug (mean reduction in treated
    patients minus mean reduction in untreated patients) is larger in patients
    in the top third of baseline pressures than in patients in the bottom third
    of baseline pressures, by at least 3 mmHg. The reduction of a patient is the
    baseline pressure minus the 6-month pressure.

    d['baseline_sbp']: float array (patients,) = (900,); systolic blood
        pressure in mmHg at baseline.
    d['followup_sbp']: float array (patients,) = (900,); systolic blood
        pressure in mmHg after 6 months.
    d['treated']: bool array (patients,) = (900,); True if the patient
        received the drug.

    Returns True when the difference is >= 3 mmHg, False otherwise; None when
    a value is non-finite or a group needed for the difference is empty.
    """
'''
PRE_069 = '''    b = np.asarray(d['baseline_sbp'], dtype=float)
    f = np.asarray(d['followup_sbp'], dtype=float)
    tr = np.asarray(d['treated'], dtype=bool)
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(f))):
        return None
    red = b - f
'''
F_069 = HEAD + '''def criterion(d):
''' + DOC_069 + PRE_069 + '''    if not np.any(tr):
        return None
    q1, q2 = np.percentile(b[tr], [100.0 / 3.0, 200.0 / 3.0])
    lo = tr & (b <= q1)
    hi = tr & (b >= q2)
    if not np.any(lo) or not np.any(hi):
        return None
    return bool(red[hi].mean() - red[lo].mean() >= 3.0)
'''
X_069 = HEAD + '''def criterion(d):
''' + DOC_069 + PRE_069 + '''    if b.size < 1:
        return None
    q1, q2 = np.percentile(b, [100.0 / 3.0, 200.0 / 3.0])
    lo = b <= q1
    hi = b >= q2
    cells = (hi & tr, hi & ~tr, lo & tr, lo & ~tr)
    if not all(np.any(c) for c in cells):
        return None
    eff_hi = red[cells[0]].mean() - red[cells[1]].mean()
    eff_lo = red[cells[2]].mean() - red[cells[3]].mean()
    return bool(eff_hi - eff_lo >= 3.0)
'''
write('D-069', 'faulty', F_069)
write('D-069', 'fixed', X_069)

# ---------------------------------------------------------------- D-032 (DEC-05)
DOC_032 = '''    """Claim: the drug raises the proportion of responders more in carriers than
    in non-carriers, that is, the difference between the two drug-minus-vehicle
    differences in responder proportion (carriers minus non-carriers) is
    positive, judged by a one-sided test at the 0.05 level.

    d['responder']: bool array (participants,) = (240,); True if the
        participant met the response criterion.
    d['drug']: bool array (participants,) = (240,); True if the participant
        received the drug, False if the vehicle.
    d['carrier']: bool array (participants,) = (240,); True if the participant
        carries the gene variant.

    Returns True when the claim is supported at the 0.05 level, False
    otherwise; None when a (carrier, drug) cell is empty or the variance
    needed for the test is zero.
    """
'''
PRE_032 = '''    r = np.asarray(d['responder'], dtype=bool)
    g = np.asarray(d['drug'], dtype=bool)
    c = np.asarray(d['carrier'], dtype=bool)
    k11, n11 = _cell(r, g, c, True, True)
    k10, n10 = _cell(r, g, c, True, False)
    k01, n01 = _cell(r, g, c, False, True)
    k00, n00 = _cell(r, g, c, False, False)
    if min(n11, n10, n01, n00) < 1:
        return None
'''
Z_POOL = '''def _z_pooled(k1, n1, k0, n0):
    p = (k1 + k0) / (n1 + n0)
    se2 = p * (1.0 - p) * (1.0 / n1 + 1.0 / n0)
    if se2 <= 0.0:
        return None
    return (k1 / n1 - k0 / n0) / np.sqrt(se2)


'''
F_032 = HEAD + CELL + Z_POOL + '''def criterion(d):
''' + DOC_032 + PRE_032 + '''    z_carrier = _z_pooled(k11, n11, k10, n10)
    z_non = _z_pooled(k01, n01, k00, n00)
    if z_carrier is None or z_non is None:
        return None
    return bool(z_carrier > ''' + ZC + ''' and not z_non > ''' + ZC + ''')
'''
X_032 = HEAD + CELL + '''def criterion(d):
''' + DOC_032 + PRE_032 + '''    p11 = k11 / n11
    p10 = k10 / n10
    p01 = k01 / n01
    p00 = k00 / n00
    var = (p11 * (1.0 - p11) / n11 + p10 * (1.0 - p10) / n10
           + p01 * (1.0 - p01) / n01 + p00 * (1.0 - p00) / n00)
    if var <= 0.0:
        return None
    z = ((p11 - p10) - (p01 - p00)) / np.sqrt(var)
    return bool(z > ''' + ZC + ''')
'''
write('D-032', 'faulty', F_032)
write('D-032', 'fixed', X_032)

# ---------------------------------------------------------------- D-012 (DEC-06) and D-021 (DEC-R4)
DOC_012 = '''    """Claim: mean occupancy is higher in fenced plots than in open plots by at
    least 0.10, where the occupancy of a plot is the fraction of its quadrats
    that are occupied, and a one-sided test of the difference between the mean
    occupancy of fenced plots and that of open plots is significant at the
    0.05 level.

    d['occupied']: bool array (plots, quadrats) = (10, 30); True if the species
        was present in that quadrat of that plot.
    d['exclosure']: bool array (plots,) = (10,); True if the plot was fenced
        against grazers.

    Returns True when the difference is >= 0.10 and the test is significant at
    the 0.05 level, False otherwise; None when a group has too few units for
    the test or the variance needed for the test is zero.
    """
'''
F_012 = HEAD + '''def criterion(d):
''' + DOC_012 + '''    y = np.asarray(d['occupied'], dtype=float)
    g = np.asarray(d['exclosure'], dtype=bool)
    a = y[g]
    b = y[~g]
    n1 = a.size
    n0 = b.size
    if n1 < 1 or n0 < 1:
        return None
    k1 = a.sum()
    k0 = b.sum()
    p = (k1 + k0) / (n1 + n0)
    se2 = p * (1.0 - p) * (1.0 / n1 + 1.0 / n0)
    if se2 <= 0.0:
        return None
    diff = k1 / n1 - k0 / n0
    return bool(diff >= 0.10 and diff / np.sqrt(se2) > ''' + ZC + ''')
'''
X_012 = HEAD + LGAMMA + WELCH + '''def criterion(d):
''' + DOC_012 + '''    y = np.asarray(d['occupied'], dtype=float)
    g = np.asarray(d['exclosure'], dtype=bool)
    occ = y.mean(axis=1)
    a = occ[g]
    b = occ[~g]
    if a.size < 2 or b.size < 2:
        return None
    res = _welch(a, b)
    if res is None:
        return None
    return bool(res[0] >= 0.10 and res[1] < 0.05)
'''
write('D-012', 'faulty', F_012)
write('D-012', 'fixed', X_012)

DOC_021 = '''    """Claim: mean occupancy is higher in fenced plots than in open plots by at
    least 0.15, where the occupancy of a plot is the fraction of dates on which
    it is occupied, and a one-sided test of the difference between the mean
    occupancy of fenced plots and that of open plots is significant at the
    0.05 level.

    d['present']: bool array (plots, dates) = (8, 12); True if the species was
        present in that plot on that date; dates are in time order.
    d['fenced']: bool array (plots,) = (8,); True if the plot was fenced
        against grazers.

    Returns True when the difference is >= 0.15 and the test is significant at
    the 0.05 level, False otherwise; None when a group has too few units for
    the test or the variance needed for the test is zero.
    """
'''
F_021 = HEAD + '''def criterion(d):
''' + DOC_021 + '''    y = np.asarray(d['present'], dtype=float)
    g = np.asarray(d['fenced'], dtype=bool)
    a = y[g]
    b = y[~g]
    n1 = a.size
    n0 = b.size
    if n1 < 1 or n0 < 1:
        return None
    k1 = a.sum()
    k0 = b.sum()
    p = (k1 + k0) / (n1 + n0)
    se2 = p * (1.0 - p) * (1.0 / n1 + 1.0 / n0)
    if se2 <= 0.0:
        return None
    diff = k1 / n1 - k0 / n0
    return bool(diff >= 0.15 and diff / np.sqrt(se2) > ''' + ZC + ''')
'''
X_021 = HEAD + LGAMMA + WELCH + '''def criterion(d):
''' + DOC_021 + '''    y = np.asarray(d['present'], dtype=float)
    g = np.asarray(d['fenced'], dtype=bool)
    occ = y.mean(axis=1)
    a = occ[g]
    b = occ[~g]
    if a.size < 2 or b.size < 2:
        return None
    res = _welch(a, b)
    if res is None:
        return None
    return bool(res[0] >= 0.15 and res[1] < 0.05)
'''
write('D-021', 'faulty', F_021)
write('D-021', 'fixed', X_021)

# ---------------------------------------------------------------- D-046 (DEC-07)
DOC_046 = '''    """Claim: response increases with dose, that is, the slope of an animal's
    mean cell response on dose, across animals, is positive, judged by a
    one-sided test at the 0.05 level.

    d['response']: float array (animals, cells) = (10, 100); response
        amplitude in mV of each recorded CA3 cell.
    d['dose']: float array (animals,) = (10,); dose of the drug given to each
        animal.

    Returns True when the one-sided test of a positive slope is significant at
    the 0.05 level, False otherwise; None when a value is non-finite, dose has
    zero variance, there are too few units, or the residual variance is zero.
    """
'''
PRE_046 = '''    y = np.asarray(d['response'], dtype=float)
    x = np.asarray(d['dose'], dtype=float)
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
'''
F_046 = HEAD + LGAMMA + SLOPEP + '''def criterion(d):
''' + DOC_046 + PRE_046 + '''    p = _slope_p(np.repeat(x, y.shape[1]), y.ravel())
    if p is None:
        return None
    return bool(p < 0.05)
'''
X_046 = HEAD + LGAMMA + SLOPEP + '''def criterion(d):
''' + DOC_046 + PRE_046 + '''    p = _slope_p(x, y.mean(axis=1))
    if p is None:
        return None
    return bool(p < 0.05)
'''
write('D-046', 'faulty', F_046)
write('D-046', 'fixed', X_046)

# ---------------------------------------------------------------- D-016 (DEC-08)
DOC_016 = '''    """Claim: across dams, the correlation between a dam's exposure level and
    the mean score of her pups is positive, judged by a one-sided test of the
    correlation against zero at the 0.05 level.

    d['exposure']: float array (dams,) = (14,); exposure level of each dam.
    d['outcome']: float array (dams, pups) = (14, 4); performance score at
        weaning of each pup of each dam.

    Returns True when the one-sided test of a positive correlation is
    significant at the 0.05 level, False otherwise; None when a value is
    non-finite, a variance is zero, or there are fewer than 3 units.
    """
'''
PRE_016 = '''    y = np.asarray(d['outcome'], dtype=float)
    x = np.asarray(d['exposure'], dtype=float)
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
'''
F_016 = HEAD + LGAMMA + CORRP + '''def criterion(d):
''' + DOC_016 + PRE_016 + '''    p = _corr_p(np.repeat(x, y.shape[1]), y.ravel())
    if p is None:
        return None
    return bool(p < 0.05)
'''
X_016 = HEAD + LGAMMA + CORRP + '''def criterion(d):
''' + DOC_016 + PRE_016 + '''    p = _corr_p(x, y.mean(axis=1))
    if p is None:
        return None
    return bool(p < 0.05)
'''
write('D-016', 'faulty', F_016)
write('D-016', 'fixed', X_016)

# ---------------------------------------------------------------- D-052 (DEC-R3)
DOC_052 = '''    """Claim: the mean improvement (after minus before) is larger in young than
    in old participants, judged by a one-sided test of the difference between
    the two groups' mean improvements at the 0.05 level.

    d['pre']: float array (participants,) = (40,); performance score before
        the programme.
    d['post']: float array (participants,) = (40,); performance score after
        the programme.
    d['young']: bool array (participants,) = (40,); True for young
        participants, False for old participants.

    Returns True when the claim is supported at the 0.05 level, False
    otherwise; None when a value is non-finite, a group has fewer than 2
    participants, or the variance needed for the test is zero.
    """
'''
PRE_052 = '''    pre = np.asarray(d['pre'], dtype=float)
    post = np.asarray(d['post'], dtype=float)
    g = np.asarray(d['young'], dtype=bool)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    imp = post - pre
    a = imp[g]
    b = imp[~g]
    if a.size < 2 or b.size < 2:
        return None
'''
F_052 = HEAD + LGAMMA + T1P + '''def criterion(d):
''' + DOC_052 + PRE_052 + '''    pa = _t1_p(a)
    pb = _t1_p(b)
    if pa is None or pb is None:
        return None
    return bool(pa < 0.05 and not pb < 0.05)
'''
X_052 = HEAD + LGAMMA + WELCH + '''def criterion(d):
''' + DOC_052 + PRE_052 + '''    res = _welch(a, b)
    if res is None:
        return None
    return bool(res[1] < 0.05)
'''
write('D-052', 'faulty', F_052)
write('D-052', 'fixed', X_052)

print('written')
