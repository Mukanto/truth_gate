"""Generator of the faulty/fixed body files of half B3A.

It only writes text (the two files of every case). It never imports or runs the bodies.
Run: py -I gen.py   (cwd anywhere; paths are absolute)
"""
import os

ROOT = r"E:\Claude Projects\Kapi\phase_d_work\criterion\B3A\half\cases"

HEADER = "import numpy as np\n\n"

H_FLAT = '''def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))
'''

H_CORR = '''def _corr(a, b):
    """Pearson correlation of two 1-D arrays; None when either has zero variance."""
    if _flat(a) or _flat(b):
        return None
    a = a - np.mean(a)
    b = b - np.mean(b)
    sa = np.sqrt(np.sum(a * a))
    sb = np.sqrt(np.sum(b * b))
    if sa == 0.0 or sb == 0.0:
        return None
    return float(np.sum(a * b) / (sa * sb))
'''

H_RESID = '''def _resid(y, X):
    """Residuals of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return y - A @ coef
'''

H_PARTIAL = '''def _partial_corr(a, b, z):
    """Partial correlation of a and b given z (all (n,)): correlation of the residuals of a and of b on z.

    None when a residual has no variance left (the partial correlation is then undefined).
    """
    Z = z.reshape(-1, 1)
    ra = _resid(a, Z)
    rb = _resid(b, Z)
    if np.sum(ra * ra) <= 1e-24 * np.sum((a - np.mean(a)) ** 2):
        return None
    if np.sum(rb * rb) <= 1e-24 * np.sum((b - np.mean(b)) ** 2):
        return None
    return _corr(ra, rb)
'''

H_R2 = '''def _r2(y, X):
    """R-squared of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    res = _resid(y, X)
    sst = np.sum((y - np.mean(y)) ** 2)
    return float(1.0 - np.sum(res * res) / sst)
'''

H_STD = '''def _std_coef(y, X, j):
    """Standardised coefficient of column j of X (n, k) in the regression of y (n,) on an intercept and X."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(coef[1 + j] * np.std(X[:, j], ddof=1) / np.std(y, ddof=1))
'''

H_SLOPE_CHANGE = '''def _change_stats(u1, u2, k):
    """Regression of the change u2 - u1 on the baseline u1, adjusted for the error-variance share k.

    Returns (b, r): the slope (b_crude + k) / (1 - k) and the correlation implied by it, with the SDs of the
    baseline and of the change reduced to their true parts (baseline variance times (1 - k); change variance
    minus 2 * k * baseline variance, equal error variance at both visits). With k = 0 these are the crude
    slope and the crude correlation. None when the baseline or the change has zero variance; b or r may be
    non-finite (k = 1, or a true-part variance that is not positive) and the caller checks the one it uses.
    """
    ch = u2 - u1
    v1 = np.var(u1, ddof=1)
    vc = np.var(ch, ddof=1)
    if _flat(u1) or _flat(ch):
        return None
    b_crude = np.sum((u1 - np.mean(u1)) * (ch - np.mean(ch))) / ((len(u1) - 1) * v1)
    with np.errstate(divide='ignore', invalid='ignore'):
        b = (b_crude + k) / (1.0 - k)
        sd_x = np.sqrt(v1 * (1.0 - k))
        var_c = vc - 2.0 * k * v1
        sd_c = np.sqrt(var_c) if var_c > 0.0 else np.nan
        r = b * sd_x / sd_c
    return float(b), float(r)
'''


def doc(lines):
    return '    """' + lines[0] + "\n" + "".join(("    " + l).rstrip() + "\n" for l in lines[1:]) + '    """\n'


CASES = {}


def case(cid, helpers, body):
    CASES[cid] = (helpers, body)


