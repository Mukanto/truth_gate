"""Source text of the module-level helper functions shared by every body file (B2B half).

Each entry is a function definition. gen_bodies.py assembles a body file as
`import numpy as np` + the chosen helpers + the case's `criterion`. The same helper text goes into the faulty and the
fixed file of a case, so the two files differ only in the lines of `criterion` that carry the error and its correction.
This module is a text store; it is not imported by any body.
"""

HELPERS = {}

HELPERS["_standardise"] = '''def _standardise(xtr, xte):
    """Centre and scale the columns of xtr and apply the same centring and scaling to xte."""
    mu = xtr.mean(axis=0)
    sd = xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (xtr - mu) / sd, (xte - mu) / sd
'''

HELPERS["_ridge_predict"] = '''def _ridge_predict(xtr, ytr, xte, lam):
    """Ridge regression with penalty lam on standardised columns (dual form); predictions for the rows of xte."""
    a, b = _standardise(xtr, xte)
    ym = ytr.mean()
    k = a @ a.T
    alpha = np.linalg.solve(k + lam * np.eye(k.shape[0]), ytr - ym)
    return ym + (b @ a.T) @ alpha
'''

HELPERS["_logit_scores"] = '''def _logit_scores(xtr, ytr, xte, lam):
    """L2-penalised logistic regression (penalty lam, unpenalised intercept) on standardised columns, fitted by
    Newton steps in dual form; returns the linear scores of the rows of xte."""
    a, b = _standardise(xtr, xte)
    k = a @ a.T
    n = k.shape[0]
    yv = ytr.astype(float)
    f = np.zeros(n)
    alpha = np.zeros(n)
    bias = 0.0
    for _ in range(60):
        pr = 1.0 / (1.0 + np.exp(-np.clip(f, -35.0, 35.0)))
        w = np.maximum(pr * (1.0 - pr), 1e-6)
        z = f + (yv - pr) / w
        mat = np.zeros((n + 1, n + 1))
        mat[:n, :n] = k + lam * np.diag(1.0 / w)
        mat[:n, n] = 1.0
        mat[n, :n] = 1.0
        sol = np.linalg.solve(mat, np.concatenate([z, [0.0]]))
        alpha = sol[:n]
        bias = sol[n]
        f_new = k @ alpha + bias
        done = np.max(np.abs(f_new - f)) < 1e-9
        f = f_new
        if done:
            break
    return (b @ a.T) @ alpha + bias
'''

HELPERS["_r2"] = '''def _r2(y, pred):
    """1 - SSE/SST, with SST taken about the mean of y."""
    return 1.0 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
'''

HELPERS["_corr"] = '''def _corr(a, b):
    """Pearson correlation of two vectors."""
    a = a - a.mean()
    b = b - b.mean()
    return (a @ b) / np.sqrt((a @ a) * (b @ b))
'''

HELPERS["_random_folds"] = '''def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
    return fid
'''

HELPERS["_stratified_folds"] = '''def _stratified_folds(rng, y, k):
    """Fold index (0..k-1) of each item, assigned at random within each class of the bool vector y."""
    fid = np.empty(y.size, dtype=np.int64)
    off = 0
    for c in (False, True):
        idx = np.flatnonzero(y == c)
        idx = idx[rng.permutation(idx.size)]
        fid[idx] = (np.arange(idx.size) + off) % k
        off += idx.size
    return fid
'''

HELPERS["_auc"] = '''def _auc(score, y):
    """Area under the ROC curve of score for the bool vector y (average ranks for ties)."""
    n = score.size
    order = np.argsort(score, kind="mergesort")
    s = score[order]
    new = np.concatenate([[True], s[1:] != s[:-1]])
    gid = np.cumsum(new) - 1
    first = np.flatnonzero(new)
    last = np.concatenate([first[1:], [n]])
    avg = (first + last + 1) / 2.0
    ranks = np.empty(n)
    ranks[order] = avg[gid]
    n1 = float(y.sum())
    n0 = n - n1
    return (ranks[y].sum() - n1 * (n1 + 1.0) / 2.0) / (n1 * n0)
'''

