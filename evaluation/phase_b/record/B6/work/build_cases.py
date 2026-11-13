# Builds faulty.py / fixed.py of each B6 case from the frozen skeleton by replacing ONLY the line
# "    raise NotImplementedError". Nothing is run here except file writing; the faulty criterion is never executed.
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "cases")
STATS = open(os.path.join(ROOT, "work", "stats_helpers.txt"), encoding="utf-8").read()

ONE = '''
    def _one(x):
        # one-sample t test against zero: (mean, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        n = x.size
        if n < 3 or not np.all(np.isfinite(x)):
            return None
        s = x.std(ddof=1)
        if not s > 1e-12:
            return None
        return float(x.mean()), _p2(x.mean() / (s / np.sqrt(n)), n - 1)
'''

TWO = '''
    def _two(x, y):
        # two-sample Student t test (pooled variance), mean(x) - mean(y): (difference, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n1, n2 = x.size, y.size
        if n1 < 2 or n2 < 2 or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        sp2 = ((n1 - 1) * x.var(ddof=1) + (n2 - 1) * y.var(ddof=1)) / (n1 + n2 - 2)
        if not sp2 > 1e-24:
            return None
        diff = x.mean() - y.mean()
        return float(diff), _p2(diff / np.sqrt(sp2 * (1.0 / n1 + 1.0 / n2)), n1 + n2 - 2)
'''

WELCH = '''
    def _welch(x, y):
        # two-sample Welch t test, mean(x) - mean(y): (difference, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n1, n2 = x.size, y.size
        if n1 < 3 or n2 < 3 or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        a, b = x.var(ddof=1) / n1, y.var(ddof=1) / n2
        if not a + b > 1e-24:
            return None
        diff = x.mean() - y.mean()
        df = (a + b) ** 2 / (a ** 2 / (n1 - 1) + b ** 2 / (n2 - 1))
        return float(diff), _p2(diff / np.sqrt(a + b), df)
'''

OLS = '''
    def _ols(x, y):
        # least-squares slope of y on x with its t test: (slope, two-sided p), or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n = x.size
        if n < 4 or y.size != n or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        xc = x - x.mean()
        yc = y - y.mean()
        sxx = xc @ xc
        if not sxx > 1e-24:
            return None
        b = (xc @ yc) / sxx
        res = yc - b * xc
        s2 = (res @ res) / (n - 2)
        if not s2 > 1e-24:
            return None
        return float(b), _p2(b / np.sqrt(s2 / sxx), n - 2)
'''

CORR = '''
    def _corr(x, y):
        # Pearson correlation and its sample size, or None from a guard
        x = np.asarray(x, dtype=float).ravel()
        y = np.asarray(y, dtype=float).ravel()
        n = x.size
        if n < 5 or y.size != n or not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
            return None
        xc = x - x.mean()
        yc = y - y.mean()
        sxx, syy = xc @ xc, yc @ yc
        if not (sxx > 1e-24 and syy > 1e-24):
            return None
        r = (xc @ yc) / np.sqrt(sxx * syy)
        if not abs(r) < 1.0:
            return None
        return float(r), n

    def _rp2(r, n):
        # two-sided p-value of a Pearson correlation r from n pairs
        return _p2(r * np.sqrt((n - 2.0) / (1.0 - r * r)), n - 2)
'''

SLOPES = '''
    def _slopes(y):
        # per-participant least-squares slope across the columns (sessions), one value per row
        y = np.asarray(y, dtype=float)
        t = np.arange(y.shape[1], dtype=float)
        tc = t - t.mean()
        return (y - y.mean(axis=1, keepdims=True)) @ tc / (tc @ tc)
'''

# ---- bodies -------------------------------------------------------------------------------------------------
cases = {}

cases["B6-01"] = dict(
    helpers=[ONE, WELCH],
    pre='''
    gt = np.asarray(d["post_trained"], dtype=float) - np.asarray(d["pre_trained"], dtype=float)
    gu = np.asarray(d["post_untrained"], dtype=float) - np.asarray(d["pre_untrained"], dtype=float)
''',
    faulty='''
    a = _one(gt)
    b = _one(gu)
    if a is None or b is None:
        return None
    # trained gain significant (two-sided 0.05, positive), untrained gain not significant, trained gain larger
    return bool(a[1] < 0.05 and a[0] > 0 and b[1] >= 0.05 and a[0] > b[0])
''',
    fixed='''
    r = _welch(gt, gu)
    if r is None:
        return None
    # direct comparison of the two groups' gains (interaction), two-sided 0.05, trained larger
    return bool(r[1] < 0.05 and r[0] > 0)
''')

