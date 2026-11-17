"""Extra checks (not case files).
1. B2-12: in-sample OLS R^2 of stay on the 15 characteristics (all 240 rows) in minus: the most a linear model can
   exploit, compared with the threshold 0.40.
2. B2-03: the faulty criterion on a minus-like world with more genes (same generator form, blocks of ten genes,
   no class difference), to see how the selection bias grows with the number of candidate genes.
Seeds: minus sample i uses np.random.default_rng(i), i = 0..N-1."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from load import load

m = load("B2-12", "faulty")
r2 = []
for i in range(200):
    d = m.minus(np.random.default_rng(i))
    x = d["x"].reshape(-1, d["x"].shape[2])
    y = d["stay"].reshape(-1)
    a = np.column_stack([np.ones(y.size), x])
    b = np.linalg.lstsq(a, y, rcond=None)[0]
    r2.append(1 - np.sum((y - a @ b) ** 2) / np.sum((y - y.mean()) ** 2))
r2 = np.array(r2)
print("B2-12 in-sample OLS R2 minus: mean %.3f, q95 %.3f, max %.3f, >=0.40: %d/200" % (r2.mean(), np.quantile(r2, 0.95), r2.max(), np.sum(r2 >= 0.4)))

m3 = load("B2-03", "faulty")


def gen_minus(rng, G, N=62):
    cancer = rng.permutation(np.arange(N) < 40)
    blk = rng.standard_normal((N, G // 10))
    e = rng.standard_normal((N, G))
    mu = 8.0 + 1.2 * rng.standard_normal(G)
    sd = 0.6 + 0.6 * rng.random(G)
    z = 0.5 * np.repeat(blk, 10, axis=1) + np.sqrt(1.0 - 0.5 ** 2) * e
    return {"expr": mu[None, :] + sd[None, :] * z, "cancer": cancer.astype(bool)}


for G in (60, 600, 2000):
    n = 100
    h = sum(bool(m3.criterion(gen_minus(np.random.default_rng(i), G))) for i in range(n))
    print("B2-03 faulty on minus-like world with %d genes: holds %d/%d" % (G, h, n))
