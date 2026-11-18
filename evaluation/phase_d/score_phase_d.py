#!/usr/bin/env python3
"""Phase D scoring and report (``PREREG_PHASE_D.md`` sections 5, 6 and 8; ``REVISIONS-post-freeze.md`` P-6).

Turns the gate certificates of the Phase D run into the pre-registered tables, using the FROZEN tools of
``tools/tools/`` for every per-pair decision.  Nothing is decided here that a frozen tool decides: attributable detection,
generic/declared, the draft-1 rule, miss labels, clean-pass classes and structure statistics all come from the tools'
JSON output (kept under ``OUT/tools/``).  This script only reads the run, orchestrates the tools one at a time, counts, and
applies the closed formulas of section 6 (Wilson bounds, exact McNemar).

Usage::

    py -I score_phase_d.py [score] [--run DIR] [--pd DIR] [--package-root DIR] [--out DIR] [--force]
                           [--attrition FILE] [--tools-dir DIR] [--audit-b-map FILE]
                           [--pc-results FILE] [--pb-table FILE]
    py -I score_phase_d.py selftest

Inputs (defaults in the option help)
------------------------------------
* ``--run``: ``RUNLOG.jsonl`` (the LAST ``event == "result"`` row per (case, arm, twin) is used; arm in R, W0, W1),
  ``certs/<ARM>/<id>_<twin>.json`` and ``studies/<ARM>/<id>_<twin>.py``.
* ``--pd`` (this folder): ``EXPECTED_FLAGS_D.json`` (key ``<id>/<arm>``; R is "reference"), ``cases/<id>/PRIVATE.json``,
  ``record/shuffle/ID_MAP_D.json``, ``record/validity/SELECTION.json`` and ``FREEZE_VALIDITY.json``,
  ``record/sandboxes/audit_b/<G>/AUDIT_B.json`` with the label map ``record/work/AUDIT_B_MAP.json`` (id -> {X: arm, Y: arm};
  a "no" is the attrition "part-B no" of that arm), ``record/work/AWARENESS_MAP_first.json`` and ``..._second.json``
  (label -> {id, arm, sandbox}) with the readings ``record/sandboxes/awareness/{r1b,r2,r3,r4}/READING.json`` (r1 is EXCLUDED,
  P-6; r1b and r2 are the first reading of W-0 and W-1, r3 and r4 the second reading of W-1; a disagreement resolves to the
  higher level, P > C > N).
* ``--attrition FILE``: the designer's list of invalid skeletons: a JSON object ``{"<id>/<ARM>": "cause", ...}`` or
  ``{"<id>": "cause"}`` (every arm); a value may also be a list of causes.  Default: none (none are expected).
* ``--pc-results`` (``evaluation/phase_c/run/RESULTS.json``, PC, gate 0.5.0) and ``--pb-table``
  (``evaluation/phase_c/PHASE_B_TABLE.json``, PB) for the descriptive W-0 comparison.  PHASE_B_TABLE.json holds only
  descriptors of the Phase B pairs (no detections); PB's per-class counts are then taken from the ``phase_b_next_to_c`` block
  of PC's RESULTS.json, and the table says so.  A field that cannot be found is reported as "not found".

Rules implemented here (the frozen text of section 5 and 6, and where a tool decides)
------------------------------------------------------------------------------------
* Attrition (section 6): a timeout (runlog ``timed_out``, or ``seconds`` > 3600), a load error (certificate ``load_error`` or
  no component) or a missing / unreadable certificate of a twin; an invalid skeleton (``--attrition``); a part-B "no".  A
  faulty twin that left no result is a miss; a fixed twin that left no result is a failed clean pass and makes the pair a
  miss in that arm.  An invalid skeleton or a part-B "no" is a miss and a failed clean pass in that arm under EVERY scoring
  (the tools are then called with ``--attrition``).  A missing or unreadable certificate (no timeout, no load error) is
  treated as a load error and listed with its own cause ("no certificate").
* Attributable detection, generic, declared, qualifying streams, draft-1 rule: ``attributable.py`` (a twin without a
  certificate gets a stand-in certificate with a load error, kept under ``OUT/tools/standins/``).  Draft-1 rule: the exact
  frozen definition is ``draft1_rule`` of ``attributable.py`` (TOOLS_SPEC_D.md, "Labels": an expected rate flag on s with
  faulty minus fixed holds >= 20 of 200 and Fisher p < 0.05, the pair PB-detected); the original wording is
  ``drafts/PREREG_PHASE_D_draft1.md`` section 5 ("Attributable detection").
* PB-style detection, clean pass, noise-only and declared-only baselines: PB section 6 as ported by Phase C
  (``run_phase_c.py``: ``is_information_flag``, ``counted_flags``, ``evaluate_pair``, ``tally``): information flags and the
  capping flag never count; a pair is detected if the faulty verdict is NOT_FALSIFIABLE and an expected flag is present; the
  label is generic if a noise flag is present; clean pass = fixed verdict FALSIFIABLE or WEAK.
* Clean pass WITHOUT the noise stream: the fixed verdict recomputed with the gate's own ``component_verdict`` /
  ``study_verdict`` after removing ``K5_HOLDS_ON_NOISE`` and ``HIGH_RATE:probe:noise`` from the flags; only a fixed verdict
  NOT_FALSIFIABLE that carries such a flag is recomputed.
* H-D1, H-D2 (arm W1): one-sided 95% Wilson lower bounds (z = 1.6448536269514722), "insufficient cases" when n < 16, else
  PASSES when both bounds >= 0.6, else FAILS.
* H-D3: exact one-sided McNemar on declared attributable detection, W1 against W0, on the comparable B-2 + B-3 pairs; the
  sensitivity analysis counts the arm of a not-comparable pair that carries attrition as a non-detection and keeps the other
  arm's result (all B-2 + B-3 pairs).  "demonstrated" if p < 0.05, else "not demonstrated".
* Clean-pass guard: exact one-sided McNemar, W0 better than W1, on the pairs entering H-D3; decoys excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from math import comb

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)

DEFAULT_RUN = r"E:\Claude Projects\Kapi\phase_d_work\run"
DEFAULT_PKG = r"E:\Claude Projects\Kapi\phase_d_work\record\pkg"
DEFAULT_OUT = r"E:\Claude Projects\Kapi\phase_d_work\score"

Z95 = 1.6448536269514722        # one-sided 95% (PC's wilson_lower)
THRESHOLD = 0.6
MIN_CLASS_PAIRS = 16            # PREREG section 6: a class with fewer pairs is "insufficient cases"
ALPHA = 0.05
TIME_LIMIT = 3600.0             # PREREG section 5: a check beyond 60 minutes is a timeout
SEED = 20261117

ARMS = (("R", "reference"), ("W0", "W0"), ("W1", "W1"))      # (arm code, name in EXPECTED_FLAGS_D.json), run order
ARM_CODES = tuple(a for a, _ in ARMS)
ARM_NAME = dict(ARMS)
TWINS = ("faulty", "fixed")
CLASSES = ("B-2", "B-3", "B-1", "B-6")
DECOY_CLASSES = ("B-1", "B-6")

NOISE_FLAGS = frozenset({"K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"})
INFORMATION_FLAGS = frozenset({"K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN"})
INFORMATION_PREFIXES = ("K1_ABSTAINED:",)
CAPPING_PREFIXES = ("K1_ABSTAINED_MAJORITY:",)
CLEAN_VERDICTS = ("FALSIFIABLE", "WEAK")
LEVELS = ("P", "C", "N")
LEVEL_RANK = {"N": 0, "C": 1, "P": 2}

FIRST_READERS = ("r1b", "r2")
SECOND_READERS = ("r3", "r4")


class ScoreError(Exception):
    """An input is missing or unusable (a usage error)."""


# --------------------------------------------------------------------------
# statistics (closed formulas)
# --------------------------------------------------------------------------

def wilson_lower(k: int, n: int, z: float = Z95):
    """One-sided Wilson score lower bound (PC's ``wilson_lower``); None when n = 0."""
    if n <= 0:
        return None
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, centre - half)


def mcnemar_exact_p(b: int, c: int) -> float:
    """Exact one-sided McNemar: sum_{k >= b} C(b + c, k) / 2^(b + c); 1.0 when b + c = 0."""
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(b, n + 1)) / 2 ** n


def rnd(x, digits=6):
    return None if x is None else round(x, digits)


def hd_verdict(k_detect: int, k_clean: int, n: int) -> dict:
    """H-D1 / H-D2 at one class of arm W1 (section 6)."""
    ld, lc = wilson_lower(k_detect, n), wilson_lower(k_clean, n)
    if n < MIN_CLASS_PAIRS:
        verdict = "insufficient cases"
    elif ld >= THRESHOLD and lc >= THRESHOLD:
        verdict = "PASSES"
    else:
        verdict = "FAILS"
    return {"n": n, "k_detect": k_detect, "k_clean": k_clean, "detect_lower": rnd(ld), "clean_lower": rnd(lc),
            "detect_ok": bool(ld is not None and ld >= THRESHOLD), "clean_ok": bool(lc is not None and lc >= THRESHOLD),
            "verdict": verdict}


# --------------------------------------------------------------------------
# flags (ported from run_phase_c.py)
# --------------------------------------------------------------------------

def is_information_flag(flag: str) -> bool:
    return (flag in INFORMATION_FLAGS or any(flag.startswith(p) for p in INFORMATION_PREFIXES)
            or any(flag.startswith(p) for p in CAPPING_PREFIXES))


def counted_flags(flags) -> list:
    return sorted(f for f in flags if not is_information_flag(f))


# --------------------------------------------------------------------------
# file helpers
# --------------------------------------------------------------------------

def read_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def read_certificate(path: str):
    """``(status, body)``: ``missing``, ``invalid`` or ``ok`` (the envelope's ``body``; a bare body is accepted)."""
    if not os.path.isfile(path):
        return "missing", None
    try:
        obj = read_json(path)
        body = obj["body"] if "body" in obj else obj
        if not isinstance(body, dict) or not isinstance(body["verdict"], str) or not isinstance(body["components"], list):
            return "invalid", None
        return "ok", body
    except (OSError, ValueError, KeyError, TypeError):
        return "invalid", None


def cert_path(run: str, arm: str, case: str, twin: str) -> str:
    return os.path.join(run, "certs", arm, f"{case}_{twin}.json")


