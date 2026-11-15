#!/usr/bin/env python3
"""Phase C runner and reporter (``PREREG_PHASE_C.md`` sections 6 and 7, ``REVISIONS-post-freeze.md`` P-7).

Adapted from ``evaluation/phase_b/run_phase_b.py`` (same structure, metric code, CLI style, determinism and selftest).

Sub-commands
------------
``run``       run the gate of one version (``v050`` = tag v0.5.0, ``v041`` = tag v0.4.1) on every twin of every case, in
              full mode, default settings, one check at a time, and store certificates, logs and a run log.
``report``    compute ``RESULTS.json`` and ``RESULTS.md`` from the certificates, the run logs and the inputs of P-7 item 6
              only.  Same inputs give byte-identical outputs.
``selftest``  check the metric code on synthetic certificates (no gate, no case file is touched).

Usage (from the repository root)::

    git worktree add --detach <DIR050> v0.5.0     # the designer creates the worktrees; this script only checks them
    git worktree add --detach <DIR041> v0.4.1
    py evaluation/phase_c/run_phase_c.py run --version v050 --worktree <DIR050> [--timeout 3600] [--redo]
    py evaluation/phase_c/run_phase_c.py run --version v041 --worktree <DIR041>
    py evaluation/phase_c/run_phase_c.py report
    py evaluation/phase_c/run_phase_c.py selftest

Options of ``run``: ``--cases-dir`` (default ``evaluation/phase_c/cases``), ``--expected`` (default
``evaluation/phase_c/EXPECTED_FLAGS.json``), ``--out`` (default ``evaluation/phase_c/run``), ``--timeout`` seconds
(default 3600), ``--redo``.  Layout under ``--out``: ``certs/<version>/<case>/<twin>.json``,
``logs/<version>/<case>/<twin>.txt`` (last 40 lines of stdout and stderr of the last attempt; ``<twin>.attempt1.txt``
when a first attempt was an infrastructure failure), ``runlog_<version>.jsonl``.

Run rules (P-7 items 1 and 2)
-----------------------------
* The worktree must be at the commit of the tag (``git rev-parse <tag>^{commit}``) and ``git status --porcelain`` must be
  empty, else the run is refused.  Both commits are written into every run-log line (``tag_commit``, ``worktree_head``).
* A check has a per-check timeout of 3600 s.  A timeout is a result and is not repeated.  A gate exit (0-7) with no
  certificate is a result and is not repeated.  An **infrastructure failure** is a check that ends without a certificate
  and with an exit code outside 0-7, a runner crash, or an attempt that left a ``start`` line in the run log without a
  result line (crash of the runner or the machine; recorded as a failed attempt when the run is resumed).  It is rerun
  once; both attempts are logged (``attempt`` 1 and 2).  After a second failure the check stays an infrastructure
  failure (no certificate, counted as a miss or a failed clean pass); ``--redo`` starts a new round.
* A check is skipped when its last run-log result is final (certificate present or recorded as absent for a gate exit or
  timeout); ``--redo`` forces every check.  Before the real run the case freeze is verified
  (``protocol/tools/freeze.py verify FREEZE_CASES.json`` must exit 0); the verification is skipped only when
  ``--cases-dir`` is not the default, and that is printed.

Rules implemented by ``report`` (PREREG_PHASE_C section 6 with P-7; PB section 6 where it says "as PB")
--------------------------------------------------------------------------------------------------------
* Expected flags: the per-case list in ``EXPECTED_FLAGS.json``; a flag counts when a component of the certificate carries
  exactly that string.  **Information flags** (``K1_ABSTAINED:*``, ``K2_MINUS_UNREAD``, ``K8_SOME_CHANGES``,
  ``BAD_RETURN``) and the **capping flag** ``K1_ABSTAINED_MAJORITY:*`` never count (``is_information_flag``): they are
  removed from the certificate's flags and from the expected list before any detection is computed.
* Detection, label (generic / declared, K2-only), clean pass, Wilson bounds and HOLDS/FAILS as PB section 6, computed with
  0.5.0 (the pre-registered primary table) and with 0.4.1 (full table, same way).  Every non-dropped pair counts.
* Baselines: flag everything, noise-only and declared-only (0.5.0 certificates, second line from 0.4.1).
* Primary comparison (one component per file; ``classify_cause`` is P-7 item 3); "not informative" when fewer than 5 study
  files have a component UNDEFINED under 0.4.1; losses are reported loudly in either case.
* Abstention share (P-7 item 4), awareness breakdown (both readings and resolved), overlap and addendum counts, Phase B
  next to Phase C, per-pair table with the label "error too small in the declared worlds at this size" (P-7 item 5).
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

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PHASE_C = HERE
PHASE_B = os.path.join(ROOT, "evaluation", "phase_b")
DEFAULT_CASES = os.path.join(PHASE_C, "cases")
DEFAULT_OUT = os.path.join(PHASE_C, "run")
FREEZE_CASES = os.path.join(PHASE_C, "FREEZE_CASES.json")
FREEZE_TOOL = os.path.join(ROOT, "protocol", "tools", "freeze.py")
DEFAULT_INPUTS = {
    "expected": os.path.join(PHASE_C, "EXPECTED_FLAGS.json"),
    "awareness": os.path.join(PHASE_C, "record", "designer", "AWARENESS_RESULT.json"),
    "lines": os.path.join(PHASE_C, "record", "designer", "DESIGNER_LINES.json"),
    "addendum": os.path.join(PHASE_C, "SOURCES_ADDENDUM.md"),
    "phase_b_results": os.path.join(PHASE_B, "run", "RESULTS.json"),
    "phase_b_expected": os.path.join(PHASE_B, "EXPECTED_FLAGS.json"),
    "r1_certs": os.path.join(ROOT, "evaluation", "r1_v050", "certs"),
}
DEFAULT_DEFAULT_EXPECTED = DEFAULT_INPUTS["expected"]

VERSIONS = {
    "v050": {"tag": "v0.5.0", "module": "truth_gate", "tool_version": "0.5.0"},
    "v041": {"tag": "v0.4.1", "module": "truth_gate", "tool_version": "0.4.1"},
}
PRIMARY = "v050"
SECOND = "v041"
VERSION_LABEL = {"v050": "0.5.0", "v041": "0.4.1"}
TWINS = ("faulty", "fixed")

Z95 = 1.6448536269514722        # one-sided 95%
THRESHOLD = 0.6
MIN_PAIRS = 10
TIME_LIMIT = 3600.0             # P-7 item 2: per-check timeout; a check beyond it is a miss / failed clean pass
TAIL_LINES = 40
GATE_EXIT_CODES = range(0, 8)   # P-7 item 2: gate exit codes 0-7
MAX_ATTEMPTS = 2                # P-7 item 2: an infrastructure failure is rerun once

NOISE_FLAGS = frozenset({"K5_HOLDS_ON_NOISE", "HIGH_RATE:probe:noise"})
K2_FLAGS = frozenset({"K2_NO_SEPARATION", "K2_FAILS_UNREACHABLE"})
# PREREG_PHASE_C section 6: these never count as an expected flag, whatever the expected list says.
INFORMATION_FLAGS = frozenset({"K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN"})
INFORMATION_PREFIXES = ("K1_ABSTAINED:",)
CAPPING_PREFIXES = ("K1_ABSTAINED_MAJORITY:",)
CLEAN_VERDICTS = ("FALSIFIABLE", "WEAK")
IN_SCOPE_CLASSES = ("B-1", "B-2", "B-3", "B-6")
B2_SUBTYPES = ("L1.1", "L1.2", "L1.3", "L1.4", "L3.1", "L3.2")
OUT_OF_SCOPE_LABELS = ("O-1", "O-2", "O-3")
K1_STREAMS = ("world:plus", "world:minus", "world:null")      # P-7 items 3 and 4

INFORMATIVE_MIN_FILES = 5       # PREREG_PHASE_C section 6: fewer files with an UNDEFINED component = not informative
NEW_SOURCE_MIN = 4              # PREREG_PHASE_C section 1: at least 4 of the 12 planned pairs on addendum sources
# PREREG_PHASE_C section 1: the source keys of SOURCES_ADDENDUM.md (the report also parses that file and checks it)
ADDENDUM_SOURCES = frozenset({"KRI10", "MOR03", "VAR06", "CUR13", "LAZ18"})
# P-7 item 5: nominal level plus two standard errors; a miss with no expected flag whose world:minus rate is at most this.
TOO_SMALL_NOMINAL = 0.05
TOO_SMALL_SE_MULTIPLIER = 2.0
TOO_SMALL_LABEL = "error too small in the declared worlds at this size"
AWARENESS_WORDS = "declared worlds that may contain what the error exploits"
OVERLAP_WORDING = "largely repeats Phase B settings with a new world author"
AWARENESS_LEVELS = ("P", "C", "N")
CAUSES = ("hard", "plus majority", "soft only", "unknown")


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


def too_small_bound(n: int) -> float:
    """P-7 item 5: 0.05 + 2 * sqrt(0.05 * 0.95 / n)  (0.0808 at n = 200)."""
    return TOO_SMALL_NOMINAL + TOO_SMALL_SE_MULTIPLIER * math.sqrt(TOO_SMALL_NOMINAL * (1.0 - TOO_SMALL_NOMINAL) / n)


def fmt(x: "float | None", digits: int = 4) -> str:
    return "-" if x is None else f"{x:.{digits}f}"


def rnd(x: "float | None", digits: int = 6) -> "float | None":
    return None if x is None else round(x, digits)


def share(k: int, n: int) -> "float | None":
    return None if n <= 0 else rnd(k / n)


# --------------------------------------------------------------------------
# Flags
# --------------------------------------------------------------------------

def is_information_flag(flag: str) -> bool:
    """Information flags and the capping flag never count as an expected flag (PREREG_PHASE_C section 6)."""
    return (flag in INFORMATION_FLAGS or any(flag.startswith(p) for p in INFORMATION_PREFIXES)
            or any(flag.startswith(p) for p in CAPPING_PREFIXES))


def counted_flags(flags) -> list:
    return sorted(f for f in flags if not is_information_flag(f))


# --------------------------------------------------------------------------
# Paths and shared file helpers
# --------------------------------------------------------------------------

def cert_path(out: str, version: str, case: str, twin: str) -> str:
    return os.path.join(out, "certs", version, case, twin + ".json")


def log_path(out: str, version: str, case: str, twin: str, attempt: "int | None" = None) -> str:
    name = twin + ("" if attempt is None else f".attempt{attempt}") + ".txt"
    return os.path.join(out, "logs", version, case, name)


def runlog_path(out: str, version: str) -> str:
    return os.path.join(out, f"runlog_{version}.jsonl")


def load_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_expected(path: str) -> dict:
    return load_json(path)["cases"]


def read_runlog_lines(out: str, version: str) -> list:
    """Every run-log line in file order (``start`` lines and result lines)."""
    path = runlog_path(out, version)
    lines: list = []
    if not os.path.isfile(path):
        return lines
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def result_lines(lines: list) -> list:
    return [row for row in lines if row.get("event", "result") == "result"]


def final_rows(lines: list) -> dict:
    """``{(case, twin): last result line}``; later lines win."""
    result: dict = {}
    for row in result_lines(lines):
        result[(row["case"], row["twin"])] = row
    return result


def append_runlog(out: str, version: str, row: dict) -> None:
    with open(runlog_path(out, version), "a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def read_certificate(path: str) -> "tuple[str, dict | None]":
    """``(status, body)``: ``missing``, ``invalid`` or ``ok``."""
    if not os.path.isfile(path):
        return "missing", None
    try:
        envelope = load_json(path)
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


def verify_worktree(version: str, worktree: str) -> "tuple[str, str]":
    """P-7 item 1: HEAD at the tag's commit and a clean tree; returns ``(tag_commit, head)``."""
    tag = VERSIONS[version]["tag"]
    rc1, tag_commit = _git("rev-parse", f"{tag}^{{commit}}")
    rc2, head = _git("-C", worktree, "rev-parse", "HEAD")
    if rc1 != 0 or rc2 != 0:
        raise SystemExit(f"cannot resolve {tag} or the worktree HEAD ({worktree})")
    if tag_commit != head:
        raise SystemExit(f"worktree {worktree} is at {head}, but {tag} is {tag_commit}: refusing to run")
    rc3, porcelain = _git("-C", worktree, "status", "--porcelain")
    if rc3 != 0:
        raise SystemExit(f"git status failed in {worktree}: refusing to run")
    if porcelain:
        raise SystemExit(f"worktree {worktree} is not clean (git status --porcelain is not empty): refusing to run")
    print(f"worktree ok: {worktree} is at {tag} ({head[:12]}), clean")
    return tag_commit, head


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
    return {"exit_code": proc.returncode, "seconds": seconds, "timed_out": timed_out, "output": output or "", "crash": None}