HELPERS["_grow"] = '''def _grow(x, y, rng, max_depth, min_leaf, mtry):
    """Grow one binary regression tree by variance reduction (equal to the Gini criterion for a 0/1 target).
    At each node mtry randomly chosen columns are searched (all columns when mtry >= number of columns)."""
    p = x.shape[1]
    feat = [-1]
    thr = [0.0]
    left = [-1]
    right = [-1]
    val = [0.0]
    stack = [(0, np.arange(x.shape[0]), 0)]
    while stack:
        node, idx, depth = stack.pop()
        yn = y[idx]
        m = idx.size
        mean = float(yn.mean())
        val[node] = mean
        if depth >= max_depth or m < 2 * min_leaf or yn.min() == yn.max():
            continue
        if mtry < p:
            cols = rng.permutation(p)[:mtry]
        else:
            cols = np.arange(p)
        xs = x[idx][:, cols]
        order = np.argsort(xs, axis=0, kind="stable")
        xsort = np.take_along_axis(xs, order, axis=0)
        csum = np.cumsum((yn - mean)[order], axis=0)
        nl = np.arange(1, m, dtype=float)[:, None]
        cl = csum[:-1]
        cr = csum[-1] - cl
        score = cl ** 2 / nl + cr ** 2 / (m - nl)
        ok = (xsort[1:] > xsort[:-1]) & (nl >= min_leaf) & (m - nl >= min_leaf)
        if not ok.any():
            continue
        score = np.where(ok, score, -np.inf)
        pos, c = divmod(int(np.argmax(score)), score.shape[1])
        lo = xsort[pos, c]
        hi = xsort[pos + 1, c]
        t = 0.5 * (lo + hi)
        if not t < hi:
            t = lo
        f = int(cols[c])
        goleft = x[idx, f] <= t
        li = len(feat)
        for _ in range(2):
            feat.append(-1)
            thr.append(0.0)
            left.append(-1)
            right.append(-1)
            val.append(0.0)
        feat[node] = f
        thr[node] = float(t)
        left[node] = li
        right[node] = li + 1
        stack.append((li, idx[goleft], depth + 1))
        stack.append((li + 1, idx[~goleft], depth + 1))
    return (np.array(feat), np.array(thr), np.array(left), np.array(right), np.array(val))
'''

HELPERS["_tree_predict"] = '''def _tree_predict(tree, x):
    """Leaf mean of the tree for each row of x."""
    feat, thr, left, right, val = tree
    node = np.zeros(x.shape[0], dtype=np.int64)
    rows = np.arange(x.shape[0])
    while rows.size:
        nd = node[rows]
        f = feat[nd]
        inner = f >= 0
        rows = rows[inner]
        nd = nd[inner]
        f = f[inner]
        go = x[rows, f] <= thr[nd]
        node[rows] = np.where(go, left[nd], right[nd])
    return val[node]
'''

HELPERS["_tree_scores"] = '''def _tree_scores(xtr, ytr, xte, rng, max_depth, min_leaf):
    """One tree on all columns; leaf mean (probability of the positive class for a 0/1 target) for each row of xte."""
    tree = _grow(xtr, ytr, rng, max_depth, min_leaf, xtr.shape[1])
    return _tree_predict(tree, xte)
'''

HELPERS["_forest_scores"] = '''def _forest_scores(xtr, ytr, xte, rng, ntree, min_leaf, mtry):
    """Random forest: ntree trees on bootstrap resamples of the rows, mtry columns searched per node; mean prediction."""
    n = xtr.shape[0]
    out = np.zeros(xte.shape[0])
    for _ in range(ntree):
        bs = rng.integers(0, n, n)
        out += _tree_predict(_grow(xtr[bs], ytr[bs], rng, 1000, min_leaf, mtry), xte)
    return out / ntree
'''

HELPERS["_smote"] = '''def _smote(x, y, rng, k):
    """SMOTE: the smaller class of the bool vector y is synthesised up to the size of the larger class; each synthetic
    row lies at a random point on the segment from a minority row to one of its k nearest minority neighbours."""
    npos = int(y.sum())
    nneg = y.size - npos
    minority = npos < nneg
    nmin = min(npos, nneg)
    nsyn = abs(npos - nneg)
    if nmin < 2 or nsyn == 0:
        return x, y
    xm = x[y == minority]
    ke = min(k, nmin - 1)
    sq = (xm ** 2).sum(axis=1)
    d2 = sq[:, None] + sq[None, :] - 2.0 * (xm @ xm.T)
    np.fill_diagonal(d2, np.inf)
    nbr = np.argpartition(d2, ke - 1, axis=1)[:, :ke]
    rows = rng.integers(0, nmin, nsyn)
    pick = nbr[rows, rng.integers(0, ke, nsyn)]
    gap = rng.random(nsyn)[:, None]
    xsyn = xm[rows] + gap * (xm[pick] - xm[rows])
    return np.vstack([x, xsyn]), np.concatenate([y, np.full(nsyn, minority)])
'''

HELPERS["_oversample"] = '''def _oversample(x, y, rng):
    """Random oversampling: rows of the smaller class of the bool vector y are copied, drawn with replacement, until
    the two classes have equal counts."""
    npos = int(y.sum())
    nneg = y.size - npos
    minority = npos < nneg
    nmin = min(npos, nneg)
    nsyn = abs(npos - nneg)
    if nmin == 0 or nsyn == 0:
        return x, y
    idx = np.flatnonzero(y == minority)
    pick = idx[rng.integers(0, idx.size, nsyn)]
    return np.vstack([x, x[pick]]), np.concatenate([y, y[pick]])
'''

