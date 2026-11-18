"""Runs the FIXED bodies on arrays generated here from each brief's keys, shapes and dtypes (pure noise; no world, no rate
is read from the result). Checks: it runs, returns a bool, is deterministic for the same data, and how long it takes.
Never run on a faulty body. Usage: py run_fixed.py [local ids ...]  (default: all)"""
import importlib.util
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HALF = os.path.dirname(HERE)
IDS = json.load(open(os.path.join(HALF, "CASE_IDS.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "run_results.json")
results = json.load(open(OUT)) if os.path.exists(OUT) else {}


def make(brief, rng):
    d = {}
    for k in brief["data_keys"]:
        shape = tuple(k["dims"])
        if k["dtype"] == "bool":
            d[k["key"]] = rng.random(shape) < 0.2
        else:
            d[k["key"]] = rng.normal(size=shape)
    return d


def load(path):
    spec = importlib.util.spec_from_file_location("body_" + os.path.basename(os.path.dirname(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


todo = sys.argv[1:] or list(IDS)
for local in todo:
    cid = IDS[local]
    folder = os.path.join(HALF, "cases", cid)
    brief = json.load(open(os.path.join(folder, "brief.json"), encoding="utf-8"))
    mod = load(os.path.join(folder, "fixed_body.py"))
    times, vals = [], []
    deterministic = None
    for seed in (101, 102, 103):
        d = make(brief, np.random.default_rng(seed))
        t0 = time.time()
        r = mod.criterion(d)
        times.append(time.time() - t0)
        assert r is None or isinstance(r, bool), (local, type(r))
        vals.append(r)
        if seed == 101:
            deterministic = (mod.criterion(d) == r)
    results[local] = dict(case=cid, runs=3, plus_repeat_of_first=1, values=vals, deterministic=deterministic,
                          seconds=[round(t, 2) for t in times])
    print(local, cid, vals, "deterministic" if deterministic else "NOT DETERMINISTIC",
          ["%.2fs" % t for t in times], flush=True)
    json.dump(results, open(OUT, "w"), indent=1)
