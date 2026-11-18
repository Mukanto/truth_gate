# Scratch: population (pooled over 500 draws) within-patient association of expired-gas VO2 with measured DO2,
# to confirm the size of the measurement-error attenuation in plus and its absence in minus. Not a per-dataset rule.
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pkg"))
import numpy as np
spec = importlib.util.spec_from_file_location("sk", os.path.join(HERE, "skeletons", "D-008.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for w in ("plus", "minus"):
    xs, ys = [], []
    for i in range(500):
        d = getattr(m, w)(np.random.default_rng([4, i]))
        do2 = 10 * d["cardiac_output"] * d["arterial_o2_content"]
        xs.append((do2 - do2.mean(1, keepdims=True)).ravel())
        ys.append((d["vo2_expired_gas"] - d["vo2_expired_gas"].mean(1, keepdims=True)).ravel())
    x, y = np.concatenate(xs), np.concatenate(ys)
    print(w, "pooled within-patient slope (population)", round(float((x * y).sum() / (x * x).sum()), 4))