# ---------------------------------------------------------------- D-040 (B3A-01) PEA97, correlation
def b01(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across skulls, cranial breadth and cranial height are positively associated after accounting",
        "for cranial length; the partial correlation of breadth and height given length is at least 0.2.",
        "",
        "d['breadth'] : (skulls,) float, maximum cranial breadth of each skull, in mm",
        "d['height']  : (skulls,) float, cranial height of each skull, in mm",
        "d['length']  : (skulls,) float, maximum cranial length of each skull, in mm",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 skulls, or a variance is zero.",
    ])
    s += """    x = np.asarray(d['breadth'], dtype=float)
    y = np.asarray(d['height'], dtype=float)
    z = np.asarray(d['length'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y)) and np.all(np.isfinite(z))):
        return None
    if x.size < 3:
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        a = x / z
        b = y / z
"""
    else:
        s += """    a = x
    b = y
"""
    s += """    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    if _flat(a) or _flat(b) or _flat(z):
        return None
"""
    s += "    r = _corr(a, b)\n" if v == "faulty" else "    r = _partial_corr(a, b, z)\n"
    s += """    if r is None or not np.isfinite(r):
        return None
    return bool(r >= 0.2)
"""
    return s


case("D-040", None, b01)


# ---------------------------------------------------------------- D-017 (B3A-02) KRO93, mean
def b02(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: at a given height, the mean forced vital capacity of smokers and of non-smokers differs by at",
        "least 0.2 L; the difference between the two group means, after accounting for height, is at least",
        "0.2 L in absolute value.",
        "",
        "d['fvc']    : (subjects,) float, forced vital capacity of each subject, in litres",
        "d['height'] : (subjects,) float, standing height of each subject, in cm",
        "d['smoker'] : (subjects,) bool, True if the subject is a current smoker",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 subjects, a group is empty, or",
        "height has zero variance.",
    ])
    s += """    fvc = np.asarray(d['fvc'], dtype=float)
    height = np.asarray(d['height'], dtype=float)
    smoker = np.asarray(d['smoker'], dtype=bool)
    if not (np.all(np.isfinite(fvc)) and np.all(np.isfinite(height))):
        return None
    n = fvc.size
    ns = int(np.sum(smoker))
    if n < 3 or ns < 1 or ns == n:
        return None
    if _flat(height):
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = fvc / height
    if not np.all(np.isfinite(ratio)):
        return None
    stat = abs((np.mean(ratio[smoker]) - np.mean(ratio[~smoker])) * np.mean(height))
"""
    else:
        s += """    A = np.column_stack([np.ones(n), smoker.astype(float), height])
    coef = np.linalg.lstsq(A, fvc, rcond=None)[0]
    stat = abs(float(coef[1]))
"""
    s += """    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.2)
"""
    return s


case("D-017", [H_FLAT], b02)


# ---------------------------------------------------------------- D-053 (B3A-03) CHI13, correlation
def b03(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across children, BMI at baseline and the subsequent change in BMI are negatively correlated;",
        "the correlation between the BMI level at baseline and the change in BMI by follow-up is at most -0.25.",
        "",
        "d['bmi_baseline']        : (children,) float, BMI of each child at the baseline visit, in kg/m2",
        "d['bmi_baseline_retest'] : (children,) float, a second BMI measurement of each child at the baseline",
        "                           visit, in kg/m2",
        "d['bmi_followup']        : (children,) float, BMI of each child at the follow-up visit five years",
        "                           after baseline, in kg/m2",
        "",
        "Returns True / False; None when a value is not finite, fewer than 2 children, or a variance is zero.",
    ])
    s += """    u1 = np.asarray(d['bmi_baseline'], dtype=float)
    u1b = np.asarray(d['bmi_baseline_retest'], dtype=float)
    u2 = np.asarray(d['bmi_followup'], dtype=float)
    if not (np.all(np.isfinite(u1)) and np.all(np.isfinite(u1b)) and np.all(np.isfinite(u2))):
        return None
    if u1.size < 2:
        return None
    change = u2 - u1
"""
    s += "    x = u1\n" if v == "faulty" else "    x = u1b\n"
    s += """    r = _corr(x, change)
    if r is None or not np.isfinite(r):
        return None
    return bool(r <= -0.25)
"""
    return s


case("D-053", [H_FLAT, H_CORR], b03)


