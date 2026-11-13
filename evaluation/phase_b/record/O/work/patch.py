"""Writes the criterion bodies into faulty.py / fixed.py (replaces only the 'raise NotImplementedError' line).
Does not execute any criterion. Cases that already have a CASE.md are skipped."""
import os

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")
MARK = "    raise NotImplementedError"

HELPER = '''    def _lgam(z):
        c = (676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
             12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)
        z = z - 1.0
        x = 0.99999999999980993
        for i in range(8):
            x += c[i] / (z + i + 1.0)
        t = z + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

    def _betacf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        if abs(dd) < tiny:
            dd = tiny
        dd = 1.0 / dd
        h = dd
        for m in range(1, 300):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            if abs(dd) < tiny:
                dd = tiny
            c = 1.0 + aa / c
            if abs(c) < tiny:
                c = tiny
            dd = 1.0 / dd
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            if abs(dd) < tiny:
                dd = tiny
            c = 1.0 + aa / c
            if abs(c) < tiny:
                c = tiny
            dd = 1.0 / dd
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-14:
                break
        return h

    def _ibeta(a, b, x):
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lgam(a + b) - _lgam(a) - _lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return bt * _betacf(a, b, x) / a
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b

    def welch_p(x, y):
        """One-sided Welch t test, H1: mean(x) > mean(y); exact t tail via the regularised incomplete beta function."""
        nx, ny = x.shape[0], y.shape[0]
        vx, vy = x.var(ddof=1) / nx, y.var(ddof=1) / ny
        if not (vx + vy > 1e-24):
            return None
        t = (x.mean() - y.mean()) / np.sqrt(vx + vy)
        df = (vx + vy) ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1))
        if t == 0.0:
            return 0.5
        tail = 0.5 * _ibeta(0.5 * df, 0.5, df / (df + t * t))
        return float(tail if t > 0 else 1.0 - tail)

'''


