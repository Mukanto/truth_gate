"""Distribution of each criterion's statistic (faulty and fixed) on minus, plus and the noise probe.
200 samples per world; world i uses np.random.default_rng(SEED + i) (minus 0..199, plus 10000.., noise 20000..),
identical samples for both twins. Output: scratch/stats_out.json"""
import sys, os, re, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from load import noise_like

PAT = re.compile(r"^(    )return bool\((.+?) (>=|<=) ([^()]+?)\)\s*$")
os.makedirs(os.path.join(HERE, "patched"), exist_ok=True)

def patched_module(case, twin):
    src = open(os.path.join(HERE, "cases", case, twin + ".py"), encoding="utf-8").read().splitlines()
    out, cmp_ = [], None
    for line in src:
        m = PAT.match(line)
        if m:
            cmp_ = (m.group(3), m.group(4))
            line = f"{m.group(1)}return float({m.group(2)})"
        out.append(line)
    assert cmp_ is not None
    p = os.path.join(HERE, "patched", f"{case}_{twin}.py")
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    spec = importlib.util.spec_from_file_location(f"p_{case}_{twin}".replace("-", "_"), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, cmp_

def thr_value(mod, s):
    s = s.strip()
    if s == "thr":
        return None  # resolved from the source below
    return float(s)

def get_thr(case, twin, cmp_):
    v = cmp_[1].strip()
    if v != "thr":
        return float(v)
    src = open(os.path.join(HERE, "cases", case, twin + ".py"), encoding="utf-8").read()
    m = re.search(r"^\s+thr = ([0-9.]+)", src, re.M)
    return float(m.group(1))

N = 200
SEED = {"minus": 0, "plus": 10000, "noise": 20000}
cases = sys.argv[1:] or sorted(c for c in os.listdir(os.path.join(HERE, "cases")) if c[:2] in ("B2", "B3"))
res = {}
for case in cases:
    res[case] = {}
    mods = {tw: patched_module(case, tw) for tw in ("faulty", "fixed")}
    base = mods["faulty"][0]
    samples = {}
    for w in ("minus", "plus", "noise"):
        lst = []
        for i in range(N):
            rng = np.random.default_rng(SEED[w] + i)
            if w == "noise":
                d = noise_like(base.plus(np.random.default_rng(SEED[w] + i + 50000)), rng)
            else:
                d = getattr(base, w)(rng)
            lst.append(d)
        samples[w] = lst
    for tw, (mod, cmp_) in mods.items():
        thr = get_thr(case, tw, cmp_)
        res[case][tw] = {"cmp": cmp_[0], "thr": thr}
        for w, lst in samples.items():
            vals = []
            for d in lst:
                try:
                    v = mod.criterion(d)
                except Exception as e:
                    v = "ERR:" + type(e).__name__
                vals.append(v)
            num = np.array([v for v in vals if isinstance(v, float) and np.isfinite(v)])
            nnone = sum(1 for v in vals if v is None)
            nerr = sum(1 for v in vals if isinstance(v, str))
            holds = int(np.sum(num >= thr)) if cmp_[0] == ">=" else int(np.sum(num <= thr))
            res[case][tw][w] = {
                "mean": round(float(num.mean()), 4) if num.size else None,
                "sd": round(float(num.std()), 4) if num.size else None,
                "q05_q50_q95": [round(float(q), 4) for q in np.quantile(num, [0.05, 0.5, 0.95])] if num.size else None,
                "holds": holds, "none": nnone, "err": nerr, "n": N,
            }
    print(case, json.dumps({tw: {w: (res[case][tw][w]["mean"], res[case][tw][w]["holds"], res[case][tw][w]["none"]) for w in ("minus", "plus", "noise")} for tw in ("faulty", "fixed")}), flush=True)
out = os.path.join(HERE, "stats_out.json")
old = json.load(open(out)) if os.path.exists(out) else {}
old.update(res)
json.dump(old, open(out, "w"), indent=1)