# ---------------------------------------------------------------- D-071 (B3A-04) ARC81, correlation
def b04(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across patients, oxygen delivery and oxygen consumption are positively correlated; the Pearson",
        "correlation coefficient between them is at least 0.4.",
        "",
        "d['cardiac_output']       : (patients,) float, cardiac output of each patient, in L/min",
        "d['arterial_o2_content']  : (patients,) float, oxygen content of arterial blood of each patient,",
        "                            in mL O2 per dL",
        "d['venous_o2_content']    : (patients,) float, oxygen content of mixed venous blood of each patient,",
        "                            in mL O2 per dL",
        "d['vo2_expired_gas']      : (patients,) float, oxygen consumption of each patient measured from",
        "                            expired-gas analysis, in mL/min",
        "",
        "Oxygen delivery is cardiac_output * arterial_o2_content * 10 (mL/min).",
        "Returns True / False; None when a value is not finite, fewer than 2 patients, or a variance is zero.",
    ])
    s += """    co = np.asarray(d['cardiac_output'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    vo = np.asarray(d['vo2_expired_gas'], dtype=float)
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))
            and np.all(np.isfinite(vo))):
        return None
    if co.size < 2:
        return None
    do2 = co * ca * 10.0
"""
    s += "    vo2 = co * (ca - cv) * 10.0\n" if v == "faulty" else "    vo2 = vo\n"
    s += """    r = _corr(do2, vo2)
    if r is None or not np.isfinite(r):
        return None
    return bool(r >= 0.4)
"""
    return s


case("D-071", [H_FLAT, H_CORR], b04)


# ---------------------------------------------------------------- D-062 (B3A-05) PEA97, proportion
def b05(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: in at least 60% of the species, femur length and humerus length are positively associated after",
        "accounting for body length; within the species, the partial correlation between femur length and",
        "humerus length, given body length, is at least 0.2.",
        "",
        "d['femur']       : (species, individuals) float, femur length of each individual sampled in each",
        "                   species, in mm",
        "d['humerus']     : (species, individuals) float, humerus length of each individual sampled in each",
        "                   species, in mm",
        "d['body_length'] : (species, individuals) float, head-and-body length of each individual sampled in",
        "                   each species, in mm",
        "",
        "Species with a non-finite value, fewer than 3 individuals or a zero variance are not counted.",
        "Returns True / False; None when no species can be counted.",
    ])
    s += """    x = np.asarray(d['femur'], dtype=float)
    y = np.asarray(d['humerus'], dtype=float)
    z = np.asarray(d['body_length'], dtype=float)
    n_species, n_ind = x.shape
    if n_species < 1 or n_ind < 3:
        return None
    hits = 0
    counted = 0
    for s in range(n_species):
        xs = x[s]
        ys = y[s]
        zs = z[s]
        if not (np.all(np.isfinite(xs)) and np.all(np.isfinite(ys)) and np.all(np.isfinite(zs))):
            continue
"""
    if v == "faulty":
        s += """        with np.errstate(divide='ignore', invalid='ignore'):
            a = xs / zs
            b = ys / zs
"""
    else:
        s += """        a = xs
        b = ys
"""
    s += """        if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
            continue
        if _flat(a) or _flat(b) or _flat(zs):
            continue
"""
    s += "        r = _corr(a, b)\n" if v == "faulty" else "        r = _partial_corr(a, b, zs)\n"
    s += """        if r is None or not np.isfinite(r):
            continue
        counted += 1
        if r >= 0.2:
            hits += 1
    if counted == 0:
        return None
    return bool(hits / counted >= 0.6)
"""
    return s


case("D-062", [H_FLAT, H_CORR], b05)


# ---------------------------------------------------------------- D-038 (B3A-06) KRO93, regression slope
def b06(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across countries, annual lung-cancer deaths and annual cigarette sales are associated after",
        "accounting for population; the standardised slope of deaths on cigarette sales, with population",
        "accounted for, is at least 0.2 in absolute value.",
        "",
        "d['lung_cancer_deaths'] : (countries,) float, total lung-cancer deaths in each country in one year,",
        "                          in thousands",
        "d['cigarettes_sold']    : (countries,) float, total cigarettes sold in each country in the same year,",
        "                          in millions",
        "d['population']         : (countries,) float, population of each country, in millions",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 countries, or a variance is zero.",
    ])
    s += """    y = np.asarray(d['lung_cancer_deaths'], dtype=float)
    sales = np.asarray(d['cigarettes_sold'], dtype=float)
    pop = np.asarray(d['population'], dtype=float)
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(sales)) and np.all(np.isfinite(pop))):
        return None
    if y.size < 3:
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        x = sales / pop
"""
    else:
        s += """    x = sales
"""
    s += """    if not np.all(np.isfinite(x)):
        return None
    if _flat(y) or _flat(x) or _flat(pop):
        return None
"""
    s += ("    b = _std_coef(y, x.reshape(-1, 1), 0)\n" if v == "faulty"
          else "    b = _std_coef(y, np.column_stack([x, pop]), 0)\n")
    s += """    if not np.isfinite(b):
        return None
    return bool(abs(b) >= 0.2)
"""
    return s


