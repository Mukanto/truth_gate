import sys, time
sys.path.insert(0, r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\work")
import numpy as np
from scipy import stats
from helpers import SF
ns = {"np": np}
exec("def f():\n" + SF + "    return _sf\n", ns)
_sf = ns["f"]()
worst = 0
for df in [1, 1.5, 2, 3, 7, 14, 19, 23.7, 39, 98, 118, 238, 298, 598]:
    t = np.array([-6, -3, -1.7, -0.3, 0, 0.3, 1.2, 1.7, 2.0, 2.5, 3.0, 3.58, 5, 8.0])
    a = _sf(t, df); b = stats.t.sf(t, df)
    err = np.max(np.abs(a - b)); rel = np.max(np.abs(a - b) / np.maximum(b, 1e-12)[b > 1e-6].max()) if False else 0
    r = np.max(np.abs(a[b > 1e-4] / b[b > 1e-4] - 1))
    worst = max(worst, err)
    print(df, "abs err %.2e  rel err (p>1e-4) %.2e" % (err, r))
# vector with varying df
t = np.random.default_rng(1).normal(0, 2, 250); df = np.random.default_rng(2).uniform(5, 28, 250)
print("vec", np.max(np.abs(_sf(t, df) - stats.t.sf(t, df))))
print("scalar", _sf(1.7, 20), stats.t.sf(1.7, 20), _sf(np.float64(0.0), 5))
t0 = time.time()
for _ in range(20): _sf(np.linspace(0, 5, 1000), 39)
print("time 1000 voxels", (time.time() - t0) / 20)
