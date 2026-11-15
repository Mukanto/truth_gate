import sys, json, time, ast
SB = r"E:\Claude Projects\Kapi\phase_c_private\fable\batch04"
sys.path.insert(0, SB + r"\pkg")
import numpy as np
from truth_gate.study import load_study
import types
briefs = json.load(open(SB + r"\BATCH.json", encoding="utf-8"))
mods = {}
for b in briefs:
    i = b["id"]; p = SB + rf"\skeletons\{i}.py"
    src = open(p, "rb").read()
    tree = ast.parse(src)
    assert ast.get_docstring(tree, clean=False) == f"{i}: {b['claim']}", i
    bad = [type(n).__name__ for n in tree.body[1:] if not isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef))]
    assert not bad, (i, bad)
    m = types.ModuleType("m"); exec(compile(src, p, "exec"), m.__dict__); mods[i] = m
    S = load_study(p, src)
    assert S.name == i
    keys = [k["key"] for k in b["data_keys"]]
    ref = None; tmax = 0
    for s in range(40):
        for w in ("plus", "minus"):
            t = time.perf_counter(); d = S.worlds[w].generate(np.random.default_rng(s)); tmax = max(tmax, time.perf_counter() - t)
            assert list(d) == keys, (i, list(d))
            sh = {k: (v.shape, str(v.dtype)) for k, v in d.items()}
            if ref is None: ref = sh; 
            assert sh == ref, (i, sh)
            assert all(np.isfinite(v).all() for v in d.values())
            assert all(v.dtype in (np.float64, np.bool_) for v in d.values())
            for c in S.controls:
                t = time.perf_counter(); e = c.transform(d, np.random.default_rng(1000 + s)); tmax = max(tmax, time.perf_counter() - t)
                assert list(e) == keys and {k: (v.shape, str(v.dtype)) for k, v in e.items()} == ref
                assert any(not np.array_equal(e[k], d[k]) for k in keys), (i, c.id)
                assert all(d2 is not None for d2 in e.values())
        dp = S.worlds["plus"].generate(np.random.default_rng(s)); dm = S.worlds["minus"].generate(np.random.default_rng(s))
        assert any(not np.array_equal(dp[k], dm[k]) for k in keys)
    print(i, "ok", ref, "max ms %.2f" % (tmax * 1e3))

def auc(score, pos):
    r = np.argsort(np.argsort(score)).astype(float)  # ties handled roughly below
    # midranks
    u, inv, cnt = np.unique(score, return_inverse=True, return_counts=True)
    cs = np.cumsum(cnt); mid = cs - (cnt - 1) / 2.0
    r = mid[inv]
    n1 = pos.sum(); n0 = (~pos).sum()
    return (r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)

# C46 population calibration
m = mods["C46"]; m.N_PATIENTS = 200000
for w in (m.plus, m.minus):
    x = w(np.random.default_rng(1))["item_scores"]; tot = x[:, 1:].sum(1); pos = tot >= 12
    print("C46 pop", w.__name__, "prev %.3f" % pos.mean(), "AUC %.3f" % auc(x[:, 0], pos), "item1 mean %.3f" % x[:, 0].mean())
# C47 oracle
m = mods["C47"]
for w in (m.plus, m.minus):
    a = []
    for s in range(50):
        d = w(np.random.default_rng(s)); z = (d["patch_features"] - m.FEATURE_OFFSET) / m.FEATURE_SCALE
        sc = (z @ m.SIGNATURE).ravel(); a.append(auc(sc, np.repeat(d["malignant"], 10)))
    print("C47 oracle patch AUC", w.__name__, "%.3f +- %.3f" % (np.mean(a), np.std(a)))
# C49 oracle
m = mods["C49"]; m.N_CHILDREN = 200000
for w in (m.plus, m.minus):
    d = w(np.random.default_rng(2)); z = (d["speech_measures"] - m.MEASURE_OFFSET) / m.MEASURE_SCALE
    z = z - z[:, 10:].mean(1, keepdims=True)
    sc = z @ m.LIABILITY_LOADING; y = d["diagnosis"]
    best = max(0.5 * ((sc[y] > t).mean() + (sc[~y] <= t).mean()) for t in np.linspace(-2, 2, 81))
    sv = d["severity_rating"]
    print("C49 pop", w.__name__, "prev %.3f oracle BA %.3f AUC %.3f; severity AUC %.3f, sev range %.1f-%.1f clipfrac %.4f" % (y.mean(), best, auc(sc, y), auc(sv, y), sv.min(), sv.max(), ((sv==0)|(sv==10)).mean()))
