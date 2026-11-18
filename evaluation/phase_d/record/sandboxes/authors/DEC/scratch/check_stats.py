import json, re, numpy as np
base = "E:/Claude Projects/Kapi/phase_d_work/authors/DEC/"
B = json.load(open(base + "BRIEFS.json")); P = {p["local_id"]: p for p in json.load(open(base + "PRIVATE.json"))}
rng = np.random.default_rng(0)
for b in B:
    sz = b["sizes"]; d = {}
    for k in b["data_keys"]:
        shp = tuple(sz[a.strip()] for a in k["shape"].strip("()").split(",") if a.strip())
        d[k["key"]] = (rng.random(shp) < 0.5) if k["dtype"] == "bool" else rng.normal(size=shp)
    ss = P[b["local_id"]]["structure_statistic"]
    if ss is None:
        print(b["local_id"], "null"); continue
    ns = {"np": np}; exec(ss["code"], ns)
    v = ns["stat"](d)
    print(b["local_id"], type(v).__name__, v, np.isfinite(v))
