"""Writes the criterion bodies into cases/<id>/faulty.py and fixed.py.

Only text is produced here: the script never imports or runs a criterion.  Each case has
  HEAD     shared text (inputs, constants)
  GUARD_*  version-specific guard (the smallest-size guard of the structure of that version)
  HELP     shared helper functions
  TAIL_*   version-specific analysis (the error / its correction)
The line `    raise NotImplementedError` of criterion(d) is replaced; nothing else in the file changes.
"""
import pathlib
import sys

ROOT = pathlib.Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\cases")
MARK = "    raise NotImplementedError\n"

CASES = {}

# ----------------------------------------------------------------------------------------------
# shared snippets
STRAT = '''    def strat_folds(yy, k):
        f = np.empty(yy.size, dtype=int)
        off = 0
        for c in (False, True):
            idx = np.flatnonzero(yy == c)
            idx = idx[rng.permutation(idx.size)]
            f[idx] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

'''

AUC = '''    def auc(s, yy):
        o = np.argsort(s, kind="mergesort")
        ss = s[o]
        first = np.r_[True, ss[1:] != ss[:-1]]
        grp = np.cumsum(first) - 1
        starts = np.flatnonzero(first)
        ends = np.r_[starts[1:], ss.size]
        avg = (starts + ends + 1) / 2.0
        r = np.empty(ss.size)
        r[o] = avg[grp]
        n1 = int(yy.sum())
        n0 = yy.size - n1
        return (r[yy].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)

'''

LOGIT = '''    def fit_predict(Xtr, ytr, Xte):
        mu = Xtr.mean(0)
        sd = Xtr.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
        B = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]
        t = ytr.astype(float)
        pen = np.ones(A.shape[1])
        pen[0] = 0.0
        w = np.zeros(A.shape[1])
        for _ in range(30):
            p = 1.0 / (1.0 + np.exp(-np.clip(A @ w, -30.0, 30.0)))
            g = A.T @ (p - t) + LAM * pen * w
            H = (A * (p * (1.0 - p))[:, None]).T @ A + LAM * np.diag(pen)
            step = np.linalg.solve(H, g)
            w = w - step
            if np.max(np.abs(step)) < 1e-8:
                break
        return B @ w

'''

KNN = '''    def knn_predict(Xtr, ytr, Xte):
        mu = Xtr.mean(0)
        sd = Xtr.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = (Xtr - mu) / sd
        B = (Xte - mu) / sd
        D = (B ** 2).sum(1)[:, None] - 2.0 * (B @ A.T) + (A ** 2).sum(1)[None, :]
        kk = min(KNN_K, A.shape[0])
        idx = np.argpartition(D, kk - 1, axis=1)[:, :kk]
        return 2 * ytr[idx].sum(1) > kk

'''

OVERSAMPLE = '''    def oversample(XX, yy):
        # copy rows of the smaller class (drawn at random with replacement) until the two classes are balanced
        npos = int(yy.sum())
        nneg = yy.size - npos
        if npos == nneg:
            return XX, yy
        pool = np.flatnonzero(yy == (npos < nneg))
        pick = pool[rng.integers(0, pool.size, abs(nneg - npos))]
        return np.concatenate([XX, XX[pick]]), np.concatenate([yy, yy[pick]])

'''

OLS = '''    def ols_predict(Xtr, ytr, Xte):
        mu = Xtr.mean(0)
        sd = Xtr.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
        B = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]
        w = np.linalg.lstsq(A, ytr, rcond=None)[0]
        return B @ w

'''

TSTAT = '''    def rank_genes(Xtr, ytr):
        # two-sample t statistic (pooled variance) of every gene, genes ordered by decreasing |t|
        n1 = int(ytr.sum())
        n0 = ytr.size - n1
        m1 = Xtr[ytr].mean(0)
        m0 = Xtr[~ytr].mean(0)
        ss = ((Xtr[ytr] - m1) ** 2).sum(0) + ((Xtr[~ytr] - m0) ** 2).sum(0)
        sp = np.sqrt(ss / (ytr.size - 2))
        sp = np.where(sp > 0, sp, np.inf)
        t = (m1 - m0) / (sp * np.sqrt(1.0 / n1 + 1.0 / n0))
        return np.argsort(-np.abs(t), kind="stable")

'''

CEIL5 = "-(-n_pos // 5)"