def is_infrastructure_failure(has_certificate: bool, timed_out: bool, exit_code: "int | None", crash: "str | None") -> bool:
    """P-7 item 2: no certificate and an exit code outside 0-7 (or no exit code), or a runner crash.  A timeout is a
    result; a gate exit (0-7) without a certificate is a result."""
    if timed_out or has_certificate:
        return False
    return crash is not None or exit_code is None or exit_code not in GATE_EXIT_CODES


def next_attempt(prior: "dict | None", cert_exists: bool, redo: bool) -> "int | None":
    """The attempt number to run for a check, or None when its last result is final."""
    if redo or prior is None:
        return 1
    if prior.get("has_certificate") and not cert_exists:
        return 1                                    # the certificate the log speaks of is gone
    attempt = int(prior.get("attempt", 1))
    if prior.get("infra_failure") and attempt < MAX_ATTEMPTS:
        return attempt + 1
    return None


def recover_dangling(out: str, version: str) -> int:
    """A ``start`` line with no result line after it is an attempt that died with the runner or the machine: record it as
    an infrastructure failure so that the resumed check counts it (P-7 item 2)."""
    lines = read_runlog_lines(out, version)
    last_by_check: dict = {}
    for row in lines:
        last_by_check[(row["case"], row["twin"])] = row
    recovered = 0
    for (case, twin), row in sorted(last_by_check.items()):
        if row.get("event") == "start":
            append_runlog(out, version, {
                "event": "result", "version": version, "case": case, "twin": twin, "attempt": row.get("attempt", 1),
                "exit_code": None, "seconds": None, "timed_out": False, "has_certificate": False, "infra_failure": True,
                "verdict": "INFRASTRUCTURE_FAILURE", "note": "start line without a result line: runner or machine crash"})
            recovered += 1
    return recovered


def cmd_run(args: argparse.Namespace) -> int:
    version = args.version
    cases_dir = os.path.abspath(args.cases_dir) if args.cases_dir else DEFAULT_CASES
    expected_path = os.path.abspath(args.expected) if args.expected else DEFAULT_DEFAULT_EXPECTED
    out = os.path.abspath(args.out) if args.out else DEFAULT_OUT
    worktree = os.path.abspath(args.worktree)
    tool_version = VERSIONS[version]["tool_version"]
    verify_case_freeze(cases_dir)
    tag_commit, head = verify_worktree(version, worktree)
    expected = load_expected(expected_path)
    cases = discover_cases(cases_dir, expected)
    missing = sorted(set(expected) - set(cases))
    if missing:
        print(f"note: expected-flags entries without a case folder: {', '.join(missing)}")
    os.makedirs(out, exist_ok=True)
    recovered = recover_dangling(out, version)
    if recovered:
        print(f"note: {recovered} earlier attempt(s) left a start line without a result; logged as infrastructure failures")
    last = final_rows(read_runlog_lines(out, version))
    total = len(cases) * len(TWINS)
    index = 0
    for case in cases:
        for twin in TWINS:
            index += 1
            cert = cert_path(out, version, case, twin)
            attempt = next_attempt(last.get((case, twin)), os.path.isfile(cert), args.redo)
            if attempt is None:
                print(f"[{index}/{total}] {case} {twin}: skip (already done: {last[(case, twin)].get('verdict')})")
                continue
            os.makedirs(os.path.dirname(cert), exist_ok=True)
            os.makedirs(os.path.dirname(log_path(out, version, case, twin)), exist_ok=True)
            study = os.path.join(cases_dir, case, twin + ".py")
            while True:
                if os.path.isfile(cert):
                    os.remove(cert)     # never mistake a stale certificate for the result of this run
                append_runlog(out, version, {"event": "start", "version": version, "case": case, "twin": twin, "attempt": attempt})
                try:
                    result = run_one(version, worktree, study, cert, args.timeout)
                except Exception as exc:  # noqa: BLE001 - a crash of the runner is an infrastructure failure
                    result = {"exit_code": None, "seconds": 0.0, "timed_out": False, "output": f"runner crash: {exc!r}\n",
                              "crash": repr(exc)}
                status, body = read_certificate(cert)
                has_certificate = os.path.isfile(cert)
                infra = is_infrastructure_failure(has_certificate, result["timed_out"], result["exit_code"], result["crash"])
                if body:
                    verdict = body["verdict"]
                elif result["timed_out"]:
                    verdict = "TIMEOUT"
                elif infra:
                    verdict = "INFRASTRUCTURE_FAILURE"
                elif has_certificate:
                    verdict = "INVALID"
                else:
                    verdict = "NO_CERTIFICATE"
                tail = _tail(result["output"]) + "\n"
                with open(log_path(out, version, case, twin), "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(tail)
                if infra and attempt < MAX_ATTEMPTS:
                    with open(log_path(out, version, case, twin, attempt), "w", encoding="utf-8", newline="\n") as handle:
                        handle.write(tail)
                row = {
                    "event": "result", "version": version, "tag": VERSIONS[version]["tag"], "case": case, "twin": twin,
                    "study": study.replace("\\", "/"), "tag_commit": tag_commit,
                    "worktree_head": _git("-C", worktree, "rev-parse", "HEAD")[1], "attempt": attempt,
                    "exit_code": result["exit_code"], "seconds": round(result["seconds"], 3),
                    "timed_out": result["timed_out"], "timeout_limit": args.timeout, "verdict": verdict,
                    "has_certificate": has_certificate, "infra_failure": infra,
                    "tool_version": body.get("tool_version") if body else None,
                }
                append_runlog(out, version, row)
                last[(case, twin)] = row
                print(f"[{index}/{total}] {case} {twin}: {verdict} (exit {result['exit_code']}) {result['seconds']:.1f} s"
                      + (" TIMEOUT" if result["timed_out"] else "")
                      + (f" INFRASTRUCTURE FAILURE (attempt {attempt} of {MAX_ATTEMPTS})" if infra else ""))
                sys.stdout.flush()
                if body and body.get("tool_version") != tool_version:
                    raise SystemExit(f"{case} {twin}: certificate says tool_version {body.get('tool_version')!r}, "
                                     f"not {tool_version!r}: the worktree is not the gate under test")
                if infra and attempt < MAX_ATTEMPTS:
                    attempt += 1
                    continue
                break
    rc, porcelain = _git("-C", worktree, "status", "--porcelain")
    if rc != 0 or porcelain:
        print("WARNING: the worktree is not clean after the run (git status --porcelain is not empty)")
    print("run finished")
    return 0


# --------------------------------------------------------------------------
# report: per-check and per-pair evaluation
# --------------------------------------------------------------------------

def load_check(out: str, version: str, case: str, twin: str, last: dict, lines: list) -> dict:
    """One check: status (ok / timeout / missing / invalid), verdict, flags, components, seconds, run-log facts."""
    status, body = read_certificate(cert_path(out, version, case, twin))
    row = last.get((case, twin))
    seconds = row.get("seconds") if row else None
    if (row and row.get("timed_out")) or (seconds is not None and seconds > TIME_LIMIT):
        status = "timeout"
    attempts = [r for r in result_lines(lines) if (r["case"], r["twin"]) == (case, twin)]
    comps: list = []
    all_flags: list = []
    verdict = None
    load_error = False
    tool_version = None
    if status == "ok" and body is not None:
        verdict = body["verdict"]
        load_error = bool(body.get("load_error"))
        tool_version = body.get("tool_version")
        seen = set()
        for comp in body["components"]:
            counts = comp.get("counts") or {}
            k1 = {}
            for stream in K1_STREAMS:
                c = counts.get(stream)
                if isinstance(c, dict):
                    k1[stream] = {k: int(c.get(k, 0)) for k in ("n", "holds", "undefined", "hard_undefined")}
            flags = sorted(comp.get("flags") or [])
            seen.update(flags)
            comps.append({"id": comp.get("id"), "regime": comp.get("regime"), "verdict": comp.get("verdict"),
                          "flags": flags, "k1": k1})
        all_flags = sorted(seen)
    return {"status": status, "verdict": verdict, "flags": all_flags, "counted": counted_flags(all_flags),
            "components": comps, "seconds": seconds, "load_error": load_error, "tool_version": tool_version,
            "exit_code": row.get("exit_code") if row else None,
            "infra_failure": bool(row and row.get("infra_failure")),
            "attempts": len(attempts),
            "infra_attempts": sum(1 for r in attempts if r.get("infra_failure"))}


def shown_verdict(check: dict) -> str:
    if check["status"] == "ok":
        return check["verdict"] + (" (load error)" if check["load_error"] else "")
    if check["status"] == "missing" and check["infra_failure"]:
        return "MISSING (infrastructure failure)"
    if check["status"] == "missing" and check["exit_code"] is not None:
        return f"MISSING (gate exit {check['exit_code']})"
    return check["status"].upper()


def too_small_label(faulty: dict, present: list, detected: bool) -> dict:
    """P-7 item 5 with P-8 item 4: a miss whose faulty study verdict is WEAK or FALSIFIABLE, that carries no expected flag
    and whose ``world:minus`` rate holds / n (0.5.0) is at most ``0.05 + 2 * sqrt(0.05 * 0.95 / n)``.  Applied to a file
    with exactly one component; an UNDEFINED or NOT_FALSIFIABLE miss gets no label."""
    out = {"applies": False, "rate": None, "n": None, "bound": None}
    if faulty["status"] != "ok" or detected or present or len(faulty["components"]) != 1:
        return out
    if faulty["verdict"] not in CLEAN_VERDICTS:       # P-8 item 4: only a WEAK or FALSIFIABLE miss
        return out
    minus = faulty["components"][0]["k1"].get("world:minus")
    if not minus or minus["n"] <= 0:
        return out
    rate = minus["holds"] / minus["n"]
    bound = too_small_bound(minus["n"])
    out.update(rate=rnd(rate), n=minus["n"], bound=rnd(bound), applies=bool(rate <= bound))
    return out


def evaluate_pair(meta: dict, faulty: dict, fixed: dict) -> dict:
    expected = {f for f in meta["expected"] if not is_information_flag(f)}
    present = sorted(expected & set(faulty["counted"])) if faulty["status"] == "ok" else []
    f_nf = faulty["status"] == "ok" and faulty["verdict"] == "NOT_FALSIFIABLE"
    detected = f_nf and bool(present)
    non_noise = [f for f in present if f not in NOISE_FLAGS]
    noise = [f for f in present if f in NOISE_FLAGS]
    generic = bool(NOISE_FLAGS & set(faulty["counted"])) if faulty["status"] == "ok" else False
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
        "too_small": too_small_label(faulty, present, detected),
    }


def group_label(meta: dict) -> str:
    """Class label for grouping: the class of an in-scope case, the O-n subtype of an out-of-scope case."""
    if meta["in_scope"]:
        return meta["class"]
    return meta.get("subtype") or meta["class"]


def tally(pairs: list, kind: str) -> dict:
    """Counts for a list of evaluated pairs. kind: gate | flag_all | noise_only | declared_only."""
    n = len(pairs)
    clean = sum(1 for p in pairs if p["clean"])
    if kind == "gate":
        dets = [p for p in pairs if p["detected"]]
        return {
            "pairs": n, "detections": len(dets),
            "generic": sum(1 for p in dets if p["label"] == "generic"),
            "declared": sum(1 for p in dets if p["label"] == "declared"),
            "k2_only": sum(1 for p in dets if p["k2_only"]),
            "clean_passes": clean,
        }
    if kind == "flag_all":
        return {"pairs": n, "detections": n, "clean_passes": 0}
    if kind == "noise_only":
        return {"pairs": n, "detections": sum(1 for p in pairs if p["detected_noise_only"]), "clean_passes": clean}
    if kind == "declared_only":
        return {"pairs": n, "detections": sum(1 for p in pairs if p["detected_declared_only"]), "clean_passes": clean}
    raise ValueError(kind)


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


