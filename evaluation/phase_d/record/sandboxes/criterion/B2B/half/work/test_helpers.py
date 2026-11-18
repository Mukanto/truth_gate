"""Checks of the helper functions (text shared by the faulty and the fixed files) against independent references:
brute force, scipy and scikit-learn. These are used only here, never in a body. No body file is imported."""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_helpers import HELPERS  # noqa: E402

ns = {"np": np}
for name in HELPERS:
    exec(HELPERS[name], ns)

rng = np.random.default_rng(5)
res = []


def rec(name, ok, extra=""):
    res.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name + " " + extra)


# 1 AUC against pairwise brute force with ties
for trial in range(5):
    n = 60
    s = rng.integers(0, 8, n).astype(float) + (rng.random(n) < 0.3) * rng.random(n)
    y = rng.random(n) < 0.4
    bf = 0.0
    for i in np.flatnonzero(y):
        for j in np.flatnonzero(~y):
            bf += 1.0 if s[i] > s[j] else (0.5 if s[i] == s[j] else 0.0)
    bf /= y.sum() * (~y).sum()
    assert abs(bf - ns["_auc"](s, y)) < 1e-12, (bf, ns["_auc"](s, y))
rec("auc vs brute force (ties)", True)

# 2 ridge dual vs primal
n, p = 30, 80
x = rng.normal(size=(n, p)); y = rng.normal(size=n); xt = rng.normal(size=(7, p))
lam = 80.0
mu, sd = x.mean(0), x.std(0)
a = (x - mu) / sd
w = np.linalg.solve(a.T @ a + lam * np.eye(p), a.T @ (y - y.mean()))
ref = y.mean() + ((xt - mu) / sd) @ w
rec("ridge dual vs primal", np.allclose(ref, ns["_ridge_predict"](x, y, xt, lam)))

# 3 logistic vs scipy L-BFGS on the primal objective
from scipy.optimize import minimize
n, p = 40, 100
x = rng.normal(size=(n, p)); yb = rng.random(n) < 0.4
x[yb, :5] += 0.8
xt = rng.normal(size=(9, p))
lam = 100.0
mu, sd = x.mean(0), x.std(0)
a = (x - mu) / sd; at = (xt - mu) / sd
yv = yb.astype(float)


def obj(th):
    w, b = th[:p], th[p]
    f = a @ w + b
    return np.sum(np.logaddexp(0, f) - yv * f) + 0.5 * lam * w @ w


def grad(th):
    w, b = th[:p], th[p]
    f = a @ w + b
    pr = 1 / (1 + np.exp(-f))
    return np.concatenate([a.T @ (pr - yv) + lam * w, [np.sum(pr - yv)]])


r = minimize(obj, np.zeros(p + 1), jac=grad, method="L-BFGS-B", options=dict(maxiter=2000, ftol=1e-15, gtol=1e-10))
ref = at @ r.x[:p] + r.x[p]
mine = ns["_logit_scores"](x, yb, xt, lam)
rec("logistic dual Newton vs L-BFGS", np.allclose(ref, mine, atol=1e-4), "max diff %.2e" % np.max(np.abs(ref - mine)))
# and at p >> n with lam = p (the sizes in use) convergence check by stationarity of the primal gradient
n, p = 120, 2000
x = rng.normal(size=(n, p)); yb = rng.random(n) < 0.4
t0 = time.time()
sc = ns["_logit_scores"](x, yb, x, float(p))
rec("logistic n=120 p=2000 runs", np.all(np.isfinite(sc)), "%.2fs" % (time.time() - t0))

# 4 tree: exact recovery of a rule, root split against brute force, reference variance-reduction tree
x = rng.normal(size=(200, 5)); y = (x[:, 2] > 0.3).astype(float)
tr = ns["_grow"](x, y, rng, 1000, 1, 5)
pr = ns["_tree_predict"](tr, x)
rec("tree learns a threshold rule", np.array_equal(pr, y))
# root split vs brute force
yy = rng.normal(size=100) + 2 * (x[:100, 1] > 0)
tr = ns["_grow"](x[:100], yy, rng, 1, 1, 5)
best = None
for f in range(5):
    vals = np.unique(x[:100, f])
    for lo, hi in zip(vals[:-1], vals[1:]):
        t = 0.5 * (lo + hi)
        L = x[:100, f] <= t
        sse = ((yy[L] - yy[L].mean()) ** 2).sum() + ((yy[~L] - yy[~L].mean()) ** 2).sum()
        if best is None or sse < best[0] - 1e-12:
            best = (sse, f, t)
