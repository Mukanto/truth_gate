"""Scratch: pre-check of the FIXED criteria only (never loads faulty.py). Usage: py precheck_fixed.py [N] [case ids...]
Draws N samples from plus, minus, each control and the probes; counts HOLDS / FAILS / None; times the fixed criterion."""
import importlib.util
import json
import sys
import time
import warnings
from pathlib import Path

PKG = r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\pkg"
sys.path.insert(0, PKG)
import numpy as np  # noqa: E402

ROOT = Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\cases")


def load_fixed(cid):
    path = ROOT / cid / "fixed.py"
    assert path.name == "fixed.py"
    spec = importlib.util.spec_from_file_location("case_" + cid.replace("-", "_") + "_fixed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def noise_probe(d, rng):
    return {k: (rng.random(v.shape) < 0.5) if v.dtype == np.bool_ else rng.standard_normal(v.shape) for k, v in d.items()}


def zeros_probe(d, rng):
    return {k: np.zeros(v.shape, dtype=v.dtype if v.dtype == np.bool_ else np.float64) for k, v in d.items()}


def count(fn, make, n, seed):
    rng = np.random.default_rng(seed)
    h = f = u = 0
    err = 0
    for _ in range(n):
        d = make(rng)
        try:
            r = fn(d)
        except Exception as e:  # a genuine error is reported, not hidden
            err += 1
            print("   EXCEPTION", type(e).__name__, e)
            continue
        if r is True:
            h += 1
        elif r is False:
            f += 1
        elif r is None:
            u += 1
        else:
            print("   BAD RETURN", type(r))
    return {"holds": h, "fails": f, "none": u, "errors": err, "n": n}


def main():
    args = sys.argv[1:]
    n = int(args[0]) if args else 200
    ids = args[1:] or [f"B1-{i:02d}" for i in range(1, 13)]
    out = {}
    for ci, cid in enumerate(ids):
        warnings.simplefilter("ignore")
        mod = load_fixed(cid)
        st = mod.STUDY
        fn = mod.criterion
        base = 70000 + 100 * int(cid[-2:])
        res = {}
        gen_plus = st.worlds["plus"].generate
        gen_minus = st.worlds["minus"].generate
        res["plus"] = count(fn, gen_plus, n, base + 1)
        res["minus"] = count(fn, gen_minus, n, base + 2)
        for k, c in enumerate(st.controls):
            if c.transform is not None:
                res["control:" + c.id] = count(fn, lambda rng, c=c: c.transform(gen_plus(rng), rng), n, base + 10 + k)
        res["probe:noise"] = count(fn, lambda rng: noise_probe(gen_plus(rng), rng), n, base + 20)
        res["probe:zeros"] = count(fn, lambda rng: zeros_probe(gen_plus(rng), rng), 5, base + 21)
        for (a, b) in st.relational:
            def make(rng, a=a, b=b):
                d = gen_plus(rng)
                d = dict(d)
                d[b] = d[b][rng.permutation(d[b].shape[0])]
                return d
            res[f"probe:shuffle:{a},{b}"] = count(fn, make, n, base + 30)
        # timing
        rng = np.random.default_rng(base + 40)
        samples = []
        tg = []
        for _ in range(30):
            t0 = time.perf_counter()
            samples.append(gen_plus(rng))
            tg.append(time.perf_counter() - t0)
        tt = []
        for s in samples:
            t0 = time.perf_counter()
            fn(s)
            tt.append(time.perf_counter() - t0)
        g = float(np.mean(tg))
        t = float(np.mean(tt))
        S = len(st.worlds) + len(st.controls) + len(st.premises) + len(st.relational) + 2
        est = 2 * 200 * (S + 1) * (t + g)
        res["timing"] = {"t": t, "g": g, "S": S, "estimate_s": est, "calls": len(tt)}
        out[cid] = res
        print(cid)
        for k, v in res.items():
            if k == "timing":
                print("   timing t=%.4f g=%.4f S=%d est=%.1f s" % (v["t"], v["g"], v["S"], v["estimate_s"]))
            else:
                print("   %-48s holds %3d fails %3d none %3d err %d (n=%d)" % (k, v["holds"], v["fails"], v["none"], v["errors"], v["n"]))
    Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\work\precheck_last.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
