"""Pre-check of the FIXED criterion only (never imports faulty.py).

usage: py precheck.py <case id> <n samples per stream> [seed0]
Counts how often the fixed criterion holds / fails / abstains on plus, minus, the declared controls
(applied to plus samples), the noise probe and the zeros probe (as agent_docs/GATE.md describes them),
and measures t (mean time of one call on plus samples) and g (mean time of one plus generation).
"""
import importlib.util
import pathlib
import sys
import time

PKG = r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\pkg"
sys.path.insert(0, PKG)
import numpy as np  # noqa: E402

ROOT = pathlib.Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\cases")


def load(case):
    path = ROOT / case / "fixed.py"
    spec = importlib.util.spec_from_file_location("fixed_" + case.replace("-", "_"), str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def noise_probe(d, rng):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        if v.dtype == bool:
            out[k] = rng.random(v.shape) < 0.5
        else:
            out[k] = rng.normal(size=v.shape)
    return out


def zeros_probe(d, rng=None):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        out[k] = np.zeros(v.shape, dtype=bool) if v.dtype == bool else np.zeros(v.shape)
    return out


def tally(vals):
    h = sum(1 for v in vals if v is True)
    f = sum(1 for v in vals if v is False)
    u = sum(1 for v in vals if v is None)
    return h, f, u


def main():
    case = sys.argv[1]
    n = int(sys.argv[2])
    seed0 = int(sys.argv[3]) if len(sys.argv) > 3 else 777000
    mod = load(case)
    crit = mod.STUDY.criteria[0].fn
    plus = mod.STUDY.worlds["plus"].generate
    minus = mod.STUDY.worlds["minus"].generate
    res = {}
    tt = 0.0
    gg = 0.0
    plus_data = []
    for i in range(n):
        rng = np.random.default_rng(seed0 + i)
        t0 = time.perf_counter()
        d = plus(rng)
        gg += time.perf_counter() - t0
        plus_data.append(d)
    out = []
    for d in plus_data:
        t0 = time.perf_counter()
        out.append(crit(d))
        tt += time.perf_counter() - t0
    res["plus"] = tally(out)
    out = []
    for i in range(n):
        d = minus(np.random.default_rng(seed0 + 100000 + i))
        out.append(crit(d))
    res["minus"] = tally(out)
    for c in mod.STUDY.controls:
        out = []
        for i, d in enumerate(plus_data):
            r = np.random.default_rng(seed0 + 200000 + i)
            out.append(crit(c.transform(d, r)))
        res["control:" + c.id] = tally(out)
    out = [crit(noise_probe(d, np.random.default_rng(seed0 + 300000 + i))) for i, d in enumerate(plus_data)]
    res["noise"] = tally(out)
    out = [crit(zeros_probe(d)) for d in plus_data]
    res["zeros"] = tally(out)
    print(case, "n =", n, "(holds, fails, None)")
    for k, v in res.items():
        print("  %-60s %s  rate %.3f" % (k, v, v[0] / n))
    print("  t (mean call on plus, %d calls) = %.4f s   g (mean plus generation) = %.4f s" % (n, tt / n, gg / n))
    S = 2 + len(mod.STUDY.controls) + len(getattr(mod.STUDY, "premises", []) or []) + len(getattr(mod.STUDY, "relational", []) or []) + 2
    print("  S = %d, estimate 2*200*(S+1)*(t+g) = %.0f s" % (S, 2 * 200 * (S + 1) * (tt / n + gg / n)))


if __name__ == "__main__":
    main()
