# Scratch: accuracy of the in-criterion Student-t tail helper against scipy (helper only, not a criterion).
import numpy as np
from scipy import stats

def _t_sf(t, df):
    top = np.pi / 2.0
    def tail(a):
        th = np.linspace(a, top, 4001)
        f = np.cos(th) ** (df - 1.0)
        return float(np.sum(f[:-1] + f[1:]) * (top - a) / 4000.0 / 2.0)
    half = tail(0.0)
    p = tail(float(np.arctan(abs(t) / np.sqrt(df)))) / (2.0 * half)
    return p if t >= 0 else 1.0 - p

worst = 0
for df in [1, 2, 3, 5, 10, 20, 44, 45, 100, 116, 117, 146, 296, 797]:
    for t in [-3, -1.7, -0.3, 0, 0.5, 1.3, 1.65, 2.0, 3.0, 5.0, 8.0]:
        a = _t_sf(t, df); b = stats.t.sf(t, df)
        worst = max(worst, abs(a - b))
        if abs(a - b) > 1e-5:
            print("BAD", df, t, a, b)
print("max abs err", worst)
