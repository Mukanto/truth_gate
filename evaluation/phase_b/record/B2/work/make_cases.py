"""Writes the criterion bodies of the B-2 cases into faulty.py and fixed.py.

Only the single line '    raise NotImplementedError' of each skeleton copy is replaced. Usage:
    py make_cases.py            -> writes all cases whose id is in BODIES
    py make_cases.py b2-01 ...  -> writes only those
The files are rebuilt from skeleton.py every time, so a revision is a re-run.
"""
import ast
import os
import sys
import textwrap

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")
MARK = "    raise NotImplementedError\n"

# ---------------------------------------------------------------------------------------------------------------
# shared helper text (identical in faulty and fixed of the same case)
# ---------------------------------------------------------------------------------------------------------------
H_AUC = '''
def _auc(s, y):
    p, q = s[y], s[~y]
    diff = p[:, None] - q[None, :]
    return float(((diff > 0).sum() + 0.5 * (diff == 0).sum()) / (p.size * q.size))
'''

H_FOLDS = '''
def _folds(y, k, rng):
    # stratified random fold labels 0..k-1
    f = np.empty(y.size, dtype=int)
    off = 0
    for c in (True, False):
        idx = np.flatnonzero(y == c)
        f[rng.permutation(idx)] = (np.arange(idx.size) + off) % k
        off += idx.size
    return f
'''

H_LOGIT = '''
def _logit(xt, yt, lam):
    # ridge logistic regression (Newton / IRLS), unpenalised intercept
    n, p = xt.shape
    a = np.column_stack([np.ones(n), xt])
    pen = lam * np.eye(p + 1)
    pen[0, 0] = 0.0
    t = yt.astype(float)
    w = np.zeros(p + 1)
    for _ in range(30):
        mu = 1.0 / (1.0 + np.exp(-np.clip(a @ w, -30.0, 30.0)))
        g = a.T @ (mu - t) + pen @ w
        h = (a.T * np.maximum(mu * (1.0 - mu), 1e-6)) @ a + pen
        step = np.linalg.solve(h, g)
        w = w - step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w
'''

H_RIDGE = '''
def _ridge(xt, yt, lam):
    # ridge regression on training-standardised features
    mu = xt.mean(axis=0)
    sd = np.maximum(xt.std(axis=0), 1e-12)
    z = (xt - mu) / sd
    ym = yt.mean()
    w = np.linalg.solve(z.T @ z + lam * np.eye(z.shape[1]), z.T @ (yt - ym))
    return lambda xn: ym + ((xn - mu) / sd) @ w
'''

H_KNN = '''
def _knn(xt, yt, xn, k):
    dist = ((xn[:, None, :] - xt[None, :, :]) ** 2).sum(axis=2)
    nb = np.argsort(dist, axis=1, kind="stable")[:, :k]
    return yt[nb].sum(axis=1) * 2 > k
'''

BODIES = {}

