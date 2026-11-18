import numpy as np

SRC = {}

SRC["ratio_pn"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    return float(X.shape[1] / X.shape[0])
'''

SRC["poly_terms"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    n, p = X.shape
    return float((p * (p + 3) / 2) / n)
'''

SRC["missing_frac"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    return float(np.mean(np.isnan(X)))
'''

SRC["occupied_cat"] = '''def stat(d):
    C = np.asarray(d["category"], dtype=bool)
    return float(np.sum(C.any(axis=0)) / C.shape[0])
'''

SRC["near_dup"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-12)
    sq = (X ** 2).sum(axis=1)
    D = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2.0 * (X @ X.T), 0.0))
    n = D.shape[0]
    med = np.median(D[~np.eye(n, dtype=bool)])
    np.fill_diagonal(D, np.inf)
    return float(np.mean(D.min(axis=1) < 0.1 * med))
'''

SRC["acf_series"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    a = X[:-1] - X[:-1].mean(axis=0)
    b = X[1:] - X[1:].mean(axis=0)
    den = np.sqrt((a ** 2).sum(axis=0) * (b ** 2).sum(axis=0))
    r = (a * b).sum(axis=0) / np.where(den > 0, den, 1.0)
    return float(np.mean(r))
'''

SRC["acf_panel"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    F = X.shape[2]
    a = X[:, :-1, :].reshape(-1, F)
    b = X[:, 1:, :].reshape(-1, F)
    a = a - a.mean(axis=0)
    b = b - b.mean(axis=0)
    den = np.sqrt((a ** 2).sum(axis=0) * (b ** 2).sum(axis=0))
    r = (a * b).sum(axis=0) / np.where(den > 0, den, 1.0)
    return float(np.mean(r))
'''

SRC["icc"] = '''def stat(d):
    X = np.asarray(d["X"], dtype=float)
    S, T, F = X.shape
    m = X.mean(axis=1)
    w = ((X - m[:, None, :]) ** 2).sum(axis=(0, 1)) / (S * (T - 1))
    b = m.var(axis=0, ddof=1) - w / T
    tot = b + w
    icc = b / np.where(tot > 0, tot, 1.0)
    return float(np.mean(icc))
'''

SRC["minority_frac"] = '''def stat(d):
    y = np.asarray(d["y"], dtype=bool)
    q = float(np.mean(y))
    return float(min(q, 1.0 - q))
'''


def load(name):
    ns = {"np": np}
    exec(SRC[name], ns)
    return ns["stat"]


rng = np.random.default_rng(0)


def report(name, d):
    v = load(name)(d)
    print(f"{name:14s} -> {v!r}  finite={np.isfinite(v)}  type={type(v).__name__}")


# random arrays with the brief shapes
report("ratio_pn", {"X": rng.normal(size=(100, 150)), "y": rng.normal(size=100)})
report("poly_terms", {"X": rng.normal(size=(300, 10)), "y": rng.normal(size=300)})
Xm = rng.normal(size=(250, 20)); Xm[rng.random(Xm.shape) < 0.25] = np.nan
report("missing_frac", {"X": Xm, "y": rng.normal(size=250)})
cat = np.zeros((1200, 150), dtype=bool); cat[np.arange(1200), rng.integers(0, 150, 1200)] = True
report("occupied_cat", {"category": cat})
Xd = rng.normal(size=(600, 8))
report("near_dup", {"X": Xd})  # no duplicates
Xd2 = np.vstack([Xd[:420], Xd[:180]])  # 180 exact copies
report("near_dup", {"X": Xd2})
report("near_dup", {"X": rng.normal(size=(2000, 20))})  # largest size
report("acf_series", {"X": np.cumsum(rng.normal(size=(1000, 6)), axis=0)})
report("acf_series", {"X": rng.normal(size=(1000, 6))})
report("acf_panel", {"X": rng.normal(size=(40, 250, 5))})
base = rng.normal(size=(60, 1, 25))
report("icc", {"X": base + rng.normal(size=(60, 30, 25))})
report("icc", {"X": rng.normal(size=(60, 30, 25))})
report("minority_frac", {"y": rng.random(1000) < 0.08})
