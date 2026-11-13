# Pre-check of the FIXED criteria only (plain Python). Never imports faulty.py.
import sys, time, importlib.util, os
import numpy as np
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = int(os.environ.get("NS", "200"))

def load(cid):
    p = os.path.join(ROOT, "cases", cid, "fixed.py")
    spec = importlib.util.spec_from_file_location("fixed_" + cid.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def rate(vals):
    v = [x for x in vals]
    n = len(v); u = sum(x is None for x in v); h = sum(x is True for x in v)
    return h, n, u

for cid in (sys.argv[1:] or ["B6-%02d" % i for i in range(1, 13)]):
    m = load(cid)
    out = {}
    samples = {}
    for name, f in (("plus", m.plus), ("minus", m.minus)):
        rng = np.random.default_rng(1000 + int(cid[-2:]))
        samples[name] = [f(rng) for _ in range(NS)]
        out[name] = rate([m.criterion(s) for s in samples[name]])
    ctl = m.STUDY.controls[0]
    rng = np.random.default_rng(2000 + int(cid[-2:]))
    out["control(" + ctl.id + " on plus)"] = rate([m.criterion(ctl.transform(dict(s), rng)) for s in samples["plus"]]) if hasattr(ctl, "transform") and ctl.transform else (0, 0, 0)
    rng = np.random.default_rng(3000 + int(cid[-2:]))
    out["noise N(0,1)"] = rate([m.criterion({k: rng.standard_normal(v.shape) for k, v in s.items()}) for s in samples["plus"]])
    out["zeros"] = rate([m.criterion({k: np.zeros_like(v) for k, v in s.items()}) for s in samples["plus"][:20]])
    # repeatability
    s0 = samples["plus"][0]; rep = (m.criterion(s0) == m.criterion(s0))
    # timing
    t0 = time.perf_counter(); [m.criterion(s) for s in samples["plus"][:100]]; t = (time.perf_counter() - t0) / 100
    rng = np.random.default_rng(5)
    t0 = time.perf_counter(); [m.plus(rng) for _ in range(200)]; g = (time.perf_counter() - t0) / 200
    S = len(m.STUDY.worlds) + len(m.STUDY.controls) + len(m.STUDY.premises) + len(getattr(m.STUDY, "relational", []) or []) + 2
    est = 2 * 200 * (S + 1) * (t + g)
    print(cid, " ".join("%s=%d/%d(und %d)" % ((k,) + v) for k, v in out.items()), "repeat=%s" % rep, "t=%.2fms g=%.2fms S=%d est=%.1fs" % (t * 1e3, g * 1e3, S, est))