def class_groups(evals: list) -> "tuple[dict, dict, dict]":
    """Group pair evaluations: in-scope classes, B-2 subtypes, out-of-scope labels (each ``{label: [pairs]}``)."""
    classes = {c: [] for c in IN_SCOPE_CLASSES}
    subtypes = {s: [] for s in B2_SUBTYPES}
    outside: dict = {}
    for ev in evals:
        meta = ev["meta"]
        if meta["in_scope"]:
            classes.setdefault(meta["class"], []).append(ev)
            if meta["class"] == "B-2":
                subtypes.setdefault(meta["subtype"], []).append(ev)
        else:
            outside.setdefault(group_label(meta), []).append(ev)
    return classes, subtypes, dict(sorted(outside.items()))


def _descriptive(row: dict) -> dict:
    """P-8 item 5: a B-2 subtype row with fewer than 10 pairs is descriptive and is not a class verdict."""
    row = dict(row)
    row["descriptive"] = row["pairs"] < MIN_PAIRS
    row["class_verdict"] = False if row["descriptive"] else True
    return row


def metrics_table(evals: list, kind: str) -> dict:
    classes, subtypes, outside = class_groups(evals)
    return {
        "classes": {k: add_bounds(tally(v, kind)) for k, v in classes.items()},
        "b2_subtypes": {k: _descriptive(add_bounds(tally(v, kind))) for k, v in subtypes.items()},
        "out_of_scope": {k: tally(v, kind) for k, v in outside.items()},
    }


def class_members(evals: list) -> dict:
    """``{label: [evals]}`` for the in-scope classes and the out-of-scope labels, in report order."""
    classes, _, outside = class_groups(evals)
    members = dict(classes)
    members.update(outside)
    return members


# --------------------------------------------------------------------------
# report: awareness, overlap, abstention
# --------------------------------------------------------------------------

def awareness_shares(evals: list) -> dict:
    """Resolved P / C / N counts and shares of the given pairs; P includes 'no log' (shown separately)."""
    n = len(evals)
    counts = {lv: sum(1 for e in evals if e["aw_resolved"] == lv) for lv in AWARENESS_LEVELS}
    counts["?"] = sum(1 for e in evals if e["aw_resolved"] not in AWARENESS_LEVELS)
    no_log = sum(1 for e in evals if e["aw_no_log"])
    return {"pairs": n, "P": counts["P"], "C": counts["C"], "N": counts["N"], "unclassified": counts["?"], "no_log_in_P": no_log,
            "P_share": share(counts["P"], n), "C_share": share(counts["C"], n), "N_share": share(counts["N"], n)}


def awareness_breakdown(evals: list, reading: str) -> dict:
    """Pairs, detections and clean passes by awareness level and class for one reading (reader1, reader2, resolved)."""
    key = {"reader1": "aw_reader1", "reader2": "aw_reader2", "resolved": "aw_resolved"}[reading]
    levels = ["P", "C", "N", "no log"] if reading != "resolved" else ["P", "C", "N"]
    out: dict = {}
    for level in levels + ["?"]:
        rows = [e for e in evals if (e[key] == level if level != "?" else e[key] not in levels)]
        if not rows:
            continue
        out[level] = {"all": tally(rows, "gate")}
        for label, members in class_members(rows).items():
            if members:
                out[level][label] = tally(members, "gate")
    if reading == "resolved":
        rows = [e for e in evals if e["aw_no_log"]]
        if rows:
            out["no log (counted in P)"] = {"all": tally(rows, "gate")}
            for label, members in class_members(rows).items():
                if members:
                    out["no log (counted in P)"][label] = tally(members, "gate")
    return out


def overlap_summary(evals: list, addendum: frozenset) -> dict:
    """Per in-scope class: pairs, overlapping pairs, addendum-source pairs, and the P-7 item 7 wording rule."""
    out: dict = {}
    for label, members in class_members(evals).items():
        n = len(members)
        ov = sum(1 for e in members if e["overlap"])
        ad = sum(1 for e in members if e["meta"]["source"] in addendum)
        row = {"pairs": n, "overlapping_pairs": ov, "addendum_source_pairs": ad,
               "largely_repeats_phase_b": bool(n and 2 * ov > n)}
        if label in IN_SCOPE_CLASSES:
            row["new_source_minimum_met"] = ad >= NEW_SOURCE_MIN
        out[label] = row
    return out


def k1_abstention(components: list) -> "tuple[int, int]":
    """P-7 item 4: ``(sum of undefined - hard_undefined, sum of n)`` over the K1 streams of the components."""
    soft = den = 0
    for comp in components:
        for stream in K1_STREAMS:
            c = comp["k1"].get(stream)
            if c:
                soft += c["undefined"] - c["hard_undefined"]
                den += c["n"]
    return soft, den


def abstention_table(per_label_twin: dict) -> dict:
    """``{label: {twin: {soft_undefined, n, share, checks}}}`` from ``{(label, twin): [components lists]}``."""
    out: dict = {}
    for (label, twin), comp_lists in sorted(per_label_twin.items()):
        soft = den = 0
        for comps in comp_lists:
            s, d = k1_abstention(comps)
            soft += s
            den += d
        out.setdefault(label, {})[twin] = {"soft_undefined": soft, "n": den, "share": share(soft, den), "checks": len(comp_lists)}
    return out


def phase_b_abstention(r1_certs: str, pb_expected_path: str) -> "dict | None":
    """The same share from the 0.5.0 certificates of the Phase B files recorded by the official R1 (P-7 item 4)."""
    if not (os.path.isdir(r1_certs) and os.path.isfile(pb_expected_path)):
        return None
    cases = load_expected(pb_expected_path)
    per: dict = {}
    missing = []
    for case in sorted(cases):
        label = group_label(cases[case])
        for twin in TWINS:
            name = f"evaluation__phase_b__cases__{case}__{twin}.py.json"
            status, body = read_certificate(os.path.join(r1_certs, name))
            if status != "ok":
                missing.append(f"{case}/{twin}")
                continue
            comps = [{"k1": {s: {k: int(c.get(k, 0)) for k in ("n", "undefined", "hard_undefined")}
                             for s in K1_STREAMS for c in [(comp.get("counts") or {}).get(s)] if isinstance(c, dict)}}
                     for comp in body["components"]]
            per.setdefault((label, twin), []).append(comps)
    return {"table": abstention_table(per), "missing_certificates": missing}


# --------------------------------------------------------------------------
# report: primary comparison 0.5.0 against 0.4.1
# --------------------------------------------------------------------------

def classify_cause(comp050: "dict | None") -> str:
    """P-7 item 3, from the 0.5.0 component of the same file: hard / plus majority / soft only / unknown."""
    if comp050 is None:
        return "unknown"
    k1 = comp050["k1"]
    if any(c["hard_undefined"] > 0 for c in k1.values()):
        return "hard"
    plus = k1.get("world:plus")
    if plus and plus["n"] > 0 and 2 * plus["undefined"] > plus["n"]:
        return "plus majority"
    return "soft only"


def _comp_key(comp: dict) -> tuple:
    return (str(comp["id"]), str(comp["regime"]))


def _comp_name(case: str, twin: str, comp: dict) -> str:
    return f"{case}/{twin}/{comp['id']}"


def compare_versions(recs050: list, recs041: list) -> dict:
    files: list = []
    for r5, r4 in zip(recs050, recs041):
        for twin in TWINS:
            c5, c4 = r5["checks"][twin], r4["checks"][twin]
            comparable = c5["status"] == "ok" and c4["status"] == "ok"
            entry = {"case": r5["case"], "twin": twin, "label": group_label(r5["meta"]), "comparable": comparable,
                     "status_v050": c5["status"], "status_v041": c4["status"],
                     "verdict_v050": c5["verdict"], "verdict_v041": c4["verdict"], "undefined": [], "changed": [],
                     "abstained_majority": []}
            by5 = {_comp_key(c): c for c in c5["components"]}
            by4 = {_comp_key(c): c for c in c4["components"]}
            if c4["status"] == "ok":
                for comp in c4["components"]:
                    if comp["verdict"] == "UNDEFINED":
                        other = by5.get(_comp_key(comp)) if c5["status"] == "ok" else None
                        entry["undefined"].append({"component": comp["id"], "cause": classify_cause(other),
                                                   "verdict_v050": other["verdict"] if other else None})
            if comparable:
                for key in sorted(set(by5) | set(by4)):
                    a, b = by4.get(key), by5.get(key)
                    if a is None or b is None or a["verdict"] != b["verdict"]:
                        entry["changed"].append({"component": key[0], "verdict_v041": a["verdict"] if a else None,
                                                 "verdict_v050": b["verdict"] if b else None})
            if c5["status"] == "ok":
                for comp in c5["components"]:
                    capped = [f for f in comp["flags"] if any(f.startswith(p) for p in CAPPING_PREFIXES)]
                    if capped:
                        entry["abstained_majority"].append({"component": comp["id"], "flags": capped})
            files.append(entry)
    return {"files": files}


def comparison_results(recs050: list, recs041: list) -> dict:
    raw = compare_versions(recs050, recs041)
    files = raw["files"]
    with_undef = [f for f in files if f["undefined"]]
    informative = len(with_undef) >= INFORMATIVE_MIN_FILES
    not_comparable = [{"case": f["case"], "twin": f["twin"], "status_v050": f["status_v050"], "status_v041": f["status_v041"]}
                      for f in files if not f["comparable"]]
    labels = list(class_members([r["eval"] for r in recs050]))
    by_case = {(r5["case"]): (r5, r4) for r5, r4 in zip(recs050, recs041)}
    gains_det: dict = {}
    gains_clean: dict = {}
    lost_det: list = []
    lost_clean: list = []
    for case, (r5, r4) in sorted(by_case.items()):
        e5, e4 = r5["eval"], r4["eval"]
        label = group_label(r5["meta"])
        if e5["faulty_status"] == "ok" and e4["faulty_status"] == "ok":
            if e5["detected"] and not e4["detected"]:
                gains_det.setdefault(label, []).append(case)
            if e4["detected"] and not e5["detected"]:
                lost_det.append({"case": case, "label": label})
        if e5["fixed_status"] == "ok" and e4["fixed_status"] == "ok":
            if e5["clean"] and not e4["clean"]:
                gains_clean.setdefault(label, []).append(case)
            if e4["clean"] and not e5["clean"]:
                lost_clean.append({"case": case, "label": label})
    changed = [f for f in files if f["changed"]]
    result: dict = {
        "informative": informative,
        "informative_min_files": INFORMATIVE_MIN_FILES,
        "files_with_undefined_v041": len(with_undef),
        "undefined_files": [{"case": f["case"], "twin": f["twin"], "label": f["label"], "components": f["undefined"]}
                            for f in with_undef],
        "not_comparable": not_comparable,
        "detections_lost": lost_det,
        "clean_passes_lost": lost_clean,
        "no_loss": not lost_det and not lost_clean,
        "per_class": None,
        "no_change": None,
    }
    if informative:
        per_class: dict = {}
        for label in labels:
            lf = [f for f in files if f["label"] == label]
            comps = [(f, u) for f in lf for u in f["undefined"]]
            faulty_moves = sorted(f["case"] for f in lf if f["twin"] == "faulty" and f["comparable"]
                                  and f["verdict_v041"] == "UNDEFINED" and f["verdict_v050"] in CLEAN_VERDICTS)
            fixed_moves = sorted(f["case"] for f in lf if f["twin"] == "fixed" and f["comparable"]
                                 and f["verdict_v041"] == "UNDEFINED" and f["verdict_v050"] == "NOT_FALSIFIABLE")
            now: dict = {}
            for _, u in comps:
                now[str(u["verdict_v050"])] = now.get(str(u["verdict_v050"]), 0) + 1
            per_class[label] = {
                "files_with_undefined_v041": sum(1 for f in lf if f["undefined"]),
                "components_undefined_v041": len(comps),
                "causes": {c: sum(1 for _, u in comps if u["cause"] == c) for c in CAUSES},
                "verdict_v050_of_these_components": dict(sorted(now.items())),
                "detections_gained": sorted(gains_det.get(label, [])),
                "clean_passes_gained": sorted(gains_clean.get(label, [])),
                "faulty_undefined_to_falsifiable_or_weak": faulty_moves,
                "fixed_undefined_to_not_falsifiable": fixed_moves,
                "components_with_k1_abstained_majority": sorted(
                    f"{f['case']}/{f['twin']}/{a['component']}" for f in lf for a in f["abstained_majority"]),
                "detections_lost": sorted(d["case"] for d in lost_det if d["label"] == label),
                "clean_passes_lost": sorted(d["case"] for d in lost_clean if d["label"] == label),
            }
        result["per_class"] = per_class
        result["no_change"] = not changed and not any(per_class[l]["detections_gained"] or per_class[l]["clean_passes_gained"]
                                                      for l in per_class)
        result["changed_components"] = [{"case": f["case"], "twin": f["twin"], "components": f["changed"]} for f in changed]
    return result


