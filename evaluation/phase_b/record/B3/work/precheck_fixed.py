"""Plain-Python pre-check of the FIXED criterion only (never imports faulty.py).
Usage: py precheck_fixed.py B3-01 [n_samples]
Draws n plus / minus samples (seeds 1000..), the control transform of plus, and the noise / zero probes
(i.i.d. N(0,1) and all-zero arrays of the same shape); reports rates of True / False / None and timing."""
import importlib.util
import sys
import time

import numpy as np

sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b\B3\cases"

case = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
path = f"{ROOT}\\{case}\\fixed.py"
spec = importlib.util.spec_from_file_location("fixed_" + case.replace("-", "_"), path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def rates(vals):
    t = sum(v is True for v in vals)
    f = sum(v is False for v in vals)
    u = sum(v is None for v in vals)
    return f"True {t}/{len(vals)} ({t / len(vals):.3f})  False {f}  None {u}"


def run(gen, crit, k, seed0):
    out = []
    for i in range(k):
        out.append(crit(gen(np.random.default_rng(seed0 + i))))
    return out


crit = m.criterion
res_plus = run(m.plus, crit, n, 1000)
res_minus = run(m.minus, crit, n, 5000)
print(case, "fixed, plus :", rates(res_plus))
print(case, "fixed, minus:", rates(res_minus))

ctrl = m.STUDY.controls[0]


def ctrl_gen(rng):
    return ctrl.transform(m.plus(rng), rng)


res_ctrl = run(ctrl_gen, crit, n, 9000)
print(case, "fixed, control", ctrl.name if hasattr(ctrl, "name") else "", ":", rates(res_ctrl))


def noise_gen(rng):
    base = m.plus(np.random.default_rng(1))
    return {k: rng.standard_normal(v.shape) for k, v in base.items()}


def zero_gen(rng):
    base = m.plus(np.random.default_rng(1))
    return {k: np.zeros_like(v) for k, v in base.items()}


print(case, "fixed, noise probe:", rates(run(noise_gen, crit, n, 13000)))
print(case, "fixed, zeros probe:", rates(run(zero_gen, crit, 5, 0)))

# determinism
d0 = m.plus(np.random.default_rng(42))
print(case, "deterministic:", crit(d0) == crit(d0))

# timing
k = 50
t0 = time.perf_counter()
samples = [m.plus(np.random.default_rng(20000 + i)) for i in range(k)]
g = (time.perf_counter() - t0) / k
t0 = time.perf_counter()
for s in samples:
    crit(s)
t = (time.perf_counter() - t0) / k
st = m.STUDY
S = len(st.worlds) + len(st.controls) + len(getattr(st, "premises", []) or []) + len(getattr(st, "relational", []) or []) + 2
est = 2 * 200 * (S + 1) * (t + g)
print(f"{case} timing: t={t * 1e3:.3f} ms  g={g * 1e3:.3f} ms  S={S}  estimate={est:.1f} s")
