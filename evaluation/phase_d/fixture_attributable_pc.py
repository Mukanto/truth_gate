"""Classify every Phase C B-2/B-3 detection under the attributable rule proposed in review 1 (R1-2):
a detection is attributable when the faulty study is NOT_FALSIFIABLE and at least one of its expected rate flags, on a
stream s, (a) is not matched by any rate flag of the fixed study on s, and (b) has a faulty count on s above the fixed
count with a one-sided Fisher exact p < 0.05. Prints one line per detected pair; the list becomes the fixture of
attributable.py (draft 2, section 10).

Note (draft 4): written for draft 2. It maps K4_CONTROL_ALSO_HOLDS and K5_HOLDS_ON_SHUFFLE to every control or
shuffle stream and has no hard-UNDEFINED rule; draft 4 maps them through the bounds condition and excludes fixed
hard-UNDEFINED streams. On the Phase C certificates the two rules give the same output, as the independent
recomputation and attributable.py confirm (recompute_d/COMPARISON.md). It reads the Phase C files of the designer's
local repository."""
import json
import os
from math import comb

import sys

# Usage: fixture_attributable_pc.py [PHASE_C_DIR]; default: the designer's local repository.
PC = sys.argv[1] if len(sys.argv) > 1 else r"E:\Claude Projects\kapi-oss\evaluation\phase_c"
EXP = json.load(open(os.path.join(PC, "EXPECTED_FLAGS.json")))["cases"]


def streams_of(flag, counts):
    if flag in ("K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE"):
        return ["world:minus"]
    if flag in ("K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"):
        return ["probe:noise"]
    if flag in ("K5_HOLDS_ON_NULL", "HIGH_RATE:world:null"):
        return ["world:null"]
    if flag == "K5_HOLDS_ON_SHUFFLE":
        return [s for s in counts if s.startswith("probe:shuffle:")]
    if flag == "K4_CONTROL_ALSO_HOLDS":
        return [s for s in counts if s.startswith("control:")]
    if flag.startswith("HIGH_RATE:"):
        return [flag[len("HIGH_RATE:"):]]
    return []  # not a rate flag (K2_NO_SEPARATION and others)


def fisher_greater(a, n1, b, n2):
    """One-sided p of Fisher's exact test that the first proportion exceeds the second."""
    k, n = a + b, n1 + n2
    total = comb(n, k)
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(k, n1) + 1)) / total


def load(case, twin):
    b = json.load(open(os.path.join(PC, "run", "certs", "v050", case, twin + ".json")))["body"]
    c = b["components"][0]
    return b["verdict"], c["flags"], {k: v["holds"] for k, v in c["counts"].items()}, {k: v["n"] for k, v in c["counts"].items()}


for case in sorted(os.listdir(os.path.join(PC, "cases"))):
    if not case.startswith(("B2-", "B3-")):
        continue
    expected = set(EXP[case]["expected"])
    v_f, fl_f, k_f, n_f = load(case, "faulty")
    v_x, fl_x, k_x, n_x = load(case, "fixed")
    hits = [f for f in fl_f if f in expected]
    if not (v_f == "NOT_FALSIFIABLE" and hits):
        continue
    fixed_streams = {s for f in fl_x for s in streams_of(f, k_x)}
    reasons, attributable = [], False
    for f in hits:
        for s in streams_of(f, k_f):
            if s not in k_x:
                reasons.append(f"{f}@{s}: fixed has no counts")
                continue
            p = fisher_greater(k_f[s], n_f[s], k_x[s], n_x[s])
            ok = (s not in fixed_streams) and p < 0.05
            attributable |= ok
            reasons.append(f"{f}@{s} {k_f[s]} vs {k_x[s]} p={p:.3g}{' fixed-flagged' if s in fixed_streams else ''}{' OK' if ok else ''}")
    print(f"{case}: {'ATTRIBUTABLE' if attributable else 'not attributable'} | " + "; ".join(reasons))
