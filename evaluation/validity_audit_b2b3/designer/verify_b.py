"""Designer's own check of two findings of the Phase B validity audit.

1. B2-06: on the gate's 200 `minus` samples, the faulty criterion's balanced accuracy is raised by the leak but stays
   below the claim's threshold 0.75 (the audit's "the leak operates, threshold not crossed").
2. The one-sided 95% Wilson lower bound of 8 of 12, printed as 0.432 in the Phase B report (B-3) and the Phase C report
   (B-2 clean passes)."""
import os
import sys
import types
from math import sqrt

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)
import numpy as np  # noqa: E402
from truth_gate.sampling import stream_rng  # noqa: E402

CASE = os.path.join(REPO, "evaluation", "phase_b", "cases", "B2-06")
for twin, var in (("faulty", "ya"), ("fixed", "y")):
    src = open(os.path.join(CASE, twin + ".py"), encoding="utf-8").read()
    old = f"    return bool(balanced(pred, {var}) >= thr)"
    assert src.count(old) == 1
    src = src.replace(old, f"    return float(balanced(pred, {var}))")
    mod = types.ModuleType(f"b206_{twin}")
    exec(compile(src, f"B2-06/{twin}.py", "exec"), mod.__dict__)
    v = np.array([mod.criterion(mod.minus(stream_rng(20261105, "world:minus", i))) for i in range(200)], dtype=float)
    print(f"B2-06 {twin}: balanced accuracy on minus mean {v.mean():.3f}  q95 {np.quantile(v, 0.95):.3f}  "
          f">= 0.75: {int((v >= 0.75).sum())}/200")

z = 1.6448536269514722
k, n = 8, 12
p = k / n
lower = (p + z * z / (2 * n) - z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
print(f"Wilson one-sided 95% lower bound, 8 of 12: {lower:.6f} (to three places {lower:.3f})")
