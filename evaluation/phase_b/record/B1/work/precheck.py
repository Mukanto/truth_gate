import sys, time, importlib.util, json
import numpy as np
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
cid = sys.argv[1]
NS = int(sys.argv[2]) if len(sys.argv) > 2 else 200
path = rf"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b\B1\cases\{cid}\fixed.py"
spec = importlib.util.spec_from_file_location("fx_" + cid.replace("-", "_"), path)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
crit = m.criterion
res = {}
def rate(vals):
    n = len(vals); h = sum(1 for v in vals if v is True); u = sum(1 for v in vals if v is None)
    return dict(n=n, holds=h, none=u, rate=round(h / n, 3))
rng = np.random.default_rng(12345)
tg = []
for name, w in (("plus", m.plus), ("minus", m.minus)):
    vals = []
    for i in range(NS):
        t0 = time.perf_counter(); d = w(rng); tg.append(time.perf_counter() - t0) if name == "plus" else None
        vals.append(crit(d))
    res[name] = rate(vals)
# controls
for ctl in m.STUDY.controls:
    vals = []
    for i in range(NS):
        d = m.plus(rng); d2 = ctl.transform(d, rng) if hasattr(ctl, "transform") else None
        vals.append(crit(d2))
    res["control:" + ctl.id if hasattr(ctl, "id") else "control"] = rate(vals)
# noise probe and zero probe: i.i.d. N(0,1) in every array of the same shape (bool: fair coin)
def noise(d, r):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        out[k] = (r.random(v.shape) < 0.5) if v.dtype == bool else r.standard_normal(v.shape)
    return out
def zeros(d):
    return {k: np.zeros_like(np.asarray(v)) for k, v in d.items()}
vals = []
for i in range(NS // 2):
    vals.append(crit(noise(m.plus(rng), rng)))
res["noise"] = rate(vals)
vals = [crit(zeros(m.plus(rng))) for i in range(10)]
res["zeros"] = rate(vals)
# timing: mean of 30 calls on plus samples
ds = [m.plus(rng) for _ in range(30)]
t0 = time.perf_counter()
for d in ds: crit(d)
t = (time.perf_counter() - t0) / 30
g = float(np.mean(tg))
# determinism
d = m.plus(np.random.default_rng(5)); det = crit(d) == crit(d)
S = len(m.STUDY.worlds) + len(m.STUDY.controls) + len(getattr(m.STUDY, "premises", []) or []) + len(getattr(m.STUDY, "relational", []) or []) + 2
est = 2 * 200 * (S + 1) * (t + g)
res["timing"] = dict(t=round(t, 5), g=round(g, 5), S=S, est_s=round(est, 1), deterministic=det)
print(cid, json.dumps(res))