case("D-038", [H_FLAT, H_STD], b06)


# ---------------------------------------------------------------- D-006 (B3A-07) CHI13, correlation, six waves
def b07(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across children, BMI at age 5 and the yearly rate of change in BMI between ages 5 and 10 are",
        "negatively correlated; the correlation between the two is at most -0.25.",
        "",
        "d['bmi'] : (children, annual_visits) float, BMI of each child at the annual visits at ages 5, 6, 7, 8,",
        "           9 and 10 (visits in age order), in kg/m2",
        "",
        "Returns True / False; None when a value is not finite, fewer than 2 children, fewer than 3 visits, a",
        "variance is zero, or (fitted random-effects model) the estimated variance of the random intercept or of",
        "the random slope is not positive, so that their correlation is not defined.",
    ])
    s += """    bmi = np.asarray(d['bmi'], dtype=float)
    if not np.all(np.isfinite(bmi)):
        return None
    n, m = bmi.shape
    if n < 2 or m < 3:
        return None
"""
    if v == "faulty":
        s += "    r = _corr(bmi[:, 0], bmi[:, -1] - bmi[:, 0])\n"
    else:
        s += """    X = np.column_stack([np.ones(m), np.arange(m, dtype=float)])
    XtXi = np.linalg.inv(X.T @ X)
    bhat = bmi @ X @ XtXi
    res = bmi - bhat @ X.T
    s2 = np.sum(res * res) / (n * (m - 2))
    G = np.cov(bhat, rowvar=False) - s2 * XtXi
    if not (G[0, 0] > 0.0 and G[1, 1] > 0.0):
        return None
    r = float(G[0, 1] / np.sqrt(G[0, 0] * G[1, 1]))
"""
    s += """    if r is None or not np.isfinite(r):
        return None
    return bool(r <= -0.25)
"""
    return s


case("D-006", [H_FLAT, H_CORR], b07)


# ---------------------------------------------------------------- D-008 (B3A-08) ARC81, slope, repeated occasions
def b08(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: within patients, oxygen consumption rises with oxygen delivery; the mean over patients of the",
        "within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min.",
        "",
        "d['cardiac_output']      : (patients, occasions) float, cardiac output of each patient at each",
        "                           measurement occasion, in L/min",
        "d['arterial_o2_content'] : (patients, occasions) float, oxygen content of arterial blood of each",
        "                           patient at each occasion, in mL O2 per dL",
        "d['venous_o2_content']   : (patients, occasions) float, oxygen content of mixed venous blood of each",
        "                           patient at each occasion, in mL O2 per dL",
        "d['vo2_expired_gas']     : (patients, occasions) float, oxygen consumption of each patient at each",
        "                           occasion measured from expired-gas analysis, in mL/min",
        "",
        "Oxygen delivery is cardiac_output * arterial_o2_content * 10 (mL/min). Patients whose delivery has no",
        "variance across occasions are not counted.",
        "Returns True / False; None when a value is not finite, fewer than 2 occasions, or no patient can be",
        "counted.",
    ])
    s += """    co = np.asarray(d['cardiac_output'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    vo = np.asarray(d['vo2_expired_gas'], dtype=float)
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))
            and np.all(np.isfinite(vo))):
        return None
    n, m = co.shape
    if n < 1 or m < 2:
        return None
    do2 = co * ca * 10.0
"""
    s += "    vo2 = co * (ca - cv) * 10.0\n" if v == "faulty" else "    vo2 = vo\n"
    s += """    ok = np.max(do2, axis=1) > np.min(do2, axis=1)
    if not np.any(ok):
        return None
    xc = do2 - np.mean(do2, axis=1, keepdims=True)
    yc = vo2 - np.mean(vo2, axis=1, keepdims=True)
    slopes = np.sum(xc * yc, axis=1)[ok] / np.sum(xc * xc, axis=1)[ok]
    stat = float(np.mean(slopes))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.1)
"""
    return s


case("D-008", [H_FLAT], b08)


