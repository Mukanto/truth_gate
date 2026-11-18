"""Checks that the estimators of the FIXED bodies recover a known true value on arrays generated here.

Uses only fixed_body.py (helper functions imported; D-006's inline estimator re-stated line by line).
Not a rate; one large array per check (n = 200000), no tuning.
Usage: py -I check_estimators.py
"""
import importlib.util
import os

import numpy as np

ROOT = r"E:\Claude Projects\Kapi\phase_d_work\criterion\B3A\half\cases"


def load(cid):
    path = os.path.join(ROOT, cid, "fixed_body.py")
    spec = importlib.util.spec_from_file_location("fx_" + cid.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rng = np.random.default_rng(11)
n = 200000
# source-like growth model: true BMI = b0 + b1 * t, t = 0..5 (ages 5..10); error SD 1.2 (ICC about 0.5)
b0 = 15 + 1.2 * rng.normal(0, 1, n)
b1 = 0.4 - 0.1 * (b0 - 15) + 0.15 * rng.normal(0, 1, n)
sd_e = 1.2
true_b = np.cov(b0, 5 * b1)[0, 1] / np.var(b0, ddof=1)  # slope of true change on true baseline
true_r_change = np.corrcoef(b0, 5 * b1)[0, 1]
true_r_slope = np.corrcoef(b0, b1)[0, 1]
t = np.arange(6)
bmi = b0[:, None] + b1[:, None] * t[None, :] + sd_e * rng.normal(0, 1, (n, 6))
u1 = bmi[:, 0]
u2 = bmi[:, 5]
u1b = b0 + sd_e * rng.normal(0, 1, n)

m = load("D-015")
k = 1.0 - m._corr(u1, u1b)
b_c, r_c = m._change_stats(u1, u2, 0.0)
b_a, r_a = m._change_stats(u1, u2, k)
print("D-015/D-037 helper: true slope of change on baseline %.4f | crude %.4f | adjusted %.4f (k=%.4f)"
      % (true_b, b_c, b_a, k))
print("                    true corr(level, change) %.4f | crude %.4f | adjusted %.4f"
      % (true_r_change, r_c, r_a))

# D-037's k from a retest sample (error variance from two sessions)
rt = (15 + 1.2 * rng.normal(0, 1, (100000, 1))) + sd_e * rng.normal(0, 1, (100000, 2))
k2 = float(np.mean(np.var(rt, axis=1, ddof=1)) / np.var(u1, ddof=1))
print("                    k from retest sample %.4f (true %.4f)" % (k2, sd_e ** 2 / np.var(u1, ddof=1)))

# D-006 inline estimator, restated from fixed_body.py
n_, m_ = bmi.shape
X = np.column_stack([np.ones(m_), np.arange(m_, dtype=float)])
XtXi = np.linalg.inv(X.T @ X)
bhat = bmi @ X @ XtXi
res = bmi - bhat @ X.T
s2 = np.sum(res * res) / (n_ * (m_ - 2))
G = np.cov(bhat, rowvar=False) - s2 * XtXi
r_re = G[0, 1] / np.sqrt(G[0, 0] * G[1, 1])
r_ols = np.corrcoef(bhat[:, 0], bhat[:, 1])[0, 1]
print("D-006 random-effects estimator: true corr(b0, b1) %.4f | corrected %.4f | per-child OLS uncorrected %.4f"
      % (true_r_slope, r_re, r_ols))

# partial correlation and standardised coefficient on a known structure
p = load("D-040")
nn = 100000
z = rng.normal(0, 1, nn)
w = rng.normal(0, 1, nn)
x = 2 * z + w + rng.normal(0, 1, nn)
y = -z + w + rng.normal(0, 1, nn)
true_pc = (1.0) / np.sqrt((1 + 1) * (1 + 1))  # cov(rx, ry) = var(w) = 1; var(rx) = var(ry) = 2
print("D-040 partial corr: true %.4f | estimated %.4f" % (true_pc, p._partial_corr(x, y, z)))
q = load("D-038")
xx = rng.normal(0, 1, nn)
pp = 0.6 * xx + rng.normal(0, 1, nn)
yy = 0.5 * xx + 2 * pp + rng.normal(0, 1, nn)
print("D-038 standardised coefficient: true %.4f | estimated %.4f"
      % (0.5 * np.std(xx) / np.std(yy), q._std_coef(yy, np.column_stack([xx, pp]), 0)))