cases["B6-02"] = dict(
    helpers=[ONE],
    pre='''
    dv = np.asarray(d["visual_drug"], dtype=float) - np.asarray(d["visual_placebo"], dtype=float)
    da = np.asarray(d["auditory_drug"], dtype=float) - np.asarray(d["auditory_placebo"], dtype=float)
''',
    faulty='''
    a = _one(dv)
    b = _one(da)
    if a is None or b is None:
        return None
    # drug effect significant in the visual region (two-sided 0.05, positive), not significant in the auditory region
    return bool(a[1] < 0.05 and a[0] > 0 and b[1] >= 0.05 and a[0] > b[0])
''',
    fixed='''
    r = _one(dv - da)
    if r is None:
        return None
    # paired test of the difference of differences, two-sided 0.05, visual larger
    return bool(r[1] < 0.05 and r[0] > 0)
''')

cases["B6-03"] = dict(
    helpers=[CORR],
    pre='''
    ry = _corr(d["sleep_young"], d["recall_young"])
    ro = _corr(d["sleep_old"], d["recall_old"])
    if ry is None or ro is None:
        return None
''',
    faulty='''
    # one-sided 0.05 test of each correlation against zero: p1 = p2 / 2 when r > 0
    old_sig = ro[0] > 0 and _rp2(ro[0], ro[1]) / 2.0 < 0.05
    young_sig = ry[0] > 0 and _rp2(ry[0], ry[1]) / 2.0 < 0.05
    return bool(old_sig and not young_sig and ro[0] > ry[0])
''',
    fixed='''
    # Fisher z test of the difference between two independent correlations, one-sided 0.05 (z crit 1.6448536269514722)
    z = (np.arctanh(ro[0]) - np.arctanh(ry[0])) / np.sqrt(1.0 / (ro[1] - 3.0) + 1.0 / (ry[1] - 3.0))
    return bool(z > 1.6448536269514722)
''')

cases["B6-04"] = dict(
    helpers=[TWO],
    pre='''
    f = np.asarray(d["biomass_fertilised"], dtype=float)
    u = np.asarray(d["biomass_unfertilised"], dtype=float)
''',
    faulty='''
    # every water sample is treated as a replicate
    r = _two(f, u)
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''',
    fixed='''
    # the pond is the unit of replication: samples are averaged within pond
    r = _two(f.mean(axis=1), u.mean(axis=1))
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''')

cases["B6-05"] = dict(
    helpers=[OLS],
    pre='''
    dose = np.asarray(d["dose"], dtype=float)
    g = np.asarray(d["growth"], dtype=float)
''',
    faulty='''
    # every mussel is a data point, its tank's dose repeated for each mussel
    r = _ols(np.repeat(dose, g.shape[1]), g)
    if r is None:
        return None
    return bool(r[0] > 0 and r[1] / 2.0 < 0.05)
''',
    fixed='''
    # the tank is the unit that received the dose: regression of tank means on dose
    r = _ols(dose, g.mean(axis=1))
    if r is None:
        return None
    return bool(r[0] > 0 and r[1] / 2.0 < 0.05)
''')

cases["B6-06"] = dict(
    helpers=[TWO],
    pre='''
    m = np.asarray(d["richness_mown"], dtype=float)
    u = np.asarray(d["richness_unmown"], dtype=float)
''',
    faulty='''
    # every plot-by-survey value is treated as a replicate
    r = _two(m, u)
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''',
    fixed='''
    # the plot is the unit of replication: surveys are averaged within plot
    r = _two(m.mean(axis=1), u.mean(axis=1))
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''')

cases["B6-07"] = dict(
    helpers=[TWO],
    pre='''
    k = np.asarray(d["rate_knockout"], dtype=float)
    w = np.asarray(d["rate_wildtype"], dtype=float)
''',
    faulty='''
    # every cell is treated as an independent unit
    r = _two(k, w)
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''',
    fixed='''
    # the animal is the unit of replication: cells are averaged within animal
    r = _two(k.mean(axis=1), w.mean(axis=1))
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''')