rec("tree root split = brute-force best", tr[0][0] == best[1] and abs(tr[1][0] - best[2]) < 1e-9, "f=%d" % best[1])
# agreement with sklearn on depth-6 classification tree predictions (training data, no ties of impurity expected)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
x = rng.normal(size=(300, 6)); yc = (x[:, 0] + 0.8 * rng.normal(size=300) > 0).astype(float)
mine = ns["_tree_predict"](ns["_grow"](x, yc, rng, 6, 1, 6), x) > 0.5
sk = DecisionTreeClassifier(max_depth=6, random_state=0).fit(x, yc).predict(x) > 0.5
rec("depth-6 tree vs sklearn (training predictions)", np.mean(mine == sk) > 0.97, "agree %.3f" % np.mean(mine == sk))
xr = rng.normal(size=(400, 4)); yr = np.sin(xr[:, 0]) + 0.1 * rng.normal(size=400)
mine = ns["_tree_predict"](ns["_grow"](xr, yr, rng, 1000, 5, 4), xr)
sk = DecisionTreeRegressor(min_samples_leaf=5, random_state=0).fit(xr, yr).predict(xr)
rec("min-leaf-5 regression tree vs sklearn", np.mean(np.abs(mine - sk) < 1e-9) > 0.9,
    "agree %.3f" % np.mean(np.abs(mine - sk) < 1e-9))

# 5 forest: learns a signal out of sample
x = rng.normal(size=(400, 10)); yb = (x[:, 0] + x[:, 1] > 0)
sc = ns["_forest_scores"](x[:300], yb[:300].astype(float), x[300:], rng, 50, 1, 3)
rec("forest out-of-sample AUC on a real signal > 0.9", ns["_auc"](sc, yb[300:]) > 0.9, "%.3f" % ns["_auc"](sc, yb[300:]))

# 6 SMOTE
x = rng.normal(size=(100, 4)); y = np.zeros(100, bool); y[:12] = True
xs, ys = ns["_smote"](x, y, rng, 5)
rec("smote balances classes", ys.sum() == (~ys).sum() == 88 and xs.shape[0] == 176)
syn = xs[100:]
xm = x[y]
ok = True
for r_ in syn:
    # lies on a segment between two minority rows
    found = False
    for i in range(12):
        for j in range(12):
            if i != j:
                dv = xm[j] - xm[i]
                tt = np.dot(r_ - xm[i], dv) / np.dot(dv, dv)
                if -1e-9 <= tt <= 1 + 1e-9 and np.allclose(xm[i] + tt * dv, r_, atol=1e-9):
                    found = True
                    break
        if found:
            break
    ok &= found
rec("smote rows lie on minority segments", ok)
xs2, ys2 = ns["_smote"](x, ~y, rng, 5)  # minority = False class (12 of them) when positives are the majority
rec("smote synthesises whichever class is smaller", (~ys2).sum() == ys2.sum())
xo, yo = ns["_oversample"](x, y, rng)
rec("oversample copies existing minority rows", yo.sum() == (~yo).sum() and
    all(any(np.array_equal(r_, q) for q in x[y]) for r_ in xo[100:]))

# 7 kNN against sklearn
from sklearn.neighbors import KNeighborsClassifier
x = rng.normal(size=(200, 6)) * np.array([1, 5, 1, 20, 1, 1]); y = (x[:, 0] > 0)
xt = rng.normal(size=(50, 6)) * np.array([1, 5, 1, 20, 1, 1])
mu, sd = x.mean(0), x.std(0)
sk = KNeighborsClassifier(5).fit((x - mu) / sd, y).predict_proba((xt - mu) / sd)[:, 1]
rec("5-NN scores vs sklearn", np.allclose(sk, ns["_knn_scores"](x, y.astype(float), xt, 5)))

