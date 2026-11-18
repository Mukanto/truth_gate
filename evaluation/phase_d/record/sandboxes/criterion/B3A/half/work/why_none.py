"""Why the fixed bodies of D-006 and D-015 return None on some independent random smoke arrays (fixed code only)."""
import sys, importlib.util, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_fixed as rf
m15 = rf.load("D-015")
for rep in range(3):
    d = rf.smoke("D-015", np.random.default_rng(1000 + rep))
    mod_path = os.path.join(rf.ROOT, "D-015", "fixed_body.py")
    spec = importlib.util.spec_from_file_location("m", mod_path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    icc = m._corr(d["bmi_baseline"], d["bmi_baseline_retest"])
    k = 1 - icc
    res = m._change_stats(d["bmi_baseline"], d["bmi_followup"], k)
    print("D-015 rep", rep, "icc %.3f k %.3f" % (icc, k), "res", res, "criterion", m15(d))
bmi_all = [rf.smoke("D-006", np.random.default_rng(1000 + rep))["bmi"] for rep in range(3)]
for rep, bmi in enumerate(bmi_all):
    n, mm = bmi.shape
    X = np.column_stack([np.ones(mm), np.arange(mm, dtype=float)])
    XtXi = np.linalg.inv(X.T @ X)
    bhat = bmi @ X @ XtXi
    res = bmi - bhat @ X.T
    s2 = np.sum(res * res) / (n * (mm - 2))
    G = np.cov(bhat, rowvar=False) - s2 * XtXi
    print("D-006 rep", rep, "G00 %.5f G11 %.6f" % (G[0, 0], G[1, 1]))
