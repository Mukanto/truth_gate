import json, sys, os, time, importlib.util
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, "pkg"))
import numpy as np
ids = sys.argv[1:] or sorted(os.listdir(os.path.join(root, "cases")))
NS = 200
for cid in ids:
    cdir = os.path.join(root, "cases", cid)
    if not os.path.exists(os.path.join(cdir, "reference.py")):
        continue
    brief = json.load(open(os.path.join(cdir, "brief.json"), encoding="utf-8"))
    note = json.load(open(os.path.join(cdir, "NOTE.json"), encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("ref_" + cid.replace("-", "_"), os.path.join(cdir, "reference.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__doc__ == cid + ": " + brief["claim"], "docstring mismatch"
    ss = note["structure_statistic"]
    stat = None
    if ss:
        ns = {"np": np}
        exec(ss["code"], ns)
        stat = ns["stat"]
    res = {}
    tmax = 0
    for w in ("plus", "minus"):
        vals = []
        for k in range(NS):
            rng = np.random.default_rng(1000 + k * 7 + (0 if w == "plus" else 500000))
            t0 = time.perf_counter()
            d = getattr(mod, w)(rng)
            tmax = max(tmax, time.perf_counter() - t0)
            assert set(d) == {x["key"] for x in brief["data_keys"]}, "keys"
            for x in brief["data_keys"]:
                a = d[x["key"]]
                assert a.shape == tuple(x["dims"]), (x["key"], a.shape)
                assert a.dtype == (np.dtype(bool) if x["dtype"] == "bool" else np.dtype("float64")), (x["key"], a.dtype)
                if a.dtype.kind == "f":
                    assert np.isfinite(a).all()
            if stat:
                vals.append(stat(d))
        res[w] = np.array(vals)
    # control
    ctl = mod.STUDY.controls[0]
    rng = np.random.default_rng(5)
    d = mod.plus(rng)
    t0 = time.perf_counter(); c = ctl.transform(d, rng); tc = time.perf_counter() - t0
    assert set(c) == set(d)
    unchanged = all(np.array_equal(c[k], d[k]) for k in d)
    for k in d:
        assert c[k].shape == d[k].shape and c[k].dtype == d[k].dtype
    out = {"id": cid, "tmax_ms": round(tmax * 1000, 1), "ctl_ms": round(tc * 1000, 1), "ctl_unchanged": unchanged}
    if stat:
        a = ss["note_value"]; nv = ss["null_value"]; av = note["approved_value"]
        mp, mm = res["plus"].mean(), res["minus"].mean()
        sp, sm = res["plus"].std(ddof=1), res["minus"].std(ddof=1)
        tolA = 0.2 * abs(av - nv)
        out.update(approved=av, mean_plus=round(mp, 4), mean_minus=round(mm, 4), sd_plus=round(sp, 4), sd_minus=round(sm, 4),
                   tol_abs=round(tolA, 4), ok_plus=abs(mp - av) <= tolA, ok_minus=abs(mm - av) <= tolA,
                   diff=round(abs(mp - mm), 4), tol_eq=round(3 * np.sqrt(sp**2 / NS + sm**2 / NS), 4),
                   ok_eq=abs(mp - mm) <= 3 * np.sqrt(sp**2 / NS + sm**2 / NS))
    print(json.dumps(out, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)))
