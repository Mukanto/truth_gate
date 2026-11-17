"""Part 2 checks (written after reading after_part1/; Part 1 unchanged).
(a) B2-09: onsets in the 60-row test window of plus/minus samples vs a binomial with the same mean (clustering at
    the window scale). Seeds: plus default_rng(10000+i), minus default_rng(i), i = 0..199.
(b) B3-10: faulty slope on minus variants: body weight recorded with 5% error; a common 5% multiplicative error in
    heart and body weight; heart weight scaling with body weight to the power 1.3 or 0.8. 200 samples each,
    default_rng(30000+i), otherwise the W51 generator.
(c) B3-07: spread of the raw-scale fixed statistic on minus (from stats_out.json)."""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from load import load

m = load("B2-09", "faulty")
for w, s in (("plus", 10000), ("minus", 0)):
    k = []
    for i in range(200):
        y = m.__dict__[w](np.random.default_rng(s + i))["onset"]
        k.append(int(y[140:].sum()))
    k = np.array(k)
    p = k.mean() / 60.0
    pb = sum(math.comb(60, j) * p ** j * (1 - p) ** (60 - j) for j in (0, 1))
    print("B2-09 %s: onsets in last 60 rows mean %.2f var %.2f (binomial var %.2f); share <2: %.3f (binomial %.4f)"
          % (w, k.mean(), k.var(), 60 * p * (1 - p), np.mean(k < 2), pb))

f = load("B3-10", "faulty")


def gen(rng, mode):
    N = 60
    zb = rng.standard_normal(N)
    zr = rng.standard_normal(N)
    e = rng.standard_normal(N)
    bw = 350.0 * np.exp(0.10 * zb)
    ratio = 0.0031 * np.exp(0.08 * zr)
    if mode == "allo1.3":
        hw = ratio * 350.0 * (bw / 350.0) ** 1.3
    elif mode == "allo0.8":
        hw = ratio * 350.0 * (bw / 350.0) ** 0.8
    else:
        hw = ratio * bw
    sbp = 130.0 + 10.0 * zb + 9.0 * e
    bw_rec = bw
    if mode == "bw_error":
        bw_rec = bw * np.exp(0.05 * rng.standard_normal(N))
    if mode == "common_error":
        c = np.exp(0.05 * rng.standard_normal(N))
        hw, bw_rec = hw * c, bw * c
    return {"systolic_pressure": sbp, "heart_weight": hw, "body_weight": bw_rec}


src = open(os.path.join(HERE, "patched", "B3-10_faulty.py"), encoding="utf-8").read()  # statistic-returning copy from stats.py
import importlib.util
spec = importlib.util.spec_from_file_location("b310p", os.path.join(HERE, "patched", "B3-10_faulty.py"))
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)
for mode in ("exact", "bw_error", "common_error", "allo1.3", "allo0.8"):
    v = np.array([pm.criterion(gen(np.random.default_rng(30000 + i), mode)) for i in range(200)])
    print("B3-10 minus variant %-12s faulty slope mean %+.3f, holds (>=0.3) %d/200" % (mode, v.mean(), int(np.sum(v >= 0.3))))

st = json.load(open(os.path.join(HERE, "stats_out.json")))
print("B3-07 fixed raw-scale on minus:", st["B3-07"]["fixed"]["minus"])