# ---------------------------------------------------------------- D-067 (B3A-09) PEA97, regression slope
def b09(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: after accounting for body mass, kidney weight and heart weight are positively related; the",
        "standardised slope of kidney weight on heart weight is at least 0.25.",
        "",
        "d['kidney_weight'] : (rats,) float, combined kidney weight of each rat, in g",
        "d['heart_weight']  : (rats,) float, heart weight of each rat, in g",
        "d['body_mass']     : (rats,) float, body mass of each rat, in g",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 rats, or a variance is zero.",
    ])
    s += """    kid = np.asarray(d['kidney_weight'], dtype=float)
    heart = np.asarray(d['heart_weight'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(kid)) and np.all(np.isfinite(heart)) and np.all(np.isfinite(body))):
        return None
    if kid.size < 3:
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        y = kid / body
        x = heart / body
"""
    else:
        s += """    y = kid
    x = heart
"""
    s += """    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    if _flat(y) or _flat(x) or _flat(body):
        return None
"""
    s += ("    b = _std_coef(y, x.reshape(-1, 1), 0)\n" if v == "faulty"
          else "    b = _std_coef(y, np.column_stack([x, body]), 0)\n")
    s += """    if not np.isfinite(b):
        return None
    return bool(b >= 0.25)
"""
    return s


case("D-067", [H_FLAT, H_STD], b09)


# ---------------------------------------------------------------- D-050 (B3A-10) KRO93, R-squared
def b10(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: age explains at least 10% of the variance in liver mass beyond what body mass explains; the",
        "increase in R-squared when age is added to a regression of liver mass on body mass is at least 0.10.",
        "",
        "d['liver_mass'] : (rats,) float, liver mass of each rat, in g",
        "d['age_days']   : (rats,) float, age of each rat, in days",
        "d['body_mass']  : (rats,) float, body mass of each rat, in g",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 rats, or a variance is zero.",
    ])
    s += """    liver = np.asarray(d['liver_mass'], dtype=float)
    age = np.asarray(d['age_days'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(age)) and np.all(np.isfinite(body))):
        return None
    if liver.size < 3:
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        y = liver / body
"""
    else:
        s += """    y = liver
"""
    s += """    if not np.all(np.isfinite(y)):
        return None
    if _flat(y) or _flat(age) or _flat(body):
        return None
"""
    s += ("    stat = _r2(y, age.reshape(-1, 1))\n" if v == "faulty"
          else "    stat = _r2(y, np.column_stack([body, age])) - _r2(y, body.reshape(-1, 1))\n")
    s += """    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.10)
"""
    return s


case("D-050", [H_FLAT, H_RESID, H_R2], b10)


# ---------------------------------------------------------------- D-020 (B3A-11) PEA97, R-squared
def b11(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: heart weight accounts for at least 10% of the variance in liver weight beyond what body mass",
        "accounts for; the increase in R-squared when heart weight is added to a regression of liver weight on",
        "body mass is at least 0.10.",
        "",
        "d['liver_weight'] : (mice,) float, liver weight of each mouse, in g",
        "d['heart_weight'] : (mice,) float, heart weight of each mouse, in g",
        "d['body_mass']    : (mice,) float, body mass of each mouse, in g",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 mice, or a variance is zero.",
    ])
    s += """    liver = np.asarray(d['liver_weight'], dtype=float)
    heart = np.asarray(d['heart_weight'], dtype=float)
    body = np.asarray(d['body_mass'], dtype=float)
    if not (np.all(np.isfinite(liver)) and np.all(np.isfinite(heart)) and np.all(np.isfinite(body))):
        return None
    if liver.size < 3:
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        y = liver / body
        x = heart / body
"""
    else:
        s += """    y = liver
    x = heart
"""
    s += """    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(x))):
        return None
    if _flat(y) or _flat(x) or _flat(body):
        return None
"""
    s += ("    stat = _r2(y, x.reshape(-1, 1))\n" if v == "faulty"
          else "    stat = _r2(y, np.column_stack([body, x])) - _r2(y, body.reshape(-1, 1))\n")
    s += """    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.10)
"""
    return s


case("D-020", [H_FLAT, H_RESID, H_R2], b11)