# C50
m = mods["C50"]
for w in (m.plus, m.minus):
    f = []; n = []; rtm = []
    for s in range(300):
        x = w(np.random.default_rng(s))["sbp"]; sel = x[:, 0] >= 160
        f.append((x[sel, 1] - x[sel, 2]).mean()); n.append(sel.sum()); rtm.append((x[sel, 0] - x[sel, 1]).mean())
    f = np.array(f)
    print("C50", w.__name__, "n sel %.0f (min %d)" % (np.mean(n), min(n)), "fall2->3 %.2f sd %.2f P(>=8) %.3f; fall1->2 %.2f" % (f.mean(), f.std(), (f >= 8).mean(), np.mean(rtm)))
# C51 signal share
m = mods["C51"]
sh = []; c = []
for s in range(100):
    d = m.plus(np.random.default_rng(s)); sig = d["drivers"] @ m.BETA
    sh.append(sig.var() / d["demand"].var())
    d2 = m.minus(np.random.default_rng(s)); c.append(np.corrcoef(d2["drivers"] @ m.BETA, d2["demand"])[0, 1])
print("C51 signal share %.3f sd %.3f; demand mean %.0f sd %.0f; minus corr(sig,dem) %.3f sd %.3f" % (np.mean(sh), np.std(sh), d["demand"].mean(), d["demand"].std(), np.mean(c), np.std(c)))
print("C51 driver sds", d["drivers"].std(0).round(2), "means", d["drivers"].mean(0).round(2))
# C52
m = mods["C52"]
for w in (m.plus, m.minus):
    dd = []
    for s in range(300):
        d = w(np.random.default_rng(s)); x = np.arange(8) - 3.5
        sl = d["rt"] @ x / (x @ x); p = d["patient"]
        dd.append((sl[~p].mean() - sl[p].mean()) / np.sqrt((sl[p].var(ddof=1) + sl[~p].var(ddof=1)) / 15))
    dd = np.array(dd); print("C52", w.__name__, "t mean %.2f; frac t<-2.05 %.3f" % (dd.mean(), (dd < -2.05).mean()), "rt min %.0f" % d["rt"].min())
# C53 population
m = mods["C53"]; m.N_PARTICIPANTS = 400000
def pc(a, b, c):
    ra = a - np.polyval(np.polyfit(c, a, 1), c); rb = b - np.polyval(np.polyfit(c, b, 1), c)
    return np.corrcoef(ra, rb)[0, 1]
for w in (m.plus, m.minus):
    d = w(np.random.default_rng(3)); A, C, G = d["albumin_excretion"], d["creatinine_excretion"], d["age"]
    print("C53 pop", w.__name__, "partial raw %.3f log %.3f; marginal r(alb,age) %.3f r(cre,age) %.3f r(alb,cre) %.3f; alb median %.1f p99 %.1f; cre min %.0f" % (pc(A, G, C), pc(np.log(A), G, np.log(C)), np.corrcoef(A, G)[0, 1], np.corrcoef(C, G)[0, 1], np.corrcoef(A, C)[0, 1], np.median(A), np.quantile(A, .99), C.min()))
# C54 oracle
m = mods["C54"]; resp = m.RESPONSE > 0
print("C54 n responsive", resp.sum(), "mean response", m.RESPONSE[resp].mean().round(2))
for w in (m.plus, m.minus):
    r2 = []; r2h = []
    for s in range(300):
        d = w(np.random.default_rng(s)); y = d["amplitude"][:, resp].mean(1)
        r2.append(np.corrcoef(y, d["stimulus"])[0, 1] ** 2); r2h.append(np.corrcoef(y[:50], d["stimulus"][:50])[0, 1] ** 2)
    print("C54 oracle R2", w.__name__, "%.3f; P(>=.1) %.3f; half-trials P %.3f" % (np.mean(r2), np.mean(np.array(r2) >= .1), np.mean(np.array(r2h) >= .1)))
