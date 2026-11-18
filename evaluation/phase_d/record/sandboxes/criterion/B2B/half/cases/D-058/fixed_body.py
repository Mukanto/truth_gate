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


def criterion(d):
    """Claim: features computed from wearable-sensor signals recognise walking in newly recruited subjects: the
    classification error rate for walking versus other activities is at most 0.10.
    d["signal_features"]: float array (subjects, windows, features); features computed from the sensor signal in each
    time window of each subject.
    d["walking"]: bool array (subjects, windows); True if the subject was walking during the window.
    Returns True when the error rate is at most 0.10, False otherwise, None at an allowed guard (non-finite values,
    no window)."""
    x3 = np.asarray(d["signal_features"], dtype=float)
    y2 = np.asarray(d["walking"], dtype=bool)
    if not np.all(np.isfinite(x3)):
        return None
    s, m, v = x3.shape
    x = x3.reshape(s * m, v)
    y = y2.reshape(s * m)
    n = y.size
    if n < 1:
        return None
    rng = np.random.default_rng(2010)
    mtry = max(1, int(np.sqrt(v)))
    folds = np.repeat(_random_folds(rng, s, 10), m)
    pred = np.zeros(n, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _forest_scores(x[~te], y[~te].astype(float), x[te], rng, 50, 1, mtry) > 0.5
    return bool(np.mean(pred != y) <= 0.10)
