import json, os, sys
sys.path.insert(0, r"E:\Independent\tasks\bc_validity_phase_c\scratch")
from truth_gate.stats import wilson_lower
base = r"E:\Independent\tasks\bc_validity_phase_c"
for c in sorted(os.listdir(os.path.join(base, "certs"))):
    if not c.startswith(("B2", "B3")): continue
    for tw in ("faulty", "fixed"):
        b = json.load(open(os.path.join(base, "certs", c, tw + ".json")))["body"]
        a = b["alpha_per_bound"]; m = b["m_comparisons"]
        kmin = next(k for k in range(201) if wilson_lower(k, 200, a) > 0.05)
        print(c, tw, "m=", m, "a=", a, "k_min_for_rate_flag=", kmin)