cases["B6-08"] = dict(
    helpers=[ONE, CORR],
    pre='''
    rt = np.asarray(d["reaction_time"], dtype=float)
    act = np.asarray(d["activity"], dtype=float)
''',
    faulty='''
    # all trials of all participants pooled into one correlation, one-sided 0.05
    r = _corr(act, rt)
    if r is None:
        return None
    return bool(r[0] > 0 and _rp2(r[0], r[1]) / 2.0 < 0.05)
''',
    fixed='''
    # one correlation per participant, Fisher z, one-sample t test of the z values against zero, one-sided 0.05
    zs = []
    for i in range(rt.shape[0]):
        ri = _corr(act[i], rt[i])
        if ri is None:
            return None
        zs.append(np.arctanh(ri[0]))
    r = _one(np.array(zs))
    if r is None:
        return None
    return bool(r[0] > 0 and r[1] / 2.0 < 0.05)
''')

cases["B6-09"] = dict(
    helpers=[ONE],
    pre='''
    dr = np.asarray(d["amp_drug"], dtype=float)
    ve = np.asarray(d["amp_vehicle"], dtype=float)
''',
    faulty='''
    # every (animal, cell index) pair is treated as an independent pair
    r = _one(dr - ve)
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''',
    fixed='''
    # the animal is the unit: paired test across animals of the per-animal mean amplitudes
    r = _one(dr.mean(axis=1) - ve.mean(axis=1))
    if r is None:
        return None
    return bool(r[1] < 0.05 and r[0] > 0)
''')

cases["B6-10"] = dict(
    helpers=[OLS],
    pre='''
    c = np.asarray(d["contrast"], dtype=float)
    ra = np.asarray(d["rt_attended"], dtype=float)
    ru = np.asarray(d["rt_unattended"], dtype=float)
''',
    faulty='''
    a = _ols(c, ra)
    b = _ols(c, ru)
    if a is None or b is None:
        return None
    # attended slope significant (two-sided 0.05, negative: reaction time falls with contrast), unattended slope not
    # significant, attended slope steeper
    return bool(a[0] < 0 and a[1] < 0.05 and b[1] >= 0.05 and a[0] < b[0])
''',
    fixed='''
    # slope of the per-participant difference (attended - unattended) on contrast, two-sided 0.05, attended steeper
    r = _ols(c, ra - ru)
    if r is None:
        return None
    return bool(r[0] < 0 and r[1] < 0.05)
''')

cases["B6-11"] = dict(
    helpers=[CORR],
    pre='''
    g = np.asarray(d["grip"], dtype=float)
    th = np.asarray(d["thickness"], dtype=float)
''',
    faulty='''
    # all participant-by-session measurements pooled into one correlation, one-sided 0.05
    r = _corr(g, th)
    if r is None:
        return None
    return bool(r[0] > 0 and _rp2(r[0], r[1]) / 2.0 < 0.05)
''',
    fixed='''
    # sessions averaged within participant, correlation across the participant means, one-sided 0.05
    r = _corr(g.mean(axis=1), th.mean(axis=1))
    if r is None:
        return None
    return bool(r[0] > 0 and _rp2(r[0], r[1]) / 2.0 < 0.05)
''')

cases["B6-12"] = dict(
    helpers=[ONE, WELCH, SLOPES],
    pre='''
    st = _slopes(d["perf_trained"])
    sc = _slopes(d["perf_control"])
''',
    faulty='''
    a = _one(st)
    b = _one(sc)
    if a is None or b is None:
        return None
    # trained slopes significantly above zero (two-sided 0.05), control slopes not significant, trained larger
    return bool(a[1] < 0.05 and a[0] > 0 and b[1] >= 0.05 and a[0] > b[0])
''',
    fixed='''
    r = _welch(st, sc)
    if r is None:
        return None
    # direct comparison of the per-participant slopes of the two groups, two-sided 0.05, trained larger
    return bool(r[1] < 0.05 and r[0] > 0)
''')


def body(spec, which):
    parts = [STATS.rstrip("\n")]
    for h in spec["helpers"]:
        parts.append(h.rstrip("\n"))
    text = "\n".join(parts) + "\n" + spec["pre"].rstrip("\n") + "\n" + spec[which].rstrip("\n")
    # the helpers define functions that the other branch does not use; unused helpers are kept in both twins
    return text


def main(ids):
    for cid in ids:
        spec = cases[cid]
        sk = open(os.path.join(CASES, cid, "skeleton.py"), "rb").read().decode("utf-8")
        marker = "    raise NotImplementedError"
        assert sk.count(marker) == 1
        for which in ("faulty", "fixed"):
            out = sk.replace(marker, body(spec, which))
            with open(os.path.join(CASES, cid, which + ".py"), "wb") as f:
                f.write(out.encode("utf-8"))
        print("built", cid)


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(cases))