# --------------------------------------------------------------------------
# report: build
# --------------------------------------------------------------------------

def parse_addendum_sources(text: str) -> frozenset:
    """Source keys (first cell, three capitals and two digits) of the table in SOURCES_ADDENDUM.md."""
    keys = set()
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.fullmatch(r"[A-Z]{3}\d{2}", cells[0]):
                keys.add(cells[0])
    return frozenset(keys)


def version_has_data(out: str, version: str) -> bool:
    return os.path.isfile(runlog_path(out, version)) or os.path.isdir(os.path.join(out, "certs", version))


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


def _awareness_fields(aw_ids: dict, world_id: str) -> dict:
    row = aw_ids.get(world_id)
    if not row:
        return {"aw_reader1": "?", "aw_reader2": "?", "aw_resolved": "?", "aw_no_log": False}
    return {"aw_reader1": row["reader1"], "aw_reader2": row["reader2"], "aw_resolved": row["resolved"],
            "aw_no_log": bool(row.get("no_log"))}


def build_results(out: str, inputs: dict) -> dict:
    expected = load_expected(inputs["expected"])
    aw_ids = load_json(inputs["awareness"])["ids"]
    lines_by_case = load_json(inputs["lines"])
    addendum = ADDENDUM_SOURCES
    parsed_addendum = None
    if os.path.isfile(inputs["addendum"]):
        with open(inputs["addendum"], encoding="utf-8") as handle:
            parsed_addendum = parse_addendum_sources(handle.read())
        if parsed_addendum != ADDENDUM_SOURCES:
            raise SystemExit(f"SOURCES_ADDENDUM.md lists {sorted(parsed_addendum)}, expected {sorted(ADDENDUM_SOURCES)}")
    versions = [v for v in (PRIMARY, SECOND) if version_has_data(out, v)]
    if PRIMARY not in versions:
        raise SystemExit(f"no {PRIMARY} certificates or run log under {out}")
    cases = sorted(expected)
    no_designer_line = [c for c in cases if c not in lines_by_case]
    if no_designer_line:
        raise SystemExit(f"cases without an entry in the designer lines file: {', '.join(no_designer_line)}")
    per_version: dict = {}
    runtimes: dict = {}
    logs: dict = {}
    for version in versions:
        lines = read_runlog_lines(out, version)
        last = final_rows(lines)
        recs = []
        all_checks = []
        for case in cases:
            meta = expected[case]
            checks = {t: load_check(out, version, case, t, last, lines) for t in TWINS}
            ev = evaluate_pair(meta, checks["faulty"], checks["fixed"])
            ev.update({"case": case, "meta": meta, "overlap": bool(lines_by_case[case]["overlap"].startswith("yes")),
                       **_awareness_fields(aw_ids, meta["world_id"])})
            recs.append({"case": case, "meta": meta, "checks": checks, "eval": ev})
            all_checks += [{"case": case, "twin": t, **checks[t]} for t in TWINS]
        per_version[version] = recs
        runtimes[version] = runtime_table(all_checks)
        logs[version] = {
            "infrastructure_attempts": sorted(
                [{"case": r["case"], "twin": r["twin"], "attempt": r.get("attempt"), "exit_code": r.get("exit_code"),
                  "final": (r["case"], r["twin"]) in last and last[(r["case"], r["twin"])] is r}
                 for r in result_lines(lines) if r.get("infra_failure")], key=lambda d: (d["case"], d["twin"], d["attempt"] or 0)),
            "tool_version_mismatches": sorted(
                f"{c['case']}/{c['twin']} ({c['tool_version']})" for c in all_checks
                if c["status"] == "ok" and c["tool_version"] != VERSIONS[version]["tool_version"]),
            "commits": sorted({(r.get("tag_commit"), r.get("worktree_head")) for r in result_lines(lines)},
                              key=lambda t: (str(t[0]), str(t[1]))),
        }
        logs[version]["commits"] = [{"tag_commit": a, "worktree_head": b} for a, b in logs[version]["commits"]]
    primary = per_version[PRIMARY]
    ev050 = [r["eval"] for r in primary]
    ev041 = [r["eval"] for r in per_version[SECOND]] if SECOND in per_version else None
    no_overlap = lambda evs: [e for e in evs if not e["overlap"]]  # noqa: E731

    gate = {PRIMARY: metrics_table(ev050, "gate")}
    gate_no_overlap = {PRIMARY: metrics_table(no_overlap(ev050), "gate")}
    baselines = {
        "flag_everything": metrics_table(ev050, "flag_all"),
        "noise_only": {PRIMARY: metrics_table(ev050, "noise_only")},
        "declared_only": {PRIMARY: metrics_table(ev050, "declared_only")},
    }
    if ev041 is not None:
        gate[SECOND] = metrics_table(ev041, "gate")
        gate_no_overlap[SECOND] = metrics_table(no_overlap(ev041), "gate")
        baselines["noise_only"][SECOND] = metrics_table(ev041, "noise_only")
        baselines["declared_only"][SECOND] = metrics_table(ev041, "declared_only")

    members050 = class_members(ev050)
    shares = {label: awareness_shares(m) for label, m in members050.items()}
    shares_no_overlap = {label: awareness_shares(no_overlap(m)) for label, m in members050.items()}
    shares_all = awareness_shares(ev050)
    awareness = {reading: awareness_breakdown(ev050, reading) for reading in ("reader1", "reader2", "resolved")}
    awareness_counts = {}
    for reading, key in (("reader1", "aw_reader1"), ("reader2", "aw_reader2"), ("resolved", "aw_resolved")):
        counts: dict = {}
        for label, m in members050.items():
            counts[label] = {lv: sum(1 for e in m if e[key] == lv) for lv in ("P", "C", "N", "no log")}
            if reading == "resolved":
                counts[label] = {lv: counts[label][lv] for lv in ("P", "C", "N")}
                counts[label]["no_log_in_P"] = sum(1 for e in m if e["aw_no_log"])
            else:
                counts[label]["unclassified"] = sum(1 for e in m if e[key] not in ("P", "C", "N", "no log"))
        awareness_counts[reading] = counts

    result: dict = {
        "primary_version": PRIMARY,
        "versions_present": versions,
        "rules": {
            "z_one_sided_95": Z95, "threshold": THRESHOLD, "min_pairs": MIN_PAIRS, "time_limit_s": TIME_LIMIT,
            "noise_flags": sorted(NOISE_FLAGS), "k2_flags": sorted(K2_FLAGS), "clean_verdicts": list(CLEAN_VERDICTS),
            "information_flags": sorted(INFORMATION_FLAGS),
            "information_prefixes": list(INFORMATION_PREFIXES), "capping_prefixes": list(CAPPING_PREFIXES),
            "k1_streams": list(K1_STREAMS), "informative_min_files": INFORMATIVE_MIN_FILES,
            "too_small_rule": f"miss, no expected flag, world:minus holds/n <= {TOO_SMALL_NOMINAL} + "
                              f"{TOO_SMALL_SE_MULTIPLIER:g} * sqrt({TOO_SMALL_NOMINAL} * {1 - TOO_SMALL_NOMINAL:g} / n)",
            "addendum_sources": sorted(ADDENDUM_SOURCES), "new_source_minimum": NEW_SOURCE_MIN,
        },
        "gate": gate,
        "gate_without_overlapping_pairs": gate_no_overlap,
        "baselines": baselines,
        "overlap": overlap_summary(ev050, addendum),
        "awareness_counts": awareness_counts,
        "awareness_breakdown": awareness,
        "awareness_shares_resolved": shares,
        "awareness_shares_resolved_without_overlapping_pairs": shares_no_overlap,
        "awareness_shares_resolved_all_pairs": shares_all,
        "abstention": {},
        "runtimes": runtimes,
        "run_logs": logs,
        "not_built": {"B-4": "no documented cases; no evidence either way", "B-5": "no documented cases; no evidence either way"},
    }
    # abstention, Phase C (0.5.0) next to Phase B (R1 certificates of 0.5.0)
    per_label_twin: dict = {}
    for r in primary:
        label = group_label(r["meta"])
        for twin in TWINS:
            if r["checks"][twin]["status"] == "ok":
                per_label_twin.setdefault((label, twin), []).append(r["checks"][twin]["components"])
    result["abstention"]["phase_c_v050"] = abstention_table(per_label_twin)
    pb_abst = phase_b_abstention(inputs["r1_certs"], inputs["phase_b_expected"])
    result["abstention"]["phase_b_r1_v050"] = pb_abst["table"] if pb_abst else None
    result["abstention"]["phase_b_missing_certificates"] = pb_abst["missing_certificates"] if pb_abst else None
    # comparison
    if SECOND in per_version:
        result["comparison"] = comparison_results(primary, per_version[SECOND])
    else:
        result["comparison"] = None
    # Phase B next to Phase C (descriptive)
    if os.path.isfile(inputs["phase_b_results"]):
        pb = load_json(inputs["phase_b_results"])
        result["phase_b_next_to_c"] = {"phase_b_gate_version": pb.get("primary_version"), "phase_b": pb["gate"],
                                       "phase_c": gate[PRIMARY]}
    else:
        result["phase_b_next_to_c"] = None
    # per pair
    pairs = []
    for i, r in enumerate(primary):
        ev, meta = r["eval"], r["meta"]
        row = {
            "case": r["case"], "class": meta["class"], "subtype": meta["subtype"], "in_scope": meta["in_scope"],
            "source": meta["source"], "world_id": meta["world_id"], "overlap": lines_by_case[r["case"]]["overlap"],
            "overlap_yes": ev["overlap"], "addendum_source": meta["source"] in addendum,
            "size_ratio": lines_by_case[r["case"]]["size_ratio"],
            "awareness_reader1": ev["aw_reader1"], "awareness_reader2": ev["aw_reader2"],
            "awareness_resolved": ev["aw_resolved"], "no_log": ev["aw_no_log"],
            "label_error_too_small": ev["too_small"]["applies"], "too_small_detail": ev["too_small"],
            "versions": {},
        }
        for version in versions:
            e = per_version[version][i]["eval"]
            row["versions"][version] = {
                k: e[k] for k in ("faulty_verdict", "faulty_flags", "expected_present", "detected", "label", "k2_only",
                                  "fixed_verdict", "fixed_flags", "clean", "faulty_seconds", "fixed_seconds")}
        pairs.append(row)
    result["pairs"] = pairs
    return result


# --------------------------------------------------------------------------
# report: Markdown
# --------------------------------------------------------------------------

def md_table(header: list, rows: list) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(lines)


def names(items: list) -> str:
    return ", ".join(items) if items else "none"


