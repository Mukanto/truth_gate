from helpers import *

CASES = {}

# ---------------------------------------------------------------- B1-01
CASES["B1-01"] = dict(helpers=[H_LG], body='''
    face = np.asarray(d["face"], dtype=float)
    house = np.asarray(d["house"], dtype=float)
    if not (np.all(np.isfinite(face)) and np.all(np.isfinite(house))):
        return None
    c = face - house                                           # (subjects, runs, voxels)
    zc = 1.6449                                                # one-sided p < 0.05, uncorrected
@@V@@
    vals = []
    for sel_map, ev_map in folds:
        scale = np.sqrt(np.mean(sel_map ** 2))
        if not scale > 0:
            return None
        sel = sel_map > zc * scale                             # voxels that respond more to faces than to houses
        cnt = sel.sum(axis=1)
        m = np.where(cnt > 0, np.where(sel, ev_map, 0.0).sum(axis=1) / np.maximum(cnt, 1), np.nan)
        vals.append(m)
    stack = np.vstack(vals)
    okm = np.isfinite(stack)
    k = okm.sum(axis=0)
    per = np.where(okm, stack, 0.0).sum(axis=0) / np.maximum(k, 1)
    x = per[k > 0]                                             # per-subject mean over the voxels
    if len(x) < 5:
        return None
    sd = x.std(ddof=1)
    if not sd > 0:
        return None
    t = x.mean() / (sd / np.sqrt(len(x)))
    return bool(x.mean() >= 0.30 and _tsf(t, len(x) - 1) < 0.05)
''',
 faulty='''    folds = [(c.mean(axis=1), c.mean(axis=1))]''',
 fixed='''    folds = [(c[:, 0], c[:, 1]), (c[:, 1], c[:, 0])]''')

# ---------------------------------------------------------------- B1-02
CASES["B1-02"] = dict(helpers=[H_LG], body='''
    r = np.asarray(d["rate"], dtype=float)
    if not np.all(np.isfinite(r)):
        return None
    n, o, _ = r.shape
@@V@@
    k = sel_r.shape[2]
    mg = sel_r.mean(axis=2)                                    # (neurons, orientations)
    ssb = k * ((mg - mg.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    ssw = ((sel_r - mg[:, :, None]) ** 2).sum(axis=(1, 2))
    dfb, dfw = o - 1, o * (k - 1)
    p = np.ones(n)
    for i in range(n):
        if ssw[i] > 0:
            f = (ssb[i] / dfb) / (ssw[i] / dfw)
            p[i] = _ib(dfw / (dfw + dfb * f), 0.5 * dfw, 0.5 * dfb)   # one-way ANOVA across orientations
    tuned = p < 0.05
    if not tuned.any():
        return None
    pref = np.argmax(mg, axis=1)
    orth = (pref + o // 2) % o
    em = ev_r.mean(axis=2)
    rp = em[np.arange(n), pref]
    ro = em[np.arange(n), orth]
    den = rp + ro
    idx = np.clip(np.where(den > 0, (rp - ro) / np.where(den > 0, den, 1.0), 0.0), -1.0, 1.0)   # the index is bounded by construction
    return bool(idx[tuned].mean() >= 0.25)
''',
 faulty='''    sel_r, ev_r = r, r''',
 fixed='''    sel_r, ev_r = r[:, :, 0::2], r[:, :, 1::2]''')

# ---------------------------------------------------------------- B1-03
CASES["B1-03"] = dict(helpers=[H_LG], body='''
    s = np.asarray(d["score"], dtype=float)
    if not np.all(np.isfinite(s)):
        return None
    n = s.shape[0]
@@V@@
    order = np.argsort(split, kind="stable")
    low, up = order[: n // 2], order[n // 2:]                  # lower-scoring and higher-scoring half
    imp = s[:, -1] - s[:, 0]                                   # late block minus early block
    a, b = imp[low], imp[up]
    if len(a) < 3 or len(b) < 3:
        return None
    sp2 = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)
    if not sp2 > 0:
        return None
    diff = a.mean() - b.mean()
    t = diff / np.sqrt(sp2 * (1.0 / len(a) + 1.0 / len(b)))
    return bool(diff >= 4.0 and _tsf(t, len(a) + len(b) - 2) < 0.05)
''',
 faulty='''    split = s[:, 0]''',
 fixed='''    split = s[:, 1]''')

