import sys, os, importlib.util
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pkg"))
spec = importlib.util.spec_from_file_location("fx_o3b", os.path.join(ROOT, "cases", "O3-B", "fixed.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out = []
for i in range(400):
    rng = np.random.default_rng(11000 + i)
    d = m.plus(rng)
    d = {**d, "debt_ratio": d["debt_ratio"][rng.permutation(d["debt_ratio"].shape[0])]}
    out.append(m.criterion(d))
print("O3-B fixed, shuffle probe (rows of debt_ratio permuted relative to growth), 400 samples: hold", sum(v is True for v in out), "fail", sum(v is False for v in out), "none", sum(v is None for v in out))
