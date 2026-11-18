import numpy as np


def _stratified_folds(rng, y, k):
    """Fold index (0..k-1) of each item, assigned at random within each class of the bool vector y."""
    fid = np.empty(y.size, dtype=np.int64)
    off = 0
    for c in (False, True):
        idx = np.flatnonzero(y == c)
        idx = idx[rng.permutation(idx.size)]
        fid[idx] = (np.arange(idx.size) + off) % k
        off += idx.size
    return fid


def _grow(x, y, rng, max_depth, min_leaf, mtry):
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


def _tree_predict(tree, x):
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


def _tree_scores(xtr, ytr, xte, rng, max_depth, min_leaf):
    """One tree on all columns; leaf mean (probability of the positive class for a 0/1 target) for each row of xte."""
    tree = _grow(xtr, ytr, rng, max_depth, min_leaf, xtr.shape[1])
    return _tree_predict(tree, xte)


def _smote(x, y, rng, k):
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


def _f1(y, pred):
    """F1 score of the positive class."""
    tp = float(np.sum(pred & y))
    fp = float(np.sum(pred & ~y))
    fn = float(np.sum(~pred & y))
    return 2.0 * tp / (2.0 * tp + fp + fn)


def criterion(d):
    """Claim: a classifier built from the 12 measured variables recognises the positive class in new records with an F1
    score for the positive class of at least 0.50.
    d["features"]: float array (records, variables); measured variables of each record.
    d["positive"]: bool array (records,); True if the condition is present in the record.
    Returns True when the F1 score is at least 0.50, False otherwise, None at an allowed guard (non-finite values, no
    positive record)."""
    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["positive"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if not np.any(y):
        return None
    rng = np.random.default_rng(2003)
    xs, ys = _smote(x, y, rng, 5)
    folds = _stratified_folds(rng, ys, 5)
    ye = ys
    pred = np.zeros(ys.size, dtype=bool)
    for f in range(5):
        te = folds == f
        pred[te] = _tree_scores(xs[~te], ys[~te].astype(float), xs[te], rng, 6, 1) > 0.5
    return bool(_f1(ye, pred) >= 0.50)