# ---------------------------------------------------------------------------------------------------------------
# b2-01  SIM03  L1.1  resubstitution; fixed: leave-one-out with gene selection, weighting and rule redone inside
# ---------------------------------------------------------------------------------------------------------------
B01 = '''
x = np.asarray(d["expr"], dtype=float)
y = np.asarray(d["tumour"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 2 or (~y).sum() < 2 or not np.all(x.std(axis=0) > 0):
    return None
n_genes = 5      # genes kept by the rule (largest absolute t statistic)
thr = 0.80       # claimed accuracy

def fit(xt, yt):
    # gene selection by |t|, weights (pooled sd) and the nearest-centroid rule, all built from the rows given
    a, b = xt[yt], xt[~yt]
    sp = np.sqrt((((a - a.mean(axis=0)) ** 2).sum(axis=0) + ((b - b.mean(axis=0)) ** 2).sum(axis=0))
                 / (xt.shape[0] - 2))
    sp = np.maximum(sp, 1e-12)
    t = (a.mean(axis=0) - b.mean(axis=0)) / (sp * np.sqrt(1.0 / a.shape[0] + 1.0 / b.shape[0]))
    sel = np.argsort(-np.abs(t), kind="stable")[:n_genes]
    ca, cb, sc = a.mean(axis=0)[sel], b.mean(axis=0)[sel], sp[sel]
    def predict(xn):
        da = (((xn[:, sel] - ca) / sc) ** 2).sum(axis=1)
        db = (((xn[:, sel] - cb) / sc) ** 2).sum(axis=1)
        return da < db
    return predict
'''
BODIES["b2-01"] = dict(
    faulty=B01 + '''
pred = fit(x, y)(x)
acc = float(np.mean(pred == y))
return bool(acc >= thr)
''',
    fixed=B01 + '''
n = y.size
pred = np.zeros(n, dtype=bool)
for i in range(n):
    keep = np.arange(n) != i
    pred[i] = fit(x[keep], y[keep])(x[i:i + 1])[0]
acc = float(np.mean(pred == y))
return bool(acc >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-02  SIM03  L1.1  resubstitution AUC of a ridge logistic model; fixed: 5-fold pooled out-of-fold AUC
# ---------------------------------------------------------------------------------------------------------------
B02 = H_AUC + H_FOLDS + H_LOGIT + '''
x = np.asarray(d["markers"], dtype=float)
y = np.asarray(d["relapse"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
    return None
lam = 1.0        # ridge penalty of the logistic model
thr = 0.75       # claimed AUC

def fit_score(xt, yt, xn):
    w = _logit(xt, yt, lam)
    return w[0] + xn @ w[1:]
'''
BODIES["b2-02"] = dict(
    faulty=B02 + '''
auc = _auc(fit_score(x, y, x), y)
return bool(auc >= thr)
''',
    fixed=B02 + '''
rng = np.random.default_rng(2)
fold = _folds(y, 5, rng)
s = np.zeros(y.size)
for k in range(5):
    te = fold == k
    s[te] = fit_score(x[~te], y[~te], x[te])
auc = _auc(s, y)
return bool(auc >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-03  AMB02  L1.3  forward selection (Fisher LDA, LOO error) on all tissues, internal LOO error reported;
#                     fixed: external 10-fold CV with pre-reduction and forward selection inside each training fold
# ---------------------------------------------------------------------------------------------------------------
B03 = H_FOLDS + '''
x = np.asarray(d["expr"], dtype=float)
y = np.asarray(d["cancer"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
    return None
n_pre = 20       # genes kept by the pre-reduction (largest absolute t statistic)
n_sel = 3        # genes chosen by forward selection
ridge = 0.05     # ridge added to the pooled covariance (relative to its mean variance)
thr = 0.80       # claimed accuracy

def lda_loo_errors(xc, yt):
    # xc: (candidates, n, k) feature sets. Leave-one-out misclassification count of Fisher's rule for each set,
    # refitting means and pooled covariance without the left-out row.
    c, n, k = xc.shape
    m = 1.0 - np.eye(n)
    w1, w0 = m * yt[None, :], m * (~yt)[None, :]
    n1, n0 = w1.sum(axis=1), w0.sum(axis=1)
    m1 = np.einsum("lj,cjk->clk", w1, xc) / n1[None, :, None]
    m0 = np.einsum("lj,cjk->clk", w0, xc) / n0[None, :, None]
    xx = (xc[:, :, :, None] * xc[:, :, None, :]).reshape(c, n, k * k)
    s1 = np.einsum("lj,cjq->clq", w1, xx).reshape(c, n, k, k) - n1[None, :, None, None] * m1[..., :, None] * m1[..., None, :]
    s0 = np.einsum("lj,cjq->clq", w0, xx).reshape(c, n, k, k) - n0[None, :, None, None] * m0[..., :, None] * m0[..., None, :]
    s = (s1 + s0) / (n1 + n0 - 2.0)[None, :, None, None]
    s = s + ridge * (np.trace(s, axis1=2, axis2=3) / k)[..., None, None] * np.eye(k)
    wv = np.linalg.solve(s, (m1 - m0)[..., None])[..., 0]
    score = np.einsum("clk,clk->cl", wv, xc - 0.5 * (m1 + m0)) + np.log(n1 / n0)[None, :]
    return ((score > 0) != yt[None, :]).sum(axis=1)

def lda_predict(xt, yt, xn):
    a, b = xt[yt], xt[~yt]
    m1, m0 = a.mean(axis=0), b.mean(axis=0)
    s = ((a - m1).T @ (a - m1) + (b - m0).T @ (b - m0)) / (xt.shape[0] - 2.0)
    s = s + ridge * (np.trace(s) / s.shape[0]) * np.eye(s.shape[0])
    wv = np.linalg.solve(s, m1 - m0)
    return (xn - 0.5 * (m1 + m0)) @ wv + np.log(a.shape[0] / b.shape[0]) > 0

def select(xt, yt):
    # pre-reduction by |t|, then sequential forward selection; each step adds the gene with the smallest
    # leave-one-out error of the rule (ties: the gene with the larger |t|). Returns genes and the leave-one-out
    # error of the final set.
    a, b = xt[yt], xt[~yt]
    sp = np.sqrt((((a - a.mean(axis=0)) ** 2).sum(axis=0) + ((b - b.mean(axis=0)) ** 2).sum(axis=0))
                 / (xt.shape[0] - 2))
    t = (a.mean(axis=0) - b.mean(axis=0)) / (np.maximum(sp, 1e-12) * np.sqrt(1.0 / a.shape[0] + 1.0 / b.shape[0]))
    pool = [int(g) for g in np.argsort(-np.abs(t), kind="stable")[:n_pre]]
    chosen = []
    err = 0.0
    for _ in range(n_sel):
        cand = [g for g in pool if g not in chosen]
        xc = np.stack([xt[:, chosen + [g]] for g in cand])
        e = lda_loo_errors(xc, yt)
        j = int(np.argmin(e))
        chosen.append(cand[j])
        err = float(e[j]) / xt.shape[0]
    return chosen, err
'''
BODIES["b2-03"] = dict(
    faulty=B03 + '''
chosen, err = select(x, y)
return bool(1.0 - err >= thr)
''',
    fixed=B03 + '''
rng = np.random.default_rng(3)
fold = _folds(y, 10, rng)
pred = np.zeros(y.size, dtype=bool)
for k in range(10):
    te = fold == k
    chosen, _ = select(x[~te], y[~te])
    pred[te] = lda_predict(x[~te][:, chosen], y[~te], x[te][:, chosen])
acc = float(np.mean(pred == y))
return bool(acc >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-04  AMB02  L1.3  RFE (ridge linear classifier) to 8 genes on all patients, leave-one-out AUC of the 8-gene rule;
#                     fixed: external 10-fold CV with RFE repeated inside each training fold
# ---------------------------------------------------------------------------------------------------------------
B04 = H_AUC + H_FOLDS + '''
x = np.asarray(d["expr"], dtype=float)
y = np.asarray(d["subtype_a"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
    return None
keep = 8         # genes kept by recursive feature elimination
lam = 70.0       # ridge penalty of the linear classifier (of the order of the number of patients; 60 genes, about 70 patients)
thr = 0.80       # claimed AUC

def rfe(xt, yt):
    # recursive elimination of the gene with the smallest absolute weight, one at a time, down to `keep` genes
    z = (xt - xt.mean(axis=0)) / np.maximum(xt.std(axis=0), 1e-12)
    t = np.where(yt, 1.0, -1.0)
    t = t - t.mean()
    g, c = z.T @ z, z.T @ t
    idx = np.arange(z.shape[1])
    while idx.size > keep:
        w = np.linalg.solve(g[np.ix_(idx, idx)] + lam * np.eye(idx.size), c[idx])
        idx = np.delete(idx, int(np.argmin(np.abs(w))))
    return idx

def rule(xt, yt, xn, idx):
    # ridge linear classifier on the selected genes, scores for the rows xn
    a = xt[:, idx]
    mu = a.mean(axis=0)
    sd = np.maximum(a.std(axis=0), 1e-12)
    z = (a - mu) / sd
    t = np.where(yt, 1.0, -1.0)
    w = np.linalg.solve(z.T @ z + lam * np.eye(z.shape[1]), z.T @ (t - t.mean()))
    return ((xn[:, idx] - mu) / sd) @ w + t.mean()
'''
BODIES["b2-04"] = dict(
    faulty=B04 + '''
n = y.size
idx = rfe(x, y)
s = np.zeros(n)
for i in range(n):
    tr = np.arange(n) != i
    s[i] = rule(x[tr], y[tr], x[i:i + 1], idx)[0]
auc = _auc(s, y)
return bool(auc >= thr)
''',
    fixed=B04 + '''
rng = np.random.default_rng(4)
fold = _folds(y, 10, rng)
s = np.zeros(y.size)
for k in range(10):
    te = fold == k
    idx = rfe(x[~te], y[~te])
    s[te] = rule(x[~te], y[~te], x[te], idx)
auc = _auc(s, y)
return bool(auc >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-05  KAP23  L1.2  label-dependent imputation over all rows, then cross-validated AUC;
#                     fixed: label-free training-fold mean imputation inside each fold
# ---------------------------------------------------------------------------------------------------------------
B05 = H_AUC + H_FOLDS + H_LOGIT + '''
x = np.asarray(d["x"], dtype=float)
obs = np.asarray(d["observed"]).astype(bool)
y = np.asarray(d["onset"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
    return None
lam = 1.0        # ridge penalty of the logistic model
thr = 0.75       # claimed AUC

def obs_means(xx, oo):
    # mean of the observed values of each indicator over the rows given; None if an indicator has none
    if np.any(oo.sum(axis=0) == 0):
        return None
    return (xx * oo).sum(axis=0) / oo.sum(axis=0)

def fill(xx, oo, means):
    return np.where(oo, xx, means[None, :])
'''
BODIES["b2-05"] = dict(
    faulty=B05 + '''
# unobserved entries are filled with the mean of the observed values of the row's own outcome class
xf = x.copy()
for c in (True, False):
    r = y == c
    m = obs_means(x[r], obs[r])
    if m is None:
        return None
    xf[r] = fill(x[r], obs[r], m)
rng = np.random.default_rng(5)
fold = _folds(y, 5, rng)
s = np.zeros(y.size)
for k in range(5):
    te = fold == k
    w = _logit(xf[~te], y[~te], lam)
    s[te] = w[0] + xf[te] @ w[1:]
auc = _auc(s, y)
return bool(auc >= thr)
''',
    fixed=B05 + '''
# unobserved entries are filled with the training-fold mean of the observed values (no use of the outcome)
rng = np.random.default_rng(5)
fold = _folds(y, 5, rng)
s = np.zeros(y.size)
for k in range(5):
    te = fold == k
    m = obs_means(x[~te], obs[~te])
    if m is None:
        return None
    xtr, xte = fill(x[~te], obs[~te], m), fill(x[te], obs[te], m)
    w = _logit(xtr, y[~te], lam)
    s[te] = w[0] + xte @ w[1:]
auc = _auc(s, y)
return bool(auc >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-06  KAP23  L1.2  SMOTE-style oversampling of positives over all rows, then 5-fold CV 3-NN balanced accuracy;
#                     fixed: oversample the training folds only, test folds untouched
# ---------------------------------------------------------------------------------------------------------------
B06 = H_FOLDS + H_KNN + '''
x = np.asarray(d["biomarkers"], dtype=float)
y = np.asarray(d["positive"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
    return None
thr = 0.75       # claimed balanced accuracy
k_nn = 3

def smote(xt, yt, rng):
    # synthetic positives: interpolation between two different random positive rows, up to class balance
    xp = xt[yt]
    m = xp.shape[0]
    n_new = max(int((~yt).sum()) - m, 0)
    a = rng.integers(0, m, n_new)
    b = (a + 1 + rng.integers(0, m - 1, n_new)) % m
    u = rng.random((n_new, 1))
    return np.vstack([xt, xp[a] + u * (xp[b] - xp[a])]), np.concatenate([yt, np.ones(n_new, dtype=bool)])

def balanced(pred, yy):
    return 0.5 * (float(np.mean(pred[yy])) + float(np.mean(~pred[~yy])))
'''
BODIES["b2-06"] = dict(
    faulty=B06 + '''
rng = np.random.default_rng(6)
xa, ya = smote(x, y, rng)
fold = _folds(ya, 5, rng)
pred = np.zeros(ya.size, dtype=bool)
for k in range(5):
    te = fold == k
    pred[te] = _knn(xa[~te], ya[~te], xa[te], k_nn)
return bool(balanced(pred, ya) >= thr)
''',
    fixed=B06 + '''
rng = np.random.default_rng(6)
fold = _folds(y, 5, rng)
pred = np.zeros(y.size, dtype=bool)
for k in range(5):
    te = fold == k
    xa, ya = smote(x[~te], y[~te], rng)
    pred[te] = _knn(xa, ya, x[te], k_nn)
return bool(balanced(pred, y) >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-07  KAP23  L1.4  10-fold 1-NN accuracy over all rows incl. repeated entries; fixed: repeats collapsed first
# ---------------------------------------------------------------------------------------------------------------
B07 = H_FOLDS + H_KNN + '''
x = np.asarray(d["records"], dtype=float)
y = np.asarray(d["diagnosis"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
thr = 0.75       # claimed accuracy
'''
BODIES["b2-07"] = dict(
    faulty=B07 + '''
if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
    return None
rng = np.random.default_rng(7)
fold = _folds(y, 10, rng)
pred = np.zeros(y.size, dtype=bool)
for k in range(10):
    te = fold == k
    pred[te] = _knn(x[~te], y[~te], x[te], 1)
return bool(np.mean(pred == y) >= thr)
''',
    fixed=B07 + '''
# repeated entries (identical rows) are collapsed to one before the evaluation
_, first = np.unique(x, axis=0, return_index=True)
first = np.sort(first)
x, y = x[first], y[first]
if y.sum() < 10 or (~y).sum() < 10 or not np.all(x.std(axis=0) > 0):
    return None
rng = np.random.default_rng(7)
fold = _folds(y, 10, rng)
pred = np.zeros(y.size, dtype=bool)
for k in range(10):
    te = fold == k
    pred[te] = _knn(x[~te], y[~te], x[te], 1)
return bool(np.mean(pred == y) >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-08  KAP23  L1.4  fraud rows copied up to balance over all rows, 5-fold 1-NN, pooled fraud F1;
#                     fixed: copies made in the training folds only, F1 on the untouched original test rows
# ---------------------------------------------------------------------------------------------------------------
B08 = H_FOLDS + H_KNN + '''
x = np.asarray(d["features"], dtype=float)
y = np.asarray(d["fraud"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
    return None
thr = 0.60       # claimed F1 for fraud

def copy_up(xt, yt, rng):
    # copies of randomly drawn fraud rows (with replacement) until the classes are balanced
    pos = np.flatnonzero(yt)
    n_new = max(int((~yt).sum()) - pos.size, 0)
    pick = pos[rng.integers(0, pos.size, n_new)]
    return np.vstack([xt, xt[pick]]), np.concatenate([yt, np.ones(n_new, dtype=bool)])

def f1(pred, yy):
    tp = float(np.sum(pred & yy))
    return 2.0 * tp / (2.0 * tp + float(np.sum(pred & ~yy)) + float(np.sum(~pred & yy)))
'''
BODIES["b2-08"] = dict(
    faulty=B08 + '''
rng = np.random.default_rng(8)
xa, ya = copy_up(x, y, rng)
fold = _folds(ya, 5, rng)
pred = np.zeros(ya.size, dtype=bool)
for k in range(5):
    te = fold == k
    pred[te] = _knn(xa[~te], ya[~te], xa[te], 1)
return bool(f1(pred, ya) >= thr)
''',
    fixed=B08 + '''
rng = np.random.default_rng(8)
fold = _folds(y, 5, rng)
pred = np.zeros(y.size, dtype=bool)
for k in range(5):
    te = fold == k
    xa, ya = copy_up(x[~te], y[~te], rng)
    pred[te] = _knn(xa, ya, x[te], 1)
return bool(f1(pred, y) >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-09  KAP23  L3.1  shuffled 5-fold CV logistic AUC; fixed: chronological split (first 70% train, last 30% test)
# ---------------------------------------------------------------------------------------------------------------
B09 = H_AUC + H_FOLDS + H_LOGIT + '''
x = np.asarray(d["x"], dtype=float)
y = np.asarray(d["onset"]).astype(bool)
if not np.all(np.isfinite(x)):
    return None
if y.sum() < 5 or (~y).sum() < 5 or not np.all(x.std(axis=0) > 0):
    return None
lam = 1.0        # ridge penalty of the logistic model
thr = 0.75       # claimed AUC

def fit_score(xt, yt, xn):
    w = _logit(xt, yt, lam)
    return w[0] + xn @ w[1:]
'''
BODIES["b2-09"] = dict(
    faulty=B09 + '''
rng = np.random.default_rng(9)
fold = _folds(y, 5, rng)          # rows are shuffled into folds irrespective of their order in time
s = np.zeros(y.size)
for k in range(5):
    te = fold == k
    s[te] = fit_score(x[~te], y[~te], x[te])
return bool(_auc(s, y) >= thr)
''',
    fixed=B09 + '''
cut = int(0.7 * y.size)           # rows are in time order: fit on the first 70%, evaluate on the last 30%
tr, te = np.arange(y.size) < cut, np.arange(y.size) >= cut
if y[tr].sum() < 2 or (~y[tr]).sum() < 2 or y[te].sum() < 2 or (~y[te]).sum() < 2:
    return None
s = fit_score(x[tr], y[tr], x[te])
return bool(_auc(s, y[te]) >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-10  KAP23  L3.1  shuffled 5-fold CV ridge R^2; fixed: fit on the first 100 weeks, R^2 on the last 50
# ---------------------------------------------------------------------------------------------------------------
B10 = H_RIDGE + '''
x = np.asarray(d["indicators"], dtype=float)
y = np.asarray(d["admissions_next"], dtype=float)
if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
    return None
if not np.all(x.std(axis=0) > 0) or not y.std() > 0:
    return None
lam = 1.0        # ridge penalty
thr = 0.30       # claimed R^2

def r2(yy, pp):
    return 1.0 - float(np.sum((yy - pp) ** 2)) / float(np.sum((yy - yy.mean()) ** 2))
'''
BODIES["b2-10"] = dict(
    faulty=B10 + '''
rng = np.random.default_rng(10)
groups = np.array_split(rng.permutation(y.size), 5)     # rows are shuffled into folds irrespective of time
p = np.zeros(y.size)
for g in groups:
    te = np.zeros(y.size, dtype=bool)
    te[g] = True
    p[te] = _ridge(x[~te], y[~te], lam)(x[te])
return bool(r2(y, p) >= thr)
''',
    fixed=B10 + '''
cut = int(y.size * 2 // 3)        # rows are in time order: fit on the first two thirds, evaluate on the last third
tr, te = np.arange(y.size) < cut, np.arange(y.size) >= cut
if not y[te].std() > 0:
    return None
p = _ridge(x[tr], y[tr], lam)(x[te])
return bool(r2(y[te], p) >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-11  KAP23  L3.2  patches flattened and shuffled into 5 folds, logistic AUC; fixed: folds over patients
# ---------------------------------------------------------------------------------------------------------------
B11 = H_AUC + H_FOLDS + H_LOGIT + '''
pt = np.asarray(d["patches"], dtype=float)
mut = np.asarray(d["mutated"]).astype(bool)
if not np.all(np.isfinite(pt)):
    return None
n_pat, n_patch, n_feat = pt.shape
x = pt.reshape(n_pat * n_patch, n_feat)          # one row per patch
y = np.repeat(mut, n_patch)                       # the patient's status on each of its patches
if mut.sum() < 5 or (~mut).sum() < 5 or not np.all(x.std(axis=0) > 0):
    return None
lam = 1.0        # ridge penalty of the logistic model
thr = 0.75       # claimed AUC
'''
BODIES["b2-11"] = dict(
    faulty=B11 + '''
rng = np.random.default_rng(11)
fold = _folds(y, 5, rng)                          # patch rows are shuffled into folds
s = np.zeros(y.size)
for k in range(5):
    te = fold == k
    w = _logit(x[~te], y[~te], lam)
    s[te] = w[0] + x[te] @ w[1:]
return bool(_auc(s, y) >= thr)
''',
    fixed=B11 + '''
rng = np.random.default_rng(11)
fold = np.repeat(_folds(mut, 5, rng), n_patch)    # folds are formed over patients; all patches of a patient go together
s = np.zeros(y.size)
for k in range(5):
    te = fold == k
    w = _logit(x[~te], y[~te], lam)
    s[te] = w[0] + x[te] @ w[1:]
return bool(_auc(s, y) >= thr)
''')

# ---------------------------------------------------------------------------------------------------------------
# b2-12  KAP23  L3.2  rows flattened and shuffled into 5 folds, ridge R^2; fixed: folds over hospitals
# ---------------------------------------------------------------------------------------------------------------
B12 = H_RIDGE + '''
xs = np.asarray(d["x"], dtype=float)
ys = np.asarray(d["stay"], dtype=float)
if not (np.all(np.isfinite(xs)) and np.all(np.isfinite(ys))):
    return None
n_hosp, n_pat, n_chr = xs.shape
x = xs.reshape(n_hosp * n_pat, n_chr)             # one row per patient
y = ys.reshape(n_hosp * n_pat)
hosp = np.repeat(np.arange(n_hosp), n_pat)
if not np.all(x.std(axis=0) > 0) or not y.std() > 0:
    return None
lam = 1.0        # ridge penalty
thr = 0.40       # claimed R^2

def r2(yy, pp):
    return 1.0 - float(np.sum((yy - pp) ** 2)) / float(np.sum((yy - yy.mean()) ** 2))
'''
BODIES["b2-12"] = dict(
    faulty=B12 + '''
rng = np.random.default_rng(12)
groups = np.array_split(rng.permutation(y.size), 5)     # patient rows are shuffled into folds
p = np.zeros(y.size)
for g in groups:
    te = np.zeros(y.size, dtype=bool)
    te[g] = True
    p[te] = _ridge(x[~te], y[~te], lam)(x[te])
return bool(r2(y, p) >= thr)
''',
    fixed=B12 + '''
rng = np.random.default_rng(12)
groups = np.array_split(rng.permutation(n_hosp), 5)     # folds are formed over hospitals; a hospital is never split
p = np.zeros(y.size)
for g in groups:
    te = np.isin(hosp, g)
    p[te] = _ridge(x[~te], y[~te], lam)(x[te])
return bool(r2(y, p) >= thr)
''')


def build(case):
    src = open(os.path.join(ROOT, case, "skeleton.py"), encoding="utf-8", newline="").read()
    assert src.count(MARK) == 1, case
    for kind in ("faulty", "fixed"):
        body = textwrap.indent(BODIES[case][kind].strip("\n") + "\n", "    ")
        out = src.replace(MARK, body)
        ast.parse(out)
        with open(os.path.join(ROOT, case, kind + ".py"), "w", encoding="utf-8", newline="") as f:
            f.write(out)


if __name__ == "__main__":
    todo = sys.argv[1:] or sorted(BODIES)
    for c in todo:
        build(c)
        print("written", c)
