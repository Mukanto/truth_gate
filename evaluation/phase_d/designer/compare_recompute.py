"""Compare three scorings of the attributable rule (PREREG_PHASE_D section 5) pair by pair:
- the designer's hand-written outcomes (tools/tests/acceptance_d/EXPECTED.json; acceptance pairs only);
- the fresh agent's independent recomputation (recompute_d/round4/out/RESULTS.json: the agent's script, unchanged,
  run on the 20 acceptance pairs and the 22 Phase C pairs);
- tools/attributable.py.
Fields compared: attributable, generic, declared and the set of qualifying streams.
Prints one line per pair and the number of differences; the designer keeps the output next to this script."""
import json
import os
import subprocess
import sys

# The set root is the folder that holds tools/, recompute_d/ and designer/ (the frozen Phase D folder); by default the
# parent of this script's folder.  Usage: compare_recompute.py [SET_ROOT]
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "tools", "attributable.py")
R4 = os.path.join(ROOT, "recompute_d", "round4")
INP = os.path.join(R4, "inputs")
REC = json.load(open(os.path.join(R4, "out", "RESULTS.json"), encoding="utf-8"))
MAP = json.load(open(os.path.join(ROOT, "recompute_d", "MAP_P_ids.json"), encoding="utf-8"))
HAND = {k: v for k, v in json.load(open(os.path.join(ROOT, "tools", "tests", "acceptance_d", "EXPECTED.json"),
                                        encoding="utf-8")).items() if not k.startswith("_")}


def key(attr, gen, decl, streams):
    return (bool(attr), bool(gen), bool(decl), tuple(sorted(streams)))


def rec(pid):
    # Section 5 defines qualifying streams for an attributable detection. The agent's script also lists stream-level
    # qualifiers when the faulty verdict is not NOT_FALSIFIABLE, with attributable false and a note (its NOTES.md
    # item 12); those are not qualifying streams of a detection, so they are compared as empty.
    e = REC[pid]
    qs = {q["stream"] for q in e["qualifying"]} if e["attributable"] else set()
    return key(e["attributable"], e["generic"], e["declared"], qs)


def tool(fa, fx, ex, case):
    out = subprocess.run([sys.executable, "-I", "-B", TOOL, "--faulty", fa, "--fixed", fx, "--expected-file", ex,
                          "--case", case], capture_output=True, text=True)
    d = json.loads(out.stdout)
    return key(d["attributable"], d["generic"], d["declared"], {q["stream"] for q in d["qualifying"]})


bad = 0
assert len(MAP) == len(HAND) == 20
for pid in sorted(MAP):
    n = MAP[pid]
    d = os.path.join(INP, "acceptance", pid)
    t = tool(os.path.join(d, "faulty.json"), os.path.join(d, "fixed.json"), os.path.join(d, "expected_flags.json"), pid)
    h = HAND[n]
    h = key(h["attributable"], h["generic"], h["declared"], h["qualifying_streams"])
    r = rec(pid)
    ok = t == r == h
    bad += not ok
    print(f"{pid} {n:36s} attr/gen/decl={h[:3]} streams={list(h[3])} hand=rec=tool: {'yes' if ok else 'NO'}")
pcs = sorted(k for k in REC if k.startswith(("B2-", "B3-")))
assert len(pcs) == 22
for c in pcs:
    d = os.path.join(INP, "pc", c)
    t = tool(os.path.join(d, "faulty.json"), os.path.join(d, "fixed.json"), os.path.join(INP, "pc", "EXPECTED_FLAGS.json"), c)
    r = rec(c)
    ok = t == r
    bad += not ok
    print(f"{c:40s} attr/gen/decl={r[:3]} streams={list(r[3])} rec=tool: {'yes' if ok else 'NO'}")
print("DIFFERENCES:", bad)
