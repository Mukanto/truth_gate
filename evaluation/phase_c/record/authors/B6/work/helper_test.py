"""Scratch test of the shared p-value helper text (HELP_P from make_cases.py) against scipy.stats.t.
It tests the helper text only; no case file is imported or run."""
import sys
import numpy as np
from scipy import stats

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import make_cases

src = "def make():\n    import numpy as np\n" + make_cases.HELP_P + "    return p2t\n"
ns = {"np": np}
exec(src, ns)
p2t = ns["make"]()

worst = 0.0
rng = np.random.default_rng(1)
rows = 0
for df in [1, 1.5, 2, 3, 4.7, 8, 10, 14, 18, 27.3, 28, 38, 78, 158, 198, 1198, 5000]:
    for t in [0.0, 1e-3, 0.3, 1.0, 1.7, 2.0, 2.1, 2.5, 3.0, 5.0, 10.0, 30.0, -2.2, -7.0]:
        a = p2t(t, df)
        b = 2 * stats.t.sf(abs(t), df)
        err = abs(a - b) / max(b, 1e-300) if b > 1e-12 else abs(a - b)
        worst = max(worst, err)
        rows += 1
# infinite statistic
print("p2t(inf, 10) =", p2t(np.float64("inf"), 10.0))
# a random sweep
for _ in range(2000):
    df = rng.uniform(1, 400)
    t = rng.standard_t(df) * rng.uniform(0.5, 3)
    a = p2t(t, df)
    b = 2 * stats.t.sf(abs(t), df)
    err = abs(a - b) / b if b > 1e-12 else abs(a - b)
    worst = max(worst, err)
    rows += 1
print("points", rows, "worst relative/absolute error", worst)
# critical values used as constants
print("two-sided 5% normal critical value", stats.norm.isf(0.025))
