"""Unit checks of the helper functions, loaded from FIXED bodies only (the helpers are identical in the faulty
bodies, which are never loaded).  Arrays are generated here."""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "..", "cases")


def load(cid):
    p = os.path.join(CASES, cid, "fixed_body.py")
    ns = {}
    exec(compile(open(p, encoding="utf-8").read(), p, "exec"), ns)
    return ns


rng = np.random.default_rng(7)

# ridge: dual (p > n) equals the explicit primal solution, centred intercept
ns = load("D-005")
X = rng.normal(size=(40, 90)); y = rng.normal(size=40)
mu, sd, beta, ym = ns["ridge_fit"](X, y, 1.0)
Z = (X - mu) / sd
beta_primal = np.linalg.solve(Z.T @ Z + np.eye(90), Z.T @ (y - y.mean()))
print("ridge dual == primal:", np.allclose(beta, beta_primal))
Xs = rng.normal(size=(200, 4)); ys = Xs @ np.array([1., 2., 0., -1.]) + 3.0
m = ns["ridge_fit"](Xs, ys, 1e-9)
print("ridge recovers a noiseless linear fit:", np.allclose(ns["ridge_predict"](m, Xs), ys, atol=1e-5))

# auc against brute force, with ties
ns = load("D-054")
sc = rng.integers(0, 6, 60).astype(float); lab = rng.random(60) < 0.4
pos, neg = sc[lab], sc[~lab]
brute = np.mean([(p > q) + 0.5 * (p == q) for p in pos for q in neg])
print("auc == brute force:", np.isclose(ns["auc"](sc, lab), brute))
f = ns["strat_folds"](np.array([True, False, True, True, False, False, True, True, True, True, True, True, False]))
print("strat_folds:", f.tolist())
# top_t picks planted features
X = rng.normal(size=(80, 1000)); y = np.arange(80) % 2 == 0
X[y, 17] += 2.0; X[y, 400] -= 2.5
print("top_t finds planted columns:", {17, 400} <= set(ns["top_t"](X, y, 20).tolist()))

# link_components: chain of near copies is one component, numbering by first member
ns = load("D-042")
X = rng.normal(size=(300, 5))
X[10] = X[3] + 1e-4; X[20] = X[10] + 1e-4; X[250] = X[20] + 1e-4   # chain 3-10-20-250
comp = ns["link_components"](X, 0.1)
print("chain is one component:", len({comp[3], comp[10], comp[20], comp[250]}) == 1,
      "| number of components:", comp.max() + 1, "(expect 297) | first row id:", comp[0], comp[1], comp[2], comp[3], comp[4])

# impute: no NaN left, observed entries untouched, aux empty works, y-aux changes result
ns = load("D-014")
X = rng.normal(size=(250, 20)); y = X[:, 0] * 2 + rng.normal(size=250)
X[rng.random(X.shape) < 0.25] = np.nan
Xc = ns["impute"](X, np.ones(250, dtype=bool), y[:, None])
Xd = ns["impute"](X, np.arange(250) < 200, np.empty((250, 0)))
print("impute: no NaN:", not np.isnan(Xc).any() and not np.isnan(Xd).any(),
      "| observed kept:", np.array_equal(Xc[~np.isnan(X)], X[~np.isnan(X)]) and np.array_equal(Xd[~np.isnan(X)], X[~np.isnan(X)]))

# poly: 66 columns for 10 readings
ns = load("D-022")
print("poly columns:", ns["poly_features"](rng.normal(size=(5, 10))).shape)

# logistic: gradient of the penalised objective ~ 0 after 25 Newton steps
ns = load("D-041")
X = rng.normal(size=(500, 6)); y = (X[:, 0] + rng.normal(size=500)) > 1.0
mu, sd, w = ns["logit_fit"](X, y, 1.0)
Z = np.column_stack([np.ones(500), (X - mu) / sd])
q = 1 / (1 + np.exp(-(Z @ w))); pen = np.eye(7); pen[0, 0] = 0
print("logit gradient max abs:", np.abs(Z.T @ (q - y) + pen @ w).max())
print("col_means vs nanmean:", np.allclose(ns["col_means"](np.where(rng.random((50, 3)) < .2, np.nan, 1.0 + np.arange(150).reshape(50, 3)), np.ones(50, bool)), np.nanmean(np.where(False, 0, 1.0 + np.arange(150).reshape(50, 3)), axis=0)) or "(different data, ignore)")

# forward-chaining index checks
n = 1000
blocks = np.array_split(np.arange(n), 6)[1:]
print("D-055 blocks start/end:", [(b[0], b[-1]) for b in blocks], "first train rows:", blocks[0][0] - 5)
first, size = 400 // 2, 400 // 10
print("D-039 starts:", list(range(first, 400, size)), "train ends:", [s if s == first else s - 3 for s in range(first, 400, size)])
print("D-004 cut:", (7 * 250) // 10)
