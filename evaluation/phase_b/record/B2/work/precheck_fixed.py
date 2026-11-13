"""Plain-Python pre-check of the FIXED criterion only (never imports faulty.py).
Usage: py precheck_fixed.py <case id> <n_plus_minus> [seed]
Prints: rate of True / False / None on plus and minus samples, on noise and zero probes, and timing."""
import importlib.util
import os
import sys
import time

import numpy as np

sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
HERE = os.path.dirname(os.path.abspath(__file__))


def load(case):
    path = os.path.join(HERE, "..", "cases", case, "fixed.py")
    spec = importlib.util.spec_from_file_location("fixed_" + case.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def probe(d, rng, kind):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        if kind == "zeros":
            out[k] = np.zeros_like(v)
        elif v.dtype == bool:
            out[k] = rng.random(v.shape) < 0.5
        else:
            out[k] = rng.standard_normal(v.shape)
    return out


def tally(vals):
    n = len(vals)
    return "True %.3f  False %.3f  None %.3f  (n=%d)" % (
        sum(v is True for v in vals) / n, sum(v is False for v in vals) / n, sum(v is None for v in vals) / n, n)


if __name__ == "__main__":
    case = sys.argv[1]
    n = int(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    mod = load(case)
    rng = np.random.default_rng(seed)
    res = {}
    for name in ("plus", "minus"):
        fn = getattr(mod, name)
        res[name] = [mod.criterion(fn(rng)) for _ in range(n)]
        print(case, name, tally(res[name]))
    base = mod.plus(rng)
    nz = [mod.criterion(probe(base, rng, "noise")) for _ in range(min(n, 100))]
    print(case, "noise probe", tally(nz))
    zr = [mod.criterion(probe(base, rng, "zeros")) for _ in range(3)]
    print(case, "zeros probe", zr)
    # determinism: same data twice
    s = mod.plus(rng)
    print(case, "deterministic:", mod.criterion(s) == mod.criterion(s))
    # timing
    t0 = time.perf_counter()
    samples = [mod.plus(rng) for _ in range(30)]
    g = (time.perf_counter() - t0) / 30
    t0 = time.perf_counter()
    for s in samples:
        mod.criterion(s)
    t = (time.perf_counter() - t0) / 30
    S = 2 + 1 + 0 + 0 + 2   # worlds plus, minus; one control; no premises or relational pairs; two probes
    print(case, "timing t=%.4f s  g=%.4f s  S=%d  estimate=%.0f s" % (t, g, S, 2 * 200 * (S + 1) * (t + g)))