# ---------------------------------------------------------------- D-031 (B3A-12) KRO93, correlation
def b12(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across cities, annual offences recorded and the median age of residents are associated after",
        "accounting for population; the partial correlation coefficient between offences and median age, given",
        "population, is at least 0.25 in absolute value.",
        "",
        "d['offences']   : (cities,) float, total offences recorded in each city in one year",
        "d['median_age'] : (cities,) float, median age of the residents of each city, in years",
        "d['population'] : (cities,) float, population of each city, in thousands",
        "",
        "Returns True / False; None when a value is not finite, fewer than 3 cities, or a variance is zero.",
    ])
    s += """    off = np.asarray(d['offences'], dtype=float)
    age = np.asarray(d['median_age'], dtype=float)
    pop = np.asarray(d['population'], dtype=float)
    if not (np.all(np.isfinite(off)) and np.all(np.isfinite(age)) and np.all(np.isfinite(pop))):
        return None
    if off.size < 3:
        return None
"""
    if v == "faulty":
        s += """    with np.errstate(divide='ignore', invalid='ignore'):
        a = off / pop
"""
    else:
        s += """    a = off
"""
    s += """    if not np.all(np.isfinite(a)):
        return None
    if _flat(a) or _flat(age) or _flat(pop):
        return None
"""
    s += "    r = _corr(a, age)\n" if v == "faulty" else "    r = _partial_corr(a, age, pop)\n"
    s += """    if r is None or not np.isfinite(r):
        return None
    return bool(abs(r) >= 0.25)
"""
    return s


case("D-031", [H_FLAT, H_CORR], b12)


# ---------------------------------------------------------------- D-037 (B3A-13) CHI13, slope, retest sample
def b13(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: the expected change in BMI between baseline and follow-up is smaller for children with a higher",
        "baseline BMI; each additional 1 kg/m2 of baseline BMI goes with a change in BMI that is at least",
        "0.2 kg/m2 smaller (slope of at most -0.2).",
        "",
        "d['bmi_baseline'] : (children,) float, BMI of each child at the baseline visit, in kg/m2",
        "d['bmi_followup'] : (children,) float, BMI of each child at the follow-up visit five years after",
        "                    baseline, in kg/m2",
        "d['bmi_retest']   : (retest_children, retest_sessions) float, BMI of each child of a test-retest sample",
        "                    at two sessions a few days apart, in kg/m2",
        "",
        "Returns True / False; None when a value is not finite, fewer than 2 children in the main sample or in",
        "the retest sample, fewer than 2 sessions, a zero variance, or a non-finite result.",
    ])
    s += """    u1 = np.asarray(d['bmi_baseline'], dtype=float)
    u2 = np.asarray(d['bmi_followup'], dtype=float)
    rt = np.asarray(d['bmi_retest'], dtype=float)
    if not (np.all(np.isfinite(u1)) and np.all(np.isfinite(u2)) and np.all(np.isfinite(rt))):
        return None
    if u1.size < 2 or rt.shape[0] < 2 or rt.shape[1] < 2:
        return None
    if _flat(u1):
        return None
"""
    if v == "faulty":
        s += "    k = 0.0\n"
    else:
        s += "    k = float(np.mean(np.var(rt, axis=1, ddof=1)) / np.var(u1, ddof=1))\n"
    s += """    res = _change_stats(u1, u2, k)
    if res is None or not np.isfinite(res[0]):
        return None
    return bool(res[0] <= -0.2)
"""
    return s


case("D-037", [H_FLAT, H_SLOPE_CHANGE], b13)


# ---------------------------------------------------------------- D-015 (B3A-14) CHI13, R-squared
def b14(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: baseline BMI explains at least 10% of the variance in the change in BMI between baseline and",
        "follow-up (R-squared of at least 0.10).",
        "",
        "d['bmi_baseline']        : (children,) float, BMI of each child at the baseline visit, in kg/m2",
        "d['bmi_baseline_retest'] : (children,) float, a second BMI measurement of each child at the baseline",
        "                           visit, in kg/m2",
        "d['bmi_followup']        : (children,) float, BMI of each child at the follow-up visit five years",
        "                           after baseline, in kg/m2",
        "",
        "Returns True / False; None when a value is not finite, fewer than 2 children, a variance is zero, or the",
        "corrected correlation is not defined (error-variance share k = 1, or a true-part variance that is not",
        "positive).",
    ])
    s += """    u1 = np.asarray(d['bmi_baseline'], dtype=float)
    u1b = np.asarray(d['bmi_baseline_retest'], dtype=float)
    u2 = np.asarray(d['bmi_followup'], dtype=float)
    if not (np.all(np.isfinite(u1)) and np.all(np.isfinite(u1b)) and np.all(np.isfinite(u2))):
        return None
    if u1.size < 2:
        return None
"""
    if v == "faulty":
        s += "    k = 0.0\n"
    else:
        s += """    icc = _corr(u1, u1b)
    if icc is None:
        return None
    k = 1.0 - icc
"""
    s += """    res = _change_stats(u1, u2, k)
    if res is None or not np.isfinite(res[1]):
        return None
    return bool(res[1] ** 2 >= 0.10)
"""
    return s


