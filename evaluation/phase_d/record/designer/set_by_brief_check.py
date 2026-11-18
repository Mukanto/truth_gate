"""For every case: run the note's structure statistic on two independent random datasets with the brief's keys, shapes
and dtypes (N(0,1) floats, Bernoulli(0.5) bools; float keys made positive by exp for statistics that need positive data
are not needed: a statistic that depends only on the sizes gives the same value on both). A statistic whose two values
are identical is a function of the sizes; its note_value must equal that value (PREREG_PHASE_D section 2.1: "set by the
brief"). Prints every such case with set_by_brief, note_value and the computed value."""
import json, os, glob
import numpy as np
rows = []
for d in sorted(glob.glob("cases/D-*")):
    b = json.load(open(os.path.join(d, "brief.json"), encoding="utf-8"))
    p = json.load(open(os.path.join(d, "PRIVATE.json"), encoding="utf-8"))
    ss = p.get("structure_statistic")
    if not ss:
        continue
    ns = {"np": np}
    exec(ss["code"], ns)
    vals = []
    for seed in (1, 2):
        rng = np.random.default_rng(seed)
        data = {}
        for k in b["data_keys"]:
            data[k["key"]] = rng.random(k["dims"]) < 0.5 if k["dtype"] == "bool" else np.abs(rng.normal(1.0, 0.3, k["dims"])) + 0.1
        try:
            vals.append(float(ns["stat"](data)))
        except Exception as e:
            vals.append(f"error: {e}")
    const = isinstance(vals[0], float) and vals[0] == vals[1]
    if const or ss.get("set_by_brief"):
        rows.append((os.path.basename(d), ss.get("set_by_brief"), ss.get("note_value"), vals[0], vals[1]))
for r in rows:
    flag = "MISMATCH" if not (isinstance(r[3], float) and abs(float(r[2]) - r[3]) <= 1e-9 * max(1, abs(r[3]))) else "ok"
    print(f"{r[0]} set_by_brief={r[1]} note={r[2]} computed={r[3]} / {r[4]} {flag}")
