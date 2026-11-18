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


def _r2(y, pred):
    """1 - SSE/SST, with SST taken about the mean of y."""
    return 1.0 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def criterion(d):
    """Claim: the monthly environmental measurements predict the abundance in later months of the series: the
    out-of-sample R-squared is at least 0.30.
    d["abundance"]: float array (months,); monthly abundance index of the species, on a log scale, in time order.
    d["environment"]: float array (months, variables); monthly environmental measurements, in time order.
    Returns True when the R-squared is at least 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 evaluated months, constant evaluated abundance)."""
    y = np.asarray(d["abundance"], dtype=float)
    x = np.asarray(d["environment"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    rng = np.random.default_rng(2008)
    mtry = max(1, x.shape[1] // 3)
    edges = (np.arange(11) * n) // 10
    parts = []
    for b in range(2, 10):
        tr = np.arange(edges[b])
        te = np.arange(edges[b], edges[b + 1])
        parts.append(_forest_scores(x[tr], y[tr], x[te], rng, 50, 5, mtry))
    pred = np.concatenate(parts)
    ye = y[edges[2]:]
    if ye.size < 2 or ye.max() == ye.min():
        return None
    return bool(_r2(ye, pred) >= 0.30)
