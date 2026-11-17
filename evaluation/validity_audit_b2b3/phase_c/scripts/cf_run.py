"""Counterfactual for pairs whose fixed twin is not clean: threshold at the fixed twin's 95th percentile on the
same 200 minus samples (the gate's seeds), and the faulty twin's minus rate at that threshold."""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_run import load, stream_rng, SEED, N
out = {}
for case in ["B2-08", "B2-09", "B2-10", "B2-11", "B3-04", "B3-12"]:
    fau, fix = load(case, "faulty"), load(case, "fixed")
    minus = fix.STUDY.worlds["minus"].generate
    fs, xs = [], []
    for i in range(N):
        d = minus(stream_rng(SEED, "world:minus", i))
        fs.append(fau.criterion({k: np.array(v, copy=True) for k, v in d.items()})[0])
        xs.append(fix.criterion({k: np.array(v, copy=True) for k, v in d.items()})[0])
    fs, xs = np.array(fs), np.array(xs)
    if case == "B3-12":   # statistic is the t value; holds = t > t_crit; compare on t
        pass
    thr = float(np.quantile(xs, 0.95))
    rec = {"fixed_q95_threshold": round(thr, 4), "fixed_rate_at_thr": int((xs > thr).sum()),
           "faulty_rate_at_thr": int((fs > thr).sum()), "n": N}
    out[case] = rec
    print(case, rec, flush=True)
json.dump(out, open("cf_out.json", "w"), indent=1)
