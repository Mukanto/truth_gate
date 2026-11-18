import json, re
import numpy as np

base = r"E:\Claude Projects\Kapi\phase_d_work\authors\B3B"
briefs = json.load(open(base + r"\BRIEFS.json", encoding="utf-8"))
priv = {p["local_id"]: p for p in json.load(open(base + r"\PRIVATE.json", encoding="utf-8"))}
rng = np.random.default_rng(1)
for b in briefs:
    sizes = b["sizes"]
    d = {}
    for k in b["data_keys"]:
        names = [s.strip() for s in k["shape"].strip("()").split(",") if s.strip()]
        shape = tuple(sizes[n] for n in names)
        if k["dtype"] == "bool":
            a = rng.random(shape) < 0.5
        else:
            a = rng.normal(10.0, 2.0, shape)
        d[k["key"]] = a
    ns = {"np": np}
    exec(priv[b["local_id"]]["structure_statistic"]["code"], ns)
    v = ns["stat"](d)
    print(b["local_id"], type(v).__name__, v, np.isfinite(v))
