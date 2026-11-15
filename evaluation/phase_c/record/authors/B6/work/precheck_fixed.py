"""Scratch pre-check of the FIXED criteria only (plain Python, no Truth_Gate run).
For each case: hold rate of fixed.criterion on plus / minus / control(plus) / noise / zeros / shuffle probes, agreement with an
independent scipy reference on plus and minus samples, and timing (t, g) with the estimate 2*200*(S+1)*(t+g).
Never imports or runs faulty.py.

Usage: py work\\precheck_fixed.py [n_samples]
"""
import importlib.util
import sys
import time
import pathlib
import numpy as np
from scipy import stats

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pkg"))   # pkg first, so the case files load

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400


def load(case):
    spec = importlib.util.spec_from_file_location("fixed_" + case.replace("-", "_"), ROOT / "cases" / case / "fixed.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# independent references (scipy) for the fixed decision -------------------------------------------------------
def ref_ttest(x, y, equal_var, sign):
    r = stats.ttest_ind(x, y, equal_var=equal_var)
    return bool(sign * (x.mean() - y.mean()) > 0 and r.pvalue < 0.05)


REF = {
    "B6-01": lambda d: ref_ttest(d["activity"][d["exposed"]].mean(1), d["activity"][~d["exposed"]].mean(1), True, +1),
    "B6-02": lambda d: ref_ttest(d["responded"][d["treated"]].mean(1), d["responded"][~d["treated"]].mean(1), False, +1),
    "B6-03": lambda d: (lambda r: bool(r.slope > 0 and r.pvalue < 0.05))(stats.linregress(d["dose"], d["spine_density"].mean((1, 2)))),
    "B6-04": lambda d: ref_ttest(d["weight_gain"][d["treated"]].mean(1), d["weight_gain"][~d["treated"]].mean(1), False, -1),
    "B6-05": lambda d: ref_ttest((d["post"] - d["pre"])[d["trained"]], (d["post"] - d["pre"])[~d["trained"]], True, +1),
    "B6-06": lambda d: (lambda s: ref_ttest(s[~d["patient"]], s[d["patient"]], True, -1))(
        np.array([np.polyfit(np.arange(d["rt"].shape[1]), row, 1)[0] for row in d["rt"]])),
    "B6-07": lambda d: (lambda diff: bool(diff.mean() > 0 and stats.ttest_1samp(diff, 0.0).pvalue < 0.05))(
        (d["task_a"] - d["rest_a"]) - (d["task_b"] - d["rest_b"])),
    "B6-08": lambda d: ref_ttest(d["density"][d["treated"]].mean(1), d["density"][~d["treated"]].mean(1), False, -1),
    "B6-09": lambda d: (lambda x, y: (lambda u: bool(u.statistic > x.size * y.size / 2 and u.pvalue < 0.05))(
        stats.mannwhitneyu(x, y, alternative="two-sided", method="asymptotic", use_continuity=True)))(
        d["abundance"][d["treated"]].mean(1), d["abundance"][~d["treated"]].mean(1)),
    "B6-10": lambda d: ref_ttest(d["latency"][d["treated"]].mean(1), d["latency"][~d["treated"]].mean(1), True, +1),
    "B6-11": lambda d: (lambda r: bool(r[0] > 0 and r[1] < 0.05))(stats.pearsonr(d["heart_rate"].mean(1), d["cortisol"].mean(1))),
    "B6-12": lambda d: (lambda ra, rb, na, nb: bool(ra > rb and abs((np.arctanh(ra) - np.arctanh(rb)) / np.sqrt(1 / (na - 3) + 1 / (nb - 3))) > stats.norm.isf(0.025)))(
        stats.pearsonr(d["task_score"][d["group_a"]], d["symptom_score"][d["group_a"]])[0],
        stats.pearsonr(d["task_score"][~d["group_a"]], d["symptom_score"][~d["group_a"]])[0],
        int(d["group_a"].sum()), int((~d["group_a"]).sum())),
}


def noise_like(d, rng):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        out[k] = (rng.random(v.shape) < 0.5) if v.dtype == bool else rng.normal(size=v.shape)
    return out


def zeros_like(d):
    return {k: np.zeros_like(np.asarray(v)) for k, v in d.items()}


def rate(vals):
    vals = list(vals)
    holds = sum(1 for v in vals if v is True)
    nones = sum(1 for v in vals if v is None)
    return f"{holds}/{len(vals)}={holds / len(vals):.3f} (None {nones})"


cases = sorted(p.name for p in (ROOT / "cases").iterdir() if p.is_dir())
if len(sys.argv) > 2:
    cases = sys.argv[2:]
for case in cases:
    m = load(case)
    crit = m.criterion
    st = m.STUDY
    rng = np.random.default_rng(20261115)
    plus_s = [m.plus(rng) for _ in range(N)]
    minus_s = [m.minus(rng) for _ in range(N)]
    r_plus = [crit(d) for d in plus_s]
    r_minus = [crit(d) for d in minus_s]
    ctrl = st.controls[0]
    r_ctrl = [crit(ctrl.transform(d, rng)) for d in plus_s]
    r_noise = [crit(noise_like(d, rng)) for d in plus_s]
    r_zero = [crit(zeros_like(d)) for d in plus_s[:20]]
    line = f"{case} {st.name}  plus {rate(r_plus)}  minus {rate(r_minus)}  control({ctrl.id}) {rate(r_ctrl)}  noise {rate(r_noise)}  zeros {rate(r_zero)}"
    print(line)
    for a, b in (st.relational or []):
        r_sh = []
        for d in plus_s:
            d2 = dict(d)
            d2[b] = np.asarray(d[b])[rng.permutation(np.asarray(d[b]).shape[0])]
            r_sh.append(crit(d2))
        print(f"   shuffle({a},{b}) {rate(r_sh)}")
    # agreement with the scipy reference (plus and minus samples)
    ref = REF[case]
    dis = 0
    for d, r in zip(plus_s + minus_s, r_plus + r_minus):
        if r is not None and bool(ref(d)) != r:
            dis += 1
    print(f"   scipy reference disagreements on {2 * N} samples: {dis}")
    # timing: t = mean of calls on plus samples, g = mean plus generation
    k = min(N, 100)
    t0 = time.perf_counter()
    for d in plus_s[:k]:
        crit(d)
    t = (time.perf_counter() - t0) / k
    rng2 = np.random.default_rng(7)
    t0 = time.perf_counter()
    for _ in range(k):
        m.plus(rng2)
    g = (time.perf_counter() - t0) / k
    S = len(st.worlds) + len(st.controls) + len(getattr(st, "premises", []) or []) + len(st.relational or []) + 2
    est = 2 * 200 * (S + 1) * (t + g)
    print(f"   timing t={t * 1e3:.3f} ms  g={g * 1e3:.3f} ms  S={S}  estimate={est:.2f} s  (calls {k})")
