# Scratch: descriptive and population-level (pooled over many draws) checks that the modelled effect is present in
# plus and absent in minus, and that values are realistic. No per-dataset decision rule, no model fitting, no gate.
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pkg"))
import numpy as np  # noqa: E402


def load_mod(bid):
    path = os.path.join(HERE, "skeletons", f"{bid}.py")
    spec = importlib.util.spec_from_file_location("sk_" + bid.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def draws(mod, world, n, seed=0):
    return [getattr(mod, world)(np.random.default_rng([seed, i])) for i in range(n)]


def q(a):
    return np.round(np.quantile(a, [0.0, 0.05, 0.5, 0.95, 1.0]), 2)


# D-007: realism of survival; average |gene-survival correlation| (descriptive)
m = load_mod("D-007")
for w in ("plus", "minus"):
    ds = draws(m, w, 30)
    s = np.concatenate([d["survival_months"] for d in ds])
    e = ds[0]["expression"]
    ac = []
    for d in ds:
        x = d["expression"] - d["expression"].mean(0)
        ls = np.log(d["survival_months"]); ls = ls - ls.mean()
        r = (x * ls[:, None]).sum(0) / np.sqrt((x ** 2).sum(0) * (ls ** 2).sum())
        ac.append(np.mean(np.sort(np.abs(r))[-50:]))
    print("D-007", w, "survival q", q(s), "expr q", q(e), "mean top-50 |r|", np.round(np.mean(ac), 3))

# D-008: ranges and clip hits
m = load_mod("D-008")
for w in ("plus", "minus"):
    ds = draws(m, w, 300)
    co = np.concatenate([d["cardiac_output"].ravel() for d in ds])
    ca = np.concatenate([d["arterial_o2_content"].ravel() for d in ds])
    cv = np.concatenate([d["venous_o2_content"].ravel() for d in ds])
    vo = np.concatenate([d["vo2_expired_gas"].ravel() for d in ds])
    print("D-008", w, "CO", q(co), "CaO2", q(ca), "CvO2", q(cv), "VO2", q(vo),
          "frac CvO2/CaO2<0.2", np.mean(cv / ca < 0.2), "CvO2 at floor", np.mean(cv <= 0.5))

# D-010: realism
m = load_mod("D-010")
for w in ("plus", "minus"):
    d = m.plus(np.random.default_rng(3)) if w == "plus" else m.minus(np.random.default_rng(3))
    cnt = d["category"].sum(0)
    print("D-010", w, "rows one-hot", bool(np.all(d["category"].sum(1) == 1)), "district n q", q(cnt),
          "empty districts", int(np.sum(cnt == 0)), "age", q(d["covariates"][:, 0]), "bmi", q(d["covariates"][:, 1]),
          "sbp", q(d["covariates"][:, 2]), "y", q(d["y"]))

# D-011: number of strongly differential genes (descriptive)
m = load_mod("D-011")
for w in ("plus", "minus"):
    ds = draws(m, w, 10)
    nd = []
    for d in ds:
        e, lab = d["expression"], d["myeloid"]
        diff = e[lab].mean(0) - e[~lab].mean(0)
        sd = np.sqrt((e[lab].var(0, ddof=1) + e[~lab].var(0, ddof=1)) / 2)
        nd.append(np.sum(np.abs(diff / sd) > 1.5))
    print("D-011", w, "mean #genes with |d|>1.5", np.mean(nd), "n AML", int(ds[0]["myeloid"].sum()))

# D-012: population mean occupancy by group (pooled over draws)
m = load_mod("D-012")
for w in ("plus", "minus"):
    ds = draws(m, w, 2000)
    occ = np.stack([d["occupied"].mean(1) for d in ds])
    fen = np.stack([d["exclosure"] for d in ds])
    print("D-012", w, "pooled fenced", np.round(occ[fen].mean(), 3), "open", np.round(occ[~fen].mean(), 3),
          "plot occupancy SD within group (open)", np.round(occ[~fen].std(), 3))

# D-022 / D-027: y realism
for bid in ("D-022", "D-027"):
    m = load_mod(bid)
    for w in ("plus", "minus"):
        d = getattr(m, w)(np.random.default_rng(5))
        print(bid, w, "y", q(d["y"]), "X col0", q(d["X"][:, 0]))

# D-023 / D-040: marginal correlations (descriptive realism)
for bid, keys in (("D-023", ("head_width", "wing_length", "body_length")), ("D-040", ("breadth", "height", "length"))):
    m = load_mod(bid)
    for w in ("plus", "minus"):
        d = getattr(m, w)(np.random.default_rng(9))
        c = np.corrcoef(np.vstack([d[k] for k in keys]))
        print(bid, w, "r(a,b) r(a,c) r(b,c)", np.round([c[0, 1], c[0, 2], c[1, 2]], 3),
              "means", [np.round(d[k].mean(), 2) for k in keys])

# D-035: prevalence and ranges
m = load_mod("D-035")
d = m.plus(np.random.default_rng(1))
print("D-035 prevalence", d["positive"].mean(), "feature medians", np.round(np.median(d["features"], 0), 2))

# D-042: replicate structure
m = load_mod("D-042")
for w in ("plus", "minus"):
    d = getattr(m, w)(np.random.default_rng(2))
    u, inv, cnt = np.unique(d["X"], axis=0, return_inverse=True, return_counts=True)
    print("D-042", w, "unique rows", u.shape[0], "records/compound q", q(cnt), "y", q(d["y"]))

# D-047: population mean changes among screening>=60 (pooled over draws)
m = load_mod("D-047")
for w in ("plus", "minus"):
    ds = draws(m, w, 500)
    sel = [d["screening"] >= 60 for d in ds]
    ent = np.concatenate([d["entry"][s] for d, s in zip(ds, sel)])
    scr = np.concatenate([d["screening"][s] for d, s in zip(ds, sel)])
    wk = np.concatenate([d["week12"][s] for d, s in zip(ds, sel)])
    print("D-047", w, "mean n selected", np.mean([s.sum() for s in sel]), "pooled mean entry-week12",
          np.round((ent - wk).mean(), 2), "pooled mean screening-entry (RTM)", np.round((scr - ent).mean(), 2),
          "entry q", q(ent))