def study_path(run: str, arm: str, case: str, twin: str) -> str:
    return os.path.join(run, "studies", arm, f"{case}_{twin}.py")


def load_runlog(run: str) -> list:
    path = os.path.join(run, "RUNLOG.jsonl")
    if not os.path.isfile(path):
        raise ScoreError(f"no RUNLOG.jsonl under {run}")
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def last_results(rows: list) -> dict:
    """``{(case, arm, twin): last result row}`` (later rows win)."""
    out = {}
    for row in rows:
        if row.get("event") == "result":
            out[(row["case"], row["arm"], row["twin"])] = row
    return out


# --------------------------------------------------------------------------
# gate functions (exact verdict logic, for the clean pass without the noise stream)
# --------------------------------------------------------------------------

_GATE = {}


def gate_checks(package_root: str, tools_dir: str):
    key = (os.path.abspath(package_root), os.path.abspath(tools_dir))
    if key not in _GATE:
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from structure_stat import import_truth_gate
        import_truth_gate(package_root)
        from truth_gate import checks
        _GATE[key] = checks
    return _GATE[key]


def clean_without_noise(body: dict, checks) -> bool:
    """Clean pass when the noise stream's flags are ignored (see the module docstring)."""
    verdict = body["verdict"]
    if verdict in CLEAN_VERDICTS:
        return True
    comps = body.get("components") or []
    if verdict != "NOT_FALSIFIABLE" or body.get("load_error") or not comps:
        return False
    kept = [[f for f in c["flags"] if f not in NOISE_FLAGS] for c in comps]
    if kept == [list(c["flags"]) for c in comps]:
        return False                                  # no noise flag: nothing changes
    new = checks.study_verdict([checks.component_verdict(fl) for fl in kept], list(body.get("study_flags") or []))
    return new in CLEAN_VERDICTS


# --------------------------------------------------------------------------
# tools (one subprocess at a time)
# --------------------------------------------------------------------------

class Tools:
    """Runs a frozen tool as ``py -I -B tool.py ...``, keeps its JSON output, and logs the command."""

    def __init__(self, tools_dir: str, package_root: str, out: str):
        self.tools_dir, self.package_root, self.out = tools_dir, package_root, out
        self.log = os.path.join(out, "tools", "COMMANDS.jsonl")

    def run(self, tool: str, args: list, rel_out: str) -> dict:
        script = os.path.join(self.tools_dir, tool + ".py")
        cmd = [sys.executable, "-I", "-B", script, *map(str, args)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=self.out)
        data = None
        try:
            data = json.loads(proc.stdout)
        except ValueError:
            data = None
        path = os.path.join(self.out, "tools", tool, rel_out)
        if proc.returncode == 0 and data is not None:
            write_json(path, data)
            error = None
        else:
            error = {"exit_code": proc.returncode, "stderr": proc.stderr.strip()[-2000:], "stdout": proc.stdout.strip()[-500:]}
            write_json(path, {"tool_error": error})
        os.makedirs(os.path.dirname(self.log), exist_ok=True)
        with open(self.log, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({"tool": tool, "args": [str(a) for a in args], "exit_code": proc.returncode,
                                     "output": os.path.relpath(path, self.out)}, ensure_ascii=False) + "\n")
        return {"exit_code": proc.returncode, "data": data if proc.returncode == 0 else None, "error": error,
                "file": os.path.relpath(path, self.out).replace("\\", "/")}


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------

def load_inputs(args) -> dict:
    pd = args.pd
    expected_path = os.path.join(pd, "EXPECTED_FLAGS_D.json")
    if not os.path.isfile(expected_path):
        raise ScoreError(f"missing {expected_path}")
    cases = read_json(expected_path)["cases"]
    ids = sorted({k.split("/")[0] for k in cases})
    for case in ids:
        for _, name in ARMS:
            if f"{case}/{name}" not in cases:
                raise ScoreError(f"EXPECTED_FLAGS_D.json has no key {case}/{name}")
    idmap_path = os.path.join(pd, "record", "shuffle", "ID_MAP_D.json")
    if not os.path.isfile(idmap_path):
        raise ScoreError(f"missing {idmap_path}")
    idmap = {row["id"]: row for row in read_json(idmap_path)}
    private = {}
    for case in ids:
        p = os.path.join(pd, "cases", case, "PRIVATE.json")
        private[case] = {"path": p, "data": read_json(p) if os.path.isfile(p) else None}
    notes = {}
    attrition_file = {}
    if args.attrition:
        raw = read_json(args.attrition)
        for key, val in raw.items():
            causes = val if isinstance(val, list) else [val]
            targets = [key] if "/" in key else [f"{key}/{a}" for a in ARM_CODES]
            for t in targets:
                attrition_file.setdefault(t, []).extend(str(c) for c in causes)
    # part-B
    part_b = {}
    audit_b_raw = {}
    map_path = args.audit_b_map or os.path.join(pd, "record", "work", "AUDIT_B_MAP.json")
    notes["audit_b"] = "found"
    try:
        amap = read_json(map_path)
        root = os.path.join(pd, "record", "sandboxes", "audit_b")
        for group in sorted(os.listdir(root)):
            f = os.path.join(root, group, "AUDIT_B.json")
            if not os.path.isfile(f):
                continue
            for row in read_json(f):
                case = row["case"]
                audit_b_raw[case] = {"X": row.get("X"), "Y": row.get("Y")}
                for label in ("X", "Y"):
                    arm = amap[case][label]
                    if str(row.get(label, "")).strip().lower() == "no":
                        part_b.setdefault(f"{case}/{arm}", []).append("part-B no")
    except (OSError, KeyError, ValueError) as e:
        notes["audit_b"] = f"not found or unusable: {type(e).__name__}: {e}"
    return {"cases": cases, "ids": ids, "idmap": idmap, "private": private, "attrition_file": attrition_file,
            "part_b": part_b, "audit_b_raw": audit_b_raw, "notes": notes}


def load_awareness(pd: str) -> dict:
    """``{(id, arm): {"first": {...}, "second": {...} | None}}`` or ``{"error": text}``."""
    try:
        rec = os.path.join(pd, "record")
        maps = {"first": read_json(os.path.join(rec, "work", "AWARENESS_MAP_first.json")),
                "second": read_json(os.path.join(rec, "work", "AWARENESS_MAP_second.json"))}
        readings = {r: read_json(os.path.join(rec, "sandboxes", "awareness", r, "READING.json"))
                    for r in FIRST_READERS + SECOND_READERS}
    except (OSError, ValueError) as e:
        return {"error": f"not found or unusable: {type(e).__name__}: {e}"}

    def level(reader, label):
        row = readings[reader].get(label)
        lv = str((row or {}).get("level", "")).strip().upper()[:1]
        return lv if lv in LEVELS else "?"

    def resolve(levels):
        if any(lv not in LEVELS for lv in levels):
            return "?"
        return max(levels, key=lambda lv: LEVEL_RANK[lv])

    out = {}
    for reading, readers in (("first", FIRST_READERS), ("second", SECOND_READERS)):
        for label, ent in maps[reading].items():
            lvs = [level(r, label) for r in readers]
            slot = out.setdefault((ent["id"], ent["arm"]), {"first": None, "second": None})
            slot[reading] = {readers[0]: lvs[0], readers[1]: lvs[1], "resolved": resolve(lvs)}
    return out


# --------------------------------------------------------------------------
# per (id, arm) records
# --------------------------------------------------------------------------

def twin_state(run: str, last: dict, case: str, arm: str, twin: str) -> dict:
    row = last.get((case, arm, twin))
    status, body = read_certificate(cert_path(run, arm, case, twin))
    seconds = row.get("seconds") if row else None
    timed_out = bool(row and row.get("timed_out")) or (seconds is not None and seconds > TIME_LIMIT)
    if timed_out:
        state = "timeout"
    elif status == "ok":
        state = "load error" if (body.get("load_error") or not body["components"]) else "ok"
    elif status == "invalid":
        state = "invalid certificate"
    else:
        state = "no certificate"
    flags = []
    if state == "ok":
        flags = sorted({f for c in body["components"] for f in c.get("flags", [])})
    cause = {"timeout": "timeout", "load error": "load error", "invalid certificate": "invalid certificate",
             "no certificate": "no certificate"}.get(state)
    return {"state": state, "cause": f"{twin} {cause}" if cause else None, "body": body if state in ("ok", "load error") else None,
            "verdict": body["verdict"] if state in ("ok", "load error") else None, "flags": flags,
            "counted": counted_flags(flags), "seconds": seconds, "exit_code": row.get("exit_code") if row else None,
            "infrastructure_failure": bool(row and row.get("infrastructure_failure")),
            "attempt": row.get("attempt") if row else None, "has_row": row is not None}


def pb_style(expected, faulty: dict, fixed: dict, checks, arm_attrition: bool) -> dict:
    """PB section 6 as ported by Phase C (``evaluate_pair``); an invalid skeleton or a part-B "no" overrides every scoring."""
    exp = {f for f in expected if not is_information_flag(f)}
    ok = faulty["state"] == "ok"
    present = sorted(exp & set(faulty["counted"])) if ok else []
    f_nf = ok and faulty["verdict"] == "NOT_FALSIFIABLE"
    generic = bool(NOISE_FLAGS & set(faulty["counted"])) if ok else False
    detected = f_nf and bool(present)
    noise = [f for f in present if f in NOISE_FLAGS]
    non_noise = [f for f in present if f not in NOISE_FLAGS]
    clean = fixed["state"] == "ok" and fixed["verdict"] in CLEAN_VERDICTS
    clean_wo = bool(fixed["state"] == "ok" and clean_without_noise(fixed["body"], checks))
    if arm_attrition:
        detected = f_nf = clean = clean_wo = False
        noise = non_noise = []
    return {"detected": bool(detected), "label": ("generic" if generic else "declared") if detected else None,
            "expected_present": present, "baseline_noise_only": bool(f_nf and noise),
            "baseline_declared_only": bool(f_nf and non_noise), "clean": bool(clean), "clean_wo_noise": bool(clean_wo)}


def standin(ctx: dict, arm: str, case: str, twin: str, cause: str) -> str:
    path = os.path.join(ctx["out"], "tools", "standins", arm, f"{case}_{twin}.json")
    write_json(path, {"body": {"verdict": "UNDEFINED", "load_error": {"type": f"stand-in: {cause}"}, "components": [],
                               "study_flags": []}})
    return path


