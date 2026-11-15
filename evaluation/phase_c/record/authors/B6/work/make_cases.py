"""Scratch generator (text only): builds faulty.py and fixed.py of every B-6 case from the frozen skeleton.py by
replacing the single line '    raise NotImplementedError'. It never imports or executes any case file.

Usage: py work\\make_cases.py            (writes all 12 cases)
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"
MARK = "    raise NotImplementedError"

# ---------------------------------------------------------------------------------------------------------------
# Shared helper text (identical in faulty and fixed bodies that use it): two-sided p of Student's t from the
# regularized incomplete beta function, numpy only (no scipy, no new import).
# ---------------------------------------------------------------------------------------------------------------
HELP_P = '''    def lgam(x):
        g = (676.5203681218851, -1259.1392167224028, 771.3234287776531, -176.6150291621406,
             12.507343278686905, -0.13857109526572012, 9.984369578019572e-6, 1.5056327351493116e-7)
        x = x - 1.0
        a = 0.99999999999980993
        for i, gi in enumerate(g):
            a += gi / (x + i + 1.0)
        t = x + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a)

    def betacf(a, b, x):
        tiny = 1e-300
        c = 1.0
        dd = 1.0 - (a + b) * x / (a + 1.0)
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 500):
            m2 = 2 * m
            aa = m * (b - m) * x / ((a - 1.0 + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + 1.0 + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-14:
                break
        return h

    def p2t(t, df):
        # two-sided p value of Student's t statistic with df degrees of freedom
        x = df / (df + t * t)
        if x >= 1.0:
            return 1.0
        if x <= 0.0:
            return 0.0
        a, b = 0.5 * df, 0.5
        lb = lgam(a + b) - lgam(a) - lgam(b) + a * np.log(x) + b * np.log1p(-x)
        if x < (a + 1.0) / (a + b + 2.0):
            return float(np.exp(lb) * betacf(a, b, x) / a)
        return float(1.0 - np.exp(lb) * betacf(b, a, 1.0 - x) / b)

'''


def two_group_t(key, grp, pooled, direction, reduce_faulty, reduce_fixed, min_label):
    """Two-sample t test (Student pooled or Welch) of the group means; the only difference between the twins is the
    unit that enters the test (row of the second axis versus the mean over it)."""
    head = f'''{HELP_P}    v = np.asarray(d["{key}"], dtype=float)
    g = np.asarray(d["{grp}"], dtype=bool)
    if not np.all(np.isfinite(v)):
        return None
    if g.sum() < 2 or (~g).sum() < 2:
        return None
'''
    if pooled:
        test = '''    nx, ny = x.size, y.size
    df = nx + ny - 2.0
    s2 = ((nx - 1.0) * x.var(ddof=1) + (ny - 1.0) * y.var(ddof=1)) / df
    se2 = s2 * (1.0 / nx + 1.0 / ny)
    if not se2 > 0.0:
        return None
'''
    else:
        test = '''    nx, ny = x.size, y.size
    a = x.var(ddof=1) / nx
    b = y.var(ddof=1) / ny
    se2 = a + b
    if not se2 > 0.0:
        return None
    df = se2 ** 2 / (a * a / (nx - 1.0) + b * b / (ny - 1.0))
'''
    tail = f'''    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() {direction} y.mean() and p2t(t, df) < 0.05)'''
    mk = lambda red: head + red + test + tail
    return mk(reduce_faulty), mk(reduce_fixed)


BODIES = {}

# B6-01 ---------------------------------------------------------------------------------------------------------
BODIES["B6-01"] = two_group_t(
    "activity", "exposed", True, ">",
    '    x = v[g].ravel()\n    y = v[~g].ravel()\n',
    '    x = v[g].mean(axis=1)\n    y = v[~g].mean(axis=1)\n', "dams")

# B6-04 ---------------------------------------------------------------------------------------------------------
BODIES["B6-04"] = two_group_t(
    "weight_gain", "treated", False, "<",
    '    x = v[g].ravel()\n    y = v[~g].ravel()\n',
    '    x = v[g].mean(axis=1)\n    y = v[~g].mean(axis=1)\n', "cages")

# B6-08 ---------------------------------------------------------------------------------------------------------
BODIES["B6-08"] = two_group_t(
    "density", "treated", False, "<",
    '    x = v[g].ravel()\n    y = v[~g].ravel()\n',
    '    x = v[g].mean(axis=1)\n    y = v[~g].mean(axis=1)\n', "tanks")

# B6-10 ---------------------------------------------------------------------------------------------------------
BODIES["B6-10"] = two_group_t(
    "latency", "treated", True, ">",
    '    x = v[g].ravel()\n    y = v[~g].ravel()\n',
    '    x = v[g].mean(axis=1)\n    y = v[~g].mean(axis=1)\n', "rats")

# B6-02 ---------------------------------------------------------------------------------------------------------
B602_HEAD = '''    r = np.asarray(d["responded"], dtype=float)
    g = np.asarray(d["treated"], dtype=bool)
    if not np.all(np.isfinite(r)):
        return None
    if g.sum() < 2 or (~g).sum() < 2 or r.shape[1] < 1:
        return None
'''
B602_TEST = '''    nx, ny = x.size, y.size
    a = x.var(ddof=1) / nx
    b = y.var(ddof=1) / ny
    se2 = a + b
    if not se2 > 0.0:
        return None
    df = se2 ** 2 / (a * a / (nx - 1.0) + b * b / (ny - 1.0))
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() > y.mean() and p2t(t, df) < 0.05)'''
# faulty: the same Welch t test, applied to the cell-level 0/1 outcomes (cells as replicates); fixed: to the well proportions
B602_FAULTY = HELP_P + B602_HEAD + '    x = r[g].ravel()\n    y = r[~g].ravel()\n' + B602_TEST
B602_FIXED = HELP_P + B602_HEAD + '    x = r[g].mean(axis=1)\n    y = r[~g].mean(axis=1)\n' + B602_TEST
BODIES["B6-02"] = (B602_FAULTY, B602_FIXED)

# B6-03 ---------------------------------------------------------------------------------------------------------
B603_HEAD = HELP_P + '''    s = np.asarray(d["spine_density"], dtype=float)
    dose = np.asarray(d["dose"], dtype=float)
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(dose))):
        return None
    if dose.size < 3:
        return None
    s = s.reshape(s.shape[0], -1)
'''
B603_TAIL = '''    xc = x - x.mean()
    sxx = (xc ** 2).sum()
    if not sxx > 0.0:
        return None
    yc = y - y.mean()
    slope = (xc * yc).sum() / sxx
    df = x.size - 2.0
    s2 = ((yc - slope * xc) ** 2).sum() / df
    if not s2 > 0.0:
        return None
    t = slope / np.sqrt(s2 / sxx)
    return bool(slope > 0.0 and p2t(t, df) < 0.05)'''
BODIES["B6-03"] = (
    B603_HEAD + '    x = np.repeat(dose, s.shape[1])\n    y = s.ravel()\n' + B603_TAIL,
    B603_HEAD + '    x = dose\n    y = s.mean(axis=1)\n' + B603_TAIL)

# B6-05 ---------------------------------------------------------------------------------------------------------
B605_HEAD = '''    pre = np.asarray(d["pre"], dtype=float)
    post = np.asarray(d["post"], dtype=float)
    g = np.asarray(d["trained"], dtype=bool)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    if g.sum() < 2 or (~g).sum() < 2:
        return None
    change = post - pre
    x = change[g]
    y = change[~g]
'''
B605_FAULTY = HELP_P + B605_HEAD + '''    def one(v):
        # paired t test of the within-group change against zero
        se2 = v.var(ddof=1) / v.size
        if not se2 > 0.0:
            return None
        return v.mean(), p2t(v.mean() / np.sqrt(se2), v.size - 1.0)

    r1 = one(x)
    r0 = one(y)
    if r1 is None or r0 is None:
        return None
    return bool(r1[0] > 0.0 and r1[1] < 0.05 and r0[1] >= 0.05)'''
B605_FIXED = HELP_P + B605_HEAD + '''    nx, ny = x.size, y.size
    df = nx + ny - 2.0
    s2 = ((nx - 1.0) * x.var(ddof=1) + (ny - 1.0) * y.var(ddof=1)) / df
    se2 = s2 * (1.0 / nx + 1.0 / ny)
    if not se2 > 0.0:
        return None
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() > y.mean() and p2t(t, df) < 0.05)'''
BODIES["B6-05"] = (B605_FAULTY, B605_FIXED)

# B6-06 ---------------------------------------------------------------------------------------------------------
B606_HEAD = '''    rt = np.asarray(d["rt"], dtype=float)
    g = np.asarray(d["patient"], dtype=bool)
    if not np.all(np.isfinite(rt)):
        return None
    if g.sum() < 2 or (~g).sum() < 2 or rt.shape[1] < 2:
        return None
    sess = np.arange(rt.shape[1], dtype=float)
    sc = sess - sess.mean()
    slope = ((rt - rt.mean(axis=1, keepdims=True)) * sc).sum(axis=1) / (sc ** 2).sum()
    x = slope[~g]
    y = slope[g]
'''
B606_FAULTY = HELP_P + B606_HEAD + '''    def one(v):
        # one-sample t test of the within-group mean slope against zero
        se2 = v.var(ddof=1) / v.size
        if not se2 > 0.0:
            return None
        return v.mean(), p2t(v.mean() / np.sqrt(se2), v.size - 1.0)

    r1 = one(x)
    r0 = one(y)
    if r1 is None or r0 is None:
        return None
    return bool(r1[0] < 0.0 and r1[1] < 0.05 and r0[1] >= 0.05)'''
B606_FIXED = HELP_P + B606_HEAD + '''    nx, ny = x.size, y.size
    df = nx + ny - 2.0
    s2 = ((nx - 1.0) * x.var(ddof=1) + (ny - 1.0) * y.var(ddof=1)) / df
    se2 = s2 * (1.0 / nx + 1.0 / ny)
    if not se2 > 0.0:
        return None
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() < y.mean() and p2t(t, df) < 0.05)'''
BODIES["B6-06"] = (B606_FAULTY, B606_FIXED)

# B6-07 ---------------------------------------------------------------------------------------------------------
B607_HEAD = '''    ta = np.asarray(d["task_a"], dtype=float)
    ra = np.asarray(d["rest_a"], dtype=float)
    tb = np.asarray(d["task_b"], dtype=float)
    rb = np.asarray(d["rest_b"], dtype=float)
    if not (np.all(np.isfinite(ta)) and np.all(np.isfinite(ra)) and np.all(np.isfinite(tb)) and np.all(np.isfinite(rb))):
        return None
    if ta.size < 2:
        return None
    ea = ta - ra
    eb = tb - rb
'''
B607_FAULTY = HELP_P + B607_HEAD + '''    def one(v):
        # one-sample t test of the region's mean signal change against zero
        se2 = v.var(ddof=1) / v.size
        if not se2 > 0.0:
            return None
        return v.mean(), p2t(v.mean() / np.sqrt(se2), v.size - 1.0)

    r1 = one(ea)
    r0 = one(eb)
    if r1 is None or r0 is None:
        return None
    return bool(r1[0] > 0.0 and r1[1] < 0.05 and r0[1] >= 0.05)'''
B607_FIXED = HELP_P + B607_HEAD + '''    diff = ea - eb
    se2 = diff.var(ddof=1) / diff.size
    if not se2 > 0.0:
        return None
    t = diff.mean() / np.sqrt(se2)
    return bool(diff.mean() > 0.0 and p2t(t, diff.size - 1.0) < 0.05)'''
BODIES["B6-07"] = (B607_FAULTY, B607_FIXED)

# B6-09 ---------------------------------------------------------------------------------------------------------
B609_HEAD = '''    v = np.asarray(d["abundance"], dtype=float)
    g = np.asarray(d["treated"], dtype=bool)
    if not np.all(np.isfinite(v)):
        return None
    if g.sum() < 1 or (~g).sum() < 1:
        return None
'''
B609_TAIL = '''    n1, n2 = x.size, y.size
    n = n1 + n2
    u, inv, cnt = np.unique(np.concatenate([x, y]), return_inverse=True, return_counts=True)
    rank = (np.cumsum(cnt) - (cnt - 1) / 2.0)[inv.reshape(-1)]
    u1 = rank[:n1].sum() - n1 * (n1 + 1) / 2.0
    var = n1 * n2 / 12.0 * ((n + 1.0) - (cnt ** 3 - cnt).sum() / (n * (n - 1.0)))
    if not var > 0.0:
        return None
    dev = u1 - n1 * n2 / 2.0
    z = np.sign(dev) * max(abs(dev) - 0.5, 0.0) / np.sqrt(var)
    return bool(dev > 0.0 and abs(z) > 1.959963984540054)'''
BODIES["B6-09"] = (
    B609_HEAD + '    x = v[g].ravel()\n    y = v[~g].ravel()\n' + B609_TAIL,
    B609_HEAD + '    x = v[g].mean(axis=1)\n    y = v[~g].mean(axis=1)\n' + B609_TAIL)

# B6-11 ---------------------------------------------------------------------------------------------------------
B611_HEAD = HELP_P + '''    h = np.asarray(d["heart_rate"], dtype=float)
    c = np.asarray(d["cortisol"], dtype=float)
    if not (np.all(np.isfinite(h)) and np.all(np.isfinite(c))):
        return None
    if h.shape[0] < 3:
        return None
'''
B611_TAIL = '''    xc = x - x.mean()
    yc = y - y.mean()
    sxx = (xc ** 2).sum()
    syy = (yc ** 2).sum()
    if not (sxx > 0.0 and syy > 0.0):
        return None
    r = (xc * yc).sum() / np.sqrt(sxx * syy)
    df = x.size - 2.0
    t = r * np.sqrt(df / (1.0 - r * r))
    return bool(r > 0.0 and p2t(t, df) < 0.05)'''
BODIES["B6-11"] = (
    B611_HEAD + '    x = h.ravel()\n    y = c.ravel()\n' + B611_TAIL,
    B611_HEAD + '    x = h.mean(axis=1)\n    y = c.mean(axis=1)\n' + B611_TAIL)

# B6-12 ---------------------------------------------------------------------------------------------------------
B612_HEAD = '''    a = np.asarray(d["task_score"], dtype=float)
    b = np.asarray(d["symptom_score"], dtype=float)
    g = np.asarray(d["group_a"], dtype=bool)
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    if g.sum() < 4 or (~g).sum() < 4:
        return None

    def corr(u, w):
        uc = u - u.mean()
        wc = w - w.mean()
        suu = (uc ** 2).sum()
        sww = (wc ** 2).sum()
        if not (suu > 0.0 and sww > 0.0):
            return None
        return (uc * wc).sum() / np.sqrt(suu * sww)

    r_a = corr(a[g], b[g])
    r_b = corr(a[~g], b[~g])
    if r_a is None or r_b is None:
        return None
    n_a = float(g.sum())
    n_b = float((~g).sum())
'''
B612_FAULTY = HELP_P + B612_HEAD + '''    p_a = p2t(r_a * np.sqrt((n_a - 2.0) / (1.0 - r_a * r_a)), n_a - 2.0)
    p_b = p2t(r_b * np.sqrt((n_b - 2.0) / (1.0 - r_b * r_b)), n_b - 2.0)
    return bool(r_a > 0.0 and p_a < 0.05 and p_b >= 0.05)'''
B612_FIXED = B612_HEAD + '''    z = (np.arctanh(r_a) - np.arctanh(r_b)) / np.sqrt(1.0 / (n_a - 3.0) + 1.0 / (n_b - 3.0))
    return bool(r_a > r_b and abs(z) > 1.959963984540054)'''
BODIES["B6-12"] = (B612_FAULTY, B612_FIXED)


def build(case):
    sk = (CASES / case / "skeleton.py").read_bytes().decode("utf-8")
    assert sk.count(MARK) == 1 and "\r" not in sk, case
    faulty_body, fixed_body = BODIES[case]
    for name, body in (("faulty.py", faulty_body), ("fixed.py", fixed_body)):
        out = sk.replace(MARK, body)
        (CASES / case / name).write_bytes(out.encode("utf-8"))


if __name__ == "__main__":
    for c in sorted(BODIES):
        build(c)
        print("written", c)
