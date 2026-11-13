#!/usr/bin/env python3
"""R1 regression comparison of Truth_Gate 0.5.0 against the 0.4.1 baseline (spec 0.7, sections 4 and 6; R-1).

Frozen with the baseline (``evaluation/FREEZE_BASELINE_V041.json``) before the implementation starts.

Sub-commands
------------
``compare NEWDIR``   compare the 0.5.0 certificates in ``NEWDIR`` (same layout and file names as ``certs/`` of the
                     baseline: ``<study path with / replaced by __>.json``, the envelope as the tool writes it) with
                     the baseline certificates listed in ``STUDIES_V041.json``.  Writes a JSON report (default
                     ``evaluation/R1_REPORT.json``; ``--report FILE``), prints a summary per group.
``selftest``         check this script on hand-made 0.5-style certificates (scratch folder, never the baseline folder).

Rules (spec 0.7 section 6, R1; section 4)
-----------------------------------------
Each component is classified from the **0.4.1 certificate only**.  ``E`` = sum of the ``errors`` counts on the K1
streams (``world:plus``, ``world:minus``, ``world:null``), ``u_plus`` / ``n_plus`` = UNDEFINED / n on ``world:plus``.

* group **bad**: the component has the flag ``BAD_RETURN``, or its criterion has ``K7_COMPONENT_MISMATCH`` (the
  criterion id is listed in ``study_flag_details``; every component of that criterion belongs to the group).
  Separate report; 0.5.0 must have ``hard_undefined >= E`` per K1 stream.  Not part of the exit code.
* item 1: no K1 stream has an UNDEFINED outcome.   Expected: the 0.4.1 result, unchanged.
* item 2: ``E > 0`` or ``2 * u_plus > n_plus``.     Expected: the 0.4.1 result, unchanged.
* item 3: every other component with ``u_s > 0`` on a K1 stream (soft only, at most half of plus).  Expected: the 0.4.1
  flags without ``K1_UNDEFINED``, plus ``K1_ABSTAINED:<s>`` for each K1 stream with soft UNDEFINED
  ``u_s - E_s > 0`` and ``K1_ABSTAINED_MAJORITY:<s>`` for ``world:minus`` / ``world:null`` with ``2 * soft > n_s``;
  the same counts and bounds; the verdict is the 0.4.1 cascade (``component_verdict`` below, copied from
  ``truth_gate/checks.py`` at tag v0.4.1 and checked against the verdicts of every baseline component) applied to those
  flags, where ``K1_ABSTAINED_MAJORITY:`` is a capping prefix (spec 0.7 section 2.1; the 0.4.1 code does not know it).
* For items 1 to 3 (the "first group", stochastic and deterministic studies alike): per K1 stream
  ``hard_undefined == errors count of that stream`` in the 0.5.0 certificate, ``hard_undefined <= undefined`` and
  ``holds + undefined <= n`` on every stream.

The "result" compared is per component: verdict, sorted flags, per stream ``holds``, ``undefined``, ``n``, and the
bounds.  Ignored: ``tool_version``, ``spec_version``, ``known_limitations``, the new ``hard_undefined`` fields (except
as above) and the new ``errors`` keys, the renamed texts of spec section 3 (the text of a ``load_error`` is not
compared, only its type).  Item 4: the study verdict follows from the component verdicts and the study flags:
(a) the reported study verdict equals ``study_verdict`` of the reported component verdicts and study flags; (b) when
every component of the study is in items 1 to 3, it equals ``study_verdict`` of the expected component verdicts and
the 0.4.1 study flags, and the study flags are unchanged.

R-1 (``spec-0.7-REVISIONS-post-freeze.md``): studies whose 0.4.1 certificate has ``K6_NONREPRODUCIBLE`` are compared only
on the study verdict, the component verdicts and the sets of component and study flags (section 4 applied to the
flags; no count or bound comparison); they are a separate line and are not part of the first group.
Deterministic studies (``study.deterministic``) are in the first group and are also reported as a separate line.

Exit code: 0 iff every component of the first group matches (and the first group is not empty and no baseline study
lacks a 0.5.0 certificate).  1 otherwise.  The other lines (bad group, R-1 studies, item 4, anomalies) are reported with
their own counts and ``other_checks_ok``; they do not change the exit code.

Usage::

    py evaluation/baseline_v041/compare_r1.py compare NEWDIR [--baseline DIR] [--report FILE]
    py evaluation/baseline_v041/compare_r1.py selftest [--scratch DIR] [--v041-src DIR]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import shutil
import sys
import tempfile
from collections import Counter

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_REPORT = os.path.join(ROOT, "evaluation", "R1_REPORT.json")
R2_PREDICTION = os.path.join(ROOT, "docs", "design", "spec-0.7-R2-prediction.json")

K1_STREAMS = ("world:plus", "world:minus", "world:null")
MINUS_LIKE = ("world:minus", "world:null")
NONREPRODUCIBLE = "K6_NONREPRODUCIBLE"
GROUPS = ("item1", "item2", "item3")

# --------------------------------------------------------------------------
# The 0.4.1 verdict cascade (copied from truth_gate/checks.py, tag v0.4.1; spec 0.5 delta 2, SPEC 5.8)
# --------------------------------------------------------------------------

VERDICTS = ("FALSIFIABLE", "WEAK", "UNTESTED", "NOT_FALSIFIABLE", "UNDEFINED")  # severity order

MANDATORY_FLAGS = frozenset({
    "K2_HOLDS_UNREACHABLE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K2_UNRESOLVABLE", "K3_PREMISE_NOT_TESTED",
    "K4_NO_CONTROL", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE", "K5_HOLDS_ON_DEGENERATE", "K5_HOLDS_ON_NULL",
    "K5_HOLDS_ON_SHUFFLE", "K2_HIGH_SIZE",
})
MANDATORY_PREFIXES = ("HIGH_RATE:",)
MANDATORY_FLAGS_SCHEMA2 = frozenset({"K8_NOT_INVARIANT"})
CAPPING_FLAGS = frozenset({"K2_LOW_POWER", "K3_INCONCLUSIVE", "K4_WAIVED", "K4_INCONCLUSIVE"})
CAPPING_PREFIXES = ("K5_INCONCLUSIVE:",)
CAPPING_FLAGS_SCHEMA2 = frozenset({"SUGGESTED_UNREVIEWED", "K8_INCONCLUSIVE"})
UNTESTED_FLAGS = frozenset({"K2_MINUS_IDENTICAL"})
# Spec 0.7 section 2.1 item 3 (new in 0.5.0, unknown to the 0.4.1 code): capping, like K5_INCONCLUSIVE.
CAPPING_PREFIXES_V05 = CAPPING_PREFIXES + ("K1_ABSTAINED_MAJORITY:",)


def component_verdict(flags, capping_prefixes=CAPPING_PREFIXES) -> str:
    """The 0.4.1 cascade; ``capping_prefixes`` is extended for the expected 0.5.0 flags (see ``expected_verdict``)."""
    flags = set(flags)
    if "K1_UNDEFINED" in flags:
        return "UNDEFINED"
    if any(f in MANDATORY_FLAGS or f in MANDATORY_FLAGS_SCHEMA2 or f.startswith(MANDATORY_PREFIXES) for f in flags):
        return "NOT_FALSIFIABLE"
    if flags & UNTESTED_FLAGS:
        return "UNTESTED"
    if any(f in CAPPING_FLAGS or f in CAPPING_FLAGS_SCHEMA2 or f.startswith(capping_prefixes) for f in flags):
        return "WEAK"
    return "FALSIFIABLE"


def expected_verdict(flags) -> str:
    return component_verdict(flags, CAPPING_PREFIXES_V05)


def study_verdict(component_verdicts, study_flags) -> str:
    worst = max((VERDICTS.index(v) for v in component_verdicts), default=VERDICTS.index("UNDEFINED"))
    if study_flags:
        worst = max(worst, VERDICTS.index("NOT_FALSIFIABLE"))
    return VERDICTS[worst]


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------

def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def cert_name(rel_path: str) -> str:
    return rel_path.replace("/", "__") + ".json"


def load_body(path: str):
    """Certificate body of an envelope file, or ``None`` if the file is missing or unreadable."""
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except (OSError, ValueError):
        return None
    if isinstance(doc, dict) and isinstance(doc.get("body"), dict):
        return doc["body"]
    return None


def load_index(baseline_dir: str) -> dict:
    with open(os.path.join(baseline_dir, "STUDIES_V041.json"), "r", encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------
# Classification (from the 0.4.1 certificate only) and expected result
# --------------------------------------------------------------------------

def criterion_of(body: dict) -> dict:
    """Component id -> criterion id, from ``study.criteria``."""
    mapping = {}
    for crit in body.get("study", {}).get("criteria", []) or []:
        if crit.get("components") is None:
            mapping[crit["id"]] = crit["id"]
        else:
            for name in crit["components"]:
                mapping[f"{crit['id']}:{name}"] = crit["id"]
    return mapping


def classify(old_body: dict, comp: dict, criteria: dict, mismatched: set) -> dict:
    counts = comp["counts"]
    errors = comp.get("errors", {}) or {}
    k1 = [s for s in K1_STREAMS if s in counts]
    e_by = {s: sum((errors.get(s, {}) or {}).values()) for s in k1}
    plus = counts.get("world:plus", {})
    info = {
        "E": sum(e_by.values()), "E_by_stream": e_by,
        "u_plus": plus.get("undefined", 0), "n_plus": plus.get("n", 0),
        "k1_undefined": {s: counts[s]["undefined"] for s in k1},
    }
    crit = criteria.get(comp["id"])
    if "BAD_RETURN" in comp["flags"] or crit in mismatched:
        info["group"] = "bad"
    elif not any(counts[s]["undefined"] > 0 for s in k1):
        info["group"] = "item1"
    elif info["E"] > 0 or 2 * info["u_plus"] > info["n_plus"]:
        info["group"] = "item2"
    else:
        info["group"] = "item3"
    return info


def expected_result(comp: dict, info: dict):
    """Expected 0.5.0 result of a component of item 1, 2 or 3, and anomalies of the 0.4.1 certificate itself."""
    flags = set(comp["flags"])
    anomalies = []
    if info["group"] in ("item1", "item2", "item3") and (info["group"] == "item1") == ("K1_UNDEFINED" in flags):
        anomalies.append("the 0.4.1 certificate is inconsistent with the classification: "
                         + ("K1_UNDEFINED on a component without K1 UNDEFINED outcomes" if info["group"] == "item1"
                            else "UNDEFINED outcomes on a K1 stream without the flag K1_UNDEFINED"))
    if info["group"] == "item3":
        flags.discard("K1_UNDEFINED")
        for s in K1_STREAMS:
            if s not in comp["counts"]:
                continue
            soft = info["k1_undefined"][s] - info["E_by_stream"][s]
            n = comp["counts"][s]["n"]
            if soft > 0:
                flags.add(f"K1_ABSTAINED:{s}")
                if s in MINUS_LIKE and 2 * soft > n:
                    flags.add(f"K1_ABSTAINED_MAJORITY:{s}")
        verdict = expected_verdict(flags)
    else:
        verdict = comp["verdict"]
    return {"verdict": verdict, "flags": sorted(flags), "counts": comp["counts"], "bounds": comp.get("bounds", {})}, anomalies


def _count_triple(c: dict):
    return (c.get("holds"), c.get("undefined"), c.get("n"))


def compare_component(expected: dict, new: dict, info: dict, strict_counts: bool = True) -> list:
    """Reasons why a 0.5.0 component differs from the expected result (empty list: match)."""
    reasons = []
    if new["verdict"] != expected["verdict"]:
        reasons.append(f"verdict {new['verdict']} (expected {expected['verdict']})")
    new_flags = sorted(new.get("flags", []))
    if new_flags != expected["flags"]:
        missing = sorted(set(expected["flags"]) - set(new_flags))
        extra = sorted(set(new_flags) - set(expected["flags"]))
        reasons.append(f"flags: missing {missing}, unexpected {extra}")
    if not strict_counts:
        return reasons
    exp_counts, new_counts = expected["counts"], new.get("counts", {})
    if set(exp_counts) != set(new_counts):
        reasons.append(f"streams differ: missing {sorted(set(exp_counts) - set(new_counts))}, "
                       f"unexpected {sorted(set(new_counts) - set(exp_counts))}")
    for stream in sorted(set(exp_counts) & set(new_counts)):
        if _count_triple(exp_counts[stream]) != _count_triple(new_counts[stream]):
            reasons.append(f"counts {stream}: (holds, undefined, n) {_count_triple(new_counts[stream])} "
                           f"(expected {_count_triple(exp_counts[stream])})")
    if expected["bounds"] != new.get("bounds"):
        reasons.append("bounds differ")
    for stream, c in new_counts.items():
        hard = c.get("hard_undefined")
        if not isinstance(hard, int) or isinstance(hard, bool):
            reasons.append(f"hard_undefined missing or not an integer on {stream}")
            continue
        if hard > c.get("undefined", 0):
            reasons.append(f"hard_undefined {hard} > undefined {c.get('undefined')} on {stream}")
        if c.get("holds", 0) + c.get("undefined", 0) > c.get("n", 0):
            reasons.append(f"holds + undefined > n on {stream}")
    for stream in K1_STREAMS:
        if stream in new_counts and isinstance(new_counts[stream].get("hard_undefined"), int):
            if new_counts[stream]["hard_undefined"] != info["E_by_stream"].get(stream, 0):
                reasons.append(f"hard_undefined {stream}: {new_counts[stream]['hard_undefined']} "
                               f"(expected E_s = {info['E_by_stream'].get(stream, 0)})")
    return reasons


def compare_flags_only(expected: dict, new: dict) -> list:
    """R-1 comparison: verdict and flag set only."""
    reasons = []
    if new["verdict"] != expected["verdict"]:
        reasons.append(f"verdict {new['verdict']} (expected {expected['verdict']})")
    if set(new.get("flags", [])) != set(expected["flags"]):
        reasons.append(f"flags: missing {sorted(set(expected['flags']) - set(new.get('flags', [])))}, "
                       f"unexpected {sorted(set(new.get('flags', [])) - set(expected['flags']))}")
    return reasons


def compare_bad_group(info: dict, new: dict) -> list:
    reasons = []
    for stream in K1_STREAMS:
        if stream in info["E_by_stream"]:
            hard = new.get("counts", {}).get(stream, {}).get("hard_undefined")
            if not isinstance(hard, int):
                reasons.append(f"hard_undefined missing on {stream}")
            elif hard < info["E_by_stream"][stream]:
                reasons.append(f"hard_undefined {hard} < E_s {info['E_by_stream'][stream]} on {stream}")
    return reasons


# --------------------------------------------------------------------------
# Study-level comparison
# --------------------------------------------------------------------------

def load_error_type(body: dict):
    err = body.get("load_error")
    return err.get("type") if isinstance(err, dict) else None


def compare_study(entry: dict, old: dict, new) -> dict:
    """One study: per-component records plus the study-level checks."""
    nonrep = NONREPRODUCIBLE in old.get("study_flags", [])
    deterministic = bool(old.get("study", {}).get("deterministic"))
    criteria = criterion_of(old)
    mismatched = set(old.get("study_flag_details", {}).get("K7_COMPONENT_MISMATCH", []) or [])
    if "K7_COMPONENT_MISMATCH" in old.get("study_flags", []) and not mismatched:
        mismatched = set(criteria.values())  # details missing: be conservative
    result = {"study": entry["path"], "set": entry.get("set"), "nonreproducible": nonrep, "deterministic": deterministic,
              "certificate": new is not None, "components": [], "study_checks": []}
    old_comps = {c["id"]: c for c in old["components"]}
    expected_all = {}
    all_expected = True
    for cid, comp in old_comps.items():
        info = classify(old, comp, criteria, mismatched)
        rec = {"component": cid, "group": info["group"], "E": info["E"], "u_plus": info["u_plus"],
               "n_plus": info["n_plus"], "reasons": [], "anomalies": []}
        if info["group"] == "bad":
            all_expected = False
        else:
            expected, anomalies = expected_result(comp, info)
            rec["anomalies"] = anomalies
            expected_all[cid] = expected
        result["components"].append(rec)
        rec["_info"], rec["_expected"] = info, expected_all.get(cid)
    if new is None:
        for rec in result["components"]:
            rec["reasons"].append("no 0.5.0 certificate")
        result["study_checks"].append("no 0.5.0 certificate")
        result["item4_ok"] = False
        _strip(result)
        return result
    new_comps = {c["id"]: c for c in new.get("components", [])}
    if set(new_comps) != set(old_comps):
        result["study_checks"].append(f"component ids differ: missing {sorted(set(old_comps) - set(new_comps))}, "
                                      f"unexpected {sorted(set(new_comps) - set(old_comps))}")
    if load_error_type(old) != load_error_type(new):
        result["study_checks"].append(f"load_error type {load_error_type(new)} (expected {load_error_type(old)})")
    for rec in result["components"]:
        cid, info, expected = rec["component"], rec["_info"], rec["_expected"]
        if cid not in new_comps:
            rec["reasons"].append("component missing in the 0.5.0 certificate")
        elif rec["group"] == "bad":
            rec["reasons"] += compare_bad_group(info, new_comps[cid])
        elif nonrep:
            rec["reasons"] += compare_flags_only(expected, new_comps[cid])
        else:
            rec["reasons"] += compare_component(expected, new_comps[cid], info)
    # Item 4 and the study flags
    item4 = []
    new_verdicts = [c["verdict"] for c in new.get("components", [])]
    if new.get("verdict") != study_verdict(new_verdicts, new.get("study_flags", [])):
        item4.append(f"reported study verdict {new.get('verdict')} != study_verdict(components, study flags) = "
                     f"{study_verdict(new_verdicts, new.get('study_flags', []))}")
    new_set, old_set = set(new.get("study_flags", [])), set(old.get("study_flags", []))
    if nonrep:  # K6_NONREPRODUCIBLE itself may or may not appear in another run of an unseeded study
        flags_differ = new_set - {NONREPRODUCIBLE} != old_set - {NONREPRODUCIBLE}
    else:
        flags_differ = new_set != old_set
    if flags_differ:
        item4.append(f"study flags {sorted(new_set)} (0.4.1: {sorted(old_set)})")
    if all_expected and old_comps:
        exp = study_verdict([expected_all[c]["verdict"] for c in old_comps],
                            new.get("study_flags", []) if nonrep else old.get("study_flags", []))
        if new.get("verdict") != exp:
            item4.append(f"study verdict {new.get('verdict')} (expected {exp} from the expected component verdicts)")
    result["item4_reasons"] = item4
    result["item4_ok"] = not item4
    _strip(result)
    return result


def _strip(result: dict) -> None:
    for rec in result["components"]:
        rec.pop("_info")
        rec.pop("_expected")


# --------------------------------------------------------------------------
# Whole comparison and report
# --------------------------------------------------------------------------

def run_compare(baseline_dir: str, new_dir: str) -> dict:
    index = load_index(baseline_dir)
    problems = []
    studies_out = []
    not_recorded = []
    for entry in index["studies"]:
        if entry.get("cert") is None:
            not_recorded.append(entry["path"])
            continue
        path = os.path.join(baseline_dir, *entry["cert"].split("/"))
        if not os.path.isfile(path) or sha256_file(path) != entry["cert_sha256"]:
            problems.append(f"{entry['path']}: baseline certificate missing or modified")
            continue
        old = load_body(path)
        if old is None:
            problems.append(f"{entry['path']}: baseline certificate unreadable")
            continue
        new = load_body(os.path.join(new_dir, cert_name(entry["path"])))
        studies_out.append(compare_study(entry, old, new))

    groups = {g: {"components": 0, "matched": 0, "mismatched": 0, "names": []} for g in GROUPS}
    bad = {"components": 0, "matched": 0, "mismatched": 0, "names": []}
    nonrep = {"studies": 0, "studies_matched": 0, "components": 0, "mismatched": 0, "names": []}
    det = {"studies": 0, "components": 0, "matched": 0, "mismatched": 0}
    mismatches, anomalies, item4_failures, missing_certs, study_check_failures = [], [], [], [], []
    for st in studies_out:
        if not st["certificate"]:
            missing_certs.append(st["study"])
        if st["study_checks"] and st["certificate"]:
            study_check_failures.append({"study": st["study"], "reasons": st["study_checks"]})
        if not st["item4_ok"] and st["certificate"]:
            item4_failures.append({"study": st["study"], "reasons": st.get("item4_reasons", [])})
        study_ok = True
        for rec in st["components"]:
            name = f"{st['study']}::{rec['component']}"
            ok = not rec["reasons"]
            if rec["anomalies"]:
                anomalies.append({"component": name, "reasons": rec["anomalies"]})
            if st["nonreproducible"]:
                nonrep["components"] += 1
                nonrep["mismatched"] += 0 if ok else 1
                nonrep["names"].append(name)
                study_ok &= ok
            elif rec["group"] == "bad":
                bad["components"] += 1
                bad["matched" if ok else "mismatched"] += 1
                bad["names"].append(name)
            else:
                g = groups[rec["group"]]
                g["components"] += 1
                g["matched" if ok else "mismatched"] += 1
                g["names"].append(name)
                if st["deterministic"]:
                    det["components"] += 1
                    det["matched" if ok else "mismatched"] += 1
            if not ok:
                mismatches.append({"component": name, "group": "nonreproducible" if st["nonreproducible"] else rec["group"],
                                   "reasons": rec["reasons"]})
        if st["nonreproducible"]:
            nonrep["studies"] += 1
            nonrep["studies_matched"] += 1 if study_ok and not st["study_checks"] and st["item4_ok"] else 0
        if st["deterministic"] and not st["nonreproducible"]:
            det["studies"] += 1
    first_total = sum(g["components"] for g in groups.values())
    first_mismatched = sum(g["mismatched"] for g in groups.values())
    r1_holds = first_total > 0 and first_mismatched == 0 and not missing_certs and not problems
    other_ok = (not bad["mismatched"] and not nonrep["mismatched"] and not item4_failures and not anomalies
                and not study_check_failures)
    versions = Counter((s.get("tool_version"), s.get("spec_version")) for s in
                       (load_body(os.path.join(new_dir, cert_name(e["path"]))) or {} for e in index["studies"]
                        if e.get("cert")))
    return {
        "criterion": "R1 (spec 0.7, section 6; R-1)",
        "baseline_dir": baseline_dir, "new_dir": new_dir,
        "baseline_tool": index.get("tool_under_test"),
        "new_versions": {f"{k[0]} / spec {k[1]}": v for k, v in versions.items()},
        "studies": len(studies_out), "not_recorded_in_baseline": not_recorded, "baseline_problems": problems,
        "missing_certificates": missing_certs,
        "groups": groups, "bad_return_or_mismatch": bad, "nonreproducible": nonrep, "deterministic": det,
        "first_group": {"components": first_total, "mismatched": first_mismatched},
        "item4_failures": item4_failures, "study_check_failures": study_check_failures, "anomalies": anomalies,
        "mismatches": mismatches, "r1_holds": r1_holds, "other_checks_ok": other_ok,
        "results": studies_out,
    }


def print_summary(rep: dict) -> None:
    print(f"R1: baseline {rep['baseline_tool']}  vs  {rep['new_dir']}")
    print(f"    certificates found with versions: {rep['new_versions']}")
    print(f"    studies compared: {rep['studies']}, missing 0.5.0 certificates: {len(rep['missing_certificates'])}")
    for g in GROUPS:
        x = rep["groups"][g]
        print(f"    {g}: {x['components']} components, {x['matched']} match, {x['mismatched']} differ")
    b = rep["bad_return_or_mismatch"]
    print(f"    BAD_RETURN / K7_COMPONENT_MISMATCH group: {b['components']} components, "
          f"hard_undefined >= E: {b['matched']} yes, {b['mismatched']} no  {b['names']}")
    n = rep["nonreproducible"]
    print(f"    R-1 nonreproducible studies (verdict and flag sets only): {n['studies']} studies, "
          f"{n['studies_matched']} match, {n['components']} components, {n['mismatched']} differ")
    d = rep["deterministic"]
    print(f"    deterministic studies (in the groups above): {d['studies']} studies, {d['components']} components, "
          f"{d['matched']} match, {d['mismatched']} differ")
    print(f"    item 4 (study verdict): {len(rep['item4_failures'])} studies fail; study-level check failures: "
          f"{len(rep['study_check_failures'])}; baseline anomalies: {len(rep['anomalies'])}")
    for m in rep["mismatches"][:50]:
        print(f"    DIFFERS [{m['group']}] {m['component']}: {'; '.join(m['reasons'])}")
    print(f"    other checks ok: {rep['other_checks_ok']}")
    print("R1 HOLDS" if rep["r1_holds"] else "R1 FAILS")


def cmd_compare(args) -> int:
    baseline = os.path.abspath(args.baseline)
    rep = run_compare(baseline, os.path.abspath(args.new_dir))
    with open(args.report, "wb") as handle:
        handle.write((json.dumps(rep, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print_summary(rep)
    print(f"report: {args.report}")
    return 0 if rep["r1_holds"] else 1


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def _write_env(path: str, body: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"body": body, "body_sha256": "x", "created_utc": "2026-11-13T00:00:00Z"}, handle)


def _comp(cid, verdict, flags, plus, minus, null=None, errors=None, deterministic=False, extra_streams=None):
    """A 0.4.1-style component: plus/minus/null are (holds, undefined, n)."""
    counts = {"world:plus": dict(zip(("holds", "undefined", "n"), plus)),
              "world:minus": dict(zip(("holds", "undefined", "n"), minus)),
              "probe:noise": {"holds": 0, "undefined": 0, "n": plus[2]}}
    if null is not None:
        counts["world:null"] = dict(zip(("holds", "undefined", "n"), null))
    bounds = {} if deterministic else {s: {"lower": 0.01, "upper": 0.9} for s in counts}
    return {"id": cid, "regime": "all", "verdict": verdict, "flags": sorted(flags), "counts": counts, "bounds": bounds,
            "errors": errors or {}, "unresolvable": []}


def _study(components, study_flags=(), deterministic=False, criteria=None, details=None, load_error=None):
    verdicts = [c["verdict"] for c in components]
    body = {"tool": "truth-gate", "tool_version": "0.4.1", "spec_version": "0.6", "mode": "full",
            "study": {"deterministic": deterministic,
                      "criteria": criteria or [{"id": c["id"], "components": None} for c in components]},
            "components": components, "study_flags": sorted(study_flags), "study_flag_details": details or {},
            "load_error": load_error, "verdict": study_verdict(verdicts, study_flags)}
    return body


def _v05(old: dict, edits=None) -> dict:
    """What a faithful 0.5.0 would write for an item-1/2 study: the old body plus hard_undefined from ``errors``."""
    new = copy.deepcopy(old)
    new["tool_version"], new["spec_version"] = "0.5.0", "0.7"
    for comp in new["components"]:
        for s, c in comp["counts"].items():
            c["hard_undefined"] = sum((comp["errors"].get(s, {}) or {}).values())
    return new


def _set_item3(new: dict, cid: str, flags, verdict) -> None:
    for comp in new["components"]:
        if comp["id"] == cid:
            comp["flags"], comp["verdict"] = sorted(flags), verdict
    new["verdict"] = study_verdict([c["verdict"] for c in new["components"]], new["study_flags"])


def _mini(tmp: str, name: str, studies: dict):
    """Build a baseline folder (index + certs) from ``{path: old body}`` and return its path."""
    base = os.path.join(tmp, name)
    os.makedirs(os.path.join(base, "certs"))
    index = {"tool_under_test": "synthetic 0.4.1", "studies": []}
    for path, body in studies.items():
        cert = "certs/" + cert_name(path)
        _write_env(os.path.join(base, cert), body)
        index["studies"].append({"set": "A1", "path": path, "study_sha256": "-", "cert": cert,
                                 "cert_sha256": sha256_file(os.path.join(base, cert)), "verdict": body["verdict"]})
    with open(os.path.join(base, "STUDIES_V041.json"), "w", encoding="utf-8") as handle:
        json.dump(index, handle)
    return base


def selftest(args) -> int:
    failures = []

    def check(label, condition):
        print(f"  {'ok  ' if condition else 'FAIL'} {label}")
        if not condition:
            failures.append(label)

    tmp = args.scratch or tempfile.mkdtemp(prefix="r1_selftest_")
    if args.scratch:
        os.makedirs(tmp, exist_ok=True)
    if os.path.realpath(tmp).startswith(os.path.realpath(HERE) + os.sep) or os.path.realpath(tmp) == os.path.realpath(HERE):
        print("the scratch folder must not be inside the baseline folder")
        return 2

    baseline = os.path.abspath(args.baseline)
    index = load_index(baseline)

    print("1. cascade against the recorded 0.4.1 verdicts")
    bad_c = bad_s = total = 0
    for entry in index["studies"]:
        body = load_body(os.path.join(baseline, *entry["cert"].split("/")))
        for comp in body["components"]:
            total += 1
            bad_c += component_verdict(comp["flags"]) != comp["verdict"]
        bad_s += study_verdict([c["verdict"] for c in body["components"]], body["study_flags"]) != body["verdict"]
    check(f"component_verdict reproduces the verdict of all {total} baseline components", bad_c == 0)
    check("study_verdict reproduces the verdict of all baseline studies", bad_s == 0)
    if args.v041_src:
        sys.path.insert(0, os.path.abspath(args.v041_src))
        import truth_gate.checks as real  # noqa: E402
        inside = os.path.realpath(real.__file__).startswith(os.path.realpath(args.v041_src))
        check(f"truth_gate.checks imported from {args.v041_src}", inside)
        universe = set(real.MANDATORY_FLAGS) | set(real.CAPPING_FLAGS) | set(real.CAPPING_FLAGS_SCHEMA2) | \
            set(real.MANDATORY_FLAGS_SCHEMA2) | set(real.UNTESTED_FLAGS) | set(real.INFORMATIONAL_FLAGS) | \
            {"K1_UNDEFINED", "HIGH_RATE:probe:noise", "K5_INCONCLUSIVE:noise", "K8_SOME_CHANGES"}
        for entry in index["studies"]:
            body = load_body(os.path.join(baseline, *entry["cert"].split("/")))
            for comp in body["components"]:
                universe |= set(comp["flags"])
        universe = sorted(universe)
        rng = random.Random(41)
        diffs = 0
        trials = 0
        for _ in range(20000):
            sample = rng.sample(universe, rng.randint(0, min(6, len(universe))))
            trials += 1
            diffs += real.component_verdict(sample) != component_verdict(sample)
        for f in universe:
            diffs += real.component_verdict([f]) != component_verdict([f])
        diffs += sum(real.study_verdict(v, f) != study_verdict(v, f) for v in ([], ["WEAK"], ["UNDEFINED", "WEAK"])
                     for f in ([], ["K6_LEAK_ATTEMPT"]))
        check(f"component_verdict equals truth_gate.checks.component_verdict on {trials} random flag sets "
              f"({len(universe)} distinct flags) and every single flag", diffs == 0)
        check("the known constants are identical to those of the 0.4.1 code",
              (real.MANDATORY_FLAGS, real.MANDATORY_PREFIXES, real.MANDATORY_FLAGS_SCHEMA2, real.CAPPING_FLAGS,
               real.CAPPING_PREFIXES, real.CAPPING_FLAGS_SCHEMA2, real.UNTESTED_FLAGS, real.VERDICTS) ==
              (MANDATORY_FLAGS, MANDATORY_PREFIXES, MANDATORY_FLAGS_SCHEMA2, CAPPING_FLAGS, CAPPING_PREFIXES,
               CAPPING_FLAGS_SCHEMA2, UNTESTED_FLAGS, VERDICTS))
    else:
        print("  (cascade check against the 0.4.1 code skipped: no --v041-src)")

    print("2. synthetic studies (hand-built 0.4.1 certificates, hand-written 0.5.0 results)")
    P = "synthetic/"
    old = {
        P + "item1.py": _study([_comp("a", "FALSIFIABLE", [], (100, 0, 100), (0, 0, 100)),
                                _comp("b", "NOT_FALSIFIABLE", ["K2_NO_SEPARATION"], (50, 0, 100), (40, 0, 100))]),
        P + "item2_hard.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K2_LOW_POWER"], (90, 0, 100), (0, 3, 100),
                                           errors={"world:minus": {"ValueError": 3}})]),
        P + "item2_plus_majority.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K2_HOLDS_UNREACHABLE"],
                                                    (10, 51, 100), (0, 0, 100))]),
        P + "item3_minus.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K2_LOW_POWER"], (90, 0, 100), (5, 30, 100))]),
        P + "item3_clean.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED"], (90, 0, 100), (0, 20, 100))]),
        P + "item3_majority.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED"], (90, 0, 100), (0, 60, 100))]),
        P + "item3_boundary.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED"], (90, 0, 100), (0, 50, 100))]),
        P + "item3_plus_half.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K2_LOW_POWER"], (40, 50, 100),
                                                (0, 10, 100), null=(0, 51, 100))]),
        P + "item3_mandatory.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K5_HOLDS_ON_NOISE"], (90, 0, 100),
                                                (0, 5, 100))]),
        P + "item3_untested.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K2_MINUS_IDENTICAL"], (90, 0, 100),
                                               (0, 5, 100))]),
        P + "det_minus_soft.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED"], (1, 0, 1), (0, 1, 1),
                                               deterministic=True)], deterministic=True),
        P + "det_plus_soft.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED", "K2_HOLDS_UNREACHABLE"], (0, 1, 1),
                                              (0, 0, 1), deterministic=True)], deterministic=True),
        P + "bad_return.py": _study([_comp("a", "UNDEFINED", ["BAD_RETURN", "K1_UNDEFINED"], (0, 30, 30), (0, 30, 30))]),
        P + "mismatch.py": _study(
            [_comp("pair:lo", "FALSIFIABLE", [], (30, 0, 30), (0, 0, 30)),
             _comp("pair:hi", "UNDEFINED", ["K1_UNDEFINED"], (0, 30, 30), (0, 30, 30))],
            study_flags=["K7_COMPONENT_MISMATCH"], criteria=[{"id": "pair", "components": ["lo", "hi"]}],
            details={"K7_COMPONENT_MISMATCH": ["pair"]}),
        P + "nonrep.py": _study([_comp("a", "UNDEFINED", ["K1_UNDEFINED"], (90, 0, 100), (0, 20, 100))],
                                study_flags=["K6_NONREPRODUCIBLE"]),
        P + "loaderr.py": {**_study([], load_error={"type": "StudyError", "message": "STUDY is not a kapi.Study"}),
                           "verdict": "UNDEFINED"},
    }
    base = _mini(tmp, "base_synth", old)
    good = {}
    for path, body in old.items():
        good[path] = _v05(body)
    # hand-written 0.5.0 results for the item-3 studies
    _set_item3(good[P + "item3_minus.py"], "a", ["K1_ABSTAINED:world:minus", "K2_LOW_POWER"], "WEAK")
    _set_item3(good[P + "item3_clean.py"], "a", ["K1_ABSTAINED:world:minus"], "FALSIFIABLE")
    _set_item3(good[P + "item3_majority.py"], "a", ["K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus"], "WEAK")
    _set_item3(good[P + "item3_boundary.py"], "a", ["K1_ABSTAINED:world:minus"], "FALSIFIABLE")
    _set_item3(good[P + "item3_plus_half.py"], "a",
               ["K1_ABSTAINED:world:minus", "K1_ABSTAINED:world:null", "K1_ABSTAINED:world:plus",
                "K1_ABSTAINED_MAJORITY:world:null", "K2_LOW_POWER"], "WEAK")
    _set_item3(good[P + "item3_mandatory.py"], "a", ["K1_ABSTAINED:world:minus", "K5_HOLDS_ON_NOISE"], "NOT_FALSIFIABLE")
    _set_item3(good[P + "item3_untested.py"], "a", ["K1_ABSTAINED:world:minus", "K2_MINUS_IDENTICAL"], "UNTESTED")
    _set_item3(good[P + "det_minus_soft.py"], "a", ["K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus"], "WEAK")
    good[P + "bad_return.py"]["components"][0]["counts"]["world:plus"]["hard_undefined"] = 30
    good[P + "bad_return.py"]["components"][0]["counts"]["world:minus"]["hard_undefined"] = 30
    for comp in good[P + "mismatch.py"]["components"]:
        for c in comp["counts"].values():
            c["hard_undefined"] = c["undefined"]
    # a nonreproducible study: counts may differ; only verdict and flag sets are compared
    nr = good[P + "nonrep.py"]
    nr["components"][0]["counts"]["world:minus"].update(undefined=22, holds=1)
    _set_item3(nr, "a", ["K1_ABSTAINED:world:minus"], "FALSIFIABLE")
    good[P + "loaderr.py"]["load_error"] = {"type": "StudyError", "message": "STUDY is not a truth_gate.Study"}

    def run(new_studies, label=None):
        folder = os.path.join(tmp, "new_" + (label or "x"))
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        for path, body in new_studies.items():
            if body is not None:
                _write_env(os.path.join(folder, cert_name(path)), body)
        os.makedirs(folder, exist_ok=True)
        return run_compare(base, folder)

    rep = run(good, "good")
    check("faithful 0.5.0 results: R1 holds", rep["r1_holds"])
    check("classification of the hand-built components: item 1: 2, item 2: 3, item 3: 8 "
          f"(found { {g: rep['groups'][g]['components'] for g in GROUPS} })",
          {g: rep["groups"][g]["components"] for g in GROUPS} == {"item1": 2, "item2": 3, "item3": 8})
    check("bad group: bad_return a, mismatch pair:lo and pair:hi", rep["bad_return_or_mismatch"]["components"] == 3
          and rep["bad_return_or_mismatch"]["mismatched"] == 0)
    check("nonreproducible study matched on verdict and flags only",
          rep["nonreproducible"]["studies"] == 1 and rep["nonreproducible"]["mismatched"] == 0)
    check("deterministic line counts the two deterministic studies", rep["deterministic"]["studies"] == 2)
    check("every item 4 check passes and no anomaly", not rep["item4_failures"] and not rep["anomalies"]
          and rep["other_checks_ok"])

    def wrong(label, path, mutate):
        broken = {p: copy.deepcopy(b) for p, b in good.items()}
        mutate(broken[path])
        rep2 = run(broken, "wrong")
        names = [m["component"] for m in rep2["mismatches"]]
        hit = any(n.startswith(path) for n in names)
        check(f"deliberately wrong: {label}", not rep2["r1_holds"] and hit)
        return rep2

    def comp_of(body, cid="a"):
        return next(c for c in body["components"] if c["id"] == cid)

    wrong("item 3 keeps K1_UNDEFINED", P + "item3_minus.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:minus", "K1_UNDEFINED", "K2_LOW_POWER"], verdict="UNDEFINED"))
    wrong("item 3 verdict wrong", P + "item3_minus.py", lambda b: comp_of(b).update(verdict="FALSIFIABLE"))
    wrong("item 3 without the abstained flag", P + "item3_clean.py", lambda b: comp_of(b).update(flags=[]))
    wrong("item 3 majority flag missing (verdict stays FALSIFIABLE)", P + "item3_majority.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:minus"], verdict="FALSIFIABLE"))
    wrong("item 3 majority flag present at exactly one half", P + "item3_boundary.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus"], verdict="WEAK"))
    wrong("item 3 majority flag on plus", P + "item3_plus_half.py",
          lambda b: comp_of(b)["flags"].append("K1_ABSTAINED_MAJORITY:world:plus"))
    wrong("item 3 abstained flag for plus missing", P + "item3_plus_half.py",
          lambda b: comp_of(b).update(flags=[f for f in comp_of(b)["flags"] if f != "K1_ABSTAINED:world:plus"]))
    wrong("item 3 count changed", P + "item3_minus.py",
          lambda b: comp_of(b)["counts"]["world:minus"].update(holds=6))
    wrong("item 3 bound changed", P + "item3_minus.py",
          lambda b: comp_of(b)["bounds"]["world:minus"].update(upper=0.5))
    wrong("item 3 hard_undefined not zero", P + "item3_minus.py",
          lambda b: comp_of(b)["counts"]["world:minus"].update(hard_undefined=1))
    wrong("item 3 hard_undefined missing", P + "item3_minus.py",
          lambda b: comp_of(b)["counts"]["world:minus"].pop("hard_undefined"))
    wrong("item 2 (hard) turned into an abstention", P + "item2_hard.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:minus", "K2_LOW_POWER"], verdict="WEAK"))
    wrong("item 2 hard_undefined 0 instead of E", P + "item2_hard.py",
          lambda b: comp_of(b)["counts"]["world:minus"].update(hard_undefined=0))
    wrong("item 2 hard_undefined above undefined", P + "item2_hard.py",
          lambda b: comp_of(b)["counts"]["world:minus"].update(hard_undefined=4))
    wrong("item 2 plus majority turned into an abstention", P + "item2_plus_majority.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:plus", "K2_HOLDS_UNREACHABLE"], verdict="NOT_FALSIFIABLE"))
    wrong("item 1 gets a K1_ABSTAINED flag", P + "item1.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:minus"]))
    wrong("item 1 hard_undefined non-zero", P + "item1.py",
          lambda b: comp_of(b)["counts"]["world:plus"].update(hard_undefined=1))
    wrong("item 1 verdict changed", P + "item1.py", lambda b: comp_of(b, "b").update(verdict="WEAK"))
    wrong("deterministic abstention without the majority flag", P + "det_minus_soft.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:minus"], verdict="FALSIFIABLE"))
    wrong("deterministic plus abstention not UNDEFINED", P + "det_plus_soft.py",
          lambda b: comp_of(b).update(flags=["K1_ABSTAINED:world:plus", "K2_HOLDS_UNREACHABLE"], verdict="NOT_FALSIFIABLE"))
    rep_b = run({**good, P + "mismatch.py": _drop_hard(good[P + "mismatch.py"])}, "wrong_bad")
    check("deliberately wrong: bad group without hard_undefined is reported on its own line, first group untouched",
          rep_b["bad_return_or_mismatch"]["mismatched"] == 2 and rep_b["r1_holds"])
    rep_n = run({**good, P + "nonrep.py": _nonrep_wrong(good[P + "nonrep.py"])}, "wrong_nonrep")
    check("deliberately wrong: nonreproducible mismatch is reported on its own line, first group untouched",
          rep_n["nonreproducible"]["mismatched"] == 1 and rep_n["r1_holds"] and not rep_n["other_checks_ok"])
    rep_v = run({**good, P + "item3_minus.py": _study_verdict_wrong(good[P + "item3_minus.py"])}, "wrong_study")
    check("deliberately wrong: study verdict not following from components (item 4) is reported",
          len(rep_v["item4_failures"]) == 1 and rep_v["r1_holds"] and not rep_v["other_checks_ok"])
    rep_m = run({k: v for k, v in good.items() if k != P + "item1.py"}, "missing")
    check("deliberately wrong: missing 0.5.0 certificate fails R1",
          not rep_m["r1_holds"] and rep_m["missing_certificates"] == [P + "item1.py"])
    rep_e = run({**good, P + "loaderr.py": {**good[P + "loaderr.py"], "load_error": {"type": "ValueError"}}}, "wrong_load")
    check("deliberately wrong: load_error type differs is reported", len(rep_e["study_check_failures"]) == 1)
    rep_x = run({**good, P + "item1.py": _extra_comp(good[P + "item1.py"])}, "extra")
    check("deliberately wrong: component ids differ is reported", len(rep_x["study_check_failures"]) == 1)

    print("3. the real baseline: mimic 0.5.0 certificates")
    mimic = os.path.join(tmp, "mimic")
    if os.path.isdir(mimic):
        shutil.rmtree(mimic)
    with open(R2_PREDICTION, "r", encoding="utf-8") as handle:
        prediction = {(c["case"], c["twin"], c["component"]): c for c in json.load(handle)["components"]}
    hand = {  # hand-written 0.5.0 result of the one A1 item-3 component that is not in the R2 prediction
        ("evaluation/cases/E2/E2-07_faulty.py", "peak_at_drive"):
            (["K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus", "K5_INCONCLUSIVE:zeros"], "WEAK"),
    }
    edited = 0
    for entry in index["studies"]:
        body = load_body(os.path.join(baseline, *entry["cert"].split("/")))
        new = _v05(body)
        for comp in new["components"]:
            key = None
            if entry["set"] == "phase_b":
                parts = entry["path"].split("/")
                key = (parts[-2], parts[-1][:-3], comp["id"])
            if key in prediction:
                comp["flags"] = sorted(prediction[key]["expected_flags_0_5_0"])
                comp["verdict"] = prediction[key]["expected_verdict_0_5_0"]
                edited += 1
            elif (entry["path"], comp["id"]) in hand:
                comp["flags"], comp["verdict"] = hand[(entry["path"], comp["id"])][0], hand[(entry["path"], comp["id"])][1]
                edited += 1
        new["verdict"] = study_verdict([c["verdict"] for c in new["components"]], new["study_flags"])
        if "load_error" in new and isinstance(new["load_error"], dict) and "message" in new["load_error"]:
            new["load_error"]["message"] = new["load_error"]["message"].replace("kapi.Study", "truth_gate.Study")
        _write_env(os.path.join(mimic, cert_name(entry["path"])), new)
    print(f"  ({edited} item-3 components edited with the R2 prediction / hand-written results)")
    rep_real = run_compare(baseline, mimic)
    check("mimic certificates of the real baseline: R1 holds", rep_real["r1_holds"])
    check("mimic: no mismatch, no item 4 failure, no anomaly", not rep_real["mismatches"] and rep_real["other_checks_ok"])
    check(f"mimic: item 3 has {rep_real['groups']['item3']['components']} components, "
          f"{edited} edited", rep_real["groups"]["item3"]["components"] == edited)
    # break one real item-3 component and one item-2 component
    victim = next((e for e in index["studies"] if e["path"].endswith("B1-05/faulty.py")))
    if victim:
        broken = os.path.join(tmp, "mimic_broken")
        if os.path.isdir(broken):
            shutil.rmtree(broken)
        shutil.copytree(mimic, broken)
        p = os.path.join(broken, cert_name(victim["path"]))
        with open(p, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        doc["body"]["components"][0]["flags"].remove("K1_ABSTAINED:world:plus")
        _write_env(p, doc["body"])
        rep_broken = run_compare(baseline, broken)
        check("mimic with one K1_ABSTAINED flag removed from B1-05 faulty: R1 fails on exactly that component",
              not rep_broken["r1_holds"] and [m["component"] for m in rep_broken["mismatches"]] == [victim["path"] + "::C"])
    print("selftest:", "ALL OK" if not failures else f"{len(failures)} FAILED: {failures}")
    if not args.scratch:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if not failures else 1


def _drop_hard(body: dict) -> dict:
    body = copy.deepcopy(body)
    for comp in body["components"]:
        for c in comp["counts"].values():
            c.pop("hard_undefined", None)
    return body


def _nonrep_wrong(body: dict) -> dict:
    body = copy.deepcopy(body)
    body["components"][0]["flags"] = []
    body["components"][0]["verdict"] = "FALSIFIABLE"
    return body


def _study_verdict_wrong(body: dict) -> dict:
    body = copy.deepcopy(body)
    body["verdict"] = "FALSIFIABLE"
    return body


def _extra_comp(body: dict) -> dict:
    body = copy.deepcopy(body)
    extra = copy.deepcopy(body["components"][0])
    extra["id"] = "zzz"
    body["components"].append(extra)
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("compare", help="compare a folder of 0.5.0 certificates with the baseline")
    p.add_argument("new_dir")
    p.add_argument("--baseline", default=HERE, help="baseline folder (default: the folder of this script)")
    p.add_argument("--report", default=DEFAULT_REPORT)
    p.set_defaults(func=cmd_compare)
    t = sub.add_parser("selftest", help="test this script on hand-made certificates")
    t.add_argument("--baseline", default=HERE)
    t.add_argument("--scratch", default=None, help="scratch folder (default: a temporary folder, removed afterwards)")
    t.add_argument("--v041-src", default=None, help="folder with the 0.4.1 package: also test the cascade against its code")
    t.set_defaults(func=selftest)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