def _bounded_rows(table: dict, full: bool) -> list:
    rows = []
    for label, c in table.items():
        row = [label, c["pairs"], c["detections"]]
        if full:
            row += [c["generic"], c["declared"], c["k2_only"]]
        shown = c["verdict"] + (" (descriptive, not a class verdict)" if c.get("descriptive") else "")
        row += [c["clean_passes"], fmt(c["detection_lower"]), fmt(c["clean_lower"]), "yes" if c["pairs_ge_10"] else "no", shown]
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
             "B-2 subtypes (descriptive when fewer than 10 pairs: bounds and the rule's result are shown, not a class verdict)", "",
             md_table(_bounded_header(full), _bounded_rows(block["b2_subtypes"], full)), ""]
    if block["out_of_scope"]:
        if full:
            head = ["group", "pairs", "detections", "generic", "declared", "K2-only", "clean passes"]
            rows = [[k, c["pairs"], c["detections"], c["generic"], c["declared"], c["k2_only"], c["clean_passes"]]
                    for k, c in block["out_of_scope"].items()]
        else:
            head = ["group", "pairs", "detections", "clean passes"]
            rows = [[k, c["pairs"], c["detections"], c["clean_passes"]] for k, c in block["out_of_scope"].items()]
        parts += ["Out of scope (counts only, descriptive)", "", md_table(head, rows), ""]
    return "\n".join(parts)


def _shares_text(s: dict) -> str:
    n = s["pairs"]
    return (f"resolved awareness of these {n} pairs: P {s['P']}/{n} ({fmt(s['P_share'], 3)}; "
            f"of which no log {s['no_log_in_P']}), C {s['C']}/{n} ({fmt(s['C_share'], 3)}), "
            f"N {s['N']}/{n} ({fmt(s['N_share'], 3)})"
            + (f", unclassified {s['unclassified']}" if s["unclassified"] else "")
            + f"; {AWARENESS_WORDS}")


def verdict_line(version: str, label: str, c: dict, s: dict, note: str = "") -> str:
    return (f"* {label} ({VERSION_LABEL[version]}{note}): **{c['verdict']}** - pairs {c['pairs']}, detections {c['detections']} "
            f"(lower bound {fmt(c['detection_lower'])}), clean passes {c['clean_passes']} (lower bound {fmt(c['clean_lower'])}); "
            f"{_shares_text(s)}.")


def _sbs_row(label: str, b: "dict | None", c: "dict | None") -> list:
    def cells(x: "dict | None") -> list:
        if not x:
            return ["-", "-", "-", "-", "-", "-"]
        return [x["pairs"], x["detections"], x["clean_passes"], fmt(x.get("detection_lower")), fmt(x.get("clean_lower")),
                x.get("verdict", "-")]
    return [label] + cells(b) + cells(c)


def render_markdown(res: dict) -> str:
    versions = res["versions_present"]
    two = SECOND in versions
    out = ["# Phase C results", "",
           f"Gate under test (pre-registered primary table): {VERSION_LABEL[PRIMARY]}. Versions with data: "
           + ", ".join(VERSION_LABEL[v] for v in versions) + ".",
           f"Wilson bounds are one-sided 95% (z = {Z95}); HOLDS needs pairs >= {MIN_PAIRS} and both lower bounds >= {THRESHOLD}.",
           f"B-4: {res['not_built']['B-4']}. B-5: {res['not_built']['B-5']}.",
           "Information flags (K1_ABSTAINED:*, K2_MINUS_UNREAD, K8_SOME_CHANGES, BAD_RETURN) and the capping flag "
           "K1_ABSTAINED_MAJORITY:* never count as expected flags.",
           f"Allowed claims (I-8): what the gate did on errors documented in the literature, with worlds declared by a different "
           f"Claude model line that was not told the error; every class verdict carries its resolved P/C/N shares ({AWARENESS_WORDS}).",
           "", "## 1. Truth_Gate per class", ""]
    gate = res["gate"]
    out += [_metric_block(f"Truth_Gate {VERSION_LABEL[PRIMARY]} (pre-registered primary table)", gate[PRIMARY], True)]
    if two:
        out += [_metric_block(f"Truth_Gate {VERSION_LABEL[SECOND]} (same files, same rules)", gate[SECOND], True)]
    out += ["### Class verdicts", ""]
    shares = res["awareness_shares_resolved"]
    for version in versions:
        for label, c in gate[version]["classes"].items():
            out.append(verdict_line(version, label, c, shares[label]))
    out += [""]
    for label, row in res["overlap"].items():
        if label in IN_SCOPE_CLASSES and row["largely_repeats_phase_b"]:
            out += [f"**{label}: the class's Phase C result \"{OVERLAP_WORDING}\" "
                    f"({row['overlapping_pairs']} of {row['pairs']} pairs overlap Phase B); the Phase B and Phase C results of this "
                    f"class are not presented as separate evidence.**", ""]

    out += ["## 2. Baselines (same pairs)", ""]
    out += [_metric_block("Flag everything (detection = all, clean pass = none)", res["baselines"]["flag_everything"], False)]
    for key, title in (("noise_only", "Noise-only"), ("declared_only", "Declared-only")):
        for version in versions:
            out += [_metric_block(f"{title}, from the {VERSION_LABEL[version]} certificates", res["baselines"][key][version], False)]

    out += ["## 3. Primary comparison: 0.5.0 against 0.4.1 (unit: the one component of each file)", ""]
    cmp_ = res["comparison"]
    if cmp_ is None:
        out += ["No 0.4.1 data: the comparison cannot be made.", ""]
    else:
        out += [f"Study files (faulty and fixed, all classes) with a component UNDEFINED under 0.4.1: "
                f"{cmp_['files_with_undefined_v041']} (the comparison is informative from {cmp_['informative_min_files']}).", ""]
        if not cmp_["informative"]:
            out += ["**NOT INFORMATIVE**: fewer than "
                    f"{cmp_['informative_min_files']} files have a component UNDEFINED under 0.4.1. No per-class statement is made.", ""]
            if cmp_["undefined_files"]:
                rows = [[f["case"], f["twin"], f["label"], c["component"], c["cause"], c["verdict_v050"]]
                        for f in cmp_["undefined_files"] for c in f["components"]]
                out += [md_table(["case", "twin", "class", "component", "cause", "0.5.0 verdict"], rows), ""]
            else:
                out += ["List: none.", ""]
        else:
            pc = cmp_["per_class"]
            head = ["class", "files with UNDEFINED", "components UNDEFINED", "hard", "plus majority", "soft only", "unknown",
                    "detections gained", "clean passes gained", "faulty UNDEFINED -> FALSIFIABLE/WEAK",
                    "fixed UNDEFINED -> NOT_FALSIFIABLE", "components K1_ABSTAINED_MAJORITY"]
            rows = [[l, c["files_with_undefined_v041"], c["components_undefined_v041"], c["causes"]["hard"],
                     c["causes"]["plus majority"], c["causes"]["soft only"], c["causes"]["unknown"],
                     len(c["detections_gained"]), len(c["clean_passes_gained"]),
                     len(c["faulty_undefined_to_falsifiable_or_weak"]), len(c["fixed_undefined_to_not_falsifiable"]),
                     len(c["components_with_k1_abstained_majority"])] for l, c in pc.items()]
            out += [md_table(head, rows), "", "By name", ""]
            for label, c in pc.items():
                out += [f"* {label}: detections gained: {names(c['detections_gained'])}; clean passes gained: "
                        f"{names(c['clean_passes_gained'])}; faulty twins UNDEFINED -> FALSIFIABLE/WEAK (misses 0.4.1 hid): "
                        f"{names(c['faulty_undefined_to_falsifiable_or_weak'])}; fixed twins UNDEFINED -> NOT_FALSIFIABLE "
                        f"(false alarms 0.4.1 hid): {names(c['fixed_undefined_to_not_falsifiable'])}; components with "
                        f"K1_ABSTAINED_MAJORITY: {names(c['components_with_k1_abstained_majority'])}; 0.5.0 verdicts of the "
                        f"components UNDEFINED under 0.4.1: "
                        + (", ".join(f"{k} {v}" for k, v in c["verdict_v050_of_these_components"].items()) or "none") + "."]
            out += [""]
            if cmp_["no_change"]:
                out += ["**No change**: every comparable component has the same verdict under both versions and no detection or "
                        "clean pass was gained.", ""]
            else:
                ch = cmp_["changed_components"]
                out += ["Components whose verdict differs between the versions: "
                        + (", ".join(f"{d['case']}/{d['twin']}" for d in ch) if ch else "none") + ".", ""]
        out += ["### Losses (spec 0.7 section 4: none can occur; a loss counts against 0.5.0)", ""]
        if cmp_["no_loss"]:
            out += ["No 0.4.1 detection and no 0.4.1 clean pass is lost under 0.5.0.", ""]
        else:
            if cmp_["detections_lost"]:
                out += ["**LOSS: 0.4.1 detections lost under 0.5.0: "
                        + ", ".join(f"{d['case']} ({d['label']})" for d in cmp_["detections_lost"]) + "**", ""]
            if cmp_["clean_passes_lost"]:
                out += ["**LOSS: 0.4.1 clean passes lost under 0.5.0: "
                        + ", ".join(f"{d['case']} ({d['label']})" for d in cmp_["clean_passes_lost"]) + "**", ""]
        nc = cmp_["not_comparable"]
        out += ["Not comparable (a check without a certificate or a timeout in either version): "
                + (", ".join(f"{d['case']}/{d['twin']} (0.5.0 {d['status_v050']}, 0.4.1 {d['status_v041']})" for d in nc)
                   if nc else "none") + ".", ""]

    out += ["## 4. Abstention shares (sum of undefined - hard_undefined over the K1 streams / sum of n), 0.5.0", ""]
    ab_c = res["abstention"]["phase_c_v050"]
    ab_b = res["abstention"]["phase_b_r1_v050"]
    rows = []
    for label in list(IN_SCOPE_CLASSES) + sorted(l for l in ab_c if l not in IN_SCOPE_CLASSES):
        for twin in TWINS:
            c = (ab_c.get(label) or {}).get(twin)
            b = ((ab_b or {}).get(label) or {}).get(twin)
            rows.append([label, twin,
                         f"{c['soft_undefined']} / {c['n']}" if c else "-", fmt(c["share"]) if c else "-",
                         f"{b['soft_undefined']} / {b['n']}" if b else "-", fmt(b["share"]) if b else "-"])
    out += [md_table(["class", "twin", "Phase C soft undefined / n", "Phase C share",
                      "Phase B (R1, 0.5.0) soft undefined / n", "Phase B share"], rows), "",
            "Phase B column: descriptive, from the 0.5.0 certificates of the Phase B files recorded by the official R1."
            + ("" if ab_b else " (not available: R1 certificates or the Phase B expected-flags file are missing)"), ""]

    out += ["## 5. Awareness breakdown (descriptive)", "",
            "Resolved reading = the higher of the two readers (N < C < P); 'no log' counts as P and is shown separately.", ""]
    ac = res["awareness_counts"]
    labels = list(ac["resolved"])
    rows = []
    for label in labels:
        r1, r2, rs = ac["reader1"][label], ac["reader2"][label], ac["resolved"][label]
        rows.append([label, f"{r1['P']}/{r1['C']}/{r1['N']}/{r1['no log']}", f"{r2['P']}/{r2['C']}/{r2['N']}/{r2['no log']}",
                     f"{rs['P']}/{rs['C']}/{rs['N']}", rs["no_log_in_P"]])
    out += [md_table(["class", "reader 1 P/C/N/no log", "reader 2 P/C/N/no log", "resolved P/C/N", "no log (inside resolved P)"], rows), ""]
    for reading in ("resolved", "reader1", "reader2"):
        rows = []
        for level, groups in res["awareness_breakdown"][reading].items():
            for label, c in groups.items():
                rows.append([level, label, c["pairs"], c["detections"], c["generic"], c["declared"], c["k2_only"], c["clean_passes"]])
        out += [f"### Results by awareness level, {reading} reading (0.5.0, counts only)", "",
                md_table(["level", "class", "pairs", "detections", "generic", "declared", "K2-only", "clean passes"], rows), ""]

    out += ["## 6. Overlap with Phase B and addendum sources", ""]
    rows = [[l, r["pairs"], r["overlapping_pairs"], r["addendum_source_pairs"],
             ("yes" if r["new_source_minimum_met"] else "NO - new-source minimum not met") if "new_source_minimum_met" in r else "-",
             OVERLAP_WORDING if r["largely_repeats_phase_b"] and l in IN_SCOPE_CLASSES else "-"]
            for l, r in res["overlap"].items()]
    out += [md_table(["class", "pairs", "overlapping pairs", "addendum-source pairs", f">= {NEW_SOURCE_MIN} addendum pairs",
                      "wording (more than half overlap)"], rows), ""]
    out += [_metric_block(f"Truth_Gate {VERSION_LABEL[PRIMARY]} without the overlapping pairs (descriptive)",
                          res["gate_without_overlapping_pairs"][PRIMARY], True)]
    if two:
        out += [_metric_block(f"Truth_Gate {VERSION_LABEL[SECOND]} without the overlapping pairs (descriptive)",
                              res["gate_without_overlapping_pairs"][SECOND], True)]
    out += ["Class lines without the overlapping pairs (descriptive):", ""]
    for label, c in res["gate_without_overlapping_pairs"][PRIMARY]["classes"].items():
        out.append(verdict_line(PRIMARY, label, c, res["awareness_shares_resolved_without_overlapping_pairs"][label],
                                ", without overlapping pairs, descriptive"))
    out += [""]

    out += ["## 7. Phase B next to Phase C (descriptive: briefs, worlds, criteria and the size rule differ)", ""]
    pbc = res["phase_b_next_to_c"]
    if pbc is None:
        out += ["Phase B results file not available.", ""]
    else:
        head = ["group", "B pairs", "B detections", "B clean passes", "B det. lower", "B clean lower", "B verdict",
                "C pairs", "C detections", "C clean passes", "C det. lower", "C clean lower", "C verdict"]
        rows = []
        for section in ("classes", "b2_subtypes", "out_of_scope"):
            for label, c in pbc["phase_c"][section].items():
                rows.append(_sbs_row(label, pbc["phase_b"].get(section, {}).get(label), c))
        out += [f"Phase B gate: {pbc['phase_b_gate_version']}; Phase C gate: {VERSION_LABEL[PRIMARY]}.", "", md_table(head, rows), ""]

    out += ["## 8. Run times (seconds per check)", ""]
    rows = []
    for version, t in res["runtimes"].items():
        rows.append([VERSION_LABEL[version], t["checks_with_time"], fmt(t["min"], 1), fmt(t["median"], 1), fmt(t["max"], 1),
                     len(t["beyond_3600_s"])])
    out += [md_table(["version", "checks", "min", "median", "max", "beyond 3600 s"], rows), ""]
    for version, t in res["runtimes"].items():
        if t["beyond_3600_s"]:
            out += [f"Beyond 3600 s ({VERSION_LABEL[version]}): " + ", ".join(
                f"{d['case']}/{d['twin']} ({fmt(d['seconds'], 1)} s{', timeout' if d['timed_out'] else ''})"
                for d in t["beyond_3600_s"]), ""]
    for version, lg in res["run_logs"].items():
        if lg["infrastructure_attempts"]:
            out += [f"Infrastructure failures ({VERSION_LABEL[version]}), every attempt: " + ", ".join(
                f"{d['case']}/{d['twin']} attempt {d['attempt']} (exit {d['exit_code']}{', final' if d['final'] else ''})"
                for d in lg["infrastructure_attempts"]), ""]
        if lg["tool_version_mismatches"]:
            out += [f"**Certificates with another tool_version than {VERSION_LABEL[version]}: "
                    + ", ".join(lg["tool_version_mismatches"]) + "**", ""]
        out += [f"Commits recorded in the {VERSION_LABEL[version]} run log (tag commit, worktree HEAD): "
                + (", ".join(f"{c['tag_commit']} / {c['worktree_head']}" for c in lg["commits"]) or "none") + ".", ""]

    out += ["## 9. Pairs", "",
            f"Label \"{TOO_SMALL_LABEL}\": a miss under 0.5.0 whose faulty file carries no expected flag and whose world:minus rate "
            f"holds / n is at most {TOO_SMALL_NOMINAL} + {TOO_SMALL_SE_MULTIPLIER:g} * sqrt({TOO_SMALL_NOMINAL} * "
            f"{1 - TOO_SMALL_NOMINAL:g} / n) (P-7 item 5).", ""]
    rows = []
    for p in res["pairs"]:
        row = [p["case"], p["class"], p["subtype"] or "-", p["source"], p["world_id"], p["overlap"],
               p["size_ratio"], f"{p['awareness_reader1']}/{p['awareness_reader2']}/{p['awareness_resolved']}"]
        for version in versions:
            v = p["versions"][version]
            label = "-"
            if v["detected"]:
                label = v["label"] + (", K2-only" if v["k2_only"] else "")
            row += [v["faulty_verdict"], "yes" if v["detected"] else "no", label, v["fixed_verdict"], "yes" if v["clean"] else "no",
                    f"{fmt(v['faulty_seconds'], 1)} / {fmt(v['fixed_seconds'], 1)}"]
        d = p["too_small_detail"]
        row.append(TOO_SMALL_LABEL + (f" (rate {fmt(d['rate'])} <= {fmt(d['bound'])}, n {d['n']})" if d["applies"] else "")
                   if p["label_error_too_small"] else "-")
        rows.append(row)
    head = ["case", "class", "subtype", "source", "world", "overlap with Phase B", "size ratio", "awareness r1/r2/resolved"]
    for version in versions:
        v = VERSION_LABEL[version]
        head += [f"faulty {v}", f"detected {v}", f"label {v}", f"fixed {v}", f"clean {v}", f"seconds {v} faulty / fixed"]
    head.append("interpretation label (0.5.0)")
    out += [md_table(head, rows), "", "### Flags per pair", ""]
    rows = []
    for p in res["pairs"]:
        row = [p["case"]]
        for version in versions:
            v = p["versions"][version]
            row += [", ".join(v["expected_present"]) or "-", ", ".join(v["faulty_flags"]) or "-", ", ".join(v["fixed_flags"]) or "-"]
        rows.append(row)
    head = ["case"]
    for version in versions:
        v = VERSION_LABEL[version]
        head += [f"expected flags present {v}", f"all faulty flags {v}", f"all fixed flags {v}"]
    out += [md_table(head, rows), ""]
    return "\n".join(out)