HELPERS["_knn_scores"] = '''def _knn_scores(xtr, ytr, xte, k):
    """k-nearest-neighbour mean of ytr over the k nearest rows of xtr (Euclidean, columns standardised with xtr)."""
    a, b = _standardise(xtr, xte)
    d2 = (b ** 2).sum(axis=1)[:, None] + (a ** 2).sum(axis=1)[None, :] - 2.0 * (b @ a.T)
    nb = np.argpartition(d2, k - 1, axis=1)[:, :k]
    return ytr[nb].mean(axis=1)
'''

HELPERS["_f1"] = '''def _f1(y, pred):
    """F1 score of the positive class."""
    tp = float(np.sum(pred & y))
    fp = float(np.sum(pred & ~y))
    fn = float(np.sum(~pred & y))
    return 2.0 * tp / (2.0 * tp + fp + fn)
'''

HELPERS["_balanced_accuracy"] = '''def _balanced_accuracy(y, pred):
    """Mean of sensitivity and specificity."""
    sens = np.sum(pred & y) / float(np.sum(y))
    spec = np.sum(~pred & ~y) / float(np.sum(~y))
    return 0.5 * (sens + spec)
'''

HELPERS["_top_genes"] = '''def _top_genes(x, y, k):
    """Indices of the k columns of x with the largest absolute two-sample (pooled-variance) t-statistic for the bool
    vector y."""
    x1 = x[y]
    x0 = x[~y]
    n1 = x1.shape[0]
    n0 = x0.shape[0]
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    ss = ((x1 - m1) ** 2).sum(axis=0) + ((x0 - m0) ** 2).sum(axis=0)
    den = np.sqrt(ss / (n1 + n0 - 2) * (1.0 / n1 + 1.0 / n0))
    t = np.where(den > 0, (m1 - m0) / np.where(den > 0, den, 1.0), 0.0)
    return np.argsort(-np.abs(t), kind="stable")[:k]
'''

HELPERS["_lda_predict"] = '''def _lda_predict(xtr, ytr, xte):
    """Fisher's linear discriminant (pooled within-class covariance, midpoint threshold); bool prediction for xte."""
    x1 = xtr[ytr]
    x0 = xtr[~ytr]
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    sc = ((x1 - m1).T @ (x1 - m1) + (x0 - m0).T @ (x0 - m0)) / (xtr.shape[0] - 2)
    w = np.linalg.pinv(sc) @ (m1 - m0)
    return (xte - 0.5 * (m1 + m0)) @ w > 0
'''

HELPERS["_centroid_scores"] = '''def _centroid_scores(xtr, ytr, xte):
    """Nearest-centroid score: distance to the centroid of the False class minus distance to that of the True class."""
    m1 = xtr[ytr].mean(axis=0)
    m0 = xtr[~ytr].mean(axis=0)
    return np.sqrt(((xte - m0) ** 2).sum(axis=1)) - np.sqrt(((xte - m1) ** 2).sum(axis=1))
'''

HELPERS["_nsc_errors"] = '''def _nsc_errors(xtr, ytr, xte, yte, deltas):
    """Nearest shrunken centroids (standardised centroid differences soft-thresholded at each value of deltas, class
    proportions as priors) fitted on (xtr, ytr); number of misclassified rows of xte for each threshold."""
    n = xtr.shape[0]
    x1 = xtr[ytr]
    x0 = xtr[~ytr]
    n1 = x1.shape[0]
    n0 = n - n1
    m1 = x1.mean(axis=0)
    m0 = x0.mean(axis=0)
    xbar = xtr.mean(axis=0)
    ss = ((x1 - m1) ** 2).sum(axis=0) + ((x0 - m0) ** 2).sum(axis=0)
    s = np.sqrt(ss / (n - 2))
    sj = s + np.median(s)
    mk = np.sqrt(np.array([1.0 / n0 - 1.0 / n, 1.0 / n1 - 1.0 / n]))
    cm = np.stack([m0, m1])
    dk = (cm - xbar) / (mk[:, None] * sj)
    ds = np.sign(dk)[None] * np.maximum(np.abs(dk)[None] - deltas[:, None, None], 0.0)
    cent = xbar + mk[None, :, None] * sj * ds
    logpi = np.log(np.array([n0, n1], dtype=float) / n)
    diff = (xte[None, :, None, :] - cent[:, None, :, :]) / sj
    delta = (diff ** 2).sum(axis=3) - 2.0 * logpi
    pred = delta[:, :, 1] < delta[:, :, 0]
    return (pred != yte[None, :]).sum(axis=1)
'''

HELPERS["_cv_errors_nsc"] = '''def _cv_errors_nsc(x, y, folds, nf, deltas):
    """Cross-validation error counts of the shrunken-centroid classifier for each threshold, with the given folds."""
    err = np.zeros(deltas.size, dtype=np.int64)
    for f in range(nf):
        te = folds == f
        err += _nsc_errors(x[~te], y[~te], x[te], y[te], deltas)
    return err
'''

HELPERS["_pick_delta"] = '''def _pick_delta(err):
    """Index of the smallest error count; ties go to the larger threshold (thresholds are in increasing order)."""
    return int(np.flatnonzero(err == err.min())[-1])
'''