# ---------------------------------------------------------------- B1-04
CASES["B1-04"] = dict(helpers=[H_LG, H_TQ, H_CORR], body='''
    act = np.asarray(d["act"], dtype=float)
    trait = np.asarray(d["trait"], dtype=float)
    if not (np.all(np.isfinite(act)) and np.all(np.isfinite(trait))):
        return None
    allidx = np.arange(act.shape[0])
@@V@@
    means = []
    for sel_idx, ev_idx in folds:
        if not (np.var(trait[sel_idx]) > 0 and np.var(trait[ev_idx]) > 0):
            return None
        r_sel = _corr(act[sel_idx], trait[sel_idx])
        df = len(sel_idx) - 2
        tt = r_sel * np.sqrt(df / np.maximum(1.0 - r_sel ** 2, 1e-12))
        keep = (r_sel > 0) & (tt > _tq(0.005, df))             # positive, two-sided p < 0.01
        if keep.any():
            means.append(_corr(act[ev_idx], trait[ev_idx])[keep].mean())
    if not means:
        return None
    return bool(np.mean(means) >= 0.50)
''',
 faulty='''    folds = [(allidx, allidx)]''',
 fixed='''    folds = [(allidx[0::2], allidx[1::2]), (allidx[1::2], allidx[0::2])]''')

# ---------------------------------------------------------------- B1-05
CASES["B1-05"] = dict(helpers=[H_LG, H_TQ, H_CORR], body='''
    act = np.asarray(d["act"], dtype=float)
    trait = np.asarray(d["trait"], dtype=float)
    if not (np.all(np.isfinite(act)) and np.all(np.isfinite(trait))):
        return None
    n = act.shape[0]
@@V@@
    if not np.var(trait) > 0:
        return None
    r_sel = _corr(sel_act, trait)
    tt = r_sel * np.sqrt((n - 2) / np.maximum(1.0 - r_sel ** 2, 1e-12))
    keep = (r_sel > 0) & (tt > _tq(0.005, n - 2))              # positive, two-sided p < 0.01
    if not keep.any():
        return None
    m = ev_act[:, keep].mean(axis=1)
    if not np.var(m) > 0:
        return None
    zm = (m - m.mean()) / m.std()
    zt = (trait - trait.mean()) / trait.std()
    slope = (zm * zt).sum() / (zm * zm).sum()                  # least-squares slope of z(trait) on z(activity)
    ts = slope * np.sqrt((n - 2) / max(1.0 - slope ** 2, 1e-12))
    return bool(slope >= 0.50 and _tsf(ts, n - 2) < 0.05)
''',
 faulty='''    sel_act, ev_act = act.mean(axis=1), act.mean(axis=1)''',
 fixed='''    sel_act, ev_act = act[:, 0], act[:, 1]''')

# ---------------------------------------------------------------- B1-06
CASES["B1-06"] = dict(helpers=[H_LG, H_WELCH], body='''
    react = np.asarray(d["react"], dtype=float)
    high = np.asarray(d["high_anx"], dtype=bool)
    if not np.all(np.isfinite(react)):
        return None
    n = react.shape[0]
    ih, il = np.flatnonzero(high), np.flatnonzero(~high)
    if len(ih) < 3 or len(il) < 3:
        return None
    allidx = np.arange(n)
    half_a = np.concatenate([ih[0::2], il[0::2]])
    half_b = np.concatenate([ih[1::2], il[1::2]])
@@V@@
    val = np.full(n, np.nan)
    for sel_idx, ev_idx in folds:
        gh = sel_idx[high[sel_idx]]
        gl = sel_idx[~high[sel_idx]]
        if len(gh) < 3 or len(gl) < 3:
            return None
        t, df = _welch(react[gh], react[gl])
        keep = np.array([(t[v] > 0) and (_tsf(t[v], df[v]) < 0.05) for v in range(len(t))])   # higher in the high group, one-sided p < 0.05
        if not keep.any():
            return None
        val[ev_idx] = react[ev_idx][:, keep].mean(axis=1)
    a, b = val[high], val[~high]
    if not (a.var(ddof=1) + b.var(ddof=1) > 0):
        return None
    t_fin, _ = _welch(a, b)
    return bool(t_fin >= 3.0)
''',
 faulty='''    folds = [(allidx, allidx)]''',
 fixed='''    folds = [(half_a, half_b), (half_b, half_a)]''')

# ---------------------------------------------------------------- B1-07
CASES["B1-07"] = dict(helpers=[H_LG, H_WELCH], body='''
    expr = np.asarray(d["expr"], dtype=float)
    tum = np.asarray(d["tumour"], dtype=bool)
    if not np.all(np.isfinite(expr)):
        return None
    n = expr.shape[0]
    it, inn = np.flatnonzero(tum), np.flatnonzero(~tum)
    if len(it) < 4 or len(inn) < 4:
        return None
    allidx = np.arange(n)
    half_a = np.concatenate([it[0::2], inn[0::2]])
    half_b = np.concatenate([it[1::2], inn[1::2]])
@@V@@
    vals = []
    for sel_idx, ev_idx in folds:
        st, sn = sel_idx[tum[sel_idx]], sel_idx[~tum[sel_idx]]
        et, en = ev_idx[tum[ev_idx]], ev_idx[~tum[ev_idx]]
        t, df = _welch(expr[st], expr[sn])
        keep = np.array([2.0 * _tsf(abs(t[g]), df[g]) < 0.05 for g in range(len(t))])   # two-sided p < 0.05
        if keep.any():
            sign = np.sign(expr[st].mean(axis=0) - expr[sn].mean(axis=0))
            fc = expr[et].mean(axis=0) - expr[en].mean(axis=0)
            vals.append(np.mean((sign * fc)[keep]))
    if not vals:
        return None
    return bool(np.mean(vals) >= 0.5)
''',
 faulty='''    folds = [(allidx, allidx)]''',
 fixed='''    folds = [(half_a, half_b), (half_b, half_a)]''')

