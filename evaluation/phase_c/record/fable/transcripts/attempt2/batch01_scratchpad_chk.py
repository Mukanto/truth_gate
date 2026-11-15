import sys, json, time, ast, importlib.util
B = r"E:\Claude Projects\Kapi\phase_c_private\fable\batch01"
sys.path.insert(0, B + r"\pkg")
import numpy as np
briefs = json.load(open(B + r"\BATCH.json", encoding="utf-8"))
def pc(x, y, z):
    Z = np.column_stack([np.ones(len(z)), z]); rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]; ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
    return np.corrcoef(rx, ry)[0, 1]
def coef(y, x, z):
    X = np.column_stack([x, z, np.ones(len(x))]); return np.linalg.lstsq(X, y, rcond=None)[0][0]
def stat(i, d):
    if i in ("C01", "C07"):
        g = d["group_b" if i == "C01" else "tumour"]; x = d["expression"]
        a, b = x[g], x[~g]; t = (a.mean(0) - b.mean(0)) / np.sqrt(a.var(0, ddof=1) / len(a) + b.var(0, ddof=1) / len(b))
        return (np.abs(t) > 4).sum()
    if i == "C02": return np.mean([coef(d["claw_length"][s], d["abdomen_length"][s], d["body_length"][s]) for s in range(15)])
    if i == "C03": return np.corrcoef(d["heart_rate"].mean(1), d["cortisol"].mean(1))[0, 1]
    if i == "C04": return np.corrcoef(d["o2_uptake_expired"], d["cardiac_output"] * d["arterial_o2_content"] * 10)[0, 1]
    if i == "C05": return (d["resp_faces"] - d["resp_bodies"]).mean()
    if i == "C06": return np.polyfit(d["contrast"], d["response"].mean(1), 1)[0]
    if i == "C08": return ((d["task_a"] - d["rest_a"]) - (d["task_b"] - d["rest_b"])).mean()
    if i == "C09":
        e = d["estimates"]; return np.mean([pc(e[:, a], e[:, b], d["true_value"]) for a, b in ((0, 1), (0, 2), (1, 2))])
    if i == "C10": m = d["weight_gain"].mean(1); return m[d["treated"]].mean() - m[~d["treated"]].mean()
    if i == "C11": s = d["score_screen"] >= 60; return ((d["score_start"] - d["score_6m"])[s] >= 10).mean()
    if i == "C12": return pc(d["femur_length"], d["tibia_length"], d["humerus_length"])
    if i == "C13": return coef(d["liver_weight"], d["kidney_weight"], d["body_mass"])
    if i == "C14": h = d["debt_ratio"] > 90; return d["growth"][h].mean() - d["growth"][~h].mean()
    if i == "C15":
        g = d["group_a"]; return np.corrcoef(d["task_score"][g], d["symptom_score"][g])[0, 1] - np.corrcoef(d["task_score"][~g], d["symptom_score"][~g])[0, 1]
for br in briefs:
    i = br["id"]; path = B + rf"\skeletons\{i}.py"; src = open(path, encoding="utf-8").read()
    tree = ast.parse(src); doc = ast.get_docstring(tree, clean=False)
    assert doc == f"{i}: {br['claim']}", (i, "docstring")
    for node in tree.body: assert isinstance(node, (ast.Expr, ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)), (i, node)
    spec = importlib.util.spec_from_file_location("sk_" + i, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    S = m.STUDY; keys = [k["key"] for k in br["data_keys"]]; dt = {k["key"]: k["dtype"] for k in br["data_keys"]}
    res = {}; tmax = 0; shapes = None
    for w in ("plus", "minus"):
        vals = []
        for seed in range(200):
            rng = np.random.default_rng(seed); t0 = time.perf_counter(); d = S.worlds[w].generate(rng); tmax = max(tmax, time.perf_counter() - t0)
            assert list(d.keys()) == keys or set(d) == set(keys), (i, d.keys())
            sh = {k: v.shape for k, v in d.items()}
            if shapes is None: shapes = sh
            assert sh == shapes, (i, sh)
            for k, v in d.items():
                assert v.dtype == (np.float64 if dt[k] == "float" else np.bool_), (i, k, v.dtype); assert np.all(np.isfinite(v)), (i, k)
            vals.append(stat(i, d))
            if seed < 20:
                for c in S.controls:
                    t0 = time.perf_counter(); d2 = c.transform(d, np.random.default_rng(1000 + seed)); tmax = max(tmax, time.perf_counter() - t0)
                    assert set(d2) == set(keys) and all(d2[k].shape == d[k].shape and d2[k].dtype == d[k].dtype for k in keys), (i, "ctl")
                    assert any(not np.array_equal(d2[k], d[k]) for k in keys), (i, "ctl unchanged")
                    res.setdefault("ctl_" + w, []).append(stat(i, d2))
        res[w] = vals
    q = lambda v: "mean %.3f sd %.3f q05 %.3f q95 %.3f" % (np.mean(v), np.std(v), *np.quantile(v, [.05, .95]))
    print(i, shapes, "tmax %.1f ms" % (tmax * 1e3)); print("   plus ", q(res["plus"])); print("   minus", q(res["minus"])); print("   ctl+ ", q(res["ctl_plus"]))