def process_pair(ctx: dict, tools: Tools, case: str, arm: str) -> dict:
    """One (id, arm): attrition, scorings, and every frozen tool call (one at a time)."""
    run, pd, inp = ctx["run"], ctx["pd"], ctx["inputs"]
    meta = inp["idmap"].get(case, {})
    name = ARM_NAME[arm]
    tw = {t: twin_state(run, ctx["last"], case, arm, t) for t in TWINS}
    arm_causes = list(inp["attrition_file"].get(f"{case}/{arm}", [])) + list(inp["part_b"].get(f"{case}/{arm}", []))
    twin_causes = [tw[t]["cause"] for t in TWINS if tw[t]["cause"]]
    expected = inp["cases"][f"{case}/{name}"]["expected"]
    pb = pb_style(expected, tw["faulty"], tw["fixed"], ctx["checks"], bool(arm_causes))
    rec = {"id": case, "arm": arm, "class": meta.get("class", "?"), "tag": meta.get("subtype_or_tag"),
           "source": meta.get("source"), "reserve": meta.get("reserve"),
           "faulty": {k: tw["faulty"][k] for k in ("state", "verdict", "flags", "seconds", "exit_code", "attempt")},
           "fixed": {k: tw["fixed"][k] for k in ("state", "verdict", "flags", "seconds", "exit_code", "attempt")},
           "attrition": {"arm_level": arm_causes, "twin_level": twin_causes},
           "attrition_any": bool(arm_causes or twin_causes), "pb": pb,
           "attributable": False, "generic": False, "declared": False, "draft1": False, "qualifying": [],
           "tool_pb_detected": None, "attributable_reasons": [], "clean": pb["clean"], "clean_wo_noise": pb["clean_wo_noise"],
           "miss": None, "clean_class": None, "structure": None, "tool_errors": []}

    def keep_error(res, what):
        if res["error"]:
            rec["tool_errors"].append({"tool": what, "error": res["error"]})
            ctx["tool_errors"].append({"id": case, "arm": arm, "tool": what, "error": res["error"]})

    common = ["--package-root", ctx["package_root"]]
    exp_args = ["--expected-file", os.path.join(pd, "EXPECTED_FLAGS_D.json"), "--case", f"{case}/{name}"]
    f_cert, x_cert = cert_path(run, arm, case, "faulty"), cert_path(run, arm, case, "fixed")

    # 2. attributable detection
    if not arm_causes:
        fa = f_cert if tw["faulty"]["state"] in ("ok", "load error") else standin(ctx, arm, case, "faulty", tw["faulty"]["cause"])
        xa = x_cert if tw["fixed"]["state"] in ("ok", "load error") else standin(ctx, arm, case, "fixed", tw["fixed"]["cause"])
        res = tools.run("attributable", ["--faulty", fa, "--fixed", xa, *exp_args, *common], f"{arm}/{case}.json")
        keep_error(res, "attributable")
        att = res["data"]
        rec["tool_files"] = {"attributable": res["file"]}
        if att is not None:
            rec.update(attributable=bool(att["attributable"]), generic=bool(att["generic"]) and bool(att["attributable"]),
                       declared=bool(att["declared"]) and bool(att["attributable"]), draft1=bool(att["draft1_rule"]),
                       qualifying=att["qualifying"], tool_pb_detected=bool(att["pb_detected"]),
                       attributable_reasons=att["reasons"])
    else:
        rec["tool_files"] = {}
        rec["attributable_reasons"] = ["not run: " + "; ".join(arm_causes)]

    # 5. miss label (every miss)
    if not rec["attributable"]:
        private = inp["private"][case]["path"]
        f_study, x_study = study_path(run, arm, case, "faulty"), study_path(run, arm, case, "fixed")
        cmd = [*exp_args, "--private", private, *common]
        if arm_causes:
            cmd = ["--attrition", "; ".join(arm_causes), *common]
        elif tw["faulty"]["state"] in ("timeout", "no certificate", "invalid certificate", "load error"):
            cmd = ["--attrition", tw["faulty"]["cause"], *common]
        else:
            cmd += ["--faulty", f_cert, "--fixed", x_cert, "--study", f_study]
            if tw["fixed"]["state"] == "timeout":
                cmd += ["--fixed-attrition", "fixed timeout"]
            elif tw["fixed"]["state"] in ("no certificate", "invalid certificate"):
                cmd += ["--fixed-attrition", tw["fixed"]["cause"]]
        res = tools.run("miss_label", cmd, f"{arm}/{case}.json")
        keep_error(res, "miss_label")
        rec["tool_files"]["miss_label"] = res["file"]
        d = res["data"]
        rec["miss"] = ({"label": d["label"], "cause": d.get("cause"), "cause_twin": d.get("cause_twin"),
                        "structure_share": (d.get("structure") or {}).get("share_beyond_half")} if d
                       else {"label": "tool error", "cause": None, "cause_twin": None, "structure_share": None})

    # 6. clean-pass class (every failed clean pass)
    if not rec["clean"]:
        x_study = study_path(run, arm, case, "fixed")
        if arm_causes:
            cmd = ["--attrition", "; ".join(arm_causes), *common]
        elif tw["fixed"]["state"] == "timeout" and os.path.isfile(x_study):
            cmd = ["--study", x_study, "--timeout", *common]
        elif tw["fixed"]["state"] in ("timeout", "no certificate", "invalid certificate"):
            cmd = ["--attrition", tw["fixed"]["cause"], *common]
        else:
            cmd = ["--study", x_study, "--cert", x_cert, *common]
        res = tools.run("clean_pass_class", cmd, f"{arm}/{case}.json")
        keep_error(res, "clean_pass_class")
        rec["tool_files"]["clean_pass_class"] = res["file"]
        d = res["data"]
        rec["clean_class"] = ({"class": d["class"], "causes": d.get("causes", []),
                               "unconfirmed_rate_flags": d.get("unconfirmed_rate_flags", [])} if d
                              else {"class": "tool error", "causes": [], "unconfirmed_rate_flags": []})

    # 7. structure statistic (every (id, arm) with a non-null statistic)
    priv = inp["private"][case]["data"]
    spec = (priv or {}).get("structure_statistic")
    if not spec:
        rec["structure"] = {"status": "no statistic"}
    else:
        f_study = study_path(run, arm, case, "faulty")
        if not os.path.isfile(f_study):
            rec["structure"] = {"status": "no study file"}
        else:
            res = tools.run("structure_stat", ["--study", f_study, "--private", inp["private"][case]["path"], "--world", "minus",
                                               "--samples", 200, *common], f"{arm}/{case}.json")
            rec["tool_files"]["structure_stat"] = res["file"]
            d = res["data"]
            if d is None:
                rec["structure"] = {"status": "not computable", "error": (res["error"] or {}).get("stderr")}
            elif d.get("set_by_brief"):
                rec["structure"] = {"status": "set by the brief", "mean": d.get("mean")}
            else:
                rec["structure"] = {"status": "computed", "share_beyond_half": d["share_beyond_half"], "mean": d["mean"],
                                    "sd": d["sd"]}
    return rec


# --------------------------------------------------------------------------
# tables
# --------------------------------------------------------------------------

def attrition_counts(recs: list) -> dict:
    out = {}
    for r in recs:
        for cause in r["attrition"]["arm_level"] + r["attrition"]["twin_level"]:
            out[cause] = out.get(cause, 0) + 1
    return dict(sorted(out.items()))


def tally(recs: list) -> dict:
    n = len(recs)

    def cnt(pred):
        return sum(1 for r in recs if pred(r))

    t = {"pairs": n,
         "attributable": cnt(lambda r: r["attributable"]),
         "generic": cnt(lambda r: r["generic"]), "declared": cnt(lambda r: r["declared"]),
         "both": cnt(lambda r: r["generic"] and r["declared"]),
         "generic_only": cnt(lambda r: r["generic"] and not r["declared"]),
         "declared_only": cnt(lambda r: r["declared"] and not r["generic"]),
         "pb_style": cnt(lambda r: r["pb"]["detected"]),
         "pb_generic": cnt(lambda r: r["pb"]["label"] == "generic"),
         "pb_declared": cnt(lambda r: r["pb"]["label"] == "declared"),
         "draft1_rule": cnt(lambda r: r["draft1"]),
         "clean": cnt(lambda r: r["clean"]), "clean_wo_noise": cnt(lambda r: r["clean_wo_noise"]),
         "baseline_noise_only": cnt(lambda r: r["pb"]["baseline_noise_only"]),
         "baseline_declared_only": cnt(lambda r: r["pb"]["baseline_declared_only"]),
         "baseline_flag_everything": n,
         "attrition_by_cause": attrition_counts(recs),
         "attrition_list": [{"id": r["id"], "causes": r["attrition"]["arm_level"] + r["attrition"]["twin_level"]}
                            for r in recs if r["attrition_any"]]}
    t["attributable_lower"] = rnd(wilson_lower(t["attributable"], n))
    t["clean_lower"] = rnd(wilson_lower(t["clean"], n))
    t["pb_style_lower"] = rnd(wilson_lower(t["pb_style"], n))
    return t


def tally_light(recs: list) -> dict:
    return {"pairs": len(recs), "attributable": sum(r["attributable"] for r in recs),
            "declared": sum(r["declared"] for r in recs), "pb_style": sum(r["pb"]["detected"] for r in recs),
            "clean": sum(r["clean"] for r in recs)}


def by_arm_class(recs: list) -> dict:
    out = {}
    for arm in ARM_CODES:
        out[arm] = {}
        for cls in CLASSES:
            out[arm][cls] = tally([r for r in recs if r["arm"] == arm and r["class"] == cls])
        out[arm]["decoys"] = tally([r for r in recs if r["arm"] == arm and r["class"] in DECOY_CLASSES])
    return out


