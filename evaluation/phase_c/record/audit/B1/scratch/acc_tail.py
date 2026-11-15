"""Auditor helper (isolated): accuracy of the re-typed t-tail quadrature against an incomplete-beta reference."""
import math, sys
import numpy as np
sys.path.insert(0, r"E:\Claude Projects\Kapi\phase_c_private\audit\B1\scratch")
from check_tail import sf

def betacf(a, b, x):
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / d; h = d
    for m in range(1, 20000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2)); d = 1 / (1 + aa * d); c = 1 + aa / c; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2)); d = 1 / (1 + aa * d); c = 1 + aa / c; de = d * c; h *= de
        if abs(de - 1) < 1e-15:
            break
    return h

def ref(t, df):
    a, b, x = df / 2.0, 0.5, df / (df + t * t)
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x)
    I = math.exp(lbt) * betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - math.exp(lbt) * betacf(b, a, 1 - x) / b
    return 0.5 * I

for df in [1, 2, 3, 5, 7, 10, 19, 39, 60, 100, 150, 200, 238, 300, 400, 600, 800, 1000, 2000]:
    e = max(abs(float(sf(t, df)) - ref(t, df)) for t in np.linspace(0.05, 6, 120))
    print(df, f"max abs err {e:.2e}", "p(1.96):", round(float(sf(1.96, df)), 5), "ref", round(ref(1.96, df), 5))
