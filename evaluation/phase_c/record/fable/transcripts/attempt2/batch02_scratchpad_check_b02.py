import sys, json, time, ast
SB = r"E:\Claude Projects\Kapi\phase_c_private\fable\batch02"
sys.path.insert(0, SB + r"\pkg")
import numpy as np
from truth_gate import Study

briefs = json.load(open(SB + r"\BATCH.json", encoding="utf-8"))
BAD = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
       "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__", "load", "save", "savez", "savetxt",
       "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
mods = {}
for b in briefs:
    i = b["id"]
    path = SB + "\\skeletons\\" + i + ".py"
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    errs = []
    if ast.get_docstring(tree, clean=False) != i + ": " + b["claim"]:
        errs.append("docstring")
    for node in tree.body[1:]:
        if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
            errs.append("module-level " + type(node).__name__)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in BAD:
            errs.append("name " + node.id)
        if isinstance(node, ast.Attribute) and (node.attr in BAD or node.attr.startswith("__")):
            errs.append("attr " + node.attr)
        if isinstance(node, ast.Attribute) and node.attr == "random" and isinstance(node.value, ast.Name) and node.value.id == "np":
            errs.append("np.random")
    g = {}
    exec(compile(src, path, "exec"), g)
    S = g["STUDY"]
    assert isinstance(S, Study) and S.name == i
    keys = [k["key"] for k in b["data_keys"]]
    dt = {k["key"]: k["dtype"] for k in b["data_keys"]}
    shapes = None
    tmax = 0.0
    for w in ("plus", "minus"):
        for seed in range(30):
            t = time.perf_counter()
            d = S.worlds[w].generate(np.random.default_rng(seed))
            tmax = max(tmax, time.perf_counter() - t)
            if list(d.keys()) != keys:
                errs.append("keys " + w)
            sh = {k: v.shape for k, v in d.items()}
            if shapes is None:
                shapes = sh
            if sh != shapes:
                errs.append("shape differs")
            for k, v in d.items():
                want = np.float64 if dt[k] == "float" else np.bool_
                if v.dtype != want:
                    errs.append("dtype " + k)
                if not np.all(np.isfinite(v)):
                    errs.append("nonfinite " + k)
            for c in S.controls:
                t = time.perf_counter()
                d2 = c.transform(d, np.random.default_rng(1000 + seed))
                tmax = max(tmax, time.perf_counter() - t)
                if list(d2.keys()) != keys:
                    errs.append("ctrl keys " + c.id)
                if all(np.array_equal(d2[k], d[k]) for k in keys):
                    errs.append("ctrl unchanged " + c.id)
                for k in keys:
                    if d2[k].shape != d[k].shape or d2[k].dtype != d[k].dtype:
                        errs.append("ctrl shape/dtype " + c.id)
    try:
        S.criteria[0].fn(d)
        errs.append("criterion did not raise")
    except NotImplementedError:
        pass
    print(i, shapes, "tmax_ms=%.1f" % (tmax * 1e3), "ERRORS: " + str(sorted(set(errs))) if errs else "ok")
    mods[i] = S

# ---- descriptive effect checks (oracle quantities, no tests) ----
def avg(i, f, n=300):
    S = mods[i]
    out = []
    for w in ("plus", "minus"):
        vals = np.array([f(S.worlds[w].generate(np.random.default_rng(s)), s) for s in range(n)])
        out.append((vals.mean(axis=0), vals.std(axis=0)))
    print(i, "plus mean/sd", np.round(out[0][0], 3), np.round(out[0][1], 3), "| minus", np.round(out[1][0], 3), np.round(out[1][1], 3))

def gdiff(x, m):
    return x[m].mean() - x[~m].mean()

avg("C16", lambda d, s: [gdiff(d["heart_weight"] - 240 - 2.2 * d["body_mass"], d["treated"]), gdiff(d["body_mass"], d["treated"]), gdiff(d["heart_weight"], d["treated"])])
avg("C17", lambda d, s: [d["spine_density"].mean(axis=(1, 2))[d["dose"] == 20].mean() - d["spine_density"].mean(axis=(1, 2))[d["dose"] == 0].mean(), d["spine_density"].mean(axis=(1, 2)).std(ddof=1)])
avg("C18", lambda d, s: [d["liking_treatment"].mean() - d["liking_control"].mean(), d["liking_control"].std(ddof=1), d["willingness_to_pay_treatment"].mean() - d["willingness_to_pay_control"].mean(), np.corrcoef(d["liking_control"], d["willingness_to_pay_control"])[0, 1]])