def hypotheses(recs: list) -> dict:
    idx = {(r["id"], r["arm"]): r for r in recs}
    w1 = [r for r in recs if r["arm"] == "W1"]
    out = {}
    for key, cls in (("H-D1", "B-2"), ("H-D2", "B-3")):
        rows = [r for r in w1 if r["class"] == cls]
        out[key] = {"class": cls, "arm": "W1", **hd_verdict(sum(r["attributable"] for r in rows),
                                                            sum(r["clean"] for r in rows), len(rows))}
    pooled = sorted({r["id"] for r in recs if r["class"] in ("B-2", "B-3")})
    excl, comparable = [], []
    for case in pooled:
        causes = []
        for arm in ("W0", "W1"):
            r = idx[(case, arm)]
            causes += [{"arm": arm, "cause": c} for c in r["attrition"]["arm_level"] + r["attrition"]["twin_level"]]
        (excl if causes else comparable).append({"id": case, "causes": causes} if causes else case)

    def counts(ids, rule):
        b = c = both = neither = 0
        per_class = {"B-2": [0, 0], "B-3": [0, 0]}
        for case in ids:
            w1d, w0d = rule(idx[(case, "W1")]), rule(idx[(case, "W0")])
            cls = idx[(case, "W1")]["class"]
            if w1d and not w0d:
                b += 1
                per_class[cls][0] += 1
            elif w0d and not w1d:
                c += 1
                per_class[cls][1] += 1
            elif w1d and w0d:
                both += 1
            else:
                neither += 1
        p = mcnemar_exact_p(b, c)
        return {"n_pairs": len(ids), "w1_declared": sum(1 for i in ids if rule(idx[(i, "W1")])),
                "w0_declared": sum(1 for i in ids if rule(idx[(i, "W0")])), "b_w1_only": b, "c_w0_only": c, "both": both,
                "neither": neither, "p": rnd(p, 10),
                "verdict": "demonstrated" if p < ALPHA else "not demonstrated",
                "discordant_per_class": {k: {"b_w1_only": v[0], "c_w0_only": v[1]} for k, v in per_class.items()}}

    decl = lambda r: bool(r["declared"])    # noqa: E731
    cl = lambda r: bool(r["clean"])         # noqa: E731
    out["H-D3"] = {"pooled_pairs": len(pooled), "comparable_pairs": comparable, "not_comparable": excl,
                   "main": counts(comparable, decl),
                   "sensitivity_not_comparable_counted_as_non_detections": counts(pooled, decl)}
    g = counts(comparable, cl)
    b_p, c_p = g["c_w0_only"], g["b_w1_only"]          # W0 better: W0 clean only vs W1 clean only
    out["clean_pass_guard"] = {"pairs": len(comparable), "w0_clean": g["w0_declared"], "w1_clean": g["w1_declared"],
                               "w0_clean_only": b_p, "w1_clean_only": c_p, "p": rnd(mcnemar_exact_p(b_p, c_p), 10),
                               "direction": "W0 better than W1"}
    dec_w = {a: [r for r in recs if r["arm"] == a and r["class"] in DECOY_CLASSES] for a in ("W0", "W1")}
    out["adoption_inputs"] = {
        "pooled_clean_difference_w1_minus_w0_on_h_d3_pairs": g["w1_declared"] - g["w0_declared"],
        "decoys_clean_w0": sum(r["clean"] for r in dec_w["W0"]), "decoys_clean_w1": sum(r["clean"] for r in dec_w["W1"]),
        "decoys_n": len(dec_w["W1"]),
        "decoys_clean_difference_w1_minus_w0": sum(r["clean"] for r in dec_w["W1"]) - sum(r["clean"] for r in dec_w["W0"])}
    return out


def count_by(recs, key_fn) -> dict:
    out = {}
    for r in recs:
        k = key_fn(r)
        if k is not None:
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def miss_and_clean_tables(recs: list) -> dict:
    miss, clean = {}, {}
    for arm in ARM_CODES:
        miss[arm], clean[arm] = {}, {}
        for cls in CLASSES:
            rows = [r for r in recs if r["arm"] == arm and r["class"] == cls]
            ms = [r for r in rows if r["miss"]]
            miss[arm][cls] = {"misses": len(ms), "by_label": count_by(ms, lambda r: r["miss"]["label"]),
                              "e_by_cause": count_by([r for r in ms if r["miss"]["label"] == "e"],
                                                     lambda r: r["miss"]["cause"] or "?")}
            cs = [r for r in rows if r["clean_class"]]
            clean[arm][cls] = {"failed_clean_passes": len(cs), "by_class": count_by(cs, lambda r: r["clean_class"]["class"]),
                               "e_by_cause": count_by([c for r in cs if r["clean_class"]["class"] == "e"
                                                       for c in (r["clean_class"]["causes"] or ["?"])], lambda c: c)}
    return {"miss_labels": miss, "clean_pass_classes": clean}


def structure_table(recs: list) -> dict:
    out = {}
    for arm in ARM_CODES:
        out[arm] = {}
        for cls in CLASSES:
            rows = [r for r in recs if r["arm"] == arm and r["class"] == cls]
            c = {"pairs": len(rows), "share_ge_half": 0, "share_lt_half": 0, "set_by_brief": 0, "no_statistic": 0,
                 "not_computable": 0, "no_study_file": 0}
            for r in rows:
                s = r["structure"]
                if s["status"] == "computed":
                    c["share_ge_half" if s["share_beyond_half"] >= 0.5 else "share_lt_half"] += 1
                elif s["status"] == "set by the brief":
                    c["set_by_brief"] += 1
                elif s["status"] == "no statistic":
                    c["no_statistic"] += 1
                elif s["status"] == "no study file":
                    c["no_study_file"] += 1
                else:
                    c["not_computable"] += 1
            out[arm][cls] = c
    return out


def decoy_tables(recs: list) -> dict:
    out = {}
    for arm in ARM_CODES:
        out[arm] = {}
        for cls in DECOY_CLASSES:
            tags = sorted({r["tag"] for r in recs if r["class"] == cls})
            out[arm][cls] = {tag: tally_light([r for r in recs if r["arm"] == arm and r["class"] == cls and r["tag"] == tag])
                             for tag in tags}
    return out


def validity_table(pd: str, idmap: dict) -> dict:
    path = os.path.join(pd, "record", "validity", "FREEZE_VALIDITY.json")
    try:
        fv = read_json(path)
        sel = read_json(os.path.join(pd, "record", "validity", "SELECTION.json"))
    except (OSError, ValueError) as e:
        return {"error": f"not found or unusable: {type(e).__name__}: {e}"}
    status = {}
    pre = {k: v.split(" (")[0] for k, v in fv["pre_validity_drops"].items()}
    decided = {p["id"]: p for p in fv["pairs"]}
    for case in idmap:
        if case in pre:
            status[case] = pre[case]
        elif case in decided and decided[case]["decision"] == "drop":
            status[case] = decided[case]["counting_label"]
        elif fv["audit_a"].get(case, {}).get("overall", "pass") != "pass":
            status[case] = "fidelity A (" + ",".join(fv["audit_a"][case]["failed_items"]) + ")"
        elif case in decided:
            status[case] = "pass"
        else:
            status[case] = "pending"
    groups = {}
    for case, row in idmap.items():
        g = groups.setdefault(f"{row['class']} {row['subtype_or_tag']}", {"built": 0, "labels": {}})
        g["built"] += 1
        g["labels"][status[case]] = g["labels"].get(status[case], 0) + 1
    for g in groups.values():
        g["labels"] = dict(sorted(g["labels"].items()))
        g["dropped"] = sum(v for k, v in g["labels"].items() if k not in ("pass", "pending"))
        g["drop_rate"] = rnd(g["dropped"] / g["built"])
    per_class = {}
    for case, row in idmap.items():
        g = per_class.setdefault(row["class"], {"built": 0, "labels": {}})
        g["built"] += 1
        g["labels"][status[case]] = g["labels"].get(status[case], 0) + 1
    for g in per_class.values():
        g["labels"] = dict(sorted(g["labels"].items()))
        g["dropped"] = sum(v for k, v in g["labels"].items() if k not in ("pass", "pending"))
        g["drop_rate"] = rnd(g["dropped"] / g["built"])
    return {"label_counts_file": fv["label_counts"], "pairs_built": len(idmap), "by_class": dict(sorted(per_class.items())),
            "by_subtype_or_tag": dict(sorted(groups.items())), "selected_per_class": {k: v["n_selected"] for k, v in sel.items()}}


def awareness_tables(aw: dict, recs: list) -> dict:
    if "error" in aw:
        return aw
    for r in recs:
        slot = aw.get((r["id"], r["arm"]))
        r["awareness"] = {"first": (slot or {}).get("first"), "second": (slot or {}).get("second")} if r["arm"] != "R" else None
    out = {"first_reading": {}, "second_reading_w1": {}, "split_first_resolved": {}, "split_second_resolved": {}}

    def level_counts(rows, getter):
        c = {lv: 0 for lv in LEVELS + ("?",)}
        for r in rows:
            c[getter(r)] += 1
        return c

    for arm in ("W0", "W1"):
        out["first_reading"][arm] = {}
        out["split_first_resolved"][arm] = {}
        for cls in CLASSES + ("all",):
            rows = [r for r in recs if r["arm"] == arm and (cls == "all" or r["class"] == cls)]
            first = lambda r, k="resolved": ((r["awareness"] or {}).get("first") or {}).get(k, "?")   # noqa: E731
            out["first_reading"][arm][cls] = {"resolved": level_counts(rows, first),
                                              **{rd: level_counts(rows, lambda r, rd=rd: first(r, rd)) for rd in FIRST_READERS}}
            out["split_first_resolved"][arm][cls] = {lv: tally_light([r for r in rows if first(r) == lv])
                                                     for lv in LEVELS + ("?",)}
    out["second_reading_w1"] = {}
    out["split_second_resolved"]["W1"] = {}
    for cls in CLASSES + ("all",):
        rows = [r for r in recs if r["arm"] == "W1" and (cls == "all" or r["class"] == cls)]
        second = lambda r, k="resolved": ((r["awareness"] or {}).get("second") or {}).get(k, "?")   # noqa: E731
        out["second_reading_w1"][cls] = {"resolved": level_counts(rows, second),
                                         **{rd: level_counts(rows, lambda r, rd=rd: second(r, rd)) for rd in SECOND_READERS}}
        out["split_second_resolved"]["W1"][cls] = {lv: tally_light([r for r in rows if second(r) == lv]) for lv in LEVELS + ("?",)}
    return out