case("D-015", [H_FLAT, H_CORR, H_SLOPE_CHANGE], b14)


# ---------------------------------------------------------------- D-036 (B3A-15) ARC81, R-squared
def b15(v):
    s = "def criterion(d):\n"
    s += doc([
        "Claim: across patients, cardiac output explains at least 25% of the variance in systemic vascular",
        "resistance (R-squared of at least 0.25).",
        "",
        "d['mean_arterial_pressure']   : (patients,) float, mean arterial pressure of each patient, in mmHg",
        "d['central_venous_pressure']  : (patients,) float, central venous pressure of each patient, in mmHg",
        "d['co_thermodilution']        : (patients,) float, cardiac output of each patient measured by",
        "                                thermodilution, in L/min",
        "d['co_fick']                  : (patients,) float, cardiac output of each patient measured by the Fick",
        "                                method from expired-gas oxygen uptake, in L/min",
        "",
        "Systemic vascular resistance is 80 * (mean_arterial_pressure - central_venous_pressure) /",
        "co_thermodilution (dyn s / cm5).",
        "Returns True / False; None when a value is not finite, fewer than 2 patients, or a variance is zero.",
    ])
    s += """    mapp = np.asarray(d['mean_arterial_pressure'], dtype=float)
    cvp = np.asarray(d['central_venous_pressure'], dtype=float)
    cot = np.asarray(d['co_thermodilution'], dtype=float)
    cof = np.asarray(d['co_fick'], dtype=float)
    if not (np.all(np.isfinite(mapp)) and np.all(np.isfinite(cvp)) and np.all(np.isfinite(cot))
            and np.all(np.isfinite(cof))):
        return None
    if mapp.size < 2:
        return None
    with np.errstate(divide='ignore', invalid='ignore'):
        svr = 80.0 * (mapp - cvp) / cot
    if not np.all(np.isfinite(svr)):
        return None
"""
    s += "    x = cot\n" if v == "faulty" else "    x = cof\n"
    s += """    if _flat(svr) or _flat(x):
        return None
    stat = _r2(svr, x.reshape(-1, 1))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.25)
"""
    return s


case("D-036", [H_FLAT, H_RESID, H_R2], b15)

# helper sets per case (identical in both files of a case)
HELPERS = {
    "D-040": [H_FLAT, H_CORR, H_RESID, H_PARTIAL],
    "D-017": [H_FLAT],
    "D-053": [H_FLAT, H_CORR],
    "D-071": [H_FLAT, H_CORR],
    "D-062": [H_FLAT, H_CORR, H_RESID, H_PARTIAL],
    "D-038": [H_FLAT, H_STD],
    "D-006": [H_FLAT, H_CORR],
    "D-008": [H_FLAT],
    "D-067": [H_FLAT, H_STD],
    "D-050": [H_FLAT, H_RESID, H_R2],
    "D-020": [H_FLAT, H_RESID, H_R2],
    "D-031": [H_FLAT, H_CORR, H_RESID, H_PARTIAL],
    "D-037": [H_FLAT, H_SLOPE_CHANGE],
    "D-015": [H_FLAT, H_CORR, H_SLOPE_CHANGE],
    "D-036": [H_FLAT, H_RESID, H_R2],
}


def main():
    for cid, (_, fn) in CASES.items():
        for v in ("faulty", "fixed"):
            text = HEADER + "\n\n".join(HELPERS[cid]) + "\n\n" + fn(v)
            path = os.path.join(ROOT, cid, v + "_body.py")
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        print("wrote", cid)


if __name__ == "__main__":
    main()