# ---------------------------------------------------------------- B1-08
CASES["B1-08"] = dict(helpers=[H_LG], body='''
    pre = np.asarray(d["pre"], dtype=float)
    post = np.asarray(d["post"], dtype=float)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    nt = pre.shape[1]
@@V@@
    diff = post - pre
    ds = diff[:, sel_t]
    k = ds.shape[1]
    sd = ds.std(axis=1, ddof=1)
    t = np.where(sd > 0, ds.mean(axis=1) / (np.where(sd > 0, sd, 1.0) / np.sqrt(k)), 0.0)
    resp = np.array([(x > 0) and (_tsf(x, k - 1) < 0.05) for x in t])   # post > pre, one-sided p < 0.05
    if resp.sum() < 5:
        return None
    prop = np.mean(diff[resp][:, ev_t].mean(axis=1) > 0)
    return bool(prop >= 0.70)
''',
 faulty='''    sel_t, ev_t = np.arange(nt), np.arange(nt)''',
 fixed='''    sel_t, ev_t = np.arange(nt // 2), np.arange(nt // 2, nt)''')

# ---------------------------------------------------------------- B1-09
CASES["B1-09"] = dict(helpers=[H_LG], body='''
    base = np.asarray(d["base"], dtype=float)
    post = np.asarray(d["post"], dtype=float)
    if not (np.all(np.isfinite(base)) and np.all(np.isfinite(post))):
        return None
@@V@@
    k = len(sel_b) // 3
    if k < 5:
        return None
    low = np.argsort(sel_b, kind="stable")[:k]                 # the third of the neurons with the lowest baseline
    inc = post[low] - ref_b[low]
    sd = inc.std(ddof=1)
    if not sd > 0:
        return None
    t = inc.mean() / (sd / np.sqrt(k))
    return bool(inc.mean() >= 2.0 and _tsf(t, k - 1) < 0.05)
''',
 faulty='''    sel_b, ref_b = base.mean(axis=1), base.mean(axis=1)''',
 fixed='''    sel_b, ref_b = base[:, 0], base[:, 1]''')

# ---------------------------------------------------------------- B1-10
CASES["B1-10"] = dict(helpers=[H_LG, H_WELCH], body='''
    sbp = np.asarray(d["sbp"], dtype=float)
    drug = np.asarray(d["drug"], dtype=bool)
    if not np.all(np.isfinite(sbp)):
        return None
    change = sbp[:, 0] - sbp[:, 1]                             # lowering over 12 weeks
    hi = sbp[:, 0] >= 150.0
@@V@@
''',
 faulty='''    x = change[hi & drug]
    if len(x) < 5:
        return None
    sd = x.std(ddof=1)
    if not sd > 0:
        return None
    t = x.mean() / (sd / np.sqrt(len(x)))
    return bool(x.mean() >= 5.0 and _tsf(t, len(x) - 1) < 0.05)''',
 fixed='''    a, b = change[hi & drug], change[hi & ~drug]
    if len(a) < 3 or len(b) < 3:
        return None
    if not (a.var(ddof=1) + b.var(ddof=1) > 0):
        return None
    t, df = _welch(a, b)
    diff = a.mean() - b.mean()
    return bool(diff >= 5.0 and _tsf(t, df) < 0.05)''')

# ---------------------------------------------------------------- B1-11
CASES["B1-11"] = dict(helpers=[], body='''
    s = np.asarray(d["score"], dtype=float)
    if not np.all(np.isfinite(s)):
        return None
    top = np.argsort(-s[:, 0], kind="stable")[: s.shape[0] // 5]    # top fifth of the first assessment
    if len(top) < 5:
        return None
@@V@@
    return bool(np.mean(s[top, 2] < ref[top]) >= 0.70)
''',
 faulty='''    ref = s[:, 0]''',
 fixed='''    ref = s[:, 1]''')

# ---------------------------------------------------------------- B1-12
CASES["B1-12"] = dict(helpers=[H_LG], body='''
    s = np.asarray(d["score"], dtype=float)
    if not np.all(np.isfinite(s)):
        return None
    low = np.argsort(s[:, 0], kind="stable")[: s.shape[0] // 5]     # lowest fifth of the autumn test
    if len(low) < 5:
        return None
@@V@@
    gain = s[low, 2] - ref[low]
    sd = gain.std(ddof=1)
    if not sd > 0:
        return None
    t = gain.mean() / (sd / np.sqrt(len(low)))
    return bool(gain.mean() >= 5.0 and _tsf(t, len(low) - 1) < 0.05)
''',
 faulty='''    ref = s[:, 0]''',
 fixed='''    ref = s[:, 1]''')
