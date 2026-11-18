"""Sanity runs of the FIXED bodies on self-generated arrays: strong planted signal, and the allowed guards.
No rate is estimated or tuned.  Faulty bodies are never loaded."""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "..", "cases")


def crit(cid):
    p = os.path.join(CASES, cid, "fixed_body.py")
    ns = {}
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)
    return ns["criterion"]


rng = np.random.default_rng(99)


def lin(n, p, k=3, noise=0.5):
    X = rng.normal(size=(n, p))
    y = X[:, :k].sum(axis=1) + noise * rng.normal(size=n)
    return X, y


res = {}
X, y = lin(100, 150, 10, 0.3); res["D-005 signal"] = crit("D-005")({"X": X, "y": y})
X, y = lin(300, 10, 3, 0.5); y = y + X[:, 0] * X[:, 1]; res["D-022 signal"] = crit("D-022")({"X": X, "y": y})
X, y = lin(250, 20, 5, 0.5); X[rng.random(X.shape) < 0.25] = np.nan; res["D-014 signal"] = crit("D-014")({"X": X, "y": y})
n = 1200; cat = np.zeros((n, 150), bool); dist = rng.integers(0, 150, n); cat[np.arange(n), dist] = True
eff = rng.normal(size=150)[dist] * 2.0; cov = rng.normal(size=(n, 3)); y = eff + cov[:, 0] + rng.normal(size=n)
res["D-010 signal"] = crit("D-010")({"category": cat, "covariates": cov, "y": y})
X = rng.normal(size=(80, 1000)); yb = np.arange(80) % 2 == 0; X[yb, :20] += 1.5
res["D-054 signal"] = crit("D-054")({"X": X, "y": yb})
X = rng.normal(size=(600, 8)); y = X[:, 0] ** 2 + X[:, 1]; res["D-029 signal"] = crit("D-029")({"X": X, "y": y})
X = rng.normal(size=(1200, 20)); y = X[:, 0] + 0.2 * rng.normal(size=1200)
res["D-042 signal(1-NN, strong)"] = crit("D-042")({"X": X[:, :1].repeat(20, 1) * 0 + X, "y": y})
X = np.cumsum(rng.normal(size=(1000, 6)), axis=0) / 10; y = X[:, 0] + rng.normal(size=1000)
res["D-055 signal"] = crit("D-055")({"X": X, "y": y})
X = rng.normal(size=(40, 250, 5)); y = X[:, :, 0] * 2 + rng.normal(size=(40, 250)) * 0.3
res["D-004 signal"] = crit("D-004")({"X": X, "y": y})
X = rng.normal(size=(60, 30, 25)); y = X[:, :, 0] * 2 + rng.normal(size=(60, 30))
res["D-044 signal"] = crit("D-044")({"X": X, "y": y})
X, y = lin(60, 25, 3, 0.2); res["D-027 signal"] = crit("D-027")({"X": X, "y": y})
X = rng.normal(size=(1400, 25)); lo = X[:, 0] * 1.5 + X[:, 1]; yb = lo + rng.logistic(size=1400) > 4.2
X[rng.random(X.shape) < 0.3] = np.nan; res["D-041 signal (events %d)" % yb.sum()] = crit("D-041")({"X": X, "y": yb})
X, y = lin(100, 500, 20, 1.0); res["D-060 signal"] = crit("D-060")({"X": X, "y": y})
X = rng.normal(size=(1000, 15)); yb = (X[:, 0] + X[:, 1] + 0.3 * rng.normal(size=1000)) > 2.2
res["D-066 signal (pos %d)" % yb.sum()] = crit("D-066")({"X": X, "y": yb})
X = np.cumsum(rng.normal(size=(400, 3)), axis=0) / 5; y = X[:, 0] + rng.normal(size=400)
res["D-039 signal"] = crit("D-039")({"X": X, "y": y})
for k, v in res.items():
    print(k, "->", v)

print("--- guards (expect None) ---")
Xn = rng.normal(size=(100, 150)); yn = rng.normal(size=100)
Xi = Xn.copy(); Xi[0, 0] = np.nan
print("D-005 NaN in X:", crit("D-005")({"X": Xi, "y": yn}))
print("D-005 constant y:", crit("D-005")({"X": Xn, "y": np.ones(100)}))
print("D-022 constant y:", crit("D-022")({"X": rng.normal(size=(300, 10)), "y": np.ones(300)}))
print("D-054 one class:", crit("D-054")({"X": rng.normal(size=(80, 1000)), "y": np.ones(80, bool)}))
print("D-029 constant y:", crit("D-029")({"X": rng.normal(size=(600, 8)), "y": np.ones(600)}))
print("D-004 constant y:", crit("D-004")({"X": rng.normal(size=(40, 250, 5)), "y": np.ones((40, 250))}))
print("D-044 constant y:", crit("D-044")({"X": rng.normal(size=(60, 30, 25)), "y": np.ones((60, 30))}))
print("D-066 1 positive:", crit("D-066")({"X": rng.normal(size=(1000, 15)), "y": np.arange(1000) == 3}))
X = rng.normal(size=(250, 20)); X[:, 3] = np.nan
print("D-014 empty column:", crit("D-014")({"X": X, "y": rng.normal(size=250)}))
print("D-039 constant X:", crit("D-039")({"X": np.ones((400, 3)), "y": rng.normal(size=400)}))