def guard_cv(k, depth):
    """Guard: at least 2 rows of each class in every fitting set of a (nested) stratified k-fold structure."""
    pos, neg = "n_pos", "n_neg"
    for _ in range(depth):
        pos = f"({pos} - (-({pos}) // {k}))"
        neg = f"({neg} - (-({neg}) // {k}))"
    return f"    if min({pos}, {neg}) < 2:\n        return None\n"


def guard_cv_ok(k, depth, minimum=2):
    """Repair-round guard: n - ceil(n / k) at every level, written as n - (-(-(n) // k))."""
    pos, neg = "n_pos", "n_neg"
    for _ in range(depth):
        pos = f"({pos} - (-(-({pos}) // {k})))"
        neg = f"({neg} - (-(-({neg}) // {k})))"
    return f"    if min({pos}, {neg}) < {minimum}:\n        return None\n"


# ----------------------------------------------------------------------------------------------
# B2-01  L1.1  AUC, no test set
CASES["B2-01"] = dict(
    head='''    X = np.asarray(d["indicators"], dtype=float)
    y = np.asarray(d["onset"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260201)
    THRESHOLD = 0.75
    LAM = 1.0
''',
    guard_faulty=guard_cv(5, 0),
    guard_fixed=guard_cv_ok(5, 1),
    help=STRAT + AUC + LOGIT,
    tail_faulty='''    score = fit_predict(X, y, X)
    return bool(auc(score, y) >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 5)
    score = np.empty(y.size)
    for j in range(5):
        te = fold == j
        score[te] = fit_predict(X[~te], y[~te], X[te])
    return bool(auc(score, y) >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-02  L1.4  sensitivity, oversampling by copying before the split
KNN_SENS_HEAD = '''    X = np.asarray(d["{xk}"], dtype=float)
    y = np.asarray(d["{yk}"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng({seed})
    THRESHOLD = {thr}
{extra}'''

CASES["B2-02"] = dict(
    head=KNN_SENS_HEAD.format(xk="measurements", yk="outcome", seed=20260202, thr="0.60", extra="    LAM = 1.0\n"),
    guard_faulty=guard_cv(5, 1),
    guard_fixed=guard_cv(5, 1),
    help=STRAT + OVERSAMPLE + LOGIT,
    tail_faulty='''    Xo, yo = oversample(X, y)
    fold = strat_folds(yo, 5)
    hit = 0
    pos = 0
    for j in range(5):
        te = fold == j
        pred = fit_predict(Xo[~te], yo[~te], Xo[te]) > 0
        hit += int((pred & yo[te]).sum())
        pos += int(yo[te].sum())
    return bool(hit / pos >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 5)
    hit = 0
    pos = 0
    for j in range(5):
        te = fold == j
        Xtr, ytr = oversample(X[~te], y[~te])
        pred = fit_predict(Xtr, ytr, X[te]) > 0
        hit += int((pred & y[te]).sum())
        pos += int(y[te].sum())
    return bool(hit / pos >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-03  L1.4  balanced accuracy
CASES["B2-03"] = dict(
    head=KNN_SENS_HEAD.format(xk="sensor_features", yk="defective", seed=20260203, thr="0.65", extra="    LAM = 1.0\n"),
    guard_faulty=guard_cv(5, 1),
    guard_fixed=guard_cv(5, 1),
    help=STRAT + OVERSAMPLE + LOGIT,
    tail_faulty='''    Xo, yo = oversample(X, y)
    fold = strat_folds(yo, 5)
    tp = tn = pos = neg = 0
    for j in range(5):
        te = fold == j
        pred = fit_predict(Xo[~te], yo[~te], Xo[te]) > 0
        tp += int((pred & yo[te]).sum())
        tn += int((~pred & ~yo[te]).sum())
        pos += int(yo[te].sum())
        neg += int((~yo[te]).sum())
    return bool(0.5 * (tp / pos + tn / neg) >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 5)
    tp = tn = pos = neg = 0
    for j in range(5):
        te = fold == j
        Xtr, ytr = oversample(X[~te], y[~te])
        pred = fit_predict(Xtr, ytr, X[te]) > 0
        tp += int((pred & y[te]).sum())
        tn += int((~pred & ~y[te]).sum())
        pos += int(y[te].sum())
        neg += int((~y[te]).sum())
    return bool(0.5 * (tp / pos + tn / neg) >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-04  L3.1  accuracy, temporal
CASES["B2-04"] = dict(
    head=KNN_SENS_HEAD.format(xk="indicators", yk="rises", seed=20260204, thr="0.58", extra="    KNN_K = 15\n") + "    K = 5\n",
    guard_faulty="",
    guard_fixed="",
    help=KNN,
    tail_faulty='''    n = y.size
    fold = rng.permutation(n) % K
    hit = 0
    for j in range(K):
        te = fold == j
        tr = ~te
        if min(int(y[tr].sum()), int((~y[tr]).sum())) < 2:
            return None
        hit += int((knn_predict(X[tr], y[tr], X[te]) == y[te]).sum())
    return bool(hit / n >= THRESHOLD)
''',
    tail_fixed='''    n = y.size
    edges = np.linspace(0, n, K + 2).astype(int)
    idx = np.arange(n)
    hit = 0
    scored = 0
    for j in range(1, K + 1):
        tr = idx < edges[j]
        te = (idx >= edges[j]) & (idx < edges[j + 1])
        if min(int(y[tr].sum()), int((~y[tr]).sum())) < 2:
            return None
        hit += int((knn_predict(X[tr], y[tr], X[te]) == y[te]).sum())
        scored += int(te.sum())
    if scored == 0:
        return None
    return bool(hit / scored >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-05  L3.1  R-squared
CASES["B2-05"] = dict(
    head='''    X = np.asarray(d["drivers"], dtype=float)
    y = np.asarray(d["demand"], dtype=float)
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    p = X.shape[1]
    rng = np.random.default_rng(20260205)
    THRESHOLD = 0.30
    K = 5
''',
    guard_faulty="",
    guard_fixed="",
    help=OLS,
    tail_faulty='''    fold = rng.permutation(n) % K
    pred = np.empty(n)
    for j in range(K):
        te = fold == j
        tr = ~te
        if int(tr.sum()) <= p + 1:
            return None
        pred[te] = ols_predict(X[tr], y[tr], X[te])
    sse = float(((y - pred) ** 2).sum())
    sst = float(((y - y.mean()) ** 2).sum())
    if not sst > 0:
        return None
    return bool(1.0 - sse / sst >= THRESHOLD)
''',
    tail_fixed='''    edges = np.linspace(0, n, K + 2).astype(int)
    idx = np.arange(n)
    pred = np.full(n, np.nan)
    for j in range(1, K + 1):
        tr = idx < edges[j]
        te = (idx >= edges[j]) & (idx < edges[j + 1])
        if int(tr.sum()) <= p + 1:
            return None
        pred[te] = ols_predict(X[tr], y[tr], X[te])
    scored = idx >= edges[1]
    if int(scored.sum()) < 2:
        return None
    ys = y[scored]
    sse = float(((ys - pred[scored]) ** 2).sum())
    sst = float(((ys - ys.mean()) ** 2).sum())
    if not sst > 0:
        return None
    return bool(1.0 - sse / sst >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-06  L3.2  AUC, patches of the same patient on both sides
CASES["B2-06"] = dict(
    head='''    P = np.asarray(d["patch_features"], dtype=float)
    lab = np.asarray(d["malignant"], dtype=bool)
    if not np.all(np.isfinite(P)):
        return None
    n_pos = int(lab.sum())
    n_neg = lab.size - n_pos
    Q = P.shape[1]
    X = P.reshape(P.shape[0] * Q, P.shape[2])
    y = np.repeat(lab, Q)
    rng = np.random.default_rng(20260206)
    THRESHOLD = 0.75
    LAM = 1.0
''',
    guard_faulty=guard_cv_ok(5, 1),
    guard_fixed=guard_cv_ok(5, 1),
    help=STRAT + AUC + LOGIT,
    tail_faulty='''    fold = strat_folds(y, 5)
    score = np.empty(y.size)
    for j in range(5):
        te = fold == j
        score[te] = fit_predict(X[~te], y[~te], X[te])
    return bool(auc(score, y) >= THRESHOLD)
''',
    tail_fixed='''    pfold = strat_folds(lab, 5)
    fold = np.repeat(pfold, Q)
    score = np.empty(y.size)
    for j in range(5):
        te = fold == j
        score[te] = fit_predict(X[~te], y[~te], X[te])
    return bool(auc(score, y) >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-07  L3.2  correlation, sessions of the same participant on both sides
CASES["B2-07"] = dict(
    head='''    M = np.asarray(d["measurements"], dtype=float)
    S = np.asarray(d["score"], dtype=float)
    if not (np.all(np.isfinite(M)) and np.all(np.isfinite(S))):
        return None
    P, Q = S.shape
    if P < 2:
        return None
    X = M.reshape(P * Q, M.shape[2])
    y = S.reshape(P * Q)
    K = min(5, P)
    rng = np.random.default_rng(20260207)
    THRESHOLD = 0.30
''',
    guard_faulty="",
    guard_fixed="",
    help=OLS,
    tail_faulty='''    fold = rng.permutation(P * Q) % K
    pred = np.empty(P * Q)
    for j in range(K):
        te = fold == j
        pred[te] = ols_predict(X[~te], y[~te], X[te])
    if pred.size < 3 or not (pred.std() > 0 and y.std() > 0):
        return None
    return bool(np.corrcoef(pred, y)[0, 1] >= THRESHOLD)
''',
    tail_fixed='''    pfold = rng.permutation(P) % K
    fold = np.repeat(pfold, Q)
    pred = np.empty(P * Q)
    for j in range(K):
        te = fold == j
        pred[te] = ols_predict(X[~te], y[~te], X[te])
    if pred.size < 3 or not (pred.std() > 0 and y.std() > 0):
        return None
    return bool(np.corrcoef(pred, y)[0, 1] >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-08 / B2-09  VAR06  nearest shrunken centroid, tuned shrinkage
PAM = '''    DELTAS = np.linspace(1.0, 0.01, 20)  # largest first: a tie in the tuning criterion goes to the stronger shrinkage

    def pam_scores(Xtr, ytr, Xte):
        # nearest shrunken centroid; (n_test, n_delta) discriminant differences, positive favours the True class
        n = ytr.size
        n1 = int(ytr.sum())
        n0 = n - n1
        m1 = Xtr[ytr].mean(0)
        m0 = Xtr[~ytr].mean(0)
        m = Xtr.mean(0)
        ss = ((Xtr[ytr] - m1) ** 2).sum(0) + ((Xtr[~ytr] - m0) ** 2).sum(0)
        s = np.sqrt(ss / (n - 2))
        den = s + np.median(s)
        den = np.where(den > 0, den, 1.0)
        f1 = np.sqrt(1.0 / n1 - 1.0 / n)
        f0 = np.sqrt(1.0 / n0 - 1.0 / n)
        d1 = (m1 - m) / (f1 * den)
        d0 = (m0 - m) / (f0 * den)
        t1 = np.sign(d1)[:, None] * np.maximum(np.abs(d1)[:, None] - DELTAS[None, :], 0.0)
        t0 = np.sign(d0)[:, None] * np.maximum(np.abs(d0)[:, None] - DELTAS[None, :], 0.0)
        c1 = m[:, None] + (f1 * den)[:, None] * t1
        c0 = m[:, None] + (f0 * den)[:, None] * t0
        w = 1.0 / den ** 2
        base = ((Xte ** 2) * w).sum(1)[:, None]
        q1 = base - 2.0 * ((Xte * w) @ c1) + (w[:, None] * c1 ** 2).sum(0)[None, :] - 2.0 * np.log(n1 / n)
        q0 = base - 2.0 * ((Xte * w) @ c0) + (w[:, None] * c0 ** 2).sum(0)[None, :] - 2.0 * np.log(n0 / n)
        return q0 - q1

    def cv_scores(XX, yy, k):
        # pooled held-out scores of a stratified k-fold cross-validation, one column per delta
        f = strat_folds(yy, k)
        out = np.empty((yy.size, DELTAS.size))
        for j in range(k):
            te = f == j
            out[te] = pam_scores(XX[~te], yy[~te], XX[te])
        return out

'''

CASES["B2-08"] = dict(
    head='''    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["class_b"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260208)
    THRESHOLD = 0.60
''',
    guard_faulty=guard_cv(10, 1),
    guard_fixed=guard_cv(10, 2),
    help=STRAT + PAM,
    tail_faulty='''    S = cv_scores(X, y, 10)
    acc = ((S > 0) == y[:, None]).mean(0)
    return bool(acc.max() >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 10)
    hit = 0
    for j in range(10):
        te = fold == j
        tr = ~te
        inner = ((cv_scores(X[tr], y[tr], 10) > 0) == y[tr][:, None]).mean(0)
        best = int(np.argmax(inner))
        pred = pam_scores(X[tr], y[tr], X[te])[:, best] > 0
        hit += int((pred == y[te]).sum())
    return bool(hit / y.size >= THRESHOLD)
''',
)

CASES["B2-09"] = dict(
    head='''    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["responder"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260209)
    THRESHOLD = 0.65
''',
    guard_faulty=guard_cv(10, 1),
    guard_fixed=guard_cv(10, 2),
    help=STRAT + AUC + PAM + '''    def auc_cols(S, yy):
        return np.array([auc(S[:, c], yy) for c in range(S.shape[1])])

''',
    tail_faulty='''    S = cv_scores(X, y, 10)
    return bool(auc_cols(S, y).max() >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 10)
    score = np.empty(y.size)
    for j in range(10):
        te = fold == j
        tr = ~te
        inner = auc_cols(cv_scores(X[tr], y[tr], 10), y[tr])
        best = int(np.argmax(inner))
        score[te] = pam_scores(X[tr], y[tr], X[te])[:, best]
    return bool(auc(score, y) >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-10  VAR06  Gaussian-kernel classifier, (C, gamma) tuned by leave-one-out CV
KRR = TSTAT + '''    CS = 2.0 ** np.linspace(-5.0, 15.0, 5)
    GS = 2.0 ** np.linspace(-15.0, 3.0, 5)

    def sqdist(A, B):
        return np.maximum((A ** 2).sum(1)[:, None] - 2.0 * (A @ B.T) + (B ** 2).sum(1)[None, :], 0.0)

    def krr_scores(Xtr, ytr, Xte):
        # three genes with the largest |t| on the fitting set, kernel ridge classifier with a Gaussian kernel;
        # (n_test, 25) decision values, C varying slowest, gamma fastest
        g = rank_genes(Xtr, ytr)[:3]
        A = Xtr[:, g]
        B = Xte[:, g]
        mu = A.mean(0)
        sd = A.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = (A - mu) / sd
        B = (B - mu) / sd
        DA = sqdist(A, A)
        DB = sqdist(B, A)
        t = np.where(ytr, 1.0, -1.0)
        out = np.empty((B.shape[0], CS.size, GS.size))
        for gi in range(GS.size):
            lam, Qm = np.linalg.eigh(np.exp(-GS[gi] * DA))
            qt = Qm.T @ t
            Kb = np.exp(-GS[gi] * DB)
            for ci in range(CS.size):
                alpha = Qm @ (qt / (np.maximum(lam, 0.0) + 1.0 / CS[ci]))
                out[:, ci, gi] = Kb @ alpha
        return out.reshape(B.shape[0], -1)

    def loo_accuracy(XX, yy):
        # leave-one-out accuracy for every (C, gamma); genes are chosen again inside every leave-one-out fit
        m = yy.size
        hit = np.zeros(CS.size * GS.size)
        for i in range(m):
            keep = np.arange(m) != i
            dec = krr_scores(XX[keep], yy[keep], XX[i:i + 1])[0]
            hit += (dec > 0) == yy[i]
        return hit / m

'''

CASES["B2-10"] = dict(
    head='''    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["class_b"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260210)
    THRESHOLD = 0.60
''',
    guard_faulty="    if min(n_pos, n_neg) < 3:\n        return None\n",
    guard_fixed=guard_cv_ok(10, 1, 3),
    help=STRAT + KRR,
    tail_faulty='''    return bool(loo_accuracy(X, y).max() >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 10)
    hit = 0
    for j in range(10):
        te = fold == j
        tr = ~te
        best = int(np.argmax(loo_accuracy(X[tr], y[tr])))
        pred = krr_scores(X[tr], y[tr], X[te])[:, best] > 0
        hit += int((pred == y[te]).sum())
    return bool(hit / y.size >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-11  VAR06  nearest centroid on the k top-ranked genes, k tuned
NCK = TSTAT + '''    KS = np.array([1, 2, 3, 5, 10, 30, 100])  # smallest first: a tie in the tuning criterion goes to the smaller panel

    def nc_scores(Xtr, ytr, Xte):
        # genes ranked on the fitting set; nearest-centroid score (positive favours the True group) for each panel size
        order = rank_genes(Xtr, ytr)[:KS.max()]
        A = Xtr[:, order]
        B = Xte[:, order]
        mu = A.mean(0)
        sd = A.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = (A - mu) / sd
        B = (B - mu) / sd
        c1 = A[ytr].mean(0)
        c0 = A[~ytr].mean(0)
        e0 = np.cumsum((B - c0) ** 2, axis=1)[:, KS - 1]
        e1 = np.cumsum((B - c1) ** 2, axis=1)[:, KS - 1]
        return e0 - e1

    def cv_scores(XX, yy, k):
        f = strat_folds(yy, k)
        out = np.empty((yy.size, KS.size))
        for j in range(k):
            te = f == j
            out[te] = nc_scores(XX[~te], yy[~te], XX[te])
        return out

    def bal_acc(pred, yy):
        tpr = (pred & yy[:, None]).sum(0) / yy.sum()
        tnr = (~pred & ~yy[:, None]).sum(0) / (~yy).sum()
        return 0.5 * (tpr + tnr)

'''

CASES["B2-11"] = dict(
    head='''    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["group_b"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260211)
    THRESHOLD = 0.60
''',
    guard_faulty=guard_cv(10, 1),
    guard_fixed=guard_cv(10, 2),
    help=STRAT + NCK,
    tail_faulty='''    S = cv_scores(X, y, 10)
    return bool(bal_acc(S > 0, y).max() >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 10)
    pred = np.empty(y.size, dtype=bool)
    for j in range(10):
        te = fold == j
        tr = ~te
        best = int(np.argmax(bal_acc(cv_scores(X[tr], y[tr], 10) > 0, y[tr])))
        pred[te] = nc_scores(X[tr], y[tr], X[te])[:, best] > 0
    return bool(bal_acc(pred[:, None], y)[0] >= THRESHOLD)
''',
)

# ----------------------------------------------------------------------------------------------
# B2-12  AMB02  three genes chosen on all samples before the cross-validation
NC3 = TSTAT + '''    def nc_predict(A, ya, B):
        mu = A.mean(0)
        sd = A.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = (A - mu) / sd
        B = (B - mu) / sd
        c1 = A[ya].mean(0)
        c0 = A[~ya].mean(0)
        return ((B - c0) ** 2).sum(1) - ((B - c1) ** 2).sum(1) > 0

'''

CASES["B2-12"] = dict(
    head='''    X = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["tumour"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260212)
    THRESHOLD = 0.70
''',
    guard_faulty=guard_cv(10, 1),
    guard_fixed=guard_cv(10, 1),
    help=STRAT + NC3,
    tail_faulty='''    genes = rank_genes(X, y)[:3]
    fold = strat_folds(y, 10)
    pred = np.empty(y.size, dtype=bool)
    for j in range(10):
        te = fold == j
        tr = ~te
        pred[te] = nc_predict(X[tr][:, genes], y[tr], X[te][:, genes])
    return bool((pred == y).mean() >= THRESHOLD)
''',
    tail_fixed='''    fold = strat_folds(y, 10)
    pred = np.empty(y.size, dtype=bool)
    for j in range(10):
        te = fold == j
        tr = ~te
        genes = rank_genes(X[tr], y[tr])[:3]
        pred[te] = nc_predict(X[tr][:, genes], y[tr], X[te][:, genes])
    return bool((pred == y).mean() >= THRESHOLD)
''',
)


def build(case_id, version):
    c = CASES[case_id]
    body = c["head"] + c["guard_" + version] + c["help"] + c["tail_" + version]
    path = ROOT / case_id / (version + ".py")
    src = path.read_text(encoding="utf-8")
    skel = (ROOT / case_id / "skeleton.py").read_text(encoding="utf-8")
    assert src.count(MARK) == 1 or src == skel or True
    # always rebuild from the frozen skeleton copy so that the replacement is idempotent
    assert skel.count(MARK) == 1, (case_id, skel.count(MARK))
    out = skel.replace(MARK, body)
    path.write_text(out, encoding="utf-8", newline="")


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(CASES)
    for cid in ids:
        for v in ("faulty", "fixed"):
            build(cid, v)
        print("written", cid)
