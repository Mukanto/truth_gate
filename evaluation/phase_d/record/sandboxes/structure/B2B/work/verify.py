import sys, json, time, os, importlib.util
B = r"E:\Claude Projects\Kapi\phase_d_work\structure\B2B"
sys.path.insert(0, B + r"\pkg")
import numpy as np
ids = sys.argv[1:] or sorted(os.listdir(B + r"\cases"))
NS = 200
for cid in ids:
    cd = B + "\cases\\" + cid
    brief = json.load(open(cd + r"\brief.json")); note = json.load(open(cd + r"\NOTE.json"))
    spec = importlib.util.spec_from_file_location("ref_" + cid.replace("-", "_"), cd + r"\reference.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert m.__doc__ == cid + ": " + brief["claim"], "docstring"
    ns = {"np": np}; exec(note["structure_statistic"]["code"], ns); stat = ns["stat"]
    res = {}; tmax = 0
    for w, fn in (("plus", m.plus), ("minus", m.minus)):
        vals = []
        for i in range(NS):
            rng = np.random.default_rng([7, 1 if w == "plus" else 2, i])
            t0 = time.perf_counter(); d = fn(rng); tmax = max(tmax, time.perf_counter() - t0)
            if i == 0:
                assert set(d) == {k["key"] for k in brief["data_keys"]}, "keys"
                for k in brief["data_keys"]:
                    a = d[k["key"]]
                    assert a.shape == tuple(k["dims"]), (k["key"], a.shape)
                    assert a.dtype == (np.bool_ if k["dtype"] == "bool" else np.float64), (k["key"], a.dtype)
            for a in d.values(): assert np.all(np.isfinite(a))
            vals.append(stat(d))
        res[w] = (np.mean(vals), np.std(vals, ddof=1))
    av = note["approved_value"]; nv = note["structure_statistic"]["null_value"]
    tol = 0.2 * abs(av - nv)
    (mp, sp), (mm, sm) = res["plus"], res["minus"]
    se3 = 3 * np.sqrt(sp ** 2 / NS + sm ** 2 / NS)
    ok1 = abs(mp - av) <= tol and abs(mm - av) <= tol
    ok2 = abs(mp - mm) <= se3 + 1e-12
    # control
    cg = np.random.default_rng([7, 3, 0]); d0 = m.plus(np.random.default_rng([7, 1, 0]))
    c = m.STUDY.controls[0].transform(d0, cg)
    chg = any(not np.array_equal(c[k], d0[k]) for k in d0)
    sh = all(c[k].shape == d0[k].shape and c[k].dtype == d0[k].dtype for k in d0)
    print(f"{cid} stat plus {mp:.4f}+-{sp:.4f} minus {mm:.4f}+-{sm:.4f} approved {av} tol {tol:.3f} | within-tol {ok1} equal {ok2} (|diff| {abs(mp-mm):.4f} <= {se3:.4f}) | tmax {tmax*1000:.0f}ms | control changed {chg} shape-ok {sh}")