def write_outputs(out: str, res: dict) -> None:
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "RESULTS.json"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(res, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
    with open(os.path.join(out, "RESULTS.md"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_markdown(res))


def _inputs_from_args(args: argparse.Namespace) -> dict:
    inputs = dict(DEFAULT_INPUTS)
    for key, attr in (("expected", "expected"), ("awareness", "awareness"), ("lines", "lines"), ("addendum", "addendum"),
                      ("phase_b_results", "phase_b_results"), ("phase_b_expected", "phase_b_expected"), ("r1_certs", "r1_certs")):
        value = getattr(args, attr, None)
        if value:
            inputs[key] = os.path.abspath(value)
    return inputs


def cmd_report(args: argparse.Namespace) -> int:
    out = os.path.abspath(args.out) if args.out else DEFAULT_OUT
    res = build_results(out, _inputs_from_args(args))
    write_outputs(out, res)
    for label, c in res["gate"][PRIMARY]["classes"].items():
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


def _stream(n: int = 200, holds: int = 0, undefined: int = 0, hard: int = 0) -> dict:
    return {"n": n, "holds": holds, "undefined": undefined, "hard_undefined": hard}


def _syn_comp(verdict: str, flags: list, plus: dict, minus: dict, cid: str = "C") -> dict:
    return {"id": cid, "regime": "all", "verdict": verdict, "flags": list(flags),
            "counts": {"world:plus": plus, "world:minus": minus, "probe:noise": _stream(), "probe:zeros": _stream(undefined=200)},
            "errors": {}, "bounds": {}, "unresolvable": []}


def _syn_cert(version: str, verdict: str, comps: list) -> dict:
    return {"body": {"verdict": verdict, "study_flags": [], "load_error": None, "tool_version": VERSIONS[version]["tool_version"],
                     "components": comps},
            "body_sha256": "synthetic", "created_utc": "synthetic"}


def _write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle)


def _make_scenario(tmp: str, informative: bool) -> "tuple[str, dict]":
    """Synthetic run folder and inputs.  ``informative`` False replaces the 0.4.1 certificates of T02, T03, T05 by plain ones."""
    out = os.path.join(tmp, "run_inf" if informative else "run_not")
    exp_flags = ["K2_HIGH_SIZE", "K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K4_CONTROL_ALSO_HOLDS", "K5_HOLDS_ON_NOISE",
                 "K5_HOLDS_ON_NULL", "HIGH_RATE:probe:noise", "HIGH_RATE:world:null",
                 # information and capping flags listed as expected on purpose: they must never count
                 "K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:minus", "K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN"]
    hard = _stream(holds=0, undefined=200, hard=200)
    plain_plus, plain_minus = _stream(holds=200), _stream(holds=10)
    maj = _stream(holds=80, undefined=120, hard=0)
    soft = _stream(holds=170, undefined=30, hard=0)

    def comp(verdict, flags=(), plus=plain_plus, minus=plain_minus):
        return [_syn_comp(verdict, list(flags), plus, minus)]

    nf = lambda flags, minus=plain_minus: ("NOT_FALSIFIABLE", comp("NOT_FALSIFIABLE", flags, minus=minus))  # noqa: E731
    ok = lambda: ("FALSIFIABLE", comp("FALSIFIABLE"))  # noqa: E731
    undef_hard = lambda: ("UNDEFINED", comp("UNDEFINED", ["K1_UNDEFINED"], hard, hard))  # noqa: E731
    # case: (class, subtype, in_scope, source, world, overlap line, {version: (faulty, fixed)})
    spec = {
        "T01": ("B-1", None, True, "KRI09", "C01", "yes, Phase B case B1-01",
                {"v050": (undef_hard(), undef_hard()), "v041": (undef_hard(), undef_hard())}),
        "T02": ("B-1", None, True, "KRI09", "C02", "yes, Phase B case B1-02",
                {"v050": (("NOT_FALSIFIABLE", comp("NOT_FALSIFIABLE", ["K2_NO_SEPARATION", "K1_ABSTAINED_MAJORITY:world:plus"], plus=maj)),
                          ("NOT_FALSIFIABLE", comp("NOT_FALSIFIABLE", ["K4_CONTROL_ALSO_HOLDS"], plus=maj))),
                 "v041": (("UNDEFINED", comp("UNDEFINED", ["K1_UNDEFINED"], maj, plain_minus)),
                          ("UNDEFINED", comp("UNDEFINED", ["K1_UNDEFINED"], maj, plain_minus)))}),
        "T03": ("B-1", None, True, "MOR03", "C03", "no (addendum source)",
                {"v050": (("WEAK", comp("WEAK", ["K1_ABSTAINED:world:plus"], plus=soft)), ok()),
                 "v041": (("UNDEFINED", comp("UNDEFINED", ["K1_UNDEFINED"], soft, plain_minus)), ok())}),
        "T04": ("B-1", None, True, "PEA97", "C04", "yes, Phase B case B1-04",
                {"v050": (nf(["K5_HOLDS_ON_NOISE", "K1_ABSTAINED:world:minus"]), ok()),
                 "v041": (nf(["K5_HOLDS_ON_NOISE"]), ok())}),
        "T05": ("B-1", None, True, "KRI10", "C05", "no (addendum source)",
                {"v050": (None, ok()), "v041": (("UNDEFINED", comp("UNDEFINED", ["K1_UNDEFINED"], hard, hard)), ok())}),
        "T06": ("B-2", "L1.3", True, "VAR06", "C06", "no (addendum source)",
                {"v050": (("WEAK", comp("WEAK")), nf(["K4_CONTROL_ALSO_HOLDS"])),
                 "v041": (nf(["K2_NO_SEPARATION"]), ok())}),
        "T07": ("B-6", None, True, "LAZ18", "C07", "no (addendum source)",
                {"v050": (("FALSIFIABLE", comp("FALSIFIABLE", minus=_stream(holds=16))), ok()),
                 "v041": (("FALSIFIABLE", comp("FALSIFIABLE", minus=_stream(holds=16))), ok())}),
        "T08": ("B-6", None, True, "NIE11", "C08", "no",
                {"v050": (("FALSIFIABLE", comp("FALSIFIABLE", minus=_stream(holds=17))), ok()),
                 "v041": (("FALSIFIABLE", comp("FALSIFIABLE", minus=_stream(holds=17))), ok())}),
        "T09": ("B-6", None, True, "HUR84", "C09", "no",
                {"v050": (nf(["K2_HIGH_SIZE"], minus=_stream(holds=8)), ok()),
                 "v041": (nf(["K2_HIGH_SIZE"], minus=_stream(holds=8)), ok())}),
        "T10": ("B-3", None, True, "CUR13", "C10", "no (addendum source)",
                {"v050": (nf(["K1_ABSTAINED_MAJORITY:world:minus", "K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN",
                              "K1_ABSTAINED:world:minus"]), ("WEAK", comp("WEAK"))),
                 "v041": (nf(["K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN"]), ("WEAK", comp("WEAK")))}),
        "T11": ("O", "O-1", False, "KAP23", "C11", "no",
                {"v050": (nf(["K5_HOLDS_ON_NOISE"]), ok()), "v041": (nf(["K5_HOLDS_ON_NOISE"]), ok())}),
    }
    exp = {"note": "synthetic", "base": [], "cases": {}}
    lines = {}
    for case, (cls, sub, scope, source, world, overlap, per_version) in spec.items():
        exp["cases"][case] = {"case_id": case, "world_id": world, "class": cls, "subtype": sub, "source": source,
                              "in_scope": scope, "expected": exp_flags}
        lines[case] = {"overlap": overlap, "mechanism_tag": "x", "statistic_family": "y", "guard_minimum": "z",
                       "size_ratio": "source states none" if case != "T07" else "samples 40/40 = 1.0"}
        for version, (faulty, fixed) in per_version.items():
            if not informative and version == "v041" and case in ("T02", "T03", "T05"):
                faulty = fixed = nf(["K2_NO_SEPARATION"]) if faulty is not None else None
                fixed = ok()
            for twin, item in (("faulty", faulty), ("fixed", fixed)):
                row_secs = 5.0
                if item is not None:
                    _write_json(cert_path(out, version, case, twin), _syn_cert(version, item[0], item[1]))
                with open(runlog_path(out, version), "a", encoding="utf-8") as handle:
                    handle.write(json.dumps({"event": "result", "version": version, "case": case, "twin": twin, "seconds": row_secs,
                                             "timed_out": False, "exit_code": 0 if item is not None else 4, "attempt": 1,
                                             "has_certificate": item is not None, "infra_failure": False,
                                             "tag_commit": "aaa", "worktree_head": "aaa"}) + "\n")
    aw = {"_note": "synthetic", "ids": {
        "C01": {"reader1": "no log", "reader2": "no log", "resolved": "P", "no_log": True},
        "C02": {"reader1": "P", "reader2": "C", "resolved": "P", "no_log": False},
        "C03": {"reader1": "C", "reader2": "C", "resolved": "C", "no_log": False},
        "C04": {"reader1": "N", "reader2": "N", "resolved": "N", "no_log": False},
        "C05": {"reader1": "P", "reader2": "P", "resolved": "P", "no_log": False},
        "C06": {"reader1": "P", "reader2": "P", "resolved": "P", "no_log": False},
        "C07": {"reader1": "C", "reader2": "P", "resolved": "P", "no_log": False},
        "C08": {"reader1": "N", "reader2": "C", "resolved": "C", "no_log": False},
        "C09": {"reader1": "P", "reader2": "P", "resolved": "P", "no_log": False},
        "C10": {"reader1": "P", "reader2": "P", "resolved": "P", "no_log": False},
        "C11": {"reader1": "N", "reader2": "N", "resolved": "N", "no_log": False}}}
    inputs = {k: os.path.join(tmp, f"{k}_{'inf' if informative else 'not'}") for k in
              ("expected", "awareness", "lines", "addendum", "phase_b_results", "phase_b_expected", "r1_certs")}
    _write_json(inputs["expected"], exp)
    _write_json(inputs["awareness"], aw)
    _write_json(inputs["lines"], lines)
    with open(inputs["addendum"], "w", encoding="utf-8") as handle:
        handle.write("| Key | Class | Reference |\n|---|---|---|\n" + "".join(
            f"| {k} | B | ref |\n" for k in sorted(ADDENDUM_SOURCES)))
    pbc = {"pairs": 12, "detections": 7, "generic": 3, "declared": 4, "k2_only": 0, "clean_passes": 7, "detection_lower": 0.355981,
           "clean_lower": 0.355981, "pairs_ge_10": True, "verdict": "FAILS", "detection_rate": 0.58, "clean_rate": 0.58}
    _write_json(inputs["phase_b_results"], {"primary_version": "v040", "gate": {"classes": {"B-1": pbc}, "b2_subtypes": {},
                                                                              "out_of_scope": {"O-1": {"pairs": 2, "detections": 1, "clean_passes": 2}}}})
    _write_json(inputs["phase_b_expected"], {"cases": {
        "P1": {"class": "B-1", "subtype": "", "in_scope": True, "world_id": "W01", "source": "S", "expected": []},
        "P2": {"class": "O", "subtype": "O-1", "in_scope": False, "world_id": "W02", "source": "S", "expected": []}}})
    for case in ("P1", "P2"):
        for twin in TWINS:
            _write_json(os.path.join(inputs["r1_certs"], f"evaluation__phase_b__cases__{case}__{twin}.py.json"),
                        _syn_cert("v050", "WEAK", [_syn_comp("WEAK", [], _stream(holds=190, undefined=10, hard=0),
                                                              _stream(holds=0, undefined=50, hard=50))]))
    return out, inputs


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
    perfect = add_bounds({"pairs": 10, "detections": 10, "clean_passes": 10})
    nine = add_bounds({"pairs": 10, "detections": 9, "clean_passes": 10})
    eight = add_bounds({"pairs": 10, "detections": 8, "clean_passes": 10})
    few = add_bounds({"pairs": 5, "detections": 5, "clean_passes": 5})
    check("10/10 and 10/10 HOLDS", perfect["verdict"] == "HOLDS")
    check("9/10 detections and 10/10 clean HOLDS (0.6523 >= 0.6)", nine["verdict"] == "HOLDS")
    check("8/10 detections FAILS (0.5408 < 0.6)", eight["verdict"] == "FAILS")
    check("5 pairs always FAILS (pairs < 10)", few["verdict"] == "FAILS")

    # P-7 item 5 bound
    check("too-small bound at n = 200 is 0.0808 (P-7: 0.081)", abs(too_small_bound(200) - 0.080822) < 1e-5, f"{too_small_bound(200):.6f}")
    check("too-small bound at n = 100 is 0.0936", abs(too_small_bound(100) - 0.093589) < 1e-5, f"{too_small_bound(100):.6f}")

    # information and capping flags
    for f in ("K1_ABSTAINED:world:minus", "K1_ABSTAINED_MAJORITY:world:plus", "K2_MINUS_UNREAD", "K8_SOME_CHANGES", "BAD_RETURN"):
        check(f"{f} is an information or capping flag", is_information_flag(f))
    for f in ("K2_NO_SEPARATION", "K1_UNDEFINED", "HIGH_RATE:probe:noise", "K2_HIGH_SIZE", "K5_INCONCLUSIVE:zeros"):
        check(f"{f} is not an information flag", not is_information_flag(f))

    # P-7 item 3: causes
    def cc(plus, minus=None, null=None):
        k1 = {"world:plus": plus, "world:minus": minus or _stream(holds=10)}
        if null:
            k1["world:null"] = null
        return {"k1": k1}
    check("cause hard: hard_undefined > 0 on a K1 stream", classify_cause(cc(_stream(undefined=200, hard=200))) == "hard")
    check("cause hard on world:null only", classify_cause(cc(_stream(), null=_stream(undefined=3, hard=3))) == "hard")
    check("cause plus majority: 2 * undefined > n", classify_cause(cc(_stream(undefined=101))) == "plus majority")
    check("cause soft only: exactly half is not a majority", classify_cause(cc(_stream(undefined=100))) == "soft only")
    check("cause soft only: soft abstention on minus only", classify_cause(cc(_stream(), minus=_stream(undefined=190))) == "soft only")
    check("cause unknown: no 0.5.0 component", classify_cause(None) == "unknown")
    check("hard wins over plus majority", classify_cause(cc(_stream(undefined=150, hard=1))) == "hard")

    # run-log logic (P-7 item 2)
    check("no certificate, exit 4 is a gate exit: a result, not an infrastructure failure",
          not is_infrastructure_failure(False, False, 4, None))
    check("no certificate, exit 9: infrastructure failure", is_infrastructure_failure(False, False, 9, None))
    check("no certificate, exit code None: infrastructure failure", is_infrastructure_failure(False, False, None, None))
    check("no certificate, runner crash: infrastructure failure", is_infrastructure_failure(False, False, 0, "OSError"))
    check("timeout is a result", not is_infrastructure_failure(False, True, None, None))
    check("certificate present is never an infrastructure failure", not is_infrastructure_failure(True, False, 9, None))
    check("next attempt: no prior is attempt 1", next_attempt(None, False, False) == 1)
    check("next attempt: first infrastructure failure gives attempt 2",
          next_attempt({"attempt": 1, "infra_failure": True, "has_certificate": False}, False, False) == 2)
    check("next attempt: second infrastructure failure is final",
          next_attempt({"attempt": 2, "infra_failure": True, "has_certificate": False}, False, False) is None)
    check("next attempt: a result with certificate is final",
          next_attempt({"attempt": 1, "infra_failure": False, "has_certificate": True}, True, False) is None)
    check("next attempt: timeout is final", next_attempt({"attempt": 1, "timed_out": True, "has_certificate": False}, False, False) is None)
    check("next attempt: --redo starts at 1", next_attempt({"attempt": 2, "infra_failure": True}, False, True) == 1)
    check("addendum table parser", parse_addendum_sources("| Key | C |\n|---|---|\n| KRI10 | B-1 |\n| MOR03 | B-1 |\n| x | y |\n")
          == frozenset({"KRI10", "MOR03"}))

    with tempfile.TemporaryDirectory() as tmp:
        out, inputs = _make_scenario(tmp, True)
        res = build_results(out, inputs)
        pairs = {p["case"]: p for p in res["pairs"]}
        v50 = lambda c: pairs[c]["versions"]["v050"]  # noqa: E731
        v41 = lambda c: pairs[c]["versions"]["v041"]  # noqa: E731
        check("T02 detected under 0.5.0 (K2_NO_SEPARATION counts; K1_ABSTAINED_MAJORITY does not)",
              v50("T02")["detected"] and v50("T02")["expected_present"] == ["K2_NO_SEPARATION"] and v50("T02")["k2_only"])
        check("T04 generic detection, K1_ABSTAINED:world:minus not counted",
              v50("T04")["label"] == "generic" and v50("T04")["expected_present"] == ["K5_HOLDS_ON_NOISE"])
        check("T10 NOT_FALSIFIABLE with information flags only is a miss, although they are in the expected list",
              not v50("T10")["detected"] and v50("T10")["expected_present"] == [])
        check("T10 fixed WEAK is a clean pass", v50("T10")["clean"])
        check("T05 missing 0.5.0 certificate: miss and MISSING shown", not v50("T05")["detected"]
              and v50("T05")["faulty_verdict"].startswith("MISSING"))
        check("T07 label: world:minus 16/200 <= 0.0808, no expected flag, miss", pairs["T07"]["label_error_too_small"])
        check("T08 no label: 17/200 > 0.0808", not pairs["T08"]["label_error_too_small"])
        check("T09 no label: detected (has expected flag)", not pairs["T09"]["label_error_too_small"] and v50("T09")["detected"])
        check("T06 labelled: WEAK under 0.5.0 (a miss), world:minus 10/200, no expected flag",
              pairs["T06"]["label_error_too_small"])
        check("T03 not detected (WEAK), T03 no flag", not v50("T03")["detected"])
        check("B-2 subtype rows are marked descriptive (fewer than 10 pairs), classes carry no such mark",
              res["gate"]["v050"]["b2_subtypes"]["L1.3"]["descriptive"] is True
              and res["gate"]["v050"]["b2_subtypes"]["L1.3"]["class_verdict"] is False
              and "descriptive" not in res["gate"]["v050"]["classes"]["B-2"]
              and "(descriptive, not a class verdict)" in render_markdown(res))
        tf = lambda verdict, flags=(), minus=_stream(holds=8): {  # noqa: E731
            "status": "ok", "verdict": verdict, "counted": list(flags), "flags": list(flags), "components": [
                {"id": "C", "regime": "all", "verdict": verdict, "flags": list(flags), "k1": {"world:minus": minus}}]}
        check("P-8 item 4: WEAK miss, no expected flag, minus 8/200: labelled", too_small_label(tf("WEAK"), [], False)["applies"])
        check("P-8 item 4: FALSIFIABLE miss labelled", too_small_label(tf("FALSIFIABLE"), [], False)["applies"])
        check("P-8 item 4: NOT_FALSIFIABLE miss without expected flag gets no label", not too_small_label(tf("NOT_FALSIFIABLE"), [], False)["applies"])
        check("P-8 item 4: UNDEFINED miss gets no label", not too_small_label(tf("UNDEFINED"), [], False)["applies"])
        check("P-8 item 4: two components get no label", not too_small_label(
            dict(tf("WEAK"), components=tf("WEAK")["components"] * 2), [], False)["applies"])
        c50 = res["gate"]["v050"]["classes"]
        c41 = res["gate"]["v041"]["classes"]
        check("0.5.0 B-1 counts: 5 pairs, detections T02 T04 = 2, generic 1", (c50["B-1"]["pairs"], c50["B-1"]["detections"], c50["B-1"]["generic"]) == (5, 2, 1),
              str(c50["B-1"]))
        check("0.5.0 B-1 clean passes: T03 T04 T05 (T01 UNDEFINED, T02 NOT_FALSIFIABLE) = 3", c50["B-1"]["clean_passes"] == 3, str(c50["B-1"]["clean_passes"]))
        check("0.4.1 B-1 detections: T04 only = 1", c41["B-1"]["detections"] == 1, str(c41["B-1"]["detections"]))
        check("B-2 L1.3 subtype has one pair", res["gate"]["v050"]["b2_subtypes"]["L1.3"]["pairs"] == 1)
        check("out-of-scope O-1: counts only", "detection_lower" not in res["gate"]["v050"]["out_of_scope"]["O-1"])
        check("noise-only 0.5.0 B-1 detections = 1 (T04); declared-only = 1 (T02)",
              res["baselines"]["noise_only"]["v050"]["classes"]["B-1"]["detections"] == 1
              and res["baselines"]["declared_only"]["v050"]["classes"]["B-1"]["detections"] == 1)
        check("noise-only second line from 0.4.1 present", res["baselines"]["noise_only"]["v041"]["classes"]["B-1"]["detections"] == 1)
        fe = res["baselines"]["flag_everything"]["classes"]["B-1"]
        check("flag-everything: 5 detections, 0 clean", (fe["detections"], fe["clean_passes"]) == (5, 0))
        # comparison
        cmp_ = res["comparison"]
        check("comparison informative: 6 files with an UNDEFINED component under 0.4.1", cmp_["informative"]
              and cmp_["files_with_undefined_v041"] == 6, str(cmp_["files_with_undefined_v041"]))
        pc = cmp_["per_class"]["B-1"]
        check("B-1 components UNDEFINED under 0.4.1: 6", pc["components_undefined_v041"] == 6, str(pc))
        check("causes: hard 2 (T01 x2), plus majority 2 (T02 x2), soft only 1 (T03), unknown 1 (T05)",
              pc["causes"] == {"hard": 2, "plus majority": 2, "soft only": 1, "unknown": 1}, str(pc["causes"]))
        check("detections gained: T02", pc["detections_gained"] == ["T02"], str(pc["detections_gained"]))
        check("clean passes gained: none", pc["clean_passes_gained"] == [], str(pc["clean_passes_gained"]))
        check("faulty UNDEFINED -> WEAK listed (T03)", pc["faulty_undefined_to_falsifiable_or_weak"] == ["T03"])
        check("fixed UNDEFINED -> NOT_FALSIFIABLE listed (T02)", pc["fixed_undefined_to_not_falsifiable"] == ["T02"])
        check("K1_ABSTAINED_MAJORITY component listed (T02 faulty)", pc["components_with_k1_abstained_majority"] == ["T02/faulty/C"],
              str(pc["components_with_k1_abstained_majority"]))
        check("T05 not comparable (0.5.0 faulty certificate missing)", [(d["case"], d["twin"]) for d in cmp_["not_comparable"]] == [("T05", "faulty")])
        check("loss of a 0.4.1 detection (T06) and of a 0.4.1 clean pass (T06) is found",
              [d["case"] for d in cmp_["detections_lost"]] == ["T06"] and [d["case"] for d in cmp_["clean_passes_lost"]] == ["T06"]
              and not cmp_["no_loss"])
        check("no 'no change' when something was gained", cmp_["no_change"] is False)
        md = render_markdown(res)
        check("markdown marks the loss loudly", "**LOSS: 0.4.1 detections lost under 0.5.0: T06" in md and "**LOSS: 0.4.1 clean passes lost" in md)
        # overlap, awareness
        ov = res["overlap"]["B-1"]
        check("B-1: 3 of 5 pairs overlap (more than half) -> wording", ov["overlapping_pairs"] == 3 and ov["largely_repeats_phase_b"], str(ov))
        check("B-1: addendum-source pairs 2 (T03 MOR03, T05 KRI10), minimum 4 not met",
              ov["addendum_source_pairs"] == 2 and ov["new_source_minimum_met"] is False)
        check("B-6: 3 pairs, 1 overlapping? no: 0 overlap, wording off", res["overlap"]["B-6"]["overlapping_pairs"] == 0
              and not res["overlap"]["B-6"]["largely_repeats_phase_b"] and res["overlap"]["B-6"]["addendum_source_pairs"] == 1)
        check("markdown carries the Phase B wording for B-1", OVERLAP_WORDING in md)
        no_ov = res["gate_without_overlapping_pairs"]["v050"]["classes"]["B-1"]
        check("B-1 without overlapping pairs: 2 pairs (T03, T05)", no_ov["pairs"] == 2, str(no_ov["pairs"]))
        sh = res["awareness_shares_resolved"]["B-1"]
        check("resolved shares B-1: P 3 (C01 no log, C02, C05), C 1, N 1", (sh["P"], sh["C"], sh["N"], sh["no_log_in_P"]) == (3, 1, 1, 1), str(sh))
        check("every class verdict line carries the awareness words and shares",
              all(f"* {l} (0.5.0)" in md for l in IN_SCOPE_CLASSES) and md.count(AWARENESS_WORDS) >= 8)
        rs = res["awareness_counts"]["resolved"]["B-1"]
        r1 = res["awareness_counts"]["reader1"]["B-1"]
        check("awareness counts: resolved B-1 P/C/N and reader 1 'no log' shown", (rs["P"], rs["C"], rs["N"]) == (3, 1, 1) and r1["no log"] == 1)
        # abstention
        ab = res["abstention"]["phase_c_v050"]["B-1"]["faulty"]
        check("abstention B-1 faulty (0.5.0): sum soft / sum n over K1 streams of T01 T02 T03 T04",
              (ab["soft_undefined"], ab["n"]) == (120 + 30, 8 * 200) and ab["checks"] == 4, str(ab))
        pb = res["abstention"]["phase_b_r1_v050"]["B-1"]["faulty"]
        check("Phase B abstention: hard_undefined excluded (minus 50 hard), plus 10 soft", (pb["soft_undefined"], pb["n"]) == (10, 400), str(pb))
        check("Phase B next to Phase C present", res["phase_b_next_to_c"]["phase_b"]["classes"]["B-1"]["pairs"] == 12)
        # determinism
        write_outputs(out, res)
        a = [open(os.path.join(out, n), "rb").read() for n in ("RESULTS.json", "RESULTS.md")]
        write_outputs(out, build_results(out, inputs))
        b = [open(os.path.join(out, n), "rb").read() for n in ("RESULTS.json", "RESULTS.md")]
        check("report is byte-identical on a second build", a == b)

        # not informative: fewer than 5 files with an UNDEFINED component
        out2, inputs2 = _make_scenario(tmp, False)
        res2 = build_results(out2, inputs2)
        c2 = res2["comparison"]
        check("not informative: 2 files with UNDEFINED under 0.4.1 (T01 faulty and fixed)", not c2["informative"]
              and c2["files_with_undefined_v041"] == 2 and c2["per_class"] is None, str(c2["files_with_undefined_v041"]))
        check("not informative: losses still reported", "T06" in [d["case"] for d in c2["detections_lost"]])
        md2 = render_markdown(res2)
        check("not informative markdown says so and has no per-class table", "**NOT INFORMATIVE**" in md2 and "faulty UNDEFINED -> FALSIFIABLE/WEAK" not in md2)
        # "no change" statement: identical versions
        out3 = os.path.join(tmp, "run_same")
        for version in ("v050", "v041"):
            for case, twin in (("T04", "faulty"), ("T04", "fixed")):
                body = _syn_cert(version, "NOT_FALSIFIABLE" if twin == "faulty" else "FALSIFIABLE",
                                 [_syn_comp("NOT_FALSIFIABLE" if twin == "faulty" else "FALSIFIABLE",
                                            ["K5_HOLDS_ON_NOISE"] if twin == "faulty" else [], _stream(holds=200), _stream(holds=10))])
                _write_json(cert_path(out3, version, case, twin), body)
        exp3 = {"cases": {"T04": load_expected(inputs["expected"])["T04"]}}
        inputs3 = dict(inputs)
        inputs3["expected"] = os.path.join(tmp, "expected_same")
        _write_json(inputs3["expected"], exp3)
        res3 = build_results(out3, inputs3)
        check("no change: fewer than 5 UNDEFINED files is 'not informative' (per-class statement withheld)", not res3["comparison"]["informative"]
              and res3["comparison"]["no_loss"])
    print("selftest: " + ("all passed" if not failures else f"{len(failures)} FAILED"))
    return 0 if not failures else 1


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run the gate on every twin of every case")
    run.add_argument("--version", required=True, choices=sorted(VERSIONS))
    run.add_argument("--worktree", required=True, help="clean git worktree of the tag")
    run.add_argument("--cases-dir", default=None, help="default: evaluation/phase_c/cases")
    run.add_argument("--expected", default=None, help="default: evaluation/phase_c/EXPECTED_FLAGS.json")
    run.add_argument("--out", default=None, help="default: evaluation/phase_c/run")
    run.add_argument("--timeout", type=float, default=TIME_LIMIT, help="seconds per check (default 3600)")
    run.add_argument("--redo", action="store_true", help="re-run checks that are already done")
    rep = sub.add_parser("report", help="write RESULTS.json and RESULTS.md")
    rep.add_argument("--out", default=None, help="default: evaluation/phase_c/run")
    rep.add_argument("--expected", default=None, help="default: evaluation/phase_c/EXPECTED_FLAGS.json")
    rep.add_argument("--awareness", default=None, help="default: evaluation/phase_c/record/designer/AWARENESS_RESULT.json")
    rep.add_argument("--lines", default=None, help="default: evaluation/phase_c/record/designer/DESIGNER_LINES.json")
    rep.add_argument("--addendum", default=None, help="default: evaluation/phase_c/SOURCES_ADDENDUM.md")
    rep.add_argument("--phase-b-results", dest="phase_b_results", default=None, help="default: evaluation/phase_b/run/RESULTS.json")
    rep.add_argument("--phase-b-expected", dest="phase_b_expected", default=None, help="default: evaluation/phase_b/EXPECTED_FLAGS.json")
    rep.add_argument("--r1-certs", dest="r1_certs", default=None, help="default: evaluation/r1_v050/certs")
    sub.add_parser("selftest", help="check the metric code on synthetic certificates")
    return parser


def main(argv: "list | None" = None) -> int:
    args = build_parser().parse_args(argv)
    return {"run": cmd_run, "report": cmd_report, "selftest": cmd_selftest}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
