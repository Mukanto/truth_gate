"""Designer's independent R1/R2 check (spec 0.7 sections 4 and 6; R-1, R-3, R-4).

Written from the spec text without reading compare_r1.py.  Reads only certificates:
  baseline: evaluation/baseline_v041/certs + STUDIES_V041.json (0.4.1)
  new:      a folder of 0.5.0 certificates with the same file names
Usage: py evaluation/r1_v050/designer_check.py NEW_CERT_DIR [--repo REPO_ROOT]
"""
import json, os, sys
from collections import Counter

repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
args = [a for a in sys.argv[1:]]
if "--repo" in args:
    i = args.index("--repo"); repo = args[i + 1]; del args[i:i + 2]
new_dir = args[0]
base = os.path.join(repo, "evaluation", "baseline_v041")
index = json.load(open(os.path.join(base, "STUDIES_V041.json"), encoding="utf-8"))

K1 = ("world:plus", "world:minus", "world:null")
# 0.4.1 cascade constants, copied from `git show v0.4.1:truth_gate/checks.py` and minus.py
MANDATORY = {"K2_HOLDS_UNREACHABLE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K2_UNRESOLVABLE",
             "K3_PREMISE_NOT_TESTED", "K4_NO_CONTROL", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
             "K5_HOLDS_ON_DEGENERATE", "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "K2_HIGH_SIZE", "K8_NOT_INVARIANT"}
MANDATORY_PREFIX = ("HIGH_RATE:",)
CAPPING = {"K2_LOW_POWER", "K3_INCONCLUSIVE", "K4_WAIVED", "K4_INCONCLUSIVE", "SUGGESTED_UNREVIEWED", "K8_INCONCLUSIVE"}
CAPPING_PREFIX = ("K5_INCONCLUSIVE:", "K1_ABSTAINED_MAJORITY:")  # the second: spec 0.7 2.1 rule 3
UNTESTED = {"K2_MINUS_IDENTICAL"}
VERDICTS = ("FALSIFIABLE", "WEAK", "UNTESTED", "NOT_FALSIFIABLE", "UNDEFINED")


def cascade(flags):
    f = set(flags)
    if "K1_UNDEFINED" in f:
        return "UNDEFINED"
    if any(x in MANDATORY or x.startswith(MANDATORY_PREFIX) for x in f):
        return "NOT_FALSIFIABLE"
    if f & UNTESTED:
        return "UNTESTED"
    if any(x in CAPPING or x.startswith(CAPPING_PREFIX) for x in f):
        return "WEAK"
    return "FALSIFIABLE"


def result(c, with_counts=True):
    r = {"verdict": c["verdict"], "flags": sorted(c["flags"])}
    if with_counts:
        r["counts"] = {s: (v["holds"], v["undefined"], v["n"]) for s, v in c["counts"].items()}
        r["bounds"] = c.get("bounds")
    return r


def err_sum(c, s):
    e = (c.get("errors") or {}).get(s) or {}
    return sum(e.values()) if isinstance(e, dict) else 0


tally = Counter()
problems = []
hard_nonk1 = []
for st in index["studies"]:
    name = os.path.basename(st["cert"])
    old = json.load(open(os.path.join(base, "certs", name), encoding="utf-8"))["body"]
    newp = os.path.join(new_dir, name)
    if not os.path.isfile(newp):
        problems.append((st["path"], "no 0.5.0 certificate")); continue
    new = json.load(open(newp, encoding="utf-8"))["body"]
    if new.get("tool_version") != "0.5.0" or new.get("spec_version") != "0.7":
        problems.append((st["path"], f"versions {new.get('tool_version')} {new.get('spec_version')}"))
    nonrepro = "K6_NONREPRODUCIBLE" in (old.get("study_flags") or [])
    det = old.get("mode") == "deterministic" or not any(c.get("bounds") for c in old["components"])
    mismatch_study = "K7_COMPONENT_MISMATCH" in (old.get("study_flags") or [])
    # study level
    if sorted(old.get("study_flags") or []) != sorted(new.get("study_flags") or []):
        problems.append((st["path"], f"study flags {old.get('study_flags')} -> {new.get('study_flags')}"))
    le_old = json.loads(json.dumps(old.get("load_error") or {}).replace("kapi.Study", "truth_gate.Study"))
    if le_old != (new.get("load_error") or {}):
        problems.append((st["path"], f"load_error {old.get('load_error')!r} -> {new.get('load_error')!r}"))
    newc = {c["id"]: c for c in new["components"]}
    if set(newc) != {c["id"] for c in old["components"]}:
        problems.append((st["path"], "component ids differ")); continue
    exp_verdicts = []
    for oc in old["components"]:
        nc = newc[oc["id"]]
        cnt = oc["counts"]
        anyu = any(cnt[s]["undefined"] > 0 for s in K1 if s in cnt)
        E = sum(err_sum(oc, s) for s in K1 if s in cnt)
        up, npl = cnt["world:plus"]["undefined"], cnt["world:plus"]["n"]
        if "BAD_RETURN" in oc["flags"] or mismatch_study:
            group = "bad"
        elif not anyu:
            group = "item1"
        elif E > 0 or 2 * up > npl:
            group = "item2"
        else:
            group = "item3"
        line = "R-1" if nonrepro else ("det" if det else "stoch")
        tally[(group, line)] += 1
        # hard_undefined fields present
        if any("hard_undefined" not in v for v in nc["counts"].values()):
            problems.append((st["path"], oc["id"], "hard_undefined missing")); continue
        hk1 = sum(nc["counts"][s]["hard_undefined"] for s in K1 if s in nc["counts"])
        # spec 2.4: error counts add up to hard_undefined on every stream (R-3 exception: combined det probes)
        for s, v in nc["counts"].items():
            if v["hard_undefined"] != err_sum(nc, s):
                hard_nonk1.append((st["path"], oc["id"], s, v["hard_undefined"], err_sum(nc, s)))
        if group == "bad":
            if hk1 < E:
                problems.append((st["path"], oc["id"], f"bad group: hard {hk1} < E {E}"))
            exp_verdicts.append(nc["verdict"]); continue
        if hk1 != E:
            problems.append((st["path"], oc["id"], group, f"hard_undefined {hk1} != E {E}"))
        if group in ("item1", "item2"):
            exp = result(oc, not nonrepro)
        else:
            fl = set(oc["flags"]) - {"K1_UNDEFINED"}
            for s in K1:
                if s in cnt and cnt[s]["undefined"] > 0:
                    fl.add(f"K1_ABSTAINED:{s}")
                    if s != "world:plus" and 2 * cnt[s]["undefined"] > cnt[s]["n"]:
                        fl.add(f"K1_ABSTAINED_MAJORITY:{s}")
            exp = result(oc, not nonrepro)
            exp["flags"] = sorted(fl)
            exp["verdict"] = cascade(fl)
        got = result(nc, not nonrepro)
        if got != exp:
            diff = {k: (exp[k], got[k]) for k in exp if exp[k] != got[k]}
            problems.append((st["path"], oc["id"], group, line, diff))
        exp_verdicts.append(exp["verdict"])
    # item 4: study verdict from component verdicts and study flags
    worst = max((VERDICTS.index(v) for v in exp_verdicts), default=VERDICTS.index("UNDEFINED"))
    if new.get("study_flags"):
        worst = max(worst, VERDICTS.index("NOT_FALSIFIABLE"))
    if new["verdict"] != VERDICTS[worst]:
        problems.append((st["path"], f"study verdict {new['verdict']} != expected {VERDICTS[worst]}"))

print("components by group and line:")
for k in sorted(tally):
    print(f"  {k[0]:6s} {k[1]:6s} {tally[k]}")
print("total components:", sum(tally.values()), "| studies:", len(index["studies"]))
print("streams where hard_undefined != sum of errors (expected only combined deterministic random probes, R-3):",
      len(hard_nonk1))
for h in hard_nonk1[:20]:
    print("  ", h)
print("PROBLEMS:", len(problems))
for p in problems:
    print("  ", p)

# R2
pred = json.load(open(os.path.join(repo, "docs", "design", "spec-0.7-R2-prediction.json"), encoding="utf-8"))
ok = 0
for p in pred["components"]:
    f = os.path.join(new_dir, f"evaluation__phase_b__cases__{p['case']}__{p['twin']}.py.json")
    comp = next(c for c in json.load(open(f, encoding="utf-8"))["body"]["components"] if c["id"] == p["component"])
    good = comp["verdict"] == p["expected_verdict_0_5_0"] and sorted(comp["flags"]) == sorted(p["expected_flags_0_5_0"])
    ok += good
    if not good:
        print("R2 DIFF", p["case"], p["twin"], comp["verdict"], sorted(comp["flags"]))
print(f"R2: {ok} of {len(pred['components'])} match the frozen prediction")
print("R1 (designer):", "HOLDS" if not problems else "DOES NOT HOLD")
