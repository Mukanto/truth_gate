# World-level effect presence: population quantities averaged over many draws (no decision rule, no threshold).
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pkg"))
import numpy as np  # noqa: E402


def load(i):
    path = os.path.join(HERE, "skeletons", i + ".py")
    spec = importlib.util.spec_from_file_location("sk_" + i.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def draws(mod, world, n, seed=7):
    return [mod.STUDY.worlds[world].generate(np.random.default_rng([seed, s])) for s in range(n)]


def resid(y, x):
    X = np.column_stack([np.ones_like(x), x])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ b


def pc(a, b, c):
    ra, rb = resid(a, c), resid(b, c)
    return float(np.corrcoef(ra, rb)[0, 1])


def d052():
    m = load("D-052")
    for w in ("plus", "minus"):
        diffs, r = [], []
        for d in draws(m, w, 400):
            imp = d["post"] - d["pre"]
            diffs.append(imp[d["young"]].mean() - imp[~d["young"]].mean())
            r.append(np.corrcoef(d["pre"], d["post"])[0, 1])
        print(f"D-052 {w}: mean(young-old improvement)={np.mean(diffs):.2f} sd={np.std(diffs):.2f}  r(pre,post)={np.mean(r):.2f}")


def d055():
    m = load("D-055")
    for w in ("plus", "minus"):
        cs = []
        for d in draws(m, w, 200):
            z = (d["X"] - m._X_MEAN) / m._X_SCALE
            s = z @ m._BETA
            cs.append(np.corrcoef(s[700:], d["y"][700:])[0, 1])
        print(f"D-055 {w}: corr(y, true signal) on last 300 days mean={np.mean(cs):.3f} sd={np.std(cs):.3f}")


def d056():
    m = load("D-056")
    for w in ("plus", "minus"):
        adj, raw = [], []
        for d in draws(m, w, 300):
            a = np.log(d["oxygen_uptake"]) - 0.75 * np.log(d["body_mass"] / 300.0)
            adj.append(a.mean(axis=1) - a.mean())
            raw.append(np.log(d["oxygen_uptake"]).mean(axis=1) - np.log(d["oxygen_uptake"]).mean())
        print(f"D-056 {w}: mass-adjusted group effects {np.round(np.mean(adj, axis=0), 3)}  raw log means {np.round(np.mean(raw, axis=0), 3)}")


def d062():
    m = load("D-062")
    for w in ("plus", "minus"):
        vals = []
        for d in draws(m, w, 100):
            for s in range(12):
                vals.append(pc(np.log(d["femur"][s]), np.log(d["humerus"][s]), np.log(d["body_length"][s])))
        r_raw = np.mean([np.corrcoef(d["femur"][0], d["humerus"][0])[0, 1] for d in draws(m, w, 50)])
        print(f"D-062 {w}: mean within-species partial corr={np.mean(vals):.3f} (sd {np.std(vals):.3f}); raw within-species r={r_raw:.2f}")


def d064():
    m = load("D-064")
    for w in ("plus", "minus"):
        c1, cg = [], []
        for d in draws(m, w, 200):
            e = d["expression"]
            ez = (e - e.mean(0)) / e.std(0)
            mod1 = ez[:, 75:150].mean(1)
            c1.append(np.corrcoef(d["clinical"][:, 1], d["response"])[0, 1])
            cg.append(np.corrcoef(mod1, d["response"])[0, 1])
        print(f"D-064 {w}: corr(resp, tumour size)={np.mean(c1):.3f}  corr(resp, module-1 average)={np.mean(cg):.3f}  "
              f"resp mean={np.mean([d['response'].mean() for d in draws(m, w, 20)]):.1f}")


def d066():
    m = load("D-066")
    for w in ("plus", "minus"):
        prev, sh = [], []
        for d in draws(m, w, 100):
            X, y = d["X"], d["y"]
            Xs = (X - X.mean(0)) / X.std(0)
            prev.append(y.mean())
            sh.append(Xs[y].mean(0) - Xs[~y].mean(0))
        print(f"D-066 {w}: prevalence={np.mean(prev):.3f}  std mean diff cases-controls={np.round(np.mean(sh, axis=0), 2)}")


def d067():
    m = load("D-067")
    for w in ("plus", "minus"):
        vals, rk = [], []
        for d in draws(m, w, 400):
            vals.append(pc(np.log(d["kidney_weight"]), np.log(d["heart_weight"]), np.log(d["body_mass"])))
            rk.append(np.corrcoef(d["kidney_weight"], d["body_mass"])[0, 1])
        print(f"D-067 {w}: mean partial corr={np.mean(vals):.3f} sd={np.std(vals):.3f}  r(kidney, mass)={np.mean(rk):.2f}")


def d068():
    m = load("D-068")
    for w in ("plus", "minus"):
        means = []
        for d in draws(m, w, 200):
            bs = []
            for p in range(25):
                X = np.column_stack([np.ones(40), d["head_width"][p], d["body_length"][p]])
                b, *_ = np.linalg.lstsq(X, d["wing_length"][p], rcond=None)
                bs.append(b[1])
            means.append(np.mean(bs))
        print(f"D-068 {w}: mean over populations of within-pop HW coefficient: avg={np.mean(means):.3f} sd={np.std(means):.3f}")


if __name__ == "__main__":
    for f in (d052, d055, d056, d062, d064, d066, d067, d068):
        f()
