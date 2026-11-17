import json, os, sys
base = r"E:\Independent\tasks\bc_validity_phase_b\certs"
order = ["world:plus","world:minus","world:null","probe:noise","probe:zeros"]
for case in sorted(os.listdir(base)):
    if not (case.startswith("B2") or case.startswith("B3")): continue
    for tw in ("faulty","fixed"):
        b = json.load(open(os.path.join(base, case, tw + ".json")))["body"]
        for comp in b["components"]:
            cnt = comp["counts"]
            keys = [k for k in order if k in cnt] + sorted(k for k in cnt if k not in order)
            parts = []
            for k in keys:
                c = cnt[k]
                u = c.get("undefined", 0)
                parts.append(f"{k.replace('world:','').replace('control:','c:').replace('probe:','p:')}={c['holds']}" + (f"(u{u})" if u else ""))
            print(case, tw[:3], comp.get("id","?"), b["verdict"], "|", " ".join(parts), "|", ",".join(comp.get("flags", [])))
