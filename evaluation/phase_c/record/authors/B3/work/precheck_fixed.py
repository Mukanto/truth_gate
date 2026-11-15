# Scratch (Part 2): plain-Python pre-check and timing of the FIXED criterion only. The faulty files are never imported.
# usage: py precheck_fixed.py [case ids...]   (default: all 12)
import importlib.util
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "pkg"))
import numpy as np  # noqa: E402

NS = int(__import__("os").environ.get("NS", "300"))


def load_fixed(cid):
    path = ROOT / "cases" / cid / "fixed.py"
    assert path.name == "fixed.py"
    spec = importlib.util.spec_from_file_location("fixed_" + cid.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def noise(d, rng):
    out = {}
    for k, v in d.items():
        if v.dtype == np.bool_:
            out[k] = rng.random(v.shape) < 0.5
        else:
            out[k] = rng.standard_normal(v.shape)
    return out


def zeros(d):
    return {k: np.zeros(v.shape, dtype=v.dtype) for k, v in d.items()}


def rate(vals):
    h = sum(1 for v in vals if v is True)
    n = sum(1 for v in vals if v is False)
    u = sum(1 for v in vals if v is None)
    return h, n, u


def main(ids):
    for cid in ids:
        mod = load_fixed(cid)
        study = mod.STUDY
        crit = mod.criterion
        res = {}
        for name, gen in (("plus", mod.plus), ("minus", mod.minus)):
            vals = []
            for s in range(NS):
                vals.append(crit(gen(np.random.default_rng(1000 + s))))
            res[name] = rate(vals)
        # controls on plus
        for c in study.controls:
            vals = []
            for s in range(NS):
                r = np.random.default_rng(5000 + s)
                d = mod.plus(r)
                d2 = c.transform(d, np.random.default_rng(9000 + s))
                vals.append(crit(d2))
            res["control:" + c.id] = rate(vals)
        vals = [crit(noise(mod.plus(np.random.default_rng(2000 + s)), np.random.default_rng(3000 + s))) for s in range(NS)]
        res["noise"] = rate(vals)
        res["zeros"] = rate([crit(zeros(mod.plus(np.random.default_rng(1))))])
        print(f"== {cid} (n samples per stream {NS}; holds/fails/None)")
        for k, (h, n, u) in res.items():
            tot = max(h + n + u, 1)
            print(f"   {k:55s} holds={h:4d} fails={n:4d} none={u:3d}  holds-rate={h / tot:.3f}")
        # timing on plus samples
        samples = [mod.plus(np.random.default_rng(7000 + s)) for s in range(40)]
        t0 = time.perf_counter()
        for d in samples:
            crit(d)
        t = (time.perf_counter() - t0) / len(samples)
        t0 = time.perf_counter()
        for s in range(40):
            mod.plus(np.random.default_rng(7100 + s))
        g = (time.perf_counter() - t0) / 40
        S = len(study.worlds) + len(study.controls) + len(getattr(study, "premises", []) or []) + len(getattr(study, "relational", []) or []) + 2
        est = 2 * 200 * (S + 1) * (t + g)
        print(f"   timing: t={t * 1e3:.3f} ms  g={g * 1e3:.3f} ms  S={S}  estimate={est:.1f} s (limit 900)")


if __name__ == "__main__":
    main(sys.argv[1:] or [f"B3-{i:02d}" for i in range(1, 13)])
