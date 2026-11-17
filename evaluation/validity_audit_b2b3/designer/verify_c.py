"""Designer's own check of audit findings W1, W2 (B2-03, B2-06) and W4 (B3-12) of the Phase C validity audit.

Loads the frozen case files from the repository, replaces the final decision line with a return of the statistic,
draws the gate's minus samples (stream_rng(20261105, "world:minus", i)) and prints the statistic's mean and 95th
percentile, and the hold count. For B3-12 it reruns the fixed criterion on 2000 minus samples with the season term
removed, and with the AR(1) waves removed, by editing the world source."""
import os
import sys
import types

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, REPO)
import numpy as np  # noqa: E402
from truth_gate.sampling import stream_rng  # noqa: E402

CASES = os.path.join(REPO, "evaluation", "phase_c", "cases")


def load(case, twin, old=None, new=None, world_edits=()):
    src = open(os.path.join(CASES, case, twin + ".py"), encoding="utf-8").read()
    if old is not None:
        assert src.count(old) == 1, (case, twin, old)
        src = src.replace(old, new)
    for a, b in world_edits:
        assert src.count(a) == 1, (case, twin, a)
        src = src.replace(a, b)
    mod = types.ModuleType(f"v_{case}_{twin}".replace("-", "_"))
    exec(compile(src, f"{case}/{twin}.py", "exec"), mod.__dict__)
    return mod


def stats(mod, n, threshold=None):
    vals = []
    for i in range(n):
        d = mod.minus(stream_rng(20261105, "world:minus", i))
        vals.append(mod.criterion(d))
    return np.array(vals, dtype=float)


for case, line, thr in (("B2-03", "    return bool(0.5 * (tp / pos + tn / neg) >= THRESHOLD)", 0.65),
                        ("B2-06", "    return bool(auc(score, y) >= THRESHOLD)", 0.75)):
    new = line.replace("return bool(", "return float(").replace(" >= THRESHOLD)", ")")
    for twin in ("faulty", "fixed"):
        v = stats(load(case, twin, line, new), 200)
        print(f"{case} {twin}: mean {v.mean():.3f}  q95 {np.quantile(v, 0.95):.3f}  holds(>= {thr}) {int((v >= thr).sum())}/200")

line = "    return bool(beta > 0.0 and t_sf(t, df) < 0.05)"
for label, edits in (("as declared", ()),
                     ("no season", (("season = 80.0 * np.cos", "season = 0.0 * np.cos"),)),
                     ("no AR(1) waves", (("waves = _ar1(rng, months, 0.6, 55.0)", "waves = 0.0 * _ar1(rng, months, 0.6, 55.0)"),))):
    mod = load("B3-12", "fixed", world_edits=edits)
    h = sum(bool(mod.criterion(mod.minus(stream_rng(20261105, "world:minus", i)))) for i in range(2000))
    print(f"B3-12 fixed, {label}: holds in minus {h}/2000 = {h / 2000:.3f}")