def prior_phase_numbers(args, w0_tables: dict) -> dict:
    """W-0 next to PB and PC per class (descriptive; not a test)."""
    note = ("not a test: briefs, sizes, validity, pairs and the world-author model differ (PB: a model of the gate's line; "
            "PC: Fable; Phase D: Claude Opus 5.5)")
    out = {"label": note, "sources": {}, "classes": {}}

    def first_found(obj, routes):
        for route in routes:
            cur = obj
            for k in route:
                cur = cur.get(k) if isinstance(cur, dict) else None
            if isinstance(cur, dict):
                return "/".join(route), cur
        return None, None

    pc_obj = pb_obj = None
    try:
        pc_obj = read_json(args.pc_results)
    except (OSError, ValueError) as e:
        out["sources"]["PC"] = f"not found: {args.pc_results} ({type(e).__name__})"
    try:
        pb_obj = read_json(args.pb_table)
    except (OSError, ValueError) as e:
        out["sources"]["PB_table"] = f"not found: {args.pb_table} ({type(e).__name__})"
    pc_route, pc_classes = first_found(pc_obj or {}, [("gate", "v050", "classes")])
    pb_route, pb_classes = first_found(pb_obj or {}, [("gate", "classes"), ("classes",), ("phase_b", "classes")])
    pb_from = "PHASE_B_TABLE.json"
    if pb_classes is None:
        pb_route, pb_classes = first_found(pc_obj or {}, [("phase_b_next_to_c", "phase_b", "classes")])
        pb_from = "PC RESULTS.json (the PB table PHASE_B_TABLE.json holds pair descriptors only, no counts)"
    out["sources"]["PC"] = out["sources"].get("PC") or (f"{args.pc_results}: {pc_route}" if pc_route else "not found")
    out["sources"]["PB"] = f"{pb_from}: {pb_route}" if pb_route else "not found"
    if pc_obj:
        out["sources"]["PC_gate_version"] = pc_obj.get("primary_version")
        out["sources"]["PB_gate_version"] = (pc_obj.get("phase_b_next_to_c") or {}).get("phase_b_gate_version")

    def pick(classes, cls):
        row = (classes or {}).get(cls)
        if not row:
            return {"pairs": "not found", "detections": "not found", "clean_passes": "not found"}
        return {k: row.get(k, "not found") for k in ("pairs", "detections", "generic", "declared", "clean_passes")}

    for cls in CLASSES:
        t = w0_tables[cls]
        out["classes"][cls] = {"W0": {"pairs": t["pairs"], "attributable": t["attributable"], "pb_style": t["pb_style"],
                                      "clean": t["clean"]},
                               "PB": pick(pb_classes, cls), "PC": pick(pc_classes, cls)}
    return out


def arm_r_exceptions(recs: list) -> list:
    return [{"id": r["id"], "class": r["class"], "attributable": r["attributable"], "clean": r["clean"],
             "miss": r["miss"], "clean_class": r["clean_class"]}
            for r in recs if r["arm"] == "R" and (not r["attributable"] or not r["clean"])]


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build(args) -> dict:
    inputs = load_inputs(args)
    rows = load_runlog(args.run)
    ctx = {"run": args.run, "pd": args.pd, "out": args.out, "package_root": args.package_root, "inputs": inputs,
           "last": last_results(rows), "tool_errors": [],
           "checks": gate_checks(args.package_root, args.tools_dir)}
    tools = Tools(args.tools_dir, args.package_root, args.out)
    recs = []
    for case in inputs["ids"]:
        for arm in ARM_CODES:
            recs.append(process_pair(ctx, tools, case, arm))
            print(f"scored {arm} {case}", file=sys.stderr)
    aw = awareness_tables(load_awareness(args.pd), recs)
    per = by_arm_class(recs)
    mc = miss_and_clean_tables(recs)
    res = {
        "meta": {"script": "score_phase_d.py", "script_sha256": sha256_file(os.path.abspath(__file__)),
                 "run": args.run, "pd": args.pd, "package_root": args.package_root,
                 "pairs": len(inputs["ids"]), "arms": list(ARM_CODES), "ids": inputs["ids"],
                 "runlog_result_rows": sum(1 for r in rows if r.get("event") == "result"),
                 "infrastructure_failure_rows": sum(1 for r in rows if r.get("event") == "result" and r.get("infrastructure_failure")),
                 "inputs": inputs["notes"], "part_b_raw": inputs["audit_b_raw"]},
        "rules": {"z_one_sided_95": Z95, "threshold": THRESHOLD, "min_class_pairs": MIN_CLASS_PAIRS, "alpha": ALPHA,
                  "time_limit_s": TIME_LIMIT, "seed": SEED, "noise_flags": sorted(NOISE_FLAGS),
                  "information_flags": sorted(INFORMATION_FLAGS), "information_prefixes": list(INFORMATION_PREFIXES),
                  "capping_prefixes": list(CAPPING_PREFIXES), "clean_verdicts": list(CLEAN_VERDICTS),
                  "draft1_rule": "attributable.py field draft1_rule (TOOLS_SPEC_D.md Labels; drafts/PREREG_PHASE_D_draft1.md "
                                 "section 5): PB-detected, an expected rate flag on s with faulty minus fixed holds >= 20 of "
                                 "200 and one-sided Fisher p < 0.05",
                  "resolution": "higher level of the two readers (P > C > N); r1 excluded (P-6)",
                  "readers": {"first": list(FIRST_READERS), "second_w1": list(SECOND_READERS)}},
        "tool_errors": ctx["tool_errors"],
        "per_arm_class": per,
        "hypotheses": hypotheses(recs),
        "descriptive": {"arm_R_exceptions": arm_r_exceptions(recs),
                        "w0_next_to_pb_pc": prior_phase_numbers(args, per["W0"]),
                        "decoys_per_arm_and_tag": decoy_tables(recs),
                        "validity_drops": validity_table(args.pd, inputs["idmap"]),
                        "structure": structure_table(recs), **mc, "awareness": aw},
        "pairs": recs,
    }
    return res


# --------------------------------------------------------------------------
# markdown (every number comes from RESULTS_D.json)
# --------------------------------------------------------------------------

def fmt(x) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.4f}"
    if isinstance(x, dict):
        return ", ".join(f"{k}: {fmt(v)}" for k, v in x.items()) or "-"
    if isinstance(x, list):
        return ", ".join(fmt(v) for v in x) or "-"
    return str(x)


def md_table(header: list, rows: list) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(fmt(c) for c in row) + " |" for row in rows]
    return "\n".join(lines) + "\n"