def c19(d, s):
    rng = np.random.default_rng(s)
    rng.normal(0, 1, 16); rng.normal(0, 1, 16)
    region = np.zeros(1000, bool); region[rng.permutation(1000)[:150]] = True
    t = d["trait"] - d["trait"].mean()
    res = []
    for k in ("act_session1", "act_session2"):
        a = d[k] - d[k].mean(axis=0)
        r = (a * t[:, None]).sum(0) / np.sqrt((a ** 2).sum(0) * (t ** 2).sum())
        res += [r[region].mean(), r[~region].mean()]
    res.append(d["act_session1"][:, region].std())
    return res
avg("C19", c19, 200)
avg("C20", lambda d, s: [d["score_treatment"].mean() - d["score_control"].mean(), d["score_control"].std(ddof=1)])
inf = np.array([3, 7, 14, 18, 31, 36])
def c21(d, s):
    x, m = d["sensor_features"], d["defective"]
    sd = x[~m].std(axis=0)
    dd = (x[m].mean(0) - x[~m].mean(0)) / sd
    return [np.abs(dd[inf]).mean(), np.abs(np.delete(dd, inf)).mean(), m.mean()]
avg("C21", c21, 100)
avg("C22", lambda d, s: [gdiff(d["density"].mean(1), d["treated"]), d["density"].mean(1)[~d["treated"]].std(ddof=1), d["density"].mean(1)[d["treated"]].std(ddof=1), d["density"][~d["treated"]].mean()])
avg("C23", lambda d, s: [gdiff(d["latency"].mean(1), d["treated"]), d["latency"].mean(1)[~d["treated"]].std(ddof=1), d["latency"].max()])
avg("C24", lambda d, s: [np.corrcoef(d["gene_b_expression"] - 0.6 * d["gene_c_expression"], d["gene_a_expression"] - 0.5 * d["gene_c_expression"])[0, 1], d["gene_b_expression"].std(), d["gene_b_expression"].min(), d["gene_a_expression"].min()])
avg("C25", lambda d, s: [(d["admissions"] - 8 * d["population"])[60:].mean() - (d["admissions"] - 8 * d["population"])[:60].mean(), d["admissions"][60:].mean() - d["admissions"][:60].mean(), d["admissions"].mean(), np.corrcoef(d["population"], d["time_years"])[0, 1]])
def c26(d, s):
    x, m = d["expression"], d["class_b"]
    dd = np.abs(x[m].mean(0) - x[~m].mean(0)) / x[~m].std(0, ddof=1)
    return [np.sort(dd)[-50:].mean(), np.median(dd)]
avg("C26", c26, 100)
avg("C27", lambda d, s: [gdiff(d["activity"].mean(1), d["exposed"]), d["activity"].mean(1)[~d["exposed"]].std(ddof=1)])
def c28(d, s):
    v, h = d["rate_vertical"], d["rate_horizontal"]
    i1 = (v[:, ::2].mean(1) - h[:, ::2].mean(1)) / (v[:, ::2].mean(1) + h[:, ::2].mean(1))
    i2 = (v[:, 1::2].mean(1) - h[:, 1::2].mean(1)) / (v[:, 1::2].mean(1) + h[:, 1::2].mean(1))
    full = (v.mean(1) - h.mean(1)) / (v.mean(1) + h.mean(1))
    return [np.corrcoef(i1, i2)[0, 1], full.std(), full.mean(), (v.mean(1) + h.mean(1)).min()]
avg("C28", c28, 100)
def c29(d, s):
    x, sig, sen = d["expression"], d["on_signature"], d["sensitive"]
    return [gdiff(x[sig].mean(0), sen), x[sig].mean(0)[~sen].std(ddof=1), gdiff(x[~sig].mean(0), sen), sig.sum(), sen.sum()]
avg("C29", c29, 100)
avg("C30", lambda d, s: [np.corrcoef(d["sbp_week12"], d["sbp_baseline_second"])[0, 1], d["sbp_week12"].std(), (d["sbp_baseline_first"] - d["sbp_week12"]).mean(), (d["sbp_baseline_first"] - d["sbp_week12"]).std()])
