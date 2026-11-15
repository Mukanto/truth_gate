"""Scratch: writes the criterion bodies into faulty.py and fixed.py of every case (only the line
`    raise NotImplementedError` is replaced). Never imports or runs the generated criteria."""
import sys
from pathlib import Path

ROOT = Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\cases")
sys.path.insert(0, str(Path(__file__).parent))
from helpers import SF

WELCH = '''    def _welch(a, b):
        # Welch t test of mean(a) > mean(b): (difference of means, one-sided p); None when both variances are zero
        va = a.var(ddof=1) / a.size
        vb = b.var(ddof=1) / b.size
        se2 = va + vb
        if not se2 > 0.0:
            return None
        df = se2 ** 2 / (va ** 2 / (a.size - 1.0) + vb ** 2 / (b.size - 1.0))
        diff = a.mean() - b.mean()
        return diff, float(_sf(diff / np.sqrt(se2), df))
'''

TTEST1 = '''    def _ttest1(x):
        # one-sample (or paired-difference) t test of mean(x) > 0: (mean, one-sided p); None when the variance is zero
        sd = x.std(ddof=1)
        if not sd > 0.0:
            return None
        return x.mean(), float(_sf(x.mean() / (sd / np.sqrt(x.size)), x.size - 1.0))
'''


def b01(v):
    sel = {"faulty": "    keep = (start >= 20.0) & active\n", "fixed": ""}[v]
    if v == "faulty":
        tail = '''    x = fall[(start >= 20.0) & active]
    if x.size < 2:
        return None
    r = _ttest1(x)
    if r is None:
        return None
    return bool(r[0] >= 3.0 and r[1] < 0.05)
'''
        helpers = SF + TTEST1
    else:
        tail = '''    keep = start >= 20.0
    a = fall[keep & active]
    b = fall[keep & ~active]
    if a.size < 2 or b.size < 2:
        return None
    r = _welch(a, b)
    if r is None:
        return None
    return bool(r[0] >= 3.0 and r[1] < 0.05)
'''
        helpers = SF + WELCH
    return helpers + '''    start = np.asarray(d["index_start"], dtype=float)
    week12 = np.asarray(d["index_week12"], dtype=float)
    active = np.asarray(d["active"], dtype=bool)
    if not (np.all(np.isfinite(start)) and np.all(np.isfinite(week12))):
        return None
    fall = start - week12
''' + tail


def b02(v):
    base = {"faulty": "m1", "fixed": "m2"}[v]
    return SF + WELCH + f'''    start = np.asarray(d["bmd_start"], dtype=float)
    m1 = np.asarray(d["bmd_m12_scan1"], dtype=float)
    m2 = np.asarray(d["bmd_m12_scan2"], dtype=float)
    m24 = np.asarray(d["bmd_m24"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (start, m1, m2, m24)):
        return None
    first = m1 - start
    rose = first > 0.0
    fell = first < 0.0
    if rose.sum() < 2 or fell.sum() < 2:
        return None
    ref = {base}
    second = 100.0 * (m24 - ref) / ref
    a = second[rose]
    b = second[fell]
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    r = _welch(a, b)
    if r is None:
        return None
    return bool(r[0] >= 0.5 and r[1] < 0.05)
'''


def b03(v):
    col = {"faulty": 1, "fixed": 0}[v]
    return SF + TTEST1 + f'''    sbp = np.asarray(d["sbp"], dtype=float)
    if not np.all(np.isfinite(sbp)):
        return None
    keep = sbp[:, {col}] >= 160.0
    fall = sbp[keep, 1] - sbp[keep, 2]
    if fall.size < 2:
        return None
    r = _ttest1(fall)
    if r is None:
        return None
    return bool(r[0] >= 8.0 and r[1] < 0.05)
'''


def b04(v):
    runs = {
        "faulty": "    sel_runs = np.arange(runs)\n    est_runs = np.arange(runs)\n",
        "fixed": "    sel_runs = np.arange(1, runs, 2)\n    est_runs = np.arange(0, runs, 2)\n",
    }[v]
    return SF + TTEST1 + '''    f = np.asarray(d["resp_faces"], dtype=float)
    b = np.asarray(d["resp_bodies"], dtype=float)
    h = np.asarray(d["resp_houses"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (f, b, h)):
        return None
    runs = f.shape[1]
''' + runs + '''    if sel_runs.size < 2 or est_runs.size < 1:
        return None
    contrast = f[:, sel_runs, :] - h[:, sel_runs, :]
    sd = contrast.std(axis=1, ddof=1)
    if not np.all(sd > 0.0):
        return None
    t = contrast.mean(axis=1) / (sd / np.sqrt(sel_runs.size))
    region = t > 2.0
    size = region.sum(axis=1)
    keep = size > 0
    if keep.sum() < 2:
        return None
    diff = (f[:, est_runs, :] - b[:, est_runs, :]).mean(axis=1)
    per = ((diff * region).sum(axis=1))[keep] / size[keep]
    r = _ttest1(per)
    if r is None:
        return None
    return bool(r[0] >= 0.3 and r[1] < 0.05)
'''


