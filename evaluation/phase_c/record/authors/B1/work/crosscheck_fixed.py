"""Scratch: cross-check of the FIXED criteria against independent scipy re-implementations of the same fixed rules
(never loads faulty.py). Disagreements in the decision are counted over plus and minus samples."""
import sys
sys.path.insert(0, r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\work")
import numpy as np
from scipy import stats
from precheck_fixed import load_fixed


def ref01(d):
    k = d["index_start"] >= 20
    fall = d["index_start"] - d["index_week12"]
    a, b = fall[k & d["active"]], fall[k & ~d["active"]]
    r = stats.ttest_ind(a, b, equal_var=False, alternative="greater")
    return bool(a.mean() - b.mean() >= 3 and r.pvalue < 0.05)


def ref02(d):
    up = d["bmd_m12_scan1"] > d["bmd_start"]
    dn = d["bmd_m12_scan1"] < d["bmd_start"]
    sec = 100 * (d["bmd_m24"] - d["bmd_m12_scan2"]) / d["bmd_m12_scan2"]
    r = stats.ttest_ind(sec[up], sec[dn], equal_var=False, alternative="greater")
    return bool(sec[up].mean() - sec[dn].mean() >= 0.5 and r.pvalue < 0.05)


def ref03(d):
    s = d["sbp"]
    k = s[:, 0] >= 160
    fall = s[k, 1] - s[k, 2]
    r = stats.ttest_1samp(fall, 0.0, alternative="greater")
    return bool(fall.mean() >= 8 and r.pvalue < 0.05)


def ref04(d):
    f, b, h = d["resp_faces"], d["resp_bodies"], d["resp_houses"]
    per = []
    for s in range(f.shape[0]):
        c = (f[s, 1::2] - h[s, 1::2])
        t = stats.ttest_1samp(c, 0.0, axis=0, alternative="greater").statistic
        reg = t > 2.0
        if reg.any():
            per.append((f[s, 0::2][:, reg] - b[s, 0::2][:, reg]).mean())
    per = np.array(per)
    r = stats.ttest_1samp(per, 0.0, alternative="greater")
    return bool(per.mean() >= 0.3 and r.pvalue < 0.05)


def ref05(d):
    e = d["effect"]
    p = stats.ttest_1samp(e[:20], 0.0, axis=0, alternative="greater").pvalue
    reg = p < 0.001
    if not reg.any():
        return None
    per = e[20:][:, reg].mean(axis=1)
    r = stats.ttest_1samp(per, 0.0, alternative="greater")
    return bool(per.mean() >= 0.25 and r.pvalue < 0.05)


def ref06(d):
    con, resp = d["contrast"], d["response"]
    sel, est = np.arange(1, 240, 2), np.arange(0, 240, 2)
    reg = []
    for v in range(resp.shape[1]):
        r = stats.pearsonr(con[sel], resp[sel, v], alternative="greater")
        reg.append(r.pvalue < 0.01)
    reg = np.array(reg)
    if not reg.any():
        return None
    avg = resp[est][:, reg].mean(axis=1)
    lr = stats.linregress(con[est], avg, alternative="greater")
    return bool(lr.slope >= 0.2 and lr.pvalue < 0.05)


def ref07(d):
    v, h = d["rate_vertical"], d["rate_horizontal"]
    sel, est = np.arange(0, 15, 2), np.arange(1, 15, 2)
    p = stats.ttest_ind(v[:, sel], h[:, sel], axis=1, equal_var=False, alternative="greater").pvalue
    ch = p < 0.05
    if not ch.any():
        return None
    mv, mh = v[ch][:, est].mean(1), h[ch][:, est].mean(1)
    return bool(((mv - mh) / (mv + mh)).mean() >= 0.1)


def ref08(d):
    a, s = d["amplitude"], d["stimulus"]
    sel, est = np.arange(0, 100, 2), np.arange(1, 100, 2)
    p = stats.ttest_ind(a[sel][s[sel]], a[sel][~s[sel]], axis=0, equal_var=False, alternative="greater").pvalue
    ch = p < 0.05
    if not ch.any():
        return None
    avg = a[est][:, ch].mean(1)
    lr = stats.linregress(s[est].astype(float), avg)
    return bool(lr.rvalue ** 2 >= 0.10)


def ref09(d):
    s1, s2, y = d["act_session1"], d["act_session2"], d["trait"]
    r1 = np.array([stats.pearsonr(s1[:, v], y).statistic for v in range(s1.shape[1])])
    p = np.array([stats.pearsonr(s1[:, v], y, alternative="greater").pvalue for v in range(s1.shape[1])])
    ch = p < 0.005
    if not ch.any():
        return None
    r2 = np.array([stats.pearsonr(s2[:, v], y).statistic for v in np.where(ch)[0]])
    return bool(r2.mean() >= 0.5)


def ref10(d):
    o = np.argsort(d["rate_rest"], kind="stable")
    ch = d["rate_post"] - d["rate_pre"]
    lo, hi = ch[o[:80]], ch[o[-80:]]
    r = stats.ttest_ind(lo, hi, equal_var=False, alternative="greater")
    return bool(lo.mean() - hi.mean() >= 1.0 and r.pvalue < 0.05)


def ref11(d):
    erp, pat = d["erp"], d["patient"]
    sel, est = np.arange(0, 60, 2), np.arange(1, 60, 2)
    win = np.stack([erp[:, i:i + 10].mean(1) for i in range(191)], axis=1)
    gap = win[sel][pat[sel]].mean(0) - win[sel][~pat[sel]].mean(0)
    b = int(np.argmax(gap))
    a_, c_ = win[est][pat[est], b], win[est][~pat[est], b]
    r = stats.ttest_ind(a_, c_, equal_var=False, alternative="greater")
    return bool(a_.mean() - c_.mean() >= 0.5 and r.pvalue < 0.05)


def ref12(d):
    k = d["score_screen"] >= 60
    return bool(np.mean((d["score_start"][k] - d["score_6m"][k]) >= 10) >= 0.40)


REFS = {1: ref01, 2: ref02, 3: ref03, 4: ref04, 5: ref05, 6: ref06, 7: ref07, 8: ref08, 9: ref09, 10: ref10, 11: ref11, 12: ref12}

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    for i, ref in REFS.items():
        cid = f"B1-{i:02d}"
        mod = load_fixed(cid)
        fn = mod.criterion
        rng = np.random.default_rng(81000 + i)
        dis = 0
        tot = 0
        for w in ("plus", "minus"):
            for _ in range(n):
                d = mod.STUDY.worlds[w].generate(rng)
                a = fn(d)
                b = ref(d)
                tot += 1
                if a != b:
                    dis += 1
        print(cid, "disagreements", dis, "of", tot)
