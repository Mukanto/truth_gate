# Verification of the p-value helper only (not of any criterion): compare with numerical integration of the t density.
import numpy as np, sys, textwrap
src = open(sys.argv[1], encoding="utf-8").read()
ns = {"np": np}
exec(textwrap.dedent(src), ns)
_p2 = ns["_p2"]
def lg(x):  # numpy-only check through Stirling-free reference: use math from the test script only
    import math
    return math.lgamma(x)
def p2_num(t, df):
    # integrate t density from |t| to inf by Gauss-Legendre on a transformed variable u = 1/(1+s), s in [|t|, inf)
    c = np.exp(lg((df + 1) / 2) - lg(df / 2)) / np.sqrt(df * np.pi)
    xs, ws = np.polynomial.legendre.leggauss(400)
    u = 0.5 * (xs + 1.0); w = 0.5 * ws        # u in (0,1)
    s = abs(t) + (1.0 / u - 1.0)
    f = c * (1.0 + s * s / df) ** (-(df + 1) / 2) / (u * u)
    return 2.0 * np.sum(w * f)
worst = 0.0
for df in (1, 2, 3, 6, 7, 10, 11, 13, 18, 33, 37, 59, 94, 142, 238, 298):
    for t in (0.0, 0.1, 0.5, 1.0, 1.645, 2.0, 2.447, 3.0, 5.0, 8.0):
        a, b = _p2(t, df), p2_num(t, df)
        worst = max(worst, abs(a - b) / max(b, 1e-12) if b > 1e-9 else abs(a - b))
print("max rel. diff vs numerical integration:", worst)
print("t=2.4469118 df=6 ->", _p2(2.4469118, 6), "(expected 0.05)")
print("t=2.0 df=10 ->", _p2(2.0, 10), "(expected 0.07338803)")
print("t=1.9600 df=1e6 ->", _p2(1.96, 1000000), "(expected ~0.05)")