def render_markdown(res: dict) -> str:
    L = []
    m = res["meta"]
    L += ["# Phase D results", "",
          f"Scoring script `{m['script']}` (SHA-256 {m['script_sha256']}); run folder `{m['run']}`; "
          f"{m['pairs']} pairs x arms {', '.join(m['arms'])}; run-log result rows {m['runlog_result_rows']} "
          f"(infrastructure failures {m['infrastructure_failure_rows']}).", ""]
    if res["tool_errors"]:
        L += ["## Tool errors", "", md_table(["id", "arm", "tool", "error"],
                                             [[e["id"], e["arm"], e["tool"], e["error"]["stderr"]] for e in res["tool_errors"]])]
    L += ["## Per arm and class", ""]
    hdr = ["class", "n", "attributable", "generic", "declared", "both", "PB-style", "draft-1", "clean", "clean w/o noise",
           "noise-only", "declared-only", "flag-everything", "attr. lower", "clean lower"]
    for arm in ARM_CODES:
        L += [f"### Arm {arm}", ""]
        rows = []
        for cls in list(CLASSES) + ["decoys"]:
            t = res["per_arm_class"][arm][cls]
            rows.append([cls if cls != "decoys" else "decoys (B-1 + B-6)", t["pairs"], t["attributable"], t["generic"],
                         t["declared"], t["both"], t["pb_style"], t["draft1_rule"], t["clean"], t["clean_wo_noise"],
                         t["baseline_noise_only"], t["baseline_declared_only"], t["baseline_flag_everything"],
                         t["attributable_lower"], t["clean_lower"]])
        L += [md_table(hdr, rows)]
        rows = [[cls, t["attrition_by_cause"], t["attrition_list"]] for cls in list(CLASSES)
                for t in [res["per_arm_class"][arm][cls]] if t["attrition_list"]]
        L += ["Attrition by cause:", "", md_table(["class", "counts", "pairs"], rows) if rows else "none\n"]
    H = res["hypotheses"]
    L += ["## H-D1 and H-D2 (arm W1)", "",
          md_table(["hypothesis", "class", "n", "k_detect", "k_clean", "detect lower", "clean lower", "verdict"],
                   [[k, H[k]["class"], H[k]["n"], H[k]["k_detect"], H[k]["k_clean"], H[k]["detect_lower"],
                     H[k]["clean_lower"], H[k]["verdict"]] for k in ("H-D1", "H-D2")])]
    h3 = H["H-D3"]
    L += ["## H-D3 (B-2 + B-3 pooled; declared attributable detection, W1 against W0)", "",
          f"Pooled pairs: {h3['pooled_pairs']}.", "",
          "Not comparable (by arm and cause):", "",
          md_table(["id", "arm", "cause"], [[e["id"], c["arm"], c["cause"]] for e in h3["not_comparable"] for c in e["causes"]])
          if h3["not_comparable"] else "none\n"]
    rows = []
    for label, key in (("comparable pairs", "main"), ("sensitivity (not comparable counted as non-detections)",
                                                    "sensitivity_not_comparable_counted_as_non_detections")):
        s = h3[key]
        rows.append([label, s["n_pairs"], s["w1_declared"], s["w0_declared"], s["b_w1_only"], s["c_w0_only"], s["both"],
                     s["neither"], s["p"], s["verdict"]])
    L += [md_table(["analysis", "n", "W1 declared", "W0 declared", "b (W1 only)", "c (W0 only)", "both", "neither", "p", "label"],
                   rows)]
    L += ["Discordant counts per class (descriptive):", "",
          md_table(["analysis", "class", "b (W1 only)", "c (W0 only)"],
                   [[label, cls, v["b_w1_only"], v["c_w0_only"]]
                    for label, key in (("comparable", "main"), ("sensitivity", "sensitivity_not_comparable_counted_as_non_detections"))
                    for cls, v in h3[key]["discordant_per_class"].items()])]
    g, a = H["clean_pass_guard"], H["adoption_inputs"]
    L += ["## Clean-pass guard (W0 better than W1; H-D3 pairs; decoys excluded)", "",
          md_table(["pairs", "W0 clean", "W1 clean", "W0 clean only", "W1 clean only", "p"],
                   [[g["pairs"], g["w0_clean"], g["w1_clean"], g["w0_clean_only"], g["w1_clean_only"], g["p"]]]),
          "Numbers for the adoption rule (I-D2):", "",
          md_table(["quantity", "value"], [[k, v] for k, v in a.items()])]
    d = res["descriptive"]
    L += ["## Arm R: pairs not attributable or without a clean pass (I-D4)", "",
          md_table(["id", "class", "attributable", "clean", "miss label", "clean-pass class"],
                   [[e["id"], e["class"], e["attributable"], e["clean"], (e["miss"] or {}).get("label"),
                     (e["clean_class"] or {}).get("class")] for e in d["arm_R_exceptions"]]) if d["arm_R_exceptions"] else "none\n"]
    w = d["w0_next_to_pb_pc"]
    L += ["## W-0 next to PB and PC (descriptive; " + w["label"] + ")", "", f"Sources: {fmt(w['sources'])}", "",
          md_table(["class", "W0 pairs", "W0 attributable", "W0 PB-style", "W0 clean", "PB pairs", "PB detections", "PB clean",
                    "PC pairs", "PC detections", "PC clean"],
                   [[cls, c["W0"]["pairs"], c["W0"]["attributable"], c["W0"]["pb_style"], c["W0"]["clean"], c["PB"]["pairs"],
                     c["PB"]["detections"], c["PB"]["clean_passes"], c["PC"]["pairs"], c["PC"]["detections"],
                     c["PC"]["clean_passes"]] for cls, c in w["classes"].items()])]
    L += ["## Decoys per arm and mechanism tag", "",
          md_table(["arm", "class", "tag", "n", "attributable", "declared", "PB-style", "clean"],
                   [[arm, cls, tag, t["pairs"], t["attributable"], t["declared"], t["pb_style"], t["clean"]]
                    for arm, per in d["decoys_per_arm_and_tag"].items() for cls, tags in per.items() for tag, t in tags.items()])]
    v = d["validity_drops"]
    L += ["## Validity drop rates", ""]
    if "error" in v:
        L += [v["error"], ""]
    else:
        L += [f"Label counts of FREEZE_VALIDITY.json: {fmt(v['label_counts_file'])}; pairs built {v['pairs_built']}; "
              f"selected per class {fmt(v['selected_per_class'])}.", "",
              md_table(["class", "built", "dropped", "drop rate", "labels"],
                       [[k, x["built"], x["dropped"], x["drop_rate"], x["labels"]] for k, x in v["by_class"].items()]),
              md_table(["class and subtype or tag", "built", "dropped", "drop rate", "labels"],
                       [[k, x["built"], x["dropped"], x["drop_rate"], x["labels"]] for k, x in v["by_subtype_or_tag"].items()])]
    L += ["## Miss labels per arm and class", "",
          md_table(["arm", "class", "misses", "by label", "(e) by cause"],
                   [[arm, cls, x["misses"], x["by_label"], x["e_by_cause"]]
                    for arm, per in d["miss_labels"].items() for cls, x in per.items()])]
    L += ["## Clean-pass classes per arm and class", "",
          md_table(["arm", "class", "failed clean passes", "by class", "(e) by cause"],
                   [[arm, cls, x["failed_clean_passes"], x["by_class"], x["e_by_cause"]]
                    for arm, per in d["clean_pass_classes"].items() for cls, x in per.items()])]
    L += ["## Structure statistic (share of 200 minus samples at or beyond the half-way point)", "",
          md_table(["arm", "class", "pairs", "share >= 0.5", "share < 0.5", "set by the brief", "no statistic", "not computable",
                    "no study file"],
                   [[arm, cls, x["pairs"], x["share_ge_half"], x["share_lt_half"], x["set_by_brief"], x["no_statistic"],
                     x["not_computable"], x["no_study_file"]] for arm, per in d["structure"].items() for cls, x in per.items()])]
    aw = d["awareness"]
    L += ["## Awareness (P / C / N)", ""]
    if "error" in aw:
        L += [aw["error"], ""]
    else:
        L += ["First reading (r1b and r2; W-0 and W-1), per arm and class:", "",
              md_table(["arm", "class", "resolved", "r1b", "r2"],
                       [[arm, cls, x["resolved"], x["r1b"], x["r2"]] for arm, per in aw["first_reading"].items()
                        for cls, x in per.items()]),
              "Second reading (r3 and r4; W-1 only), per class:", "",
              md_table(["class", "resolved", "r3", "r4"],
                       [[cls, x["resolved"], x["r3"], x["r4"]] for cls, x in aw["second_reading_w1"].items()]),
              "Detection and clean pass by resolved first-reading level:", "",
              md_table(["arm", "class", "level", "n", "attributable", "declared", "PB-style", "clean"],
                       [[arm, cls, lv, t["pairs"], t["attributable"], t["declared"], t["pb_style"], t["clean"]]
                        for arm, per in aw["split_first_resolved"].items() for cls, lvs in per.items()
                        for lv, t in lvs.items() if t["pairs"]]),
              "Detection and clean pass by resolved second-reading level (W-1):", "",
              md_table(["class", "level", "n", "attributable", "declared", "PB-style", "clean"],
                       [[cls, lv, t["pairs"], t["attributable"], t["declared"], t["pb_style"], t["clean"]]
                        for cls, lvs in aw["split_second_resolved"]["W1"].items() for lv, t in lvs.items() if t["pairs"]])]
    L += ["## Pairs", ""]
    for arm in ARM_CODES:
        L += [f"### Arm {arm}", "",
              md_table(["id", "class", "tag", "faulty", "fixed", "attributable", "generic", "declared", "PB-style", "clean",
                        "miss label", "clean-pass class", "structure share", "attrition"],
                       [[r["id"], r["class"], r["tag"], f"{r['faulty']['state']}/{r['faulty']['verdict']}",
                         f"{r['fixed']['state']}/{r['fixed']['verdict']}", r["attributable"], r["generic"], r["declared"],
                         r["pb"]["detected"], r["clean"], (r["miss"] or {}).get("label"), (r["clean_class"] or {}).get("class"),
                         (r["structure"] or {}).get("share_beyond_half"),
                         r["attrition"]["arm_level"] + r["attrition"]["twin_level"]]
                        for r in res["pairs"] if r["arm"] == arm])]
    return "\n".join(L)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Phase D scoring and report.")
    ap.add_argument("--run", default=DEFAULT_RUN, help="the run folder (RUNLOG.jsonl, certs, studies)")
    ap.add_argument("--pd", default=HERE, help="evaluation/phase_d (frozen inputs)")
    ap.add_argument("--package-root", default=DEFAULT_PKG, help="the gate at 0.5.1, for the frozen tools")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output folder (refused if it exists, unless --force)")
    ap.add_argument("--force", action="store_true", help="replace RESULTS_D.* and tools/ in an existing --out")
    ap.add_argument("--attrition", default=None, help="JSON file: designer's list of invalid skeletons")
    ap.add_argument("--tools-dir", default=None, help="default: <pd>/tools/tools")
    ap.add_argument("--audit-b-map", default=None, help="default: <pd>/record/work/AUDIT_B_MAP.json")
    ap.add_argument("--pc-results", default=os.path.join(EVAL, "phase_c", "run", "RESULTS.json"))
    ap.add_argument("--pb-table", default=os.path.join(EVAL, "phase_c", "PHASE_B_TABLE.json"))
    return ap


