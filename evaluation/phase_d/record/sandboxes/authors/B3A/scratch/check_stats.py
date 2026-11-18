import json, re, sys
import numpy as np
base = r"E:\Claude Projects\Kapi\phase_d_work\authors\B3A"
briefs = json.load(open(base + r"\BRIEFS.json", encoding="utf-8"))
priv = {p["local_id"]: p for p in json.load(open(base + r"\PRIVATE.json", encoding="utf-8"))}
rng = np.random.default_rng(1)
for b in briefs:
    d = {}
    for k in b["data_keys"]:
        axes = [a.strip() for a in k["shape"].strip("()").split(",") if a.strip()]
        shape = tuple(b["sizes"][a] for a in axes)
        if k["dtype"] == "bool":
            d[k["key"]] = rng.random(shape) < 0.4
        else:
            d[k["key"]] = np.exp(rng.normal(2.0, 0.2, shape))
    ns = {"np": np}
    exec(priv[b["local_id"]]["structure_statistic"]["code"], ns)
    v = ns["stat"](d)
    print(b["local_id"], type(v).__name__, v, np.isfinite(v))