def body(case, kind):
    F = (kind == "faulty")
    if case == "O1a":
        use = "x[:, :12]" if F else "x[:, :11]"
        cmt = ("    # all 12 variables, including column 11 (the number of therapy doses recorded during the stay)\n" if F else
               "    # the 11 variables available at admission; column 11 (therapy doses recorded during the stay) is left out\n")
        return ('''    x = np.asarray(d["vars"], dtype=float)
    y = np.asarray(d["sepsis"]).astype(bool)
    n_train = 150  # fixed block: the first 150 patients fit the classifier, the remaining ones score it
    if not (np.isfinite(x).all() and x.shape[0] > n_train):
        return None
''' + cmt + '''    use = ''' + use + '''
    ytr = y[:n_train]
    yte = y[n_train:]
    if ytr.all() or not ytr.any():
        return None
    a_tr = np.column_stack([np.ones(n_train), use[:n_train]])
    w = np.linalg.lstsq(a_tr, ytr.astype(float), rcond=None)[0]  # linear classifier: least squares on 0/1 labels
    a_te = np.column_stack([np.ones(use.shape[0] - n_train), use[n_train:]])
    pred = (a_te @ w) > 0.5
    acc = float(np.mean(pred == yte))
    return bool(acc >= 0.75)
''')
    if case == "O1b":
        if F:
            fit = "    # standardisation and PCA are fitted on all rows, test rows included\n    fit = x\n"
        else:
            fit = "    # standardisation and PCA are fitted on the training rows only\n    fit = x[:n_train]\n"
        return ('''    x = np.asarray(d["expr"], dtype=float)
    y = np.asarray(d["responder"]).astype(bool)
    n_train = 72  # fixed block: the first 72 tumours train the classifier, the remaining ones score it
    if not (np.isfinite(x).all() and x.shape[0] > n_train):
        return None
''' + fit + '''    mu = fit.mean(axis=0)
    sd = fit.std(axis=0)
    if sd.min() <= 1e-12:
        return None
    zfit = (fit - mu) / sd
    vt = np.linalg.svd(zfit, full_matrices=False)[2]
    comp = vt[:5].T  # top 5 principal axes
    s = ((x - mu) / sd) @ comp
    ytr = y[:n_train]
    yte = y[n_train:]
    if ytr.all() or not ytr.any():
        return None
    c1 = s[:n_train][ytr].mean(axis=0)
    c0 = s[:n_train][~ytr].mean(axis=0)
    st = s[n_train:]
    pred = np.sum((st - c1) ** 2, axis=1) < np.sum((st - c0) ** 2, axis=1)  # nearest centroid
    acc = float(np.mean(pred == yte))
    return bool(acc >= 0.70)
''')
    if case == "O2a":
        if F:
            ps = ('''    # the analysis that is reported is the one with the smallest p
    ps = [welch_p(a[:, 0], b[:, 0]),  # measure 1
          welch_p(a[:, 1], b[:, 1]),  # measure 2
          welch_p(a.mean(axis=1), b.mean(axis=1))]  # average of the two measures
''')
        else:
            ps = '''    ps = [welch_p(a[:, 0], b[:, 0])]  # the planned primary outcome, measure 1, only
'''
        return (HELPER + '''    a = np.asarray(d["treated"], dtype=float)
    b = np.asarray(d["control"], dtype=float)
    if not (np.isfinite(a).all() and np.isfinite(b).all()) or a.shape[0] < 2 or b.shape[0] < 2:
        return None
''' + ps + '''    if any(p is None for p in ps):
        return None
    return bool(min(ps) < 0.05)
''')
    if case == "O2b":
        if F:
            ps = ('''    # two looks: at 20 per group, and again at 30 per group; the result that is reported is the one with the smaller p
    ps = [welch_p(a[:n], b[:n]) for n in (20, 30)]
''')
        else:
            ps = '''    ps = [welch_p(a[:n], b[:n]) for n in (30,)]  # a single test at the planned 30 per group
'''
        return (HELPER + '''    a = np.asarray(d["treated"], dtype=float)
    b = np.asarray(d["control"], dtype=float)
    if not (np.isfinite(a).all() and np.isfinite(b).all()) or a.shape[0] < 30 or b.shape[0] < 30:
        return None
''' + ps + '''    if any(p is None for p in ps):
        return None
    return bool(min(ps) < 0.05)
''')
    if case == "O3a":
        sig = ("    sig = x[:, 5:10]  # columns 6 to 10 counting from 1: the gene list read one position too far\n" if F else
               "    sig = x[:, 4:9]  # the named signature genes, columns 5 to 9 counting from 1\n")
        return ('''    x = np.asarray(d["expr"], dtype=float)
    y = np.asarray(d["sensitivity"], dtype=float)
    if not (np.isfinite(x).all() and np.isfinite(y).all()):
        return None
''' + sig + '''    score = sig.mean(axis=1)
    if score.std() <= 1e-12 or y.std() <= 1e-12:
        return None
    r = float(np.corrcoef(score, y)[0, 1])
    return bool(r >= 0.5)
''')
    if case == "O3b":
        if F:
            keep = ('''    keep = np.ones(g.shape, dtype=bool)
    keep[:5, :] = False  # the first five countries (alphabetical order) are left out entirely
    keep[13, :4] = False  # the first four years of one further country are left out
''')
            stat = ('''    def bin_mean(mask):
        # each country's mean growth within the bin, then the country means averaged with equal weight
        n = mask.sum(axis=1)
        ok = n > 0
        if not ok.any():
            return None
        return float(np.mean(np.where(mask, g, 0.0).sum(axis=1)[ok] / n[ok]))

''')
        else:
            keep = '''    keep = np.ones(g.shape, dtype=bool)  # all countries and years are used
'''
            stat = ('''    def bin_mean(mask):
        # mean growth over the pooled country-years of the bin
        if not mask.any():
            return None
        return float(g[mask].mean())

''')
        return ('''    g = np.asarray(d["growth"], dtype=float)
    dbt = np.asarray(d["debt"], dtype=float)
    if not (np.isfinite(g).all() and np.isfinite(dbt).all()) or g.shape != dbt.shape or g.ndim != 2 or g.shape[0] < 14:
        return None
''' + keep + stat + '''    hi = bin_mean(keep & (dbt > 90.0))
    lo = bin_mean(keep & (dbt <= 90.0))
    if hi is None or lo is None:
        return None
    return bool(hi - lo <= -1.5)
''')
    raise KeyError(case)


for case in ["O1a", "O1b", "O2a", "O2b", "O3a", "O3b"]:
    if os.path.exists(os.path.join(root, case, "CASE.md")):
        print("skip", case)
        continue
    for kind in ["faulty", "fixed"]:
        p = os.path.join(root, case, kind + ".py")
        txt = open(p, encoding="utf-8", newline="").read()
        assert txt.count(MARK) == 1, (case, kind, txt.count(MARK))
        nl = "\r\n" if "\r\n" in txt else "\n"
        b = body(case, kind).replace("\n", nl).rstrip(nl)
        open(p, "w", encoding="utf-8", newline="").write(txt.replace(MARK, b))
        print("patched", case, kind)
