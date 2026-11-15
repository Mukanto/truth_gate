"""Pre-check of a FIXED criterion only (never imports faulty.py).
usage: py -I? precheck_fixed.py CASE N
Counts how often fixed.criterion holds on plus, minus, noise-probe, zeros-probe and the declared controls; times t and g."""
import sys, time, importlib.util, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pkg"))
import numpy as np

case, N = sys.argv[1], int(sys.argv[2])
path = os.path.join(ROOT, "cases", case, "fixed.py")
spec = importlib.util.spec_from_file_location("fixed_" + case.replace("-", "_"), path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def tally(vals):
    return {"hold": sum(v is True for v in vals), "fail": sum(v is False for v in vals), "none": sum(v is None for v in vals), "n": len(vals)}

res = {}
tg = 0.0; tc = 0.0
for name, gen in (("plus", mod.plus), ("minus", mod.minus)):
    out = []
    for i in range(N):
        rng = np.random.default_rng(1000 + i)
        t0 = time.perf_counter(); d = gen(rng); t1 = time.perf_counter()
        r = mod.criterion(d); t2 = time.perf_counter()
        if name == "plus":
            tg += t1 - t0; tc += t2 - t1
        out.append(r)
    res[name] = tally(out)
# controls declared in the skeleton
for c in mod.STUDY.controls:
    out = []
    for i in range(N):
        rng = np.random.default_rng(5000 + i)
        d = mod.plus(rng)
        out.append(mod.criterion(c.transform(d, np.random.default_rng(9000 + i))))
    res["control:" + c.id] = tally(out)
# probes: noise and zeros of the same shape
out = []
for i in range(N):
    rng = np.random.default_rng(7000 + i)
    d = mod.plus(rng)
    nd = {k: (rng.standard_normal(v.shape).astype(v.dtype) if v.dtype != bool else rng.standard_normal(v.shape) > 0) for k, v in d.items()}
    out.append(mod.criterion(nd))
res["probe:noise"] = tally(out)
out = []
for i in range(min(N, 20)):
    d = mod.plus(np.random.default_rng(8000 + i))
    zd = {k: np.zeros_like(v) for k, v in d.items()}
    out.append(mod.criterion(zd))
res["probe:zeros"] = tally(out)
for k, v in res.items():
    print(case, k, v)
S = 2 + 1 + len(mod.STUDY.controls) + len(mod.STUDY.premises) + len(getattr(mod.STUDY, "relational", []) or []) + 2 - 3 + 0
# S = worlds + controls + premises + relational pairs, plus 2
S = len(mod.STUDY.worlds) + len(mod.STUDY.controls) + len(mod.STUDY.premises) + len(getattr(mod.STUDY, "relational", []) or []) + 2
t = tc / N; g = tg / N
print(case, "t=%.6f g=%.6f S=%d estimate=%.1f s" % (t, g, S, 2 * 200 * (S + 1) * (t + g)))