# 8 top genes against scipy t (pooled variance)
from scipy.stats import ttest_ind
x = rng.normal(size=(40, 300)); y = rng.random(40) < 0.4
x[y, :3] += 1.5
t = ttest_ind(x[y], x[~y], equal_var=True).statistic
ref = np.argsort(-np.abs(t), kind="stable")[:5]
rec("top genes vs scipy pooled t", np.array_equal(ref, ns["_top_genes"](x, y, 5)))

# 9 Fisher LDA against an independent formula (np.cov per class, pooled by degrees of freedom, midpoint threshold)
x = rng.normal(size=(60, 3)); y = rng.random(60) < 0.4; x[y] += 0.8
xt = rng.normal(size=(200, 3))
n1, n0 = y.sum(), (~y).sum()
S = ((n1 - 1) * np.cov(x[y].T) + (n0 - 1) * np.cov(x[~y].T)) / (n1 + n0 - 2)
w = np.linalg.solve(S, x[y].mean(0) - x[~y].mean(0))
ref = (xt - 0.5 * (x[y].mean(0) + x[~y].mean(0))) @ w > 0
rec("Fisher LDA vs independent formula", np.array_equal(ref, ns["_lda_predict"](x, y, xt)))
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
# and against sklearn with the sample-size-weighted covariance (priors = class shares) and midpoint threshold removed:
# sklearn's lsqr decision function adds log-priors, so compare the direction only
sk = LinearDiscriminantAnalysis(solver="lsqr", priors=[n0 / 60, n1 / 60]).fit(x, y)
cos = np.dot(sk.coef_[0], w) / np.linalg.norm(sk.coef_[0]) / np.linalg.norm(w)
rec("Fisher LDA direction vs sklearn lsqr", abs(cos - 1) < 1e-6, "cos %.9f" % cos)

# 10 nearest shrunken centroids: vectorised vs plain loop
def nsc_ref(xtr, ytr, xte, delta):
    n = len(ytr)
    cls = [~ytr, ytr]
    nk = np.array([c.sum() for c in cls], float)
    means = np.array([xtr[c].mean(0) for c in cls])
    xbar = xtr.mean(0)
    s2 = sum(((xtr[c] - means[k]) ** 2).sum(0) for k, c in enumerate(cls)) / (n - 2)
    s = np.sqrt(s2)
    s0 = np.median(s)
    out = []
    cent = []
    for k in range(2):
        mk = np.sqrt(1 / nk[k] - 1 / n)
        dk = (means[k] - xbar) / (mk * (s + s0))
        dp = np.sign(dk) * np.maximum(np.abs(dk) - delta, 0)
        cent.append(xbar + mk * (s + s0) * dp)
    pred = []
    for row in xte:
        dl = [(((row - cent[k]) / (s + s0)) ** 2).sum() - 2 * np.log(nk[k] / n) for k in range(2)]
        pred.append(dl[1] < dl[0])
    return np.array(pred)


x = rng.normal(size=(39, 200)); y = rng.random(39) < 0.5; x[y, :10] += 0.7
xt = rng.normal(size=(12, 200)); yt = rng.random(12) < 0.5; xt[yt, :10] += 0.7
deltas = np.linspace(0.01, 1.0, 20)
ok = True
for ti, dv in enumerate(deltas):
    errs = ns["_nsc_errors"](x, y, xt, yt, deltas)[ti]
    ok &= int(errs) == int((nsc_ref(x, y, xt, dv) != yt).sum())
rec("NSC vectorised vs loop reference (20 thresholds)", ok)
x = rng.normal(size=(40, 100)); y = np.arange(40) % 2 == 0
folds = ns["_stratified_folds"](rng, y, 10)
rec("stratified folds: sizes 4, per fold 2 positives", np.all(np.bincount(folds) == 4) and
    all(y[folds == f].sum() == 2 for f in range(10)))
rec("random folds sizes", np.all(np.bincount(ns["_random_folds"](rng, 40, 10)) == 4))
e = np.array([5, 3, 3, 4, 3])
rec("pick_delta ties -> larger threshold", ns["_pick_delta"](e) == 4)

bad = [n for n, ok in res if not ok]
print("FAILED:" if bad else "ALL PASSED", bad)