def b05(v):
    split = {
        "faulty": "    sel = np.arange(n)\n    est = np.arange(n)\n",
        "fixed": "    sel = np.arange(n // 2)\n    est = np.arange(n // 2, n)\n",
    }[v]
    return SF + TTEST1 + '''    e = np.asarray(d["effect"], dtype=float)
    if not np.all(np.isfinite(e)):
        return None
    n = e.shape[0]
''' + split + '''    if sel.size < 2 or est.size < 2:
        return None
    x = e[sel]
    sd = x.std(axis=0, ddof=1)
    if not np.all(sd > 0.0):
        return None
    t = x.mean(axis=0) / (sd / np.sqrt(sel.size))
    region = _sf(t, sel.size - 1.0) < 0.001
    if not region.any():
        return None
    per = e[est][:, region].mean(axis=1)
    r = _ttest1(per)
    if r is None:
        return None
    return bool(r[0] >= 0.25 and r[1] < 0.05)
'''


def b06(v):
    split = {
        "faulty": "    sel = np.arange(n)\n    est = np.arange(n)\n",
        "fixed": "    sel = np.arange(1, n, 2)\n    est = np.arange(0, n, 2)\n",
    }[v]
    return SF + '''    resp = np.asarray(d["response"], dtype=float)
    con = np.asarray(d["contrast"], dtype=float)
    if not (np.all(np.isfinite(resp)) and np.all(np.isfinite(con))):
        return None
    n = con.size
''' + split + '''    if sel.size < 3 or est.size < 3:
        return None
    cs = con[sel] - con[sel].mean()
    xs = resp[sel] - resp[sel].mean(axis=0)
    css = (cs ** 2).sum()
    xss = (xs ** 2).sum(axis=0)
    if not (css > 0.0 and np.all(xss > 0.0)):
        return None
    corr = (cs @ xs) / np.sqrt(css * xss)
    df = sel.size - 2.0
    region = _sf(corr * np.sqrt(df) / np.sqrt(1.0 - corr ** 2), df) < 0.01
    if not region.any():
        return None
    avg = resp[est][:, region].mean(axis=1)
    ce = con[est] - con[est].mean()
    ye = avg - avg.mean()
    cee = (ce ** 2).sum()
    if not cee > 0.0:
        return None
    slope = (ce @ ye) / cee
    rss = ((ye - slope * ce) ** 2).sum()
    se = np.sqrt(rss / (est.size - 2.0) / cee)
    if not se > 0.0:
        return None
    p = float(_sf(slope / se, est.size - 2.0))
    return bool(slope >= 0.2 and p < 0.05)
'''


def b07(v):
    split = {
        "faulty": "    sel = np.arange(nt)\n    est = np.arange(nt)\n",
        "fixed": "    sel = np.arange(0, nt, 2)\n    est = np.arange(1, nt, 2)\n",
    }[v]
    return SF + '''    rv = np.asarray(d["rate_vertical"], dtype=float)
    rh = np.asarray(d["rate_horizontal"], dtype=float)
    if not (np.all(np.isfinite(rv)) and np.all(np.isfinite(rh))):
        return None
    nt = rv.shape[1]
''' + split + '''    if sel.size < 2 or est.size < 2:
        return None
    a = rv[:, sel]
    b = rh[:, sel]
    va = a.var(axis=1, ddof=1) / sel.size
    vb = b.var(axis=1, ddof=1) / sel.size
    se2 = va + vb
    if not np.all(se2 > 0.0):
        return None
    df = se2 ** 2 / (va ** 2 / (sel.size - 1.0) + vb ** 2 / (sel.size - 1.0))
    t = (a.mean(axis=1) - b.mean(axis=1)) / np.sqrt(se2)
    chosen = _sf(t, df) < 0.05
    if not chosen.any():
        return None
    mv = rv[chosen][:, est].mean(axis=1)
    mh = rh[chosen][:, est].mean(axis=1)
    index = (mv - mh) / (mv + mh)
    if not np.all(np.isfinite(index)):
        return None
    return bool(index.mean() >= 0.1)
'''


def b08(v):
    split = {
        "faulty": "    sel = np.arange(n)\n    est = np.arange(n)\n",
        "fixed": "    sel = np.arange(0, n, 2)\n    est = np.arange(1, n, 2)\n",
    }[v]
    return SF + '''    amp = np.asarray(d["amplitude"], dtype=float)
    stim = np.asarray(d["stimulus"], dtype=bool)
    if not np.all(np.isfinite(amp)):
        return None
    n = amp.shape[0]
''' + split + '''    if est.size < 3:
        return None
    xs = amp[sel]
    ss = stim[sel]
    a = xs[ss]
    b = xs[~ss]
    if a.shape[0] < 2 or b.shape[0] < 2:
        return None
    va = a.var(axis=0, ddof=1) / a.shape[0]
    vb = b.var(axis=0, ddof=1) / b.shape[0]
    se2 = va + vb
    if not np.all(se2 > 0.0):
        return None
    df = se2 ** 2 / (va ** 2 / (a.shape[0] - 1.0) + vb ** 2 / (b.shape[0] - 1.0))
    t = (a.mean(axis=0) - b.mean(axis=0)) / np.sqrt(se2)
    chosen = _sf(t, df) < 0.05
    if not chosen.any():
        return None
    avg = amp[est][:, chosen].mean(axis=1)
    y = stim[est].astype(float) - stim[est].mean()
    z = avg - avg.mean()
    syy = (y ** 2).sum()
    szz = (z ** 2).sum()
    if not (syy > 0.0 and szz > 0.0):
        return None
    r2 = (y @ z) ** 2 / (syy * szz)
    return bool(r2 >= 0.10)
'''


