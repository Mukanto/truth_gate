import json, os
base = r"E:\Independent\tasks\bc_validity_phase_c"
r = json.load(open(os.path.join(base, "RESULTS.json")))
ef = json.load(open(os.path.join(base, "EXPECTED_FLAGS.json")))
for p in r["pairs"]:
    if p["class"] not in ("B-2", "B-3"):
        continue
    c = p["case"]
    v = p["versions"]["v050"]
    print(f"== {c} {p['class']} {p['subtype']} src={p['source']} world={p['world_id']} overlap={p['overlap']} size_ratio={p['size_ratio']} aware={p['awareness_resolved']}")
    print(f"   detected={v['detected']} clean={v['clean']} label={v['label']} faulty={v['faulty_verdict']} fixed={v['fixed_verdict']} too_small={p['label_error_too_small']} {p['too_small_detail']}")
    print(f"   faulty_flags={v['faulty_flags']}")
    print(f"   fixed_flags={v['fixed_flags']}")
    print(f"   expected_present={v['expected_present']}")
    for tw in ("faulty", "fixed"):
        cert = json.load(open(os.path.join(base, "certs", c, tw + ".json")))["body"]
        comp = cert["components"][0]
        cnt = comp["counts"]
        s = "; ".join(f"{k}={x['holds']}/{x['n']}" + (f"(U{x['undefined']},H{x['hard_undefined']})" if x['undefined'] else "") for k, x in cnt.items())
        print(f"   {tw}: {s}")
    print(f"   expected={[e for e in ef['cases'][c]['expected'] if e.startswith('HIGH_RATE:control') or 'shuffle' in e]}")
