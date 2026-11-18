import json, re, sys
import numpy as np

base = sys.argv[1]
briefs = json.load(open(base + "/BRIEFS.json", encoding="utf-8"))
priv = {p["local_id"]: p for p in json.load(open(base + "/PRIVATE.json", encoding="utf-8"))}
rng = np.random.default_rng(0)
for b in briefs:
    d = {}
    for k in b["data_keys"]:
        axes = [a.strip() for a in k["shape"].strip("()").split(",") if a.strip()]
        shape = tuple(b["sizes"][a] for a in axes)
        assert int(np.prod(shape)) <= 2_000_000 and max(shape) <= 2000, (b["local_id"], k["key"])
        if k["dtype"] == "bool":
            d[k["key"]] = rng.random(shape) < 0.2
        else:
            d[k["key"]] = rng.normal(size=shape)
    ns = {"np": np}
    exec(priv[b["local_id"]]["structure_statistic"]["code"], ns)
    v = ns["stat"](d)
    print(b["local_id"], type(v).__name__, v, np.isfinite(v))