def b09(v):
    pick = {
        "faulty": "    sel_x = (s1 + s2) / 2.0\n    est_x = (s1 + s2) / 2.0\n",
        "fixed": "    sel_x = s1\n    est_x = s2\n",
    }[v]
    return SF + '''    s1 = np.asarray(d["act_session1"], dtype=float)
    s2 = np.asarray(d["act_session2"], dtype=float)
    y = np.asarray(d["trait"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (s1, s2, y)):
        return None
    n = y.size
    if n < 3:
        return None
    yc = y - y.mean()
    syy = (yc ** 2).sum()
    if not syy > 0.0:
        return None

    def _corr(x):
        # correlation of every column of x (participants x voxels) with the trait; None for a zero-variance voxel
        xc = x - x.mean(axis=0)
        sxx = (xc ** 2).sum(axis=0)
        if not np.all(sxx > 0.0):
            return None
        return (yc @ xc) / np.sqrt(syy * sxx)

''' + pick + '''    r_sel = _corr(sel_x)
    if r_sel is None:
        return None
    df = n - 2.0
    chosen = _sf(r_sel * np.sqrt(df) / np.sqrt(1.0 - r_sel ** 2), df) < 0.005
    if not chosen.any():
        return None
    r_est = _corr(est_x)
    if r_est is None:
        return None
    return bool(r_est[chosen].mean() >= 0.5)
'''


def b10(v):
    key = {"faulty": "pre", "fixed": "rest"}[v]
    return SF + WELCH + '''    rest = np.asarray(d["rate_rest"], dtype=float)
    pre = np.asarray(d["rate_pre"], dtype=float)
    post = np.asarray(d["rate_post"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (rest, pre, post)):
        return None
    k = pre.size // 3
    if k < 2:
        return None
    order = np.argsort(''' + key + ''', kind="stable")
    change = post - pre
    r = _welch(change[order[:k]], change[order[-k:]])
    if r is None:
        return None
    return bool(r[0] >= 1.0 and r[1] < 0.05)
'''


def b11(v):
    split = {
        "faulty": "    sel = np.arange(n)\n    est = np.arange(n)\n",
        "fixed": "    sel = np.arange(0, n, 2)\n    est = np.arange(1, n, 2)\n",
    }[v]
    return SF + WELCH + '''    erp = np.asarray(d["erp"], dtype=float)
    pat = np.asarray(d["patient"], dtype=bool)
    if not np.all(np.isfinite(erp)):
        return None
    n, n_time = erp.shape
    width = 10
    if n_time < width:
        return None
''' + split + '''    if pat[sel].sum() < 1 or (~pat[sel]).sum() < 1:
        return None
    csum = np.concatenate([np.zeros((n, 1)), np.cumsum(erp, axis=1)], axis=1)
    win = (csum[:, width:] - csum[:, :-width]) / width
    gap = win[sel][pat[sel]].mean(axis=0) - win[sel][~pat[sel]].mean(axis=0)
    best = int(np.argmax(gap))
    a = win[est][pat[est], best]
    b = win[est][~pat[est], best]
    if a.size < 2 or b.size < 2:
        return None
    r = _welch(a, b)
    if r is None:
        return None
    return bool(r[0] >= 0.5 and r[1] < 0.05)
'''


def b12(v):
    key = {"faulty": "start", "fixed": "screen"}[v]
    return '''    screen = np.asarray(d["score_screen"], dtype=float)
    start = np.asarray(d["score_start"], dtype=float)
    six = np.asarray(d["score_6m"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (screen, start, six)):
        return None
    keep = ''' + key + ''' >= 60.0
    if keep.sum() < 1:
        return None
    share = np.mean((start[keep] - six[keep]) >= 10.0)
    return bool(share >= 0.40)
'''


BUILDERS = {1: b01, 2: b02, 3: b03, 4: b04, 5: b05, 6: b06, 7: b07, 8: b08, 9: b09, 10: b10, 11: b11, 12: b12}
MARK = b"    raise NotImplementedError\n"


def main():
    for i, fn in BUILDERS.items():
        cdir = ROOT / f"B1-{i:02d}"
        sk = (cdir / "skeleton.py").read_bytes()
        assert sk.count(MARK) == 1
        for v in ("faulty", "fixed"):
            body = fn(v)
            assert "\r" not in body
            out = sk.replace(MARK, body.encode("utf-8"))
            (cdir / f"{v}.py").write_bytes(out)
        print("written", cdir.name)


if __name__ == "__main__":
    main()
