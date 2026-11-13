#!/usr/bin/env python3
"""Phase B runner and reporter (pre-registration ``PREREG_PHASE_B.md``, sections 6 and 7).

Sub-commands
------------
``run``     run the gate of one version (``v040`` = tag v0.4.0, ``v030`` = tag v0.3.0) on every twin of every case, in
            full mode, one check at a time, and store certificates, logs and a run log.
``report``  compute ``RESULTS.json`` and ``RESULTS.md`` from the certificates, the run logs, ``EXPECTED_FLAGS.json``
            and ``record/world/AWARENESS.md`` only.  Same inputs give byte-identical outputs.
``selftest`` check the metric code on synthetic certificates (no gate, no case file is touched).

Usage (from the repository root)::

    git worktree add <DIR> v0.4.0            # the designer creates the worktrees; this script only checks them
    py evaluation/phase_b/run_phase_b.py run --version v040 --worktree <DIR> [--timeout 3600] [--redo]
    py evaluation/phase_b/run_phase_b.py run --version v030 --worktree <DIR030>
    py evaluation/phase_b/run_phase_b.py report
    py evaluation/phase_b/run_phase_b.py selftest

Options of ``run``: ``--cases-dir`` (default ``evaluation/phase_b/cases``), ``--expected`` (default
``evaluation/phase_b/EXPECTED_FLAGS.json``), ``--out`` (default ``evaluation/phase_b/run``), ``--timeout`` seconds
(default 3600), ``--redo``.  Layout under ``--out``: ``certs/<version>/<case>/<twin>.json``,
``logs/<version>/<case>/<twin>.txt`` (last 40 lines of stdout and stderr), ``runlog_<version>.jsonl`` (one line per
check: exit code, wall seconds, timeout flag).  A check is skipped when its run-log line exists and its certificate
exists (or the line records a timeout, which is a result and is not repeated); ``--redo`` forces every check.
Before the real run the case freeze is verified (``protocol/tools/freeze.py verify FREEZE_CASES.json`` must exit 0);
the verification is skipped only when ``--cases-dir`` is not the default, and that is printed.

Rules implemented by ``report`` (section 6 of the pre-registration)
-------------------------------------------------------------------
* Expected flags: the per-case list in ``EXPECTED_FLAGS.json``; a flag counts when a component of the certificate
  carries exactly that string (study-level flags do not count).
* Detection of a pair: the faulty file's study verdict is NOT_FALSIFIABLE and at least one component carries an
  expected flag.  UNDEFINED, UNTESTED, WEAK, FALSIFIABLE, a load error, a missing certificate or a run beyond 3600 s
  is a miss.  Label **generic** if ``K5_HOLDS_ON_NOISE`` or ``HIGH_RATE:probe:noise`` is among the faulty file's
  flags, else **declared**; also **K2-only** when the only expected flags present are ``K2_NO_SEPARATION`` and/or
  ``K2_FAILS_UNREACHABLE``.
* Clean pass: the fixed file's verdict is FALSIFIABLE or WEAK; anything else (a timeout or a missing certificate
  included) is a failure and is reported with its flags.
* Per in-scope class (B-1, B-2, B-3, B-6) and per B-2 subtype: pairs, detections (generic / declared / K2-only),
  clean passes, one-sided 95% Wilson lower bounds (z = 1.6448536269514722) of the detection rate and of the
  clean-pass rate; verdict HOLDS iff pairs >= 10 and both lower bounds >= 0.6, else FAILS.  Out-of-scope cases get the
  same counts without bounds or verdict.
* Baselines on the same pairs: Truth_Gate 0.3.0 certificates (same metrics, plus the per-pair verdict
  differences), flag-everything (detection = all, clean pass = none), noise-only (detection from the two noise
  flags only, verdict condition unchanged, clean pass as the gate), declared-only (detection from the other expected
  flags only).
* Descriptive awareness breakdown (P, C, N from AWARENESS.md, via the world id): counts only, no bounds, no verdict.
* Run times per version: min, median, max, and the checks beyond 3600 s.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PHASE_B = os.path.join(ROOT, "evaluation", "phase_b")
DEFAULT_CASES = os.path.join(PHASE_B, "cases")
DEFAULT_EXPECTED = os.path.join(PHASE_B, "EXPECTED_FLAGS.json")
DEFAULT_OUT = os.path.join(PHASE_B, "run")
DEFAULT_AWARENESS = os.path.join(PHASE_B, "record", "world", "AWARENESS.md")
FREEZE_CASES = os.path.join(PHASE_B, "FREEZE_CASES.json")
FREEZE_TOOL = os.path.join(ROOT, "protocol", "tools", "freeze.py")

VERSIONS = {
    "v040": {"tag": "v0.4.0", "module": "truth_gate", "tool_version": "0.4.0"},
    "v030": {"tag": "v0.3.0", "module": "kapi", "tool_version": "0.3.0"},
}
PRIMARY = "v040"
TWINS = ("faulty", "fixed")

Z95 = 1.6448536269514722        # one-sided 95%
THRESHOLD = 0.6
MIN_PAIRS = 10
TIME_LIMIT = 3600.0             # PREREG section 5/6: a check beyond 60 minutes is a miss / failed clean pass
TAIL_LINES = 40

NOISE_FLAGS = frozenset({"K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"})
K2_FLAGS = frozenset({"K2_NO_SEPARATION", "K2_FAILS_UNREACHABLE"})
CLEAN_VERDICTS = ("FALSIFIABLE", "WEAK")
IN_SCOPE_CLASSES = ("B-1", "B-2", "B-3", "B-6")
B2_SUBTYPES = ("L1.1", "L1.2", "L1.3", "L1.4", "L3.1", "L3.2")


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def wilson_lower(k: int, n: int, z: float = Z95) -> "float | None":
    """One-sided Wilson score lower bound of a binomial proportion (None when n = 0)."""
    if n <= 0:
        return None
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, centre - half)


def fmt(x: "float | None", digits: int = 4) -> str:
    return "-" if x is None else f"{x:.{digits}f}"


def rnd(x: "float | None", digits: int = 6) -> "float | None":
    return None if x is None else round(x, digits)


# --------------------------------------------------------------------------
# Paths and shared file helpers
# --------------------------------------------------------------------------

def cert_path(out: str, version: str, case: str, twin: str) -> str:
    return os.path.join(out, "certs", version, case, twin + ".json")


def log_path(out: str, version: str, case: str, twin: str) -> str:
    return os.path.join(out, "logs", version, case, twin + ".txt")


def runlog_path(out: str, version: str) -> str:
    return os.path.join(out, f"runlog_{version}.jsonl")


def load_expected(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)["cases"]


def read_runlog(out: str, version: str) -> dict:
    """``{(case, twin): last run-log line}``; later lines win."""
    result: dict = {}
    path = runlog_path(out, version)
    if not os.path.isfile(path):
        return result
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            result[(row["case"], row["twin"])] = row
    return result


def read_certificate(path: str) -> "tuple[str, dict | None]":
    """``(status, body)``: ``missing``, ``invalid`` or ``ok``."""
    if not os.path.isfile(path):
        return "missing", None
    try:
        with open(path, encoding="utf-8") as handle:
            envelope = json.load(handle)
        body = envelope["body"]
        if not isinstance(body, dict) or not isinstance(body["verdict"], str) or not isinstance(body["components"], list):
            return "invalid", None
        return "ok", body
    except (OSError, ValueError, KeyError, TypeError):
        return "invalid", None


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------

def _git(*args: str, cwd: str = ROOT) -> "tuple[int, str]":
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def verify_worktree(version: str, worktree: str) -> None:
    tag = VERSIONS[version]["tag"]
    rc1, tag_commit = _git("rev-parse", f"{tag}^{{commit}}")
    rc2, head = _git("-C", worktree, "rev-parse", "HEAD")
    if rc1 != 0 or rc2 != 0:
        raise SystemExit(f"cannot resolve {tag} or the worktree HEAD ({worktree})")
    if tag_commit != head:
        raise SystemExit(f"worktree {worktree} is at {head}, but {tag} is {tag_commit}: refusing to run")
    print(f"worktree ok: {worktree} is at {tag} ({head[:12]})")


def verify_case_freeze(cases_dir: str) -> None:
    if os.path.realpath(cases_dir) != os.path.realpath(DEFAULT_CASES):
        print(f"case freeze verification SKIPPED (--cases-dir is not the default: {cases_dir})")
        return
    proc = subprocess.run([sys.executable, FREEZE_TOOL, "verify", FREEZE_CASES], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout + proc.stderr)
        raise SystemExit(f"case freeze verification failed (exit {proc.returncode}): refusing to run")
    print("case freeze verified (FREEZE_CASES.json)")


def discover_cases(cases_dir: str, expected: dict) -> list:
    names = sorted(
        d for d in os.listdir(cases_dir)
        if os.path.isfile(os.path.join(cases_dir, d, "faulty.py")) and os.path.isfile(os.path.join(cases_dir, d, "fixed.py"))
    )
    unknown = [n for n in names if n not in expected]
    if unknown:
        raise SystemExit(f"case folders without an entry in the expected-flags file: {', '.join(unknown)}")
    return names


def _tail(text: str, n: int = TAIL_LINES) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-n:])


def run_one(version: str, worktree: str, study: str, cert: str, timeout: float) -> dict:
    """Run one gate check as a child process; kills only that child on timeout."""
    module = VERSIONS[version]["module"]
    env = dict(os.environ)
    env["PYTHONPATH"] = worktree
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-m", module, "check", study, "--out", cert]
    start = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=worktree, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")
    timed_out = False
    try:
        output, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        output, _ = proc.communicate()
    seconds = time.perf_counter() - start
    if timed_out:
        output = (output or "") + f"\n[killed after the {timeout:g} s limit]\n"
    return {"exit_code": proc.returncode, "seconds": seconds, "timed_out": timed_out, "output": output or ""}


def cmd_run(args: argparse.Namespace) -> int:
    version = args.version
    cases_dir = os.path.abspath(args.cases_dir) if args.cases_dir else DEFAULT_CASES
    expected_path = os.path.abspath(args.expected) if args.expected else DEFAULT_EXPECTED
    out = os.path.abspath(args.out) if args.out else DEFAULT_OUT
    worktree = os.path.abspath(args.worktree)
    verify_case_freeze(cases_dir)
    verify_worktree(version, worktree)
    expected = load_expected(expected_path)
    cases = discover_cases(cases_dir, expected)
    missing = sorted(set(expected) - set(cases))
    if missing:
        print(f"note: expected-flags entries without a case folder: {', '.join(missing)}")
    os.makedirs(out, exist_ok=True)
    log_file = runlog_path(out, version)
    done = read_runlog(out, version)
    total = len(cases) * len(TWINS)
    index = 0
    for case in cases:
        for twin in TWINS:
            index += 1
            cert = cert_path(out, version, case, twin)
            prior = done.get((case, twin))
            if not args.redo and prior is not None and (os.path.isfile(cert) or prior.get("timed_out")):
                print(f"[{index}/{total}] {case} {twin}: skip (already done: {prior.get('verdict')})")
                continue
            os.makedirs(os.path.dirname(cert), exist_ok=True)
            os.makedirs(os.path.dirname(log_path(out, version, case, twin)), exist_ok=True)
            if os.path.isfile(cert):
                os.remove(cert)     # never mistake a stale certificate for the result of this run
            study = os.path.join(cases_dir, case, twin + ".py")
            result = run_one(version, worktree, study, cert, args.timeout)
            status, body = read_certificate(cert)
            verdict = body["verdict"] if body else ("TIMEOUT" if result["timed_out"] else status.upper())
            with open(log_path(out, version, case, twin), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(_tail(result["output"]) + "\n")
            row = {
                "version": version, "case": case, "twin": twin, "study": study.replace("\\", "/"),
                "worktree_head": _git("-C", worktree, "rev-parse", "HEAD")[1],
                "exit_code": result["exit_code"], "seconds": round(result["seconds"], 3),
                "timed_out": result["timed_out"], "timeout_limit": args.timeout, "verdict": verdict,
            }
            with open(log_file, "a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
            print(f"[{index}/{total}] {case} {twin}: {verdict} (exit {result['exit_code']}) {result['seconds']:.1f} s"
                  + (" TIMEOUT" if result["timed_out"] else ""))
            sys.stdout.flush()
    print("run finished")
    return 0


# --------------------------------------------------------------------------
# report: per-check and per-pair evaluation
# --------------------------------------------------------------------------

def load_check(out: str, version: str, case: str, twin: str, runlog: dict) -> dict:
    """One check: status (ok / timeout / missing / invalid), verdict, flags, seconds."""
    status, body = read_certificate(cert_path(out, version, case, twin))
    row = runlog.get((case, twin))
    seconds = row.get("seconds") if row else None
    if (row and row.get("timed_out")) or (seconds is not None and seconds > TIME_LIMIT):
        status = "timeout"
    comp_flags: list = []
    verdict = None
    load_error = False
    tool_version = None
    if status == "ok" and body is not None:
        verdict = body["verdict"]
        load_error = bool(body.get("load_error"))
        tool_version = body.get("tool_version")
        seen = set()
        for comp in body["components"]:
            seen.update(comp.get("flags", []))
        comp_flags = sorted(seen)
    return {"status": status, "verdict": verdict, "flags": comp_flags, "seconds": seconds,
            "load_error": load_error, "tool_version": tool_version}


def shown_verdict(check: dict) -> str:
    if check["status"] == "ok":
        return check["verdict"] + (" (load error)" if check["load_error"] else "")
    return check["status"].upper()


def evaluate_pair(meta: dict, faulty: dict, fixed: dict) -> dict:
    expected = set(meta["expected"])
    present = sorted(expected & set(faulty["flags"])) if faulty["status"] == "ok" else []
    f_nf = faulty["status"] == "ok" and faulty["verdict"] == "NOT_FALSIFIABLE"
    detected = f_nf and bool(present)
    non_noise = [f for f in present if f not in NOISE_FLAGS]
    noise = [f for f in present if f in NOISE_FLAGS]
    generic = bool(NOISE_FLAGS & set(faulty["flags"])) if faulty["status"] == "ok" else False
    return {
        "faulty_verdict": shown_verdict(faulty),
        "faulty_flags": faulty["flags"],
        "expected_present": present,
        "detected": detected,
        "label": ("generic" if generic else "declared") if detected else None,
        "k2_only": bool(detected and set(present) <= K2_FLAGS),
        "detected_noise_only": bool(f_nf and noise),
        "detected_declared_only": bool(f_nf and non_noise),
        "fixed_verdict": shown_verdict(fixed),
        "fixed_flags": fixed["flags"],
        "clean": bool(fixed["status"] == "ok" and fixed["verdict"] in CLEAN_VERDICTS),
        "faulty_seconds": faulty["seconds"],
        "fixed_seconds": fixed["seconds"],
        "faulty_status": faulty["status"],
        "fixed_status": fixed["status"],
    }


def group_label(meta: dict) -> str:
    """Class label for grouping: the class of an in-scope case, the O-n subtype of an out-of-scope case."""
    if meta["in_scope"]:
        return meta["class"]
    return meta["subtype"] or meta["class"]


def tally(pairs: list, kind: str) -> dict:
    """Counts for a list of evaluated pairs. kind: gate | flag_all | noise_only | declared_only."""
    n = len(pairs)
    clean = sum(1 for p in pairs if p["clean"])
    if kind == "gate":
        dets = [p for p in pairs if p["detected"]]
        out = {
            "pairs": n, "detections": len(dets),
            "generic": sum(1 for p in dets if p["label"] == "generic"),
            "declared": sum(1 for p in dets if p["label"] == "declared"),
            "k2_only": sum(1 for p in dets if p["k2_only"]),
            "clean_passes": clean,
        }
    elif kind == "flag_all":
        out = {"pairs": n, "detections": n, "clean_passes": 0}
    elif kind == "noise_only":
        out = {"pairs": n, "detections": sum(1 for p in pairs if p["detected_noise_only"]), "clean_passes": clean}
    elif kind == "declared_only":
        out = {"pairs": n, "detections": sum(1 for p in pairs if p["detected_declared_only"]), "clean_passes": clean}
    else:
        raise ValueError(kind)
    return out


def add_bounds(counts: dict) -> dict:
    n = counts["pairs"]
    det = wilson_lower(counts["detections"], n)
    cln = wilson_lower(counts["clean_passes"], n)
    holds = n >= MIN_PAIRS and det is not None and cln is not None and det >= THRESHOLD and cln >= THRESHOLD
    counts = dict(counts)
    counts["detection_rate"] = rnd(counts["detections"] / n) if n else None
    counts["clean_rate"] = rnd(counts["clean_passes"] / n) if n else None
    counts["detection_lower"] = rnd(det)
    counts["clean_lower"] = rnd(cln)
    counts["pairs_ge_10"] = n >= MIN_PAIRS
    counts["verdict"] = "HOLDS" if holds else "FAILS"
    return counts


def class_groups(records: list) -> "tuple[dict, dict, dict]":
    """Group pair records: in-scope classes, B-2 subtypes, out-of-scope labels (each ``{label: [pairs]}``)."""
    classes = {c: [] for c in IN_SCOPE_CLASSES}
    subtypes = {s: [] for s in B2_SUBTYPES}
    outside: dict = {}
    for rec in records:
        meta = rec["meta"]
        if meta["in_scope"]:
            classes.setdefault(meta["class"], []).append(rec["eval"])
            if meta["class"] == "B-2":
                subtypes.setdefault(meta["subtype"], []).append(rec["eval"])
        else:
            outside.setdefault(group_label(meta), []).append(rec["eval"])
    return classes, subtypes, dict(sorted(outside.items()))


def metrics_table(records: list, kind: str) -> dict:
    classes, subtypes, outside = class_groups(records)
    return {
        "classes": {k: add_bounds(tally(v, kind)) for k, v in classes.items()},
        "b2_subtypes": {k: add_bounds(tally(v, kind)) for k, v in subtypes.items()},
        "out_of_scope": {k: tally(v, kind) for k, v in outside.items()},
    }


def parse_awareness(path: str) -> dict:
    """``{world id: P|C|N}`` from the classification table of AWARENESS.md."""
    levels: dict = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] in ("P", "C", "N") and line.lstrip().startswith("|"):
                for wid in re.findall(r"\bW\d{2}\b", cells[1]):
                    levels[wid] = cells[0]
    return levels


def awareness_table(records: list) -> dict:
    out: dict = {}
    for level in ("P", "C", "N", "?"):
        rows = [r for r in records if r["awareness"] == level]
        if not rows:
            continue
        labels = sorted({group_label(r["meta"]) for r in rows})
        out[level] = {"all": tally([r["eval"] for r in rows], "gate")}
        for label in labels:
            out[level][label] = tally([r["eval"] for r in rows if group_label(r["meta"]) == label], "gate")
    return out


def runtime_table(checks: list) -> dict:
    secs = [c["seconds"] for c in checks if c["seconds"] is not None]
    long = sorted(
        ({"case": c["case"], "twin": c["twin"], "seconds": rnd(c["seconds"], 3), "timed_out": c["status"] == "timeout"}
         for c in checks if c["status"] == "timeout" or (c["seconds"] is not None and c["seconds"] > TIME_LIMIT)),
        key=lambda d: (d["case"], d["twin"]))
    return {
        "checks_with_time": len(secs),
        "min": rnd(min(secs), 3) if secs else None,
        "median": rnd(statistics.median(secs), 3) if secs else None,
        "max": rnd(max(secs), 3) if secs else None,
        "beyond_3600_s": long,
    }


def version_has_data(out: str, version: str) -> bool:
    return os.path.isfile(runlog_path(out, version)) or os.path.isdir(os.path.join(out, "certs", version))


def build_results(out: str, expected_path: str, awareness_path: str) -> dict:
    expected = load_expected(expected_path)
    awareness = parse_awareness(awareness_path) if os.path.isfile(awareness_path) else {}
    versions = [v for v in (PRIMARY, "v030") if version_has_data(out, v)]
    if PRIMARY not in versions:
        raise SystemExit(f"no {PRIMARY} certificates or run log under {out}")
    cases = sorted(expected)
    per_version: dict = {}
    runtimes: dict = {}
    for version in versions:
        runlog = read_runlog(out, version)
        recs = []
        all_checks = []
        for case in cases:
            checks = {t: load_check(out, version, case, t, runlog) for t in TWINS}
            meta = expected[case]
            recs.append({"case": case, "meta": meta, "checks": checks,
                         "eval": evaluate_pair(meta, checks["faulty"], checks["fixed"]),
                         "awareness": awareness.get(meta["world_id"], "?")})
            all_checks += [{"case": case, "twin": t, **checks[t]} for t in TWINS]
        per_version[version] = recs
        runtimes[version] = runtime_table(all_checks)
    primary = per_version[PRIMARY]
    result: dict = {
        "primary_version": PRIMARY,
        "versions_present": versions,
        "rules": {
            "z_one_sided_95": Z95, "threshold": THRESHOLD, "min_pairs": MIN_PAIRS, "time_limit_s": TIME_LIMIT,
            "noise_flags": sorted(NOISE_FLAGS), "k2_flags": sorted(K2_FLAGS), "clean_verdicts": list(CLEAN_VERDICTS),
        },
        "gate": metrics_table(primary, "gate"),
        "baselines": {
            "flag_everything": metrics_table(primary, "flag_all"),
            "noise_only": metrics_table(primary, "noise_only"),
            "declared_only": metrics_table(primary, "declared_only"),
        },
        "awareness": awareness_table(primary),
        "runtimes": runtimes,
        "not_built": {"B-4": "no documented cases; no evidence either way", "B-5": "no documented cases; no evidence either way"},
    }
    if "v030" in per_version:
        result["baselines"]["truth_gate_0_3_0"] = metrics_table(per_version["v030"], "gate")
        diffs = []
        for new, old in zip(primary, per_version["v030"]):
            row = {"case": new["case"]}
            differs = False
            for twin in TWINS:
                a, b = new["eval"][f"{twin}_verdict"], old["eval"][f"{twin}_verdict"]
                row[f"{twin}_v040"], row[f"{twin}_v030"] = a, b
                differs = differs or a != b
            row["flags_differ"] = (new["eval"]["faulty_flags"] != old["eval"]["faulty_flags"]
                                   or new["eval"]["fixed_flags"] != old["eval"]["fixed_flags"])
            if differs:
                diffs.append(row)
        result["version_verdict_differences"] = diffs
    result["pairs"] = [
        {
            "case": r["case"], "class": r["meta"]["class"], "subtype": r["meta"]["subtype"],
            "in_scope": r["meta"]["in_scope"], "world_id": r["meta"]["world_id"], "awareness": r["awareness"],
            **{k: r["eval"][k] for k in (
                "faulty_verdict", "faulty_flags", "expected_present", "detected", "label", "k2_only",
                "fixed_verdict", "fixed_flags", "clean", "faulty_seconds", "fixed_seconds")},
        }
        for r in primary
    ]
    return result


# --------------------------------------------------------------------------
# report: Markdown
# --------------------------------------------------------------------------

def md_table(header: list, rows: list) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def _bounded_rows(table: dict, full: bool) -> list:
    rows = []
    for label, c in table.items():
        row = [label, c["pairs"], c["detections"]]
        if full:
            row += [c["generic"], c["declared"], c["k2_only"]]
        row += [c["clean_passes"], fmt(c["detection_lower"]), fmt(c["clean_lower"]), "yes" if c["pairs_ge_10"] else "no", c["verdict"]]
        rows.append(row)
    return rows


def _bounded_header(full: bool) -> list:
    head = ["group", "pairs", "detections"]
    if full:
        head += ["generic", "declared", "K2-only"]
    return head + ["clean passes", "detection lower", "clean-pass lower", "pairs>=10", "verdict"]


def _metric_block(title: str, block: dict, full: bool) -> str:
    parts = [f"### {title}", "", "In-scope classes", "",
             md_table(_bounded_header(full), _bounded_rows(block["classes"], full)), "",
             "B-2 subtypes", "",
             md_table(_bounded_header(full), _bounded_rows(block["b2_subtypes"], full)), ""]
    if block["out_of_scope"]:
        if full:
            head = ["group", "pairs", "detections", "generic", "declared", "K2-only", "clean passes"]
            rows = [[k, c["pairs"], c["detections"], c["generic"], c["declared"], c["k2_only"], c["clean_passes"]]
                    for k, c in block["out_of_scope"].items()]
        else:
            head = ["group", "pairs", "detections", "clean passes"]
            rows = [[k, c["pairs"], c["detections"], c["clean_passes"]] for k, c in block["out_of_scope"].items()]
        parts += ["Out of scope (counts only)", "", md_table(head, rows), ""]
    return "\n".join(parts)


def render_markdown(res: dict) -> str:
    out = ["# Phase B results", "",
           f"Gate under test: {res['primary_version']}. Versions with data: {', '.join(res['versions_present'])}.",
           f"Wilson bounds are one-sided 95% (z = {Z95}); HOLDS needs pairs >= {MIN_PAIRS} and both lower bounds >= {THRESHOLD}.",
           f"B-4: {res['not_built']['B-4']}. B-5: {res['not_built']['B-5']}.", "",
           "## 1. Truth_Gate " + res["primary_version"], "", _metric_block("Per class", res["gate"], True)]
    out += ["## 2. Baselines", ""]
    names = {"truth_gate_0_3_0": ("Truth_Gate 0.3.0 (same files)", True), "flag_everything": ("Flag everything", False),
             "noise_only": ("Noise-only", False), "declared_only": ("Declared-only", False)}
    for key in ("truth_gate_0_3_0", "flag_everything", "noise_only", "declared_only"):
        if key in res["baselines"]:
            title, full = names[key]
            out.append(_metric_block(title, res["baselines"][key], full))
    if "version_verdict_differences" in res:
        out += ["### Verdict differences, 0.4.0 against 0.3.0", ""]
        diffs = res["version_verdict_differences"]
        if diffs:
            out += [md_table(["case", "faulty 0.4.0", "faulty 0.3.0", "fixed 0.4.0", "fixed 0.3.0", "flags differ"],
                             [[d["case"], d["faulty_v040"], d["faulty_v030"], d["fixed_v040"], d["fixed_v030"],
                               "yes" if d["flags_differ"] else "no"] for d in diffs]), ""]
        else:
            out += ["none", ""]
    out += ["## 3. Awareness of the world author (descriptive, no bounds, no verdict)", ""]
    rows = []
    for level, groups in res["awareness"].items():
        for label, c in groups.items():
            rows.append([level, label, c["pairs"], c["detections"], c["generic"], c["declared"], c["k2_only"], c["clean_passes"]])
    out += [md_table(["level", "class", "pairs", "detections", "generic", "declared", "K2-only", "clean passes"], rows), ""]
    out += ["## 4. Run times (seconds per check)", ""]
    rows = []
    for version, t in res["runtimes"].items():
        rows.append([version, t["checks_with_time"], fmt(t["min"], 1), fmt(t["median"], 1), fmt(t["max"], 1), len(t["beyond_3600_s"])])
    out += [md_table(["version", "checks", "min", "median", "max", "beyond 3600 s"], rows), ""]
    for version, t in res["runtimes"].items():
        if t["beyond_3600_s"]:
            out += [f"Beyond 3600 s ({version}): " + ", ".join(
                f"{d['case']}/{d['twin']} ({fmt(d['seconds'], 1)} s{', timeout' if d['timed_out'] else ''})"
                for d in t["beyond_3600_s"]), ""]
    out += ["## 5. Pairs", ""]
    rows = []
    for p in res["pairs"]:
        label = "-"
        if p["detected"]:
            label = p["label"] + (", K2-only" if p["k2_only"] else "")
        secs = f"{fmt(p['faulty_seconds'], 1)} / {fmt(p['fixed_seconds'], 1)}"
        rows.append([
            p["case"], p["class"], p["subtype"] or "-", p["world_id"], p["awareness"], p["faulty_verdict"],
            "yes" if p["detected"] else "no", label, ", ".join(p["expected_present"]) or "-", p["fixed_verdict"],
            "yes" if p["clean"] else "no", "-" if p["clean"] else (", ".join(p["fixed_flags"]) or "-"), secs])
    out += [md_table(["case", "class", "subtype", "world", "awareness", "faulty verdict", "detected", "label",
                      "expected flags present", "fixed verdict", "clean pass", "fixed flags (failures)", "seconds faulty / fixed"], rows), ""]
    return "\n".join(out)


def write_outputs(out: str, res: dict) -> None:
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "RESULTS.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(res, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
    with open(os.path.join(out, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(res))


def cmd_report(args: argparse.Namespace) -> int:
    out = os.path.abspath(args.out) if args.out else DEFAULT_OUT
    expected = os.path.abspath(args.expected) if args.expected else DEFAULT_EXPECTED
    awareness = os.path.abspath(args.awareness) if args.awareness else DEFAULT_AWARENESS
    res = build_results(out, expected, awareness)
    write_outputs(out, res)
    g = res["gate"]["classes"]
    for label, c in g.items():
        print(f"{label}: pairs {c['pairs']}, detections {c['detections']}, clean {c['clean_passes']}, "
              f"lower bounds {fmt(c['detection_lower'])} / {fmt(c['clean_lower'])}, {c['verdict']}")
    print(f"wrote {os.path.join(out, 'RESULTS.json')} and {os.path.join(out, 'RESULTS.md')}")
    return 0


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def _score_lower_bisect(k: int, n: int, z: float) -> float:
    """Independent computation: the p below k/n at which the score statistic (k/n - p) / sqrt(p(1-p)/n) equals z."""
    phat = k / n
    lo, hi = 0.0, phat
    for _ in range(200):
        mid = (lo + hi) / 2
        stat = (phat - mid) / math.sqrt(mid * (1 - mid) / n) if 0 < mid < 1 else float("inf")
        if stat > z:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _synthetic_cert(verdict: str, comp_flags: list) -> dict:
    return {"body": {"verdict": verdict, "study_flags": [], "load_error": None, "tool_version": "0.4.0",
                     "components": [{"id": f"c{i}", "verdict": verdict, "flags": f} for i, f in enumerate(comp_flags)]},
            "body_sha256": "synthetic", "created_utc": "synthetic"}


def cmd_selftest(_: argparse.Namespace) -> int:
    import tempfile
    failures: list = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(("ok    " if cond else "FAIL  ") + name + (f"  {detail}" if detail else ""))
        if not cond:
            failures.append(name)

    # Wilson: references 9/10 = 0.6523, 8/10 = 0.5408, 10/10 = 0.7870, and an independent bisection
    for k, ref in ((9, 0.6523), (8, 0.5408), (10, 0.7870)):
        lb = wilson_lower(k, 10)
        check(f"wilson {k}/10 = {lb:.4f} (reference {ref})", abs(lb - ref) < 1.5e-4)
        ind = _score_lower_bisect(k, 10, Z95) if k < 10 else 10 / (10 + Z95 ** 2)
        check(f"wilson {k}/10 matches independent score-test solution {ind:.6f}", abs(lb - ind) < 1e-9)
    check("wilson 0/0 is undefined", wilson_lower(0, 0) is None)

    exp_flags = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS",
                 "K5_HOLDS_ON_NOISE", "K5_HOLDS_ON_NULL", "K5_HOLDS_ON_SHUFFLE", "HIGH_RATE:probe:noise",
                 "HIGH_RATE:world:null", "HIGH_RATE:control:c1"]
    # (case, class, subtype, in_scope, world, faulty (verdict, comp flags, seconds), fixed (verdict, comp flags, seconds))
    spec = [
        ("T01", "B-1", "", True, "W01", ("NOT_FALSIFIABLE", [["K4_CONTROL_ALSO_HOLDS"]], 10), ("FALSIFIABLE", [[]], 10)),
        ("T02", "B-1", "", True, "W02", ("NOT_FALSIFIABLE", [["K5_HOLDS_ON_NOISE", "K2_HIGH_SIZE"]], 20), ("WEAK", [["K2_LOW_POWER"]], 20)),
        ("T03", "B-1", "", True, "W03", ("NOT_FALSIFIABLE", [["K2_NO_SEPARATION"], ["K2_FAILS_UNREACHABLE"]], 30), ("NOT_FALSIFIABLE", [["K4_CONTROL_ALSO_HOLDS"]], 30)),
        ("T04", "B-1", "", True, "W04", ("NOT_FALSIFIABLE", [["K3_PREMISE_NOT_TESTED"]], 40), ("FALSIFIABLE", [[]], 40)),
        ("T05", "B-1", "", True, "W05", ("WEAK", [["K5_HOLDS_ON_NULL"]], 50), ("UNTESTED", [[]], 50)),
        ("T06", "B-1", "", True, "W06", ("TIMEOUT", None, 3600.0), ("FALSIFIABLE", [[]], 60)),
        ("T07", "B-1", "", True, "W07", ("NOT_FALSIFIABLE", [["HIGH_RATE:probe:noise"]], 4000.0), ("FALSIFIABLE", [[]], 70)),
        ("T08", "B-1", "", True, "W08", ("MISSING", None, None), ("MISSING", None, None)),
        ("T09", "B-1", "", True, "W09", ("NOT_FALSIFIABLE", [["HIGH_RATE:control:c1", "HIGH_RATE:probe:zeros"]], 90), ("FALSIFIABLE", [[]], 3000.0)),
        ("T10", "B-1", "", True, "W10", ("UNDEFINED", [[]], 100), ("FALSIFIABLE", [[]], 100)),
        ("T11", "B-1", "", True, "W11", ("NOT_FALSIFIABLE", [["K5_HOLDS_ON_NULL"]], 110), ("FALSIFIABLE", [[]], 110)),
        ("T12", "B-1", "", True, "W12", ("NOT_FALSIFIABLE", [["K5_HOLDS_ON_SHUFFLE"]], 120), ("FALSIFIABLE", [[]], 120)),
        ("T13", "O", "O-1", False, "W13", ("NOT_FALSIFIABLE", [["K5_HOLDS_ON_NOISE"]], 130), ("FALSIFIABLE", [[]], 130)),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "run")
        exp = {"note": "synthetic", "base": [], "cases": {}}
        for case, cls, sub, scope, wid, f, x in spec:
            exp["cases"][case] = {"local_id": case, "world_id": wid, "class": cls, "subtype": sub, "source": "S",
                                  "in_scope": scope, "expected": exp_flags}
            for version in ("v040", "v030"):
                for twin, (verdict, flags, secs) in (("faulty", f), ("fixed", x)):
                    p = cert_path(out, version, case, twin)
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    if verdict not in ("MISSING", "TIMEOUT") and version == "v040":
                        with open(p, "w", encoding="utf-8") as h:
                            json.dump(_synthetic_cert(verdict, flags), h)
                    elif version == "v030" and verdict not in ("MISSING", "TIMEOUT"):
                        # 0.3.0 baseline: same certificates, except T01 faulty is UNTESTED
                        v = "UNTESTED" if (case == "T01" and twin == "faulty") else verdict
                        with open(p, "w", encoding="utf-8") as h:
                            json.dump(_synthetic_cert(v, flags), h)
                    if secs is not None:
                        with open(runlog_path(out, version), "a", encoding="utf-8") as h:
                            h.write(json.dumps({"version": version, "case": case, "twin": twin, "seconds": secs,
                                                "timed_out": verdict == "TIMEOUT", "exit_code": 0}) + "\n")
        exp_path = os.path.join(tmp, "expected.json")
        with open(exp_path, "w", encoding="utf-8") as h:
            json.dump(exp, h)
        aw_path = os.path.join(tmp, "AWARENESS.md")
        with open(aw_path, "w", encoding="utf-8") as h:
            h.write("| Level | Ids | Count |\n|---|---|---|\n| P | W01 W02 W03 W04 W05 W06 W07 W08 | 8 |\n"
                    "| C | W09 (considered) W10 | 2 |\n| N | W11 W12 W13 | 3 |\n")
        res = build_results(out, exp_path, aw_path)
        pairs = {p["case"]: p for p in res["pairs"]}
        check("T01 declared detection, clean pass", pairs["T01"]["detected"] and pairs["T01"]["label"] == "declared"
              and not pairs["T01"]["k2_only"] and pairs["T01"]["clean"])
        check("T02 generic detection (K5_HOLDS_ON_NOISE), WEAK fixed is a clean pass",
              pairs["T02"]["label"] == "generic" and pairs["T02"]["clean"])
        check("T03 K2-only detection and failed clean pass",
              pairs["T03"]["detected"] and pairs["T03"]["k2_only"] and pairs["T03"]["label"] == "declared" and not pairs["T03"]["clean"]
              and pairs["T03"]["fixed_flags"] == ["K4_CONTROL_ALSO_HOLDS"])
        check("T04 NOT_FALSIFIABLE with a non-expected flag is a miss", not pairs["T04"]["detected"])
        check("T05 miss by WEAK verdict even with an expected flag", not pairs["T05"]["detected"] and not pairs["T05"]["clean"]
              and pairs["T05"]["fixed_verdict"] == "UNTESTED")
        check("T06 miss by timeout (no certificate)", not pairs["T06"]["detected"] and pairs["T06"]["faulty_verdict"] == "TIMEOUT")
        check("T07 miss by run beyond 3600 s although a certificate exists", not pairs["T07"]["detected"]
              and pairs["T07"]["faulty_verdict"] == "TIMEOUT")
        check("T08 missing certificates: miss and failed clean pass", not pairs["T08"]["detected"] and not pairs["T08"]["clean"]
              and pairs["T08"]["faulty_verdict"] == "MISSING")
        check("T09 expected control flag detects, non-expected probe:zeros ignored", pairs["T09"]["detected"]
              and pairs["T09"]["expected_present"] == ["HIGH_RATE:control:c1"])
        check("T09 fixed run beyond 3600? no (3000 s): clean pass holds", pairs["T09"]["clean"])
        check("T10 UNDEFINED is a miss", not pairs["T10"]["detected"])
        c = res["gate"]["classes"]["B-1"]
        check("B-1 counts: 12 pairs, 6 detections (T01 T02 T03 T09 T11 T12)", (c["pairs"], c["detections"]) == (12, 6), str((c["pairs"], c["detections"])))
        check("B-1 generic 1, declared 5, K2-only 1", (c["generic"], c["declared"], c["k2_only"]) == (1, 5, 1),
              str((c["generic"], c["declared"], c["k2_only"])))
        check("B-1 clean passes 9 (T01 T02 T04 T06 T07 T09 T10 T11 T12)", c["clean_passes"] == 9, str(c["clean_passes"]))
        check("B-1 verdict FAILS", c["verdict"] == "FAILS")
        check("B-2 has no pairs and FAILS", res["gate"]["classes"]["B-2"]["pairs"] == 0 and res["gate"]["classes"]["B-2"]["verdict"] == "FAILS")
        check("out-of-scope O-1: counts only, no bounds", "detection_lower" not in res["gate"]["out_of_scope"]["O-1"]
              and res["gate"]["out_of_scope"]["O-1"]["detections"] == 1)
        noise = res["baselines"]["noise_only"]["classes"]["B-1"]["detections"]
        decl = res["baselines"]["declared_only"]["classes"]["B-1"]["detections"]
        check("noise-only detections = 1 (T02)", noise == 1, str(noise))
        check("declared-only detections = 6 (T01 T02 T03 T09 T11 T12; T02 has K2_HIGH_SIZE)", decl == 6, str(decl))
        fe = res["baselines"]["flag_everything"]["classes"]["B-1"]
        check("flag-everything: 12 detections, 0 clean", (fe["detections"], fe["clean_passes"]) == (12, 0))
        diffs = res["version_verdict_differences"]
        check("0.3.0 differences list exactly T01", [d["case"] for d in diffs] == ["T01"])
        aw = res["awareness"]
        check("awareness P/C/N parsed", aw["P"]["all"]["pairs"] == 8 and aw["C"]["all"]["pairs"] == 2 and aw["N"]["all"]["pairs"] == 3,
              str({k: v["all"]["pairs"] for k, v in aw.items()}))
        rt = res["runtimes"]["v040"]
        check("run times: max 4000 s, one check beyond 3600 s plus the timeout", rt["max"] == 4000.0
              and [d["case"] for d in rt["beyond_3600_s"]] == ["T06", "T07"], str(rt))
        # a perfect class: 10/10 and 10/10 HOLDS, 9/10 and 10/10 FAILS... checked through add_bounds
        perfect = add_bounds({"pairs": 10, "detections": 10, "clean_passes": 10})
        nine = add_bounds({"pairs": 10, "detections": 9, "clean_passes": 10})
        eight = add_bounds({"pairs": 10, "detections": 8, "clean_passes": 10})
        few = add_bounds({"pairs": 5, "detections": 5, "clean_passes": 5})
        check("10/10 and 10/10 HOLDS", perfect["verdict"] == "HOLDS")
        check("9/10 detections and 10/10 clean HOLDS (0.6523 >= 0.6)", nine["verdict"] == "HOLDS")
        check("8/10 detections FAILS (0.5408 < 0.6)", eight["verdict"] == "FAILS")
        check("5 pairs always FAILS (pairs < 10)", few["verdict"] == "FAILS")
        # determinism: two builds give byte-identical files
        write_outputs(out, res)
        a = [open(os.path.join(out, n), "rb").read() for n in ("RESULTS.json", "RESULTS.md")]
        write_outputs(out, build_results(out, exp_path, aw_path))
        b = [open(os.path.join(out, n), "rb").read() for n in ("RESULTS.json", "RESULTS.md")]
        check("report is byte-identical on a second build", a == b)
    print("selftest: " + ("all passed" if not failures else f"{len(failures)} FAILED"))
    return 0 if not failures else 1


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run the gate on every twin of every case")
    run.add_argument("--version", required=True, choices=sorted(VERSIONS))
    run.add_argument("--worktree", required=True, help="git worktree of the tag")
    run.add_argument("--cases-dir", default=None, help="default: evaluation/phase_b/cases")
    run.add_argument("--expected", default=None, help="default: evaluation/phase_b/EXPECTED_FLAGS.json")
    run.add_argument("--out", default=None, help="default: evaluation/phase_b/run")
    run.add_argument("--timeout", type=float, default=TIME_LIMIT, help="seconds per check (default 3600)")
    run.add_argument("--redo", action="store_true", help="re-run checks that are already done")
    rep = sub.add_parser("report", help="write RESULTS.json and RESULTS.md")
    rep.add_argument("--out", default=None, help="default: evaluation/phase_b/run")
    rep.add_argument("--expected", default=None, help="default: evaluation/phase_b/EXPECTED_FLAGS.json")
    rep.add_argument("--awareness", default=None, help="default: evaluation/phase_b/record/world/AWARENESS.md")
    sub.add_parser("selftest", help="check the metric code on synthetic certificates")
    return parser


def main(argv: "list | None" = None) -> int:
    args = build_parser().parse_args(argv)
    return {"run": cmd_run, "report": cmd_report, "selftest": cmd_selftest}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
