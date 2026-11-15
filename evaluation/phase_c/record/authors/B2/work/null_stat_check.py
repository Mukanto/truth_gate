"""Pre-check of the FIXED criterion's statistic itself (modified copy of fixed.py source returns the number, not the bool).
Not the faulty one; only B2-08 / B2-11 fixed."""
import sys, pathlib, re
sys.path.insert(0, r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\pkg")
import numpy as np
ROOT = pathlib.Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\cases")
def stat_fn(case, old, new):
    src = (ROOT / case / "fixed.py").read_text(encoding="utf-8")
    assert src.count(old) == 1
    ns = {"__name__": "x"}
    exec(compile(src.replace(old, new), "x", "exec"), ns)
    return ns["STUDY"].criteria[0].fn, ns
for case, old, new in [("B2-08", "return bool(hit / y.size >= THRESHOLD)", "return hit / y.size"),
                       ("B2-11", "return bool(bal_acc(pred[:, None], y)[0] >= THRESHOLD)", "return float(bal_acc(pred[:, None], y)[0])")]:
    fn, ns = stat_fn(case, old, new)
    minus = ns["STUDY"].worlds["minus"].generate
    vals = np.array([fn(minus(np.random.default_rng(5550000 + i))) for i in range(300)])
    print(case, "minus statistic: mean %.3f sd %.3f  P(>=0.6)=%.3f  P(>0.6)=%.3f  min %.3f max %.3f" % (vals.mean(), vals.std(), (vals >= 0.6 - 1e-9).mean(), (vals > 0.6 + 1e-9).mean(), vals.min(), vals.max()))