def cmd_score(argv) -> int:
    args = build_parser().parse_args(argv)
    args.pd = os.path.abspath(args.pd)
    args.run, args.out = os.path.abspath(args.run), os.path.abspath(args.out)
    args.tools_dir = os.path.abspath(args.tools_dir or os.path.join(args.pd, "tools", "tools"))
    if os.path.exists(args.out):
        if not args.force:
            print(f"refused: {args.out} exists (use --force to replace RESULTS_D.* and tools/)", file=sys.stderr)
            return 2
        for name in ("tools", "RESULTS_D.json", "RESULTS_D.md"):
            p = os.path.join(args.out, name)
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.isfile(p):
                os.remove(p)
    os.makedirs(args.out, exist_ok=True)
    try:
        res = build(args)
    except ScoreError as e:
        print(f"score_phase_d: {e}", file=sys.stderr)
        return 2
    write_json(os.path.join(args.out, "RESULTS_D.json"), res)
    with open(os.path.join(args.out, "RESULTS_D.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(read_json(os.path.join(args.out, "RESULTS_D.json"))) + "\n")
    print(f"wrote {os.path.join(args.out, 'RESULTS_D.json')} and RESULTS_D.md")
    return 0


# --------------------------------------------------------------------------
# selftest (synthetic certificates in a temp tree; the real frozen tools)
# --------------------------------------------------------------------------

def _bisect_wilson(k: int, n: int, z: float) -> float:
    """Independent check: the p with (k/n - p) / sqrt(p (1 - p) / n) = z (the Wilson lower bound solves this)."""
    phat = k / n
    lo, hi = 0.0, phat
    for _ in range(200):
        mid = (lo + hi) / 2
        if mid <= 0 or (phat - mid) / math.sqrt(mid * (1 - mid) / n) > z:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _comp(flags, minus, noise, plus=190, n=200, extra=None):
    counts = {"world:plus": plus, "world:minus": minus, "probe:noise": noise, "control:permute_y": 3}
    counts.update(extra or {})
    return {"id": "C", "flags": list(flags),
            "counts": {s: {"holds": h, "undefined": 0, "hard_undefined": 0, "n": n} for s, h in counts.items()}, "bounds": {}}


def _cert(verdict, flags=(), minus=4, noise=2):
    return {"body": {"verdict": verdict, "load_error": None, "components": [_comp(flags, minus, noise)], "study_flags": []}}


def cmd_selftest(_args=None) -> int:
    failures = []

    def check(name, cond, detail=""):
        print(("ok    " if cond else "FAIL  ") + name + (f"  {detail}" if (detail and not cond) else ""))
        if not cond:
            failures.append(name)

    # --- statistics
    check("wilson 8/12 = 0.431492 (PC)", abs(wilson_lower(8, 12) - 0.431492) < 1e-6)
    check("wilson 7/12 = 0.355981 (PC)", abs(wilson_lower(7, 12) - 0.355981) < 1e-6)
    check("wilson 16/20 = independent bisection", abs(wilson_lower(16, 20) - _bisect_wilson(16, 20, Z95)) < 1e-9)
    check("wilson 13/16 = independent bisection", abs(wilson_lower(13, 16) - _bisect_wilson(13, 16, Z95)) < 1e-9)
    check("wilson n = 0 is None", wilson_lower(0, 0) is None)
    for k, n in ((16, 20), (15, 19), (14, 17), (13, 16)):
        check(f"{k}/{n} reaches 0.6 (PREREG section 6)", wilson_lower(k, n) >= THRESHOLD)
    for k, n in ((15, 20), (14, 19), (13, 17), (12, 16)):
        check(f"{k}/{n} stays below 0.6", wilson_lower(k, n) < THRESHOLD)
    check("hd_verdict n = 20, 16/16 PASSES", hd_verdict(16, 16, 20)["verdict"] == "PASSES")
    check("hd_verdict one bound below 0.6 FAILS", hd_verdict(16, 15, 20)["verdict"] == "FAILS")
    check("hd_verdict n = 15 is insufficient cases", hd_verdict(15, 15, 15)["verdict"] == "insufficient cases")
    check("hd_verdict n = 16, 13/13 PASSES", hd_verdict(13, 13, 16)["verdict"] == "PASSES")
    check("mcnemar b=3 c=0 -> 0.125", mcnemar_exact_p(3, 0) == 0.125)
    check("mcnemar b=5 c=1 -> 0.109375", mcnemar_exact_p(5, 1) == 0.109375)
    check("mcnemar b=0 c=0 -> 1", mcnemar_exact_p(0, 0) == 1.0)
    check("mcnemar b=0 c=3 -> 1", mcnemar_exact_p(0, 3) == 1.0)
    check("information flag never counts", counted_flags(["K2_MINUS_UNREAD", "K1_ABSTAINED:x", "K1_ABSTAINED_MAJORITY:y",
                                                           "K2_HIGH_SIZE"]) == ["K2_HIGH_SIZE"])

    # --- the tree
    pkg = os.environ.get("KAPI_PACKAGE_ROOT") or DEFAULT_PKG
    tools_dir = os.path.join(HERE, "tools", "tools")
    if not os.path.isdir(os.path.join(pkg, "truth_gate")):
        pkg = os.path.dirname(os.path.dirname(HERE))
    if not os.path.isdir(os.path.join(pkg, "truth_gate")):
        print("SKIPPED the tool tests: no gate package root found")
        return 1 if failures else 0
    sys.path.insert(0, os.path.join(HERE, "tools", "tests"))
    sys.path.insert(0, tools_dir)
    import toy_case
    from assemble import assemble

    trivial = "import numpy as np\n\n\ndef criterion(d):\n    return True\n"

    def study_text(phi):
        return assemble(toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": phi}, trivial)

    with tempfile.TemporaryDirectory(prefix="score_phase_d_selftest_") as tmp:
        pd, run, out = (os.path.join(tmp, x) for x in ("pd", "run", "out"))
        spec = {  # id -> (class, tag, {arm: (faulty, fixed)}); faulty/fixed: ("cert", verdict, flags, minus, noise) or "TIMEOUT"
            "T-01": ("B-2", "L1.1", {"R": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 80, 2), ("FALSIFIABLE", [], 4, 2)),
                                     "W0": (("FALSIFIABLE", [], 3, 2), ("FALSIFIABLE", [], 4, 2)),
                                     "W1": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE", "K5_HOLDS_ON_NOISE"], 60, 40), ("FALSIFIABLE", [], 4, 2))}),
            "T-02": ("B-2", "L1.2", {"R": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 80, 2), ("FALSIFIABLE", [], 4, 2)),
                                     "W0": ("TIMEOUT", ("FALSIFIABLE", [], 4, 2)),
                                     "W1": (("NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"], 5, 40), ("FALSIFIABLE", [], 4, 2))}),
            "T-03": ("B-3", "change-vs-baseline", {"R": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 80, 2), ("FALSIFIABLE", [], 4, 2)),
                                                   "W0": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 60, 2), "TIMEOUT"),
                                                   "W1": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 60, 2),
                                                          ("NOT_FALSIFIABLE", ["K5_HOLDS_ON_NOISE"], 4, 40))}),
            "T-04": ("B-3", "shared-measured-component", {"R": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 80, 2), ("FALSIFIABLE", [], 4, 2)),
                                                          "W0": (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 60, 2), ("FALSIFIABLE", [], 4, 2)),
                                                          "W1": (("FALSIFIABLE", [], 3, 2), ("FALSIFIABLE", [], 4, 2))}),
            "T-05": ("B-2", "L1.4", {a: (("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 70, 2), ("FALSIFIABLE", [], 4, 2)) for a in ARM_CODES}),
            "T-06": ("B-1", "select-then-test-same-data", {"R": (("FALSIFIABLE", [], 3, 2), ("NOT_FALSIFIABLE", ["K2_HIGH_SIZE"], 30, 2)),
                                                           "W0": (("FALSIFIABLE", [], 3, 2), ("FALSIFIABLE", [], 4, 2)),
                                                           "W1": (("FALSIFIABLE", [], 3, 2), ("FALSIFIABLE", [], 4, 2))}),
        }
        phi = {("T-01", "W0"): 0.0}                              # the world of this arm lacks the structure
        expected_list = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
                         "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "HIGH_RATE:probe:noise", "HIGH_RATE:world:null",
                         "HIGH_RATE:control:permute_y"]
        write_json(os.path.join(pd, "EXPECTED_FLAGS_D.json"),
                   {"cases": {f"{i}/{name}": {"expected": expected_list} for i in spec for _, name in ARMS}})
        write_json(os.path.join(pd, "record", "shuffle", "ID_MAP_D.json"),
                   [{"id": i, "designer_id": "x", "class": c, "half": "A", "source": "S", "subtype_or_tag": t, "reserve": False}
                    for i, (c, t, _) in spec.items()])
        rows = []
        for i, (cls, tag, arms) in spec.items():
            priv = toy_case.private(0.99)
            if cls == "B-1":
                priv = {"class": cls, "subtype_or_tag": tag}
            write_json(os.path.join(pd, "cases", i, "PRIVATE.json"), priv)
            for arm, (fa, fx) in arms.items():
                for twin, item in (("faulty", fa), ("fixed", fx)):
                    row = {"event": "result", "case": i, "arm": arm, "twin": twin, "attempt": 1, "timed_out": item == "TIMEOUT",
                           "has_certificate": item != "TIMEOUT", "infrastructure_failure": False, "exit_code": 0, "seconds": 5.0,
                           "verdict": None if item == "TIMEOUT" else item[0]}
                    if item == "TIMEOUT":
                        row.update(exit_code=None, seconds=3600.5)
                    else:
                        write_json(cert_path(run, arm, i, twin), _cert(item[0], item[1], item[2], item[3]))
                    rows.append(row)
                    p = study_path(run, arm, i, twin)
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "w", encoding="utf-8", newline="\n") as handle:
                        handle.write(study_text(phi.get((i, arm), 0.99)))
        # an earlier (superseded) result row for T-01 W1 faulty: the last row must win
        rows.insert(0, {"event": "result", "case": "T-01", "arm": "W1", "twin": "faulty", "attempt": 1, "timed_out": True,
                        "has_certificate": False, "infrastructure_failure": False, "exit_code": None, "seconds": 3601.0})
        rows.insert(1, {"event": "started", "case": "T-01", "arm": "W1", "twin": "faulty", "attempt": 2})
        os.makedirs(run, exist_ok=True)
        with open(os.path.join(run, "RUNLOG.jsonl"), "w", encoding="utf-8", newline="\n") as handle:
            for r in rows:
                handle.write(json.dumps(r) + "\n")
        # part B: T-06 W1 is a "no"
        write_json(os.path.join(pd, "record", "work", "AUDIT_B_MAP.json"), {i: {"X": "W0", "Y": "W1"} for i in spec})
        for g, ids in (("B2", ["T-01", "T-02", "T-05"]), ("B3", ["T-03", "T-04"]), ("DEC", ["T-06"])):
            write_json(os.path.join(pd, "record", "sandboxes", "audit_b", g, "AUDIT_B.json"),
                       [{"case": i, "X": "yes", "Y": "no" if i == "T-06" else "yes", "reasons": {}} for i in ids])
        # awareness: first reading E01..E12 (W0 and W1 of 6 ids), second reading F01..F06 (W1)
        labels, k = {}, 0
        for i in spec:
            for arm in ("W0", "W1"):
                k += 1
                labels[f"E{k:02d}"] = {"id": i, "arm": arm, "sandbox": "s"}
        write_json(os.path.join(pd, "record", "work", "AWARENESS_MAP_first.json"), labels)
        write_json(os.path.join(pd, "record", "work", "AWARENESS_MAP_second.json"),
                   {f"F{j + 1:02d}": {"id": i, "arm": "W1", "sandbox": "s"} for j, i in enumerate(spec)})
        first = {"r1b": ["N", "C", "N", "P", "C", "C", "N", "N", "P", "N", "C", "N"],
                 "r2": ["N", "N", "C", "C", "C", "P", "N", "N", "N", "N", "N", "Z"]}
        for rd, lv in first.items():
            write_json(os.path.join(pd, "record", "sandboxes", "awareness", rd, "READING.json"),
                       {f"E{j + 1:02d}": {"level": x, "reason": "r"} for j, x in enumerate(lv)})
        write_json(os.path.join(pd, "record", "sandboxes", "awareness", "r1", "READING.json"),
                   {f"E{j + 1:02d}": {"level": "P", "reason": "excluded reader"} for j in range(12)})
        for rd, lv in (("r3", ["N", "N", "C", "N", "P", "N"]), ("r4", ["N", "C", "N", "N", "C", "N"])):
            write_json(os.path.join(pd, "record", "sandboxes", "awareness", rd, "READING.json"),
                       {f"F{j + 1:02d}": {"level": x, "reason": "r"} for j, x in enumerate(lv)})
        write_json(os.path.join(pd, "record", "validity", "SELECTION.json"), {"B-2": {"n_selected": 3}, "B-3": {"n_selected": 2}})
        write_json(os.path.join(pd, "record", "validity", "FREEZE_VALIDITY.json"),
                   {"pairs": [{"id": "T-01", "decision": "pass", "counting_label": None},
                              {"id": "T-02", "decision": "drop", "counting_label": "V1a"},
                              {"id": "T-05", "decision": "pass", "counting_label": None},
                              {"id": "T-06", "decision": "pass", "counting_label": None}],
                    "pre_validity_drops": {"T-03": "reference rejected by check_skeletons_d (P-3 event 2)"},
                    "audit_a": {"T-04": {"overall": "fail", "failed_items": ["h"]}}, "label_counts": {"V1a": 1}})
        write_json(os.path.join(tmp, "pc.json"), {"primary_version": "v050", "gate": {"v050": {"classes": {
            "B-2": {"pairs": 12, "detections": 7, "clean_passes": 8}}}},
            "phase_b_next_to_c": {"phase_b_gate_version": "v040", "phase_b": {"classes": {
                "B-2": {"pairs": 14, "detections": 9, "clean_passes": 10}}}}})
        write_json(os.path.join(tmp, "pbt.json"), {"pairs": [{"case": "B2-01"}]})
        write_json(os.path.join(tmp, "attr.json"), {"T-05/W1": "invalid skeleton"})

        argv = ["--run", run, "--pd", pd, "--package-root", pkg, "--out", out, "--tools-dir", tools_dir,
                "--pc-results", os.path.join(tmp, "pc.json"), "--pb-table", os.path.join(tmp, "pbt.json"),
                "--attrition", os.path.join(tmp, "attr.json")]
        rc = cmd_score(argv)
        check("score runs", rc == 0)
        check("score refuses an existing out folder", cmd_score(argv) == 2)
        res = read_json(os.path.join(out, "RESULTS_D.json"))
        md = open(os.path.join(out, "RESULTS_D.md"), encoding="utf-8").read()
        check("no tool error", not res["tool_errors"], str(res["tool_errors"])[:400])
        P = {(r["id"], r["arm"]): r for r in res["pairs"]}
        check("the last result row wins (T-01 W1 faulty is not a timeout)", P[("T-01", "W1")]["faulty"]["state"] == "ok")
        t01w1 = P[("T-01", "W1")]
        check("attributable via the frozen tool: generic and declared", t01w1["attributable"] and t01w1["generic"] and t01w1["declared"])
        check("attributable kept under tools/attributable/W1/T-01.json",
              os.path.isfile(os.path.join(out, "tools", "attributable", "W1", "T-01.json")))
        check("T-02 W1 attributable, generic only", P[("T-02", "W1")]["attributable"] and P[("T-02", "W1")]["generic"]
              and not P[("T-02", "W1")]["declared"])
        t02w0 = P[("T-02", "W0")]
        check("faulty timeout: miss, label e", not t02w0["attributable"] and t02w0["miss"]["label"] == "e"
              and "timeout" in (t02w0["miss"]["cause"] or ""), str(t02w0["miss"]))
        check("faulty timeout is listed as attrition", "faulty timeout" in t02w0["attrition"]["twin_level"])
        t03w0 = P[("T-03", "W0")]
        check("fixed timeout: pair is a miss (label e, fixed) and a failed clean pass (class e)",
              not t03w0["attributable"] and t03w0["miss"]["label"] == "e" and t03w0["miss"]["cause_twin"] == "fixed"
              and not t03w0["clean"] and t03w0["clean_class"]["class"] == "e", str((t03w0["miss"], t03w0["clean_class"])))
        check("fixed timeout still counts the PB-style detection (PB section 6 as PC)", t03w0["pb"]["detected"])
        t03w1 = P[("T-03", "W1")]
        check("clean pass without the noise stream (fixed flagged on noise only)",
              not t03w1["clean"] and t03w1["clean_wo_noise"] and t03w1["clean_class"]["class"] == "3", str(t03w1["clean_class"]))
        check("T-03 W1 still attributable (declared)", t03w1["declared"])
        t01w0 = P[("T-01", "W0")]
        check("miss label (a): declared world lacks the structure", t01w0["miss"]["label"] == "a", str(t01w0["miss"]))
        t04w1 = P[("T-04", "W1")]
        check("miss label (b): below the flag threshold, structure present", t04w1["miss"]["label"] == "b", str(t04w1["miss"]))
        check("structure statistic recorded for an arm with a statistic",
              t01w0["structure"]["status"] == "computed" and t01w0["structure"]["share_beyond_half"] < 0.5 <= t04w1["structure"]["share_beyond_half"],
              str((t01w0["structure"], t04w1["structure"])))
        check("decoy without a statistic: no statistic", P[("T-06", "W0")]["structure"]["status"] == "no statistic")
        t06r = P[("T-06", "R")]
        check("clean-pass class 1 by fresh samples (fixed holds on all fresh minus samples)",
              t06r["clean_class"]["class"] == "1", str(t06r["clean_class"]))
        t06w1 = P[("T-06", "W1")]
        check("part-B no: miss and failed clean pass, label e, class e",
              t06w1["attrition"]["arm_level"] == ["part-B no"] and not t06w1["clean"] and t06w1["miss"]["label"] == "e"
              and t06w1["clean_class"]["class"] == "e" and not t06w1["pb"]["detected"], str(t06w1["miss"]))
        t05w1 = P[("T-05", "W1")]
        check("designer-given invalid skeleton overrides a detectable pair", "invalid skeleton" in t05w1["attrition"]["arm_level"]
              and not t05w1["attributable"] and not t05w1["pb"]["detected"] and not t05w1["clean"])
        check("draft-1 rule comes from the tool", t01w1["draft1"] is True and P[("T-01", "W0")]["draft1"] is False)
        h = res["hypotheses"]
        check("H-D1 insufficient cases (n = 3 in W1)", h["H-D1"]["verdict"] == "insufficient cases" and h["H-D1"]["n"] == 3)
        check("H-D2 insufficient cases", h["H-D2"]["verdict"] == "insufficient cases")
        comparable, notcomp = h["H-D3"]["comparable_pairs"], [e["id"] for e in h["H-D3"]["not_comparable"]]
        check("H-D3 comparable pairs (T-02, T-03, T-05 excluded)", comparable == ["T-01", "T-04"] and
              notcomp == ["T-02", "T-03", "T-05"], str((comparable, notcomp)))
        main = h["H-D3"]["main"]
        check("H-D3 b = 1 (T-01), c = 1 (T-04), p = 0.75, not demonstrated",
              (main["b_w1_only"], main["c_w0_only"], main["p"], main["verdict"]) == (1, 1, 0.75, "not demonstrated"), str(main))
        sens = h["H-D3"]["sensitivity_not_comparable_counted_as_non_detections"]
        check("H-D3 sensitivity: attrition arms are non-detections (b = 2, c = 2, p = 0.6875)",
              (sens["n_pairs"], sens["b_w1_only"], sens["c_w0_only"], sens["p"]) == (5, 2, 2, 0.6875), str(sens))
        check("discordant counts per class", main["discordant_per_class"] == {"B-2": {"b_w1_only": 1, "c_w0_only": 0},
                                                                              "B-3": {"b_w1_only": 0, "c_w0_only": 1}})
        g = h["clean_pass_guard"]
        check("clean-pass guard on the H-D3 pairs (no clean difference, p = 1)", (g["pairs"], g["w0_clean_only"], g["w1_clean_only"], g["p"])
              == (2, 0, 0, 1.0), str(g))
        check("decoys' clean pass W1 minus W0 = -1", h["adoption_inputs"]["decoys_clean_difference_w1_minus_w0"] == -1)
        tab = res["per_arm_class"]["W1"]["B-2"]
        check("per arm and class: n, attributable, attrition list", (tab["pairs"], tab["attributable"]) == (3, 2) and
              tab["attrition_by_cause"] == {"invalid skeleton": 1}, str(tab))
        aw = res["descriptive"]["awareness"]
        check("awareness: r1 is excluded and the higher level resolves", P[("T-01", "W0")]["awareness"]["first"]["resolved"] == "N"
              and P[("T-01", "W1")]["awareness"]["first"]["resolved"] == "C" and P[("T-02", "W0")]["awareness"]["first"]["resolved"] == "C"
              and P[("T-02", "W1")]["awareness"]["first"]["resolved"] == "P", str(P[("T-02", "W1")]["awareness"]))
        check("awareness: an unreadable level resolves to ?", P[("T-06", "W1")]["awareness"]["first"]["resolved"] == "?")
        check("awareness: second reading resolves the same way", P[("T-03", "W1")]["awareness"]["second"]["resolved"] == "C"
              and P[("T-05", "W1")]["awareness"]["second"]["resolved"] == "P")
        check("awareness split by level (W1, B-2: N and C and P)", aw["split_first_resolved"]["W1"]["B-2"]["C"]["pairs"] == 1)
        check("arm R has no awareness", P[("T-01", "R")]["awareness"] is None)
        w = res["descriptive"]["w0_next_to_pb_pc"]
        check("PB and PC numbers: found, and not found", w["classes"]["B-2"]["PC"] == {"pairs": 12, "detections": 7, "generic": "not found",
                                                                                      "declared": "not found", "clean_passes": 8}
              and w["classes"]["B-3"]["PC"]["pairs"] == "not found" and w["classes"]["B-2"]["PB"]["detections"] == 9, str(w["classes"]["B-2"]))
        v = res["descriptive"]["validity_drops"]
        check("validity: labels by id (pass, V1a, pre-validity, fidelity)", v["by_class"]["B-2"]["labels"] == {"V1a": 1, "pass": 2}
              and v["by_class"]["B-3"]["labels"] == {"fidelity A (h)": 1, "reference rejected by check_skeletons_d": 1}, str(v["by_class"]))
        ex = res["descriptive"]["arm_R_exceptions"]
        check("arm R exceptions list the failed clean pass", [e["id"] for e in ex] == ["T-06"], str(ex))
        check("markdown holds the verdict labels and the p of H-D3", "insufficient cases" in md and "0.7500" in md)
        check("markdown is a function of RESULTS_D.json", md.strip() == render_markdown(res).strip())
        # --force replaces the results
        check("--force replaces RESULTS_D.* in an existing out folder", cmd_score(argv + ["--force"]) == 0)
    print("selftest: " + ("PASSED" if not failures else f"FAILED ({len(failures)}): {failures}"))
    return 1 if failures else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "selftest":
        return cmd_selftest()
    if argv and argv[0] == "score":
        argv = argv[1:]
    return cmd_score(argv)


if __name__ == "__main__":
    sys.exit(main())
