"""Pre-check of the FIXED criteria only (plain Python, no Truth_Gate). Imports fixed.py only; faulty.py is never imported.
Counts how often the fixed criterion holds in plus, minus, the declared control, and on my own approximation of the
noise and zero probes (float arrays -> N(0,1) / 0, bool arrays -> fair coin / False). Also times it."""
import sys, time, importlib.util, os
import numpy as np

sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")

NS = int(sys.argv[1]) if len(sys.argv) > 1 else 300
NP = 100
cases = sys.argv[2:] or ["O1a", "O1b", "O2a", "O2b", "O3a", "O3b"]


def load(case):
    spec = importlib.util.spec_from_file_location("fixed_" + case, os.path.join(root, case, "fixed.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def rate(vals):
    h = sum(v is True for v in vals); n = sum(v is False for v in vals); u = sum(v is None for v in vals)
    return h, n, u


def probe(d, rng, kind):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        if v.dtype == bool:
            out[k] = (rng.random(v.shape) < 0.5) if kind == "noise" else np.zeros(v.shape, bool)
        else:
            out[k] = rng.standard_normal(v.shape) if kind == "noise" else np.zeros(v.shape)
    return out


for case in cases:
    m = load(case)
    crit = m.criterion
    ctrl = m.STUDY.controls[0]
    S = len(m.STUDY.worlds) + len(m.STUDY.controls) + len(m.STUDY.premises) + len(m.STUDY.relational) + 2
    rng = np.random.default_rng(777)
    res = {"plus": [], "minus": [], "control(plus)": [], "noise": [], "zeros": []}
    tcrit = []
    for i in range(NS):
        dp = m.plus(rng)
        t0 = time.perf_counter(); r = crit(dp); tcrit.append(time.perf_counter() - t0)
        res["plus"].append(r)
        res["minus"].append(crit(m.minus(rng)))
        res["control(plus)"].append(crit(ctrl.transform(dp, rng)))
    for i in range(NP):
        dp = m.plus(rng)
        res["noise"].append(crit(probe(dp, rng, "noise")))
        res["zeros"].append(crit(probe(dp, rng, "zeros")))
    # repeatability
    dp = m.plus(np.random.default_rng(5))
    rep = crit(dp) == crit(dp)
    # timing: g and t
    gts = []
    for i in range(50):
        t0 = time.perf_counter(); dp = m.plus(rng); gts.append(time.perf_counter() - t0)
    tts = []
    for i in range(50):
        dp = m.plus(rng)
        t0 = time.perf_counter(); crit(dp); tts.append(time.perf_counter() - t0)
    t, g = float(np.mean(tts)), float(np.mean(gts))
    print(f"== {case}  (S={S}, repeatable={rep})")
    for k, v in res.items():
        h, n, u = rate(v)
        tot = h + n + u
        print(f"   {k:14s} holds {h}/{tot}  fails {n}  undefined {u}  rate_holds={h / tot:.3f}")
    est = 2 * 200 * (S + 1) * (t + g)
    print(f"   timing: t={t * 1e3:.3f} ms  g={g * 1e3:.3f} ms  estimate={est:.1f} s")
