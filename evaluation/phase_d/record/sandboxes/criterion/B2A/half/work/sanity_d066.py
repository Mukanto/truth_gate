"""Extra sanity runs of the FIXED body of D-066 (B2A-R4) on self-generated arrays; faulty body never loaded."""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "..", "cases", "D-066", "fixed_body.py")
ns = {}
exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)
rng = np.random.default_rng(5)
X = rng.normal(size=(1000, 15)); yb = rng.random(1000) < 0.1
X[yb, :6] += 3.0
print("clustered rare class, positives", yb.sum(), "->", ns["criterion"]({"X": X, "y": yb}))
X = rng.normal(size=(1000, 15))
print("noise, same labels ->", ns["criterion"]({"X": X, "y": yb}))
