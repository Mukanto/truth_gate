"""Scratch: cross-check of the repaired B1-09 fixed criterion against a scipy re-implementation (fixed.py only)."""
import sys
sys.path.insert(0, r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\work")
import numpy as np
from scipy import stats
from precheck_fixed import load_fixed

def ref(d):
    x = (d["act_session1"] + d["act_session2"]) / 2.0
    y = d["trait"]
    p = np.array([stats.pearsonr(x[:8, v], y[:8], alternative="greater").pvalue for v in range(x.shape[1])])
    ch = np.where(p < 0.005)[0]
    if ch.size == 0:
        return None
    return bool(np.mean([stats.pearsonr(x[8:, v], y[8:]).statistic for v in ch]) >= 0.5)

mod = load_fixed("B1-09"); rng = np.random.default_rng(81909); dis = 0
for w in ("plus", "minus"):
    for _ in range(60):
        d = mod.STUDY.worlds[w].generate(rng)
        dis += mod.criterion(d) != ref(d)
print("disagreements", dis, "of 120")
