import numpy as np


def _random_folds(rng, n, k):
    """Fold index (0..k-1) of each of n items, assigned uniformly at random with sizes as equal as possible."""
    fid = np.empty(n, dtype=np.int64)
    fid[rng.permutation(n)] = np.arange(n) % k
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


def _forest_scores(xtr, ytr, xte, rng, ntree, min_leaf, mtry):
    """Random forest: ntree trees on bootstrap resamples of the rows, mtry columns searched per node; mean prediction."""
    n = xtr.shape[0]
    out = np.zeros(xte.shape[0])
    for _ in range(ntree):
        bs = rng.integers(0, n, n)
        out += _tree_predict(_grow(xtr[bs], ytr[bs], rng, 1000, min_leaf, mtry), xte)
    return out / ntree


def _auc(score, y):
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


def criterion(d):
    """Claim: sensor measurements classify the disease status of newly recruited subjects: the area under the ROC curve
    of the classification is at least 0.70.
    d["measurements"]: float array (subjects, records, variables); sensor measurements of each recording of each
    subject.
    d["diseased"]: bool array (subjects,); True if the subject has the disease.
    Returns True when the AUC is at least 0.70, False otherwise, None at an allowed guard (non-finite values, fewer
    than 2 subjects, no diseased or no healthy subject)."""
    x3 = np.asarray(d["measurements"], dtype=float)
    dis = np.asarray(d["diseased"], dtype=bool)
    if not np.all(np.isfinite(x3)):
        return None
    s, m, v = x3.shape
    x = x3.reshape(s * m, v)
    y = np.repeat(dis, m)
    n = y.size
    if s < 2 or dis.all() or not dis.any():
        return None
    rng = np.random.default_rng(2015)
    mtry = max(1, int(np.sqrt(v)))
    nf = 10
    folds = _random_folds(rng, n, nf)
    scores = np.zeros(n)
    for f in range(nf):
        te = folds == f
        scores[te] = _forest_scores(x[~te], y[~te].astype(float), x[te], rng, 50, 1, mtry)
    return bool(_auc(scores, y) >= 0.70)
