# Test of the shared Welch p-value helper (numpy-only incomplete beta). Not a criterion.
import numpy as np

def _lgam(z):
    c = (676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
         12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)
    z = z - 1.0
    x = 0.99999999999980993
    for i in range(8):
        x += c[i] / (z + i + 1.0)
    t = z + 7.5
    return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

def _betacf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    dd = 1.0 - qab * x / qap
    if abs(dd) < tiny:
        dd = tiny
    dd = 1.0 / dd
    h = dd
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        h *= dd * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        dd = 1.0 + aa * dd
        if abs(dd) < tiny:
            dd = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        dd = 1.0 / dd
        de = dd * c
        h *= de
        if abs(de - 1.0) < 1e-14:
            break
    return h

def _ibeta(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = np.exp(_lgam(a + b) - _lgam(a) - _lgam(b) + a * np.log(x) + b * np.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b

def t_sf(t, df):
    if t == 0.0:
        return 0.5
    tail = 0.5 * _ibeta(0.5 * df, 0.5, df / (df + t * t))
    return tail if t > 0 else 1.0 - tail

# known one-sided critical values: P(T>t)=0.05
for df, tc in [(1, 6.313752), (2, 2.919986), (10, 1.812461), (20, 1.724718), (38, 1.685954), (58, 1.671553), (1000, 1.646379)]:
    print(df, tc, t_sf(tc, df))
print("lgam(0.5)", _lgam(0.5), 0.5*np.log(np.pi))
print("lgam(10)", _lgam(10.0), np.log(362880.0))
print("t=2.228,df=10 two-sided 0.05 -> sf", t_sf(2.228139, 10))
