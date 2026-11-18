#!/usr/bin/env python3
"""Phase D gate runner (``PREREG_PHASE_D.md`` section 5, the RUN part only).

Modelled on the run part of ``evaluation/phase_c/run_phase_c.py`` (run rules of P-7 items 1 and 2, resume, recovery of a
dangling start line).  It runs Truth_Gate ``v0.5.1`` in full mode with default settings, ONE CHECK AT A TIME (strictly
sequential, a single process, and the only writer of the run log), on both twins of every pair in arm R (reference
world), arm W0 and arm W1.  Scoring and the report are a separate, later script.

Sub-commands
------------
``run``       pre-flight, assemble the studies, run every check.  ``--dry-run`` stops after the pre-flight, the assembly
              and the plan (nothing is written, no gate is started).
``selftest``  synthetic tests in temp dirs with a fake gate (no real case, no real freeze, no real worktree is touched).

Usage::

    py -I evaluation/phase_d/run_phase_d.py run [--worktree DIR] [--out DIR] [--timeout 3600] [--redo] [--dry-run]
    py -I evaluation/phase_d/run_phase_d.py selftest

Defaults: ``--worktree`` = ``E:\\Claude Projects\\Kapi\\worktrees\\v0.5.1`` (a git worktree of tag ``v0.5.1`` that the
designer creates; this script only checks it), ``--out`` = ``E:\\Claude Projects\\Kapi\\phase_d_work\\run``.

Pre-flight (the run is refused on any failure; ``--dry-run`` reports every item)
-----------------------------------------------------------------------------
1. ``FREEZE_PREREG_D.json``, ``FREEZE_CASES_D.json`` and ``FREEZE_RECORD_D.json`` verify (``protocol/tools/freeze.py
   verify``, cwd = ``evaluation/phase_d``: exit 0 and "FREEZE OK").
2. Protocol rule 17: ``NAMED_COMMIT`` is an ancestor of ``origin/main`` (local refs only, no fetch) and the bytes of each of
   the three freeze files at ``NAMED_COMMIT`` equal the file on disk.
3. The worktree is the top level of its own git work tree, ``HEAD`` equals ``v0.5.1^{commit}`` and ``git status
   --porcelain`` is empty (PC's ``verify_worktree``).
4. Studies: for each pair id of ``EXPECTED_FLAGS_D.json`` (each with the arms reference, W0 and W1) and each arm, the
   faulty and the fixed study are ``assemble(skeleton, body)``; ``differ_only_in_criterion`` must be True.  They are written
   to ``OUT/studies/<ARM>/<id>_<twin>.py`` (ARM in R, W0, W1) and recorded in ``OUT/STUDIES.json`` (sha256 of the assembled
   file and of the skeleton and body inputs).  An existing study file or ``STUDIES.json`` with different content is
   refused, never overwritten.  Before every check the study file is hashed again and compared.

Run rules (P-7 items 1 and 2, as PC section 6)
----------------------------------------------
* Order: ids sorted, then arm R, W0, W1, then twin faulty, fixed.
* Per-check timeout 3600 s.  A timeout is a result, is never an infrastructure failure and is not repeated; only that
  child's process tree is killed (``taskkill /T /F /PID <pid>`` on Windows).
* A gate exit 0-7 without a certificate is a result, not repeated.  An **infrastructure failure** is no certificate and an
  exit code outside 0-7 (or none), or a crash of the runner, or an attempt whose ``started`` row has no result row (crash of
  the runner or the machine; recorded as a failed attempt when the run is resumed).  It is rerun once (``MAX_ATTEMPTS`` =
  2); both attempts are logged.  After a second failure the check stays an infrastructure failure.
* Resume: a check whose last result row is final is skipped.  ``--redo`` forces every check from attempt 1; the earlier
  certificate and logs are renamed aside (``*.stale-<UTC>``) instead of being deleted, and the run log keeps every row.
* Layout under ``--out``: ``certs/<ARM>/<id>_<twin>.json``, ``logs/<ARM>/<id>_<twin>.log`` (full output; attempt 2:
  ``.attempt2.log``), ``RUNLOG.jsonl`` (one row per attempt start, event ``started``, and one per attempt end, event
  ``result``), ``STUDIES.json``, ``studies/``.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PHASE_D = HERE
PHASE_REL = "evaluation/phase_d"
TOOLS_DIR = os.path.join(PHASE_D, "tools", "tools")
FREEZE_TOOL = os.path.join(ROOT, "protocol", "tools", "freeze.py")
FREEZE_FILES = ("FREEZE_PREREG_D.json", "FREEZE_CASES_D.json", "FREEZE_RECORD_D.json")
EXPECTED_PATH = os.path.join(PHASE_D, "EXPECTED_FLAGS_D.json")
CASES_DIR = os.path.join(PHASE_D, "cases")
NAMED_COMMIT = "25bdbb212ee9562461bb2058509341632d3ce257"     # protocol rule 17: the public commit that holds the freeze
PUBLIC_REF = "origin/main"
DEFAULT_WORKTREE = r"E:\Claude Projects\Kapi\worktrees\v0.5.1"
DEFAULT_OUT = r"E:\Claude Projects\Kapi\phase_d_work\run"

GATE_TAG = "v0.5.1"
GATE_MODULE = "truth_gate"
TOOL_VERSION = "0.5.1"
# arm code (paths, run log) -> arm name in EXPECTED_FLAGS_D.json; the order is the run order
ARMS = (("R", "reference"), ("W0", "W0"), ("W1", "W1"))
TWINS = ("faulty", "fixed")

TIME_LIMIT = 3600.0             # PREREG_PHASE_D section 5: a check beyond 60 minutes is a timeout
GATE_EXIT_CODES = range(0, 8)   # P-7 item 2: gate exit codes 0-7
MAX_ATTEMPTS = 2                # P-7 item 2: an infrastructure failure is rerun once


class Refused(Exception):
    """A pre-flight rule, an assembly rule or a consistency rule refuses the run."""


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def iso(moment: datetime.datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(moment: "datetime.datetime | None" = None) -> str:
    return (moment or utc_now()).strftime("%Y%m%dT%H%M%S%fZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return sha256_bytes(handle.read())


def load_json(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def check_key(case: str, arm: str, twin: str) -> str:
    return f"{arm}/{case}_{twin}"


def study_rel(case: str, arm: str, twin: str) -> str:
    return f"studies/{arm}/{case}_{twin}.py"


def cert_path(out: str, case: str, arm: str, twin: str) -> str:
    return os.path.join(out, "certs", arm, f"{case}_{twin}.json")


def log_path(out: str, case: str, arm: str, twin: str, attempt: int = 1) -> str:
    return os.path.join(out, "logs", arm, f"{case}_{twin}" + ("" if attempt == 1 else f".attempt{attempt}") + ".log")


def runlog_path(out: str) -> str:
    return os.path.join(out, "RUNLOG.jsonl")


def studies_json_path(out: str) -> str:
    return os.path.join(out, "STUDIES.json")


def archive_existing(path: str, when: str) -> "str | None":
    """Rename an existing file aside (never delete or overwrite evidence); returns the new name."""
    if not os.path.exists(path):
        return None
    target = f"{path}.stale-{when}"
    os.replace(path, target)
    return target


# --------------------------------------------------------------------------
# git
# --------------------------------------------------------------------------

def _git_bytes(repo: str, *args: str) -> "tuple[int, bytes, bytes]":
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True)
    return proc.returncode, proc.stdout, proc.stderr


def _git(repo: str, *args: str) -> "tuple[int, str]":
    rc, out, _ = _git_bytes(repo, *args)
    return rc, out.decode("utf-8", errors="replace").strip()


def _same_path(a: str, b: str) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


# --------------------------------------------------------------------------
# pre-flight
# --------------------------------------------------------------------------

def verify_freezes(phase_dir: str, names, tool: str) -> None:
    """Item 1: every freeze manifest verifies (exit 0 and "FREEZE OK"), run with cwd = the phase folder."""
    for name in names:
        path = os.path.join(phase_dir, name)
        if not os.path.isfile(path):
            raise Refused(f"freeze manifest {name} is missing")
        proc = subprocess.run([sys.executable, tool, "verify", path], cwd=phase_dir, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        text = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0 or "FREEZE OK" not in (proc.stdout or ""):
            shown = "\n".join(text.strip().splitlines()[-10:])
            raise Refused(f"freeze verification of {name} failed (exit {proc.returncode}):\n{shown}")
        print(f"  {name}: FREEZE OK")


def verify_rule17(repo: str, named: str, ref: str, phase_rel: str, phase_dir: str, names) -> None:
    """Item 2 (protocol rule 17): ``named`` is an ancestor of ``ref`` (local refs only) and holds the freeze files."""
    rc, _ = _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    if rc != 0:
        raise Refused(f"rule 17: the local ref {ref} does not exist (no fetch is done)")
    rc, _ = _git(repo, "rev-parse", "--verify", "--quiet", f"{named}^{{commit}}")
    if rc != 0:
        raise Refused(f"rule 17: the named commit {named} does not exist in the repository")
    rc, _, err = _git_bytes(repo, "merge-base", "--is-ancestor", named, ref)
    if rc == 1:
        raise Refused(f"rule 17: the named commit {named} is not an ancestor of {ref}")
    if rc != 0:
        raise Refused(f"rule 17: git merge-base --is-ancestor failed (exit {rc}): {err.decode('utf-8', 'replace').strip()}")
    print(f"  named commit {named[:12]} is an ancestor of {ref}")
    for name in names:
        rc, blob, err = _git_bytes(repo, "show", f"{named}:{phase_rel}/{name}")
        if rc != 0:
            raise Refused(f"rule 17: {name} is not in the named commit ({err.decode('utf-8', 'replace').strip()})")
        disk_path = os.path.join(phase_dir, name)
        with open(disk_path, "rb") as handle:
            disk = handle.read()
        if disk != blob:
            raise Refused(f"rule 17: {name} on disk differs from the bytes in the named commit "
                          f"(disk sha256 {sha256_bytes(disk)[:16]}, commit sha256 {sha256_bytes(blob)[:16]})")
        print(f"  {name}: bytes equal the named commit")


def verify_worktree(repo: str, tag: str, worktree: str) -> "tuple[str, str]":
    """Item 3 (PC's ``verify_worktree``): HEAD at the tag's commit and a clean tree; returns ``(tag_commit, head)``."""
    rc1, tag_commit = _git(repo, "rev-parse", f"{tag}^{{commit}}")
    if rc1 != 0:
        raise Refused(f"cannot resolve {tag} in {repo}")
    if not os.path.isdir(worktree):
        raise Refused(f"worktree {worktree} does not exist: create it first (git worktree add --detach <DIR> {tag})")
    rc2, head = _git(worktree, "rev-parse", "HEAD")
    if rc2 != 0:
        raise Refused(f"cannot read the HEAD of the worktree {worktree} (not a git work tree?)")
    rc3, top = _git(worktree, "rev-parse", "--show-toplevel")
    if rc3 != 0 or not _same_path(top, worktree):
        raise Refused(f"{worktree} is not the top level of its own git work tree (top level: {top or 'unknown'})")
    if tag_commit != head:
        raise Refused(f"worktree {worktree} is at {head}, but {tag} is {tag_commit}: refusing to run")
    rc4, porcelain = _git(worktree, "status", "--porcelain")
    if rc4 != 0:
        raise Refused(f"git status failed in {worktree}")
    if porcelain:
        raise Refused(f"worktree {worktree} is not clean (git status --porcelain is not empty): refusing to run")
    print(f"  worktree ok: {worktree} is at {tag} ({head[:12]}), clean")
    return tag_commit, head


# --------------------------------------------------------------------------
# run set, assembly, studies
# --------------------------------------------------------------------------

def load_run_set(expected_path: str) -> list:
    """The ids of ``EXPECTED_FLAGS_D.json``, sorted; each must have exactly the arms reference, W0 and W1."""
    cases = load_json(expected_path)["cases"]
    arms_by_id: dict = {}
    for key in cases:
        if key.count("/") != 1:
            raise Refused(f"expected-flags key {key!r} is not '<id>/<arm>'")
        case, arm = key.split("/")
        arms_by_id.setdefault(case, set()).add(arm)
    wanted = {name for _, name in ARMS}
    for case, arms in sorted(arms_by_id.items()):
        if arms != wanted:
            raise Refused(f"{case} has the arms {sorted(arms)}, not {sorted(wanted)}")
    if not arms_by_id:
        raise Refused("the expected-flags file has no case")
    return sorted(arms_by_id)


def load_assembler(tools_dir: str = TOOLS_DIR):
    sys.dont_write_bytecode = True
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import importlib
    return importlib.import_module("assemble")


def skeleton_rel(case: str, arm_code: str) -> str:
    return f"cases/{case}/reference.py" if arm_code == "R" else f"cases/{case}/skeletons/{arm_code}.py"


def build_studies(phase_dir: str, ids, asm) -> dict:
    """``{check_key_without_twin_... : record}`` for every study: assembled text, hashes of text, skeleton and body."""
    studies: dict = {}
    for case in ids:
        bodies = {}
        for twin in TWINS:
            rel = f"cases/{case}/{twin}_body.py"
            path = os.path.join(phase_dir, rel)
            if not os.path.isfile(path):
                raise Refused(f"missing body file {rel}")
            with open(path, "rb") as handle:
                raw = handle.read()
            bodies[twin] = (rel, raw)
        for arm, _ in ARMS:
            sk_rel = skeleton_rel(case, arm)
            sk_path = os.path.join(phase_dir, sk_rel)
            if not os.path.isfile(sk_path):
                raise Refused(f"missing skeleton file {sk_rel}")
            with open(sk_path, "rb") as handle:
                sk_raw = handle.read()
            text = {}
            for twin in TWINS:
                try:
                    text[twin] = asm.assemble(sk_raw.decode("utf-8"), bodies[twin][1].decode("utf-8"))
                except asm.AssembleError as exc:
                    raise Refused(f"{case} arm {arm} {twin}: assembly refused: {exc}") from exc
            try:
                same = asm.differ_only_in_criterion(text["faulty"], text["fixed"])
            except asm.AssembleError as exc:
                raise Refused(f"{case} arm {arm}: differ_only_in_criterion refused: {exc}") from exc
            if same is not True:
                raise Refused(f"{case} arm {arm}: the faulty and the fixed study differ outside the inserted criterion body")
            for twin in TWINS:
                data = text[twin].encode("utf-8")
                studies[check_key(case, arm, twin)] = {
                    "case": case, "arm": arm, "twin": twin, "text": text[twin], "sha256": sha256_bytes(data),
                    "skeleton": sk_rel, "skeleton_sha256": sha256_bytes(sk_raw),
                    "body": bodies[twin][0], "body_sha256": sha256_bytes(bodies[twin][1]),
                }
    return studies


def studies_manifest(studies: dict) -> dict:
    """The deterministic content of ``STUDIES.json`` (no timestamps)."""
    return {"format": 1, "phase": "D", "gate_tag": GATE_TAG,
            "studies": {key: {k: v for k, v in rec.items() if k != "text"} for key, rec in sorted(studies.items())}}


def prepare_out(out: str, studies: dict, dry_run: bool) -> "tuple[int, int]":
    """Item 4: study files and ``STUDIES.json``; returns ``(files to write, files already identical)``.  An existing file
    with different content is refused.  A dry run writes nothing."""
    if os.path.exists(out) and not os.path.isdir(out):
        raise Refused(f"output path {out} exists and is not a directory")
    to_write = identical = 0
    for key, rec in sorted(studies.items()):
        path = os.path.join(out, study_rel(rec["case"], rec["arm"], rec["twin"]))
        if os.path.exists(path):
            if sha256_file(path) != rec["sha256"]:
                raise Refused(f"study file {path} exists with different content: it is never overwritten")
            identical += 1
        else:
            to_write += 1
    manifest = studies_manifest(studies)
    mpath = studies_json_path(out)
    if os.path.exists(mpath):
        try:
            existing = load_json(mpath)
        except (OSError, ValueError) as exc:
            raise Refused(f"{mpath} cannot be read: {exc}") from exc
        if existing != manifest:
            raise Refused(f"{mpath} exists and differs from the studies assembled now: it is never overwritten")
    if dry_run:
        return to_write, identical
    os.makedirs(out, exist_ok=True)
    for key, rec in sorted(studies.items()):
        path = os.path.join(out, study_rel(rec["case"], rec["arm"], rec["twin"]))
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(rec["text"])
            if sha256_file(path) != rec["sha256"]:
                raise Refused(f"study file {path} does not read back with the expected hash")
    if not os.path.exists(mpath):
        with open(mpath, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return to_write, identical


def make_plan(ids, studies: dict, out: str) -> list:
    plan = []
    for case in ids:
        for arm, _ in ARMS:
            for twin in TWINS:
                rec = studies[check_key(case, arm, twin)]
                plan.append({"case": case, "arm": arm, "twin": twin, "study_sha256": rec["sha256"],
                             "study": os.path.join(out, study_rel(case, arm, twin))})
    return plan


# --------------------------------------------------------------------------
# run log
# --------------------------------------------------------------------------

def read_runlog_lines(out: str) -> list:
    """Every run-log row in file order.  A line that does not parse is a half-written row (the runner or the machine died
    while writing it) and is ignored with a note; it carries no result."""
    path = runlog_path(out)
    rows: list = []
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as handle:
        lines = [ln.strip() for ln in handle if ln.strip()]
    for line in lines:
        try:
            rows.append(json.loads(line))
        except ValueError:
            print("note: a run-log line that does not parse (half-written row) is ignored")
    return rows


def result_rows(rows: list) -> list:
    return [r for r in rows if r.get("event") == "result"]


def final_rows(rows: list) -> dict:
    """``{(case, arm, twin): last result row}``; later rows win."""
    final: dict = {}
    for row in result_rows(rows):
        final[(row["case"], row["arm"], row["twin"])] = row
    return final


def append_runlog(out: str, row: dict) -> None:
    path = runlog_path(out)
    prefix = ""
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                prefix = "\n"                               # never glue a row onto a half-written line
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(prefix + json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


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
    if prior.get("infrastructure_failure") and attempt < MAX_ATTEMPTS:
        return attempt + 1
    return None


def recover_dangling(out: str) -> int:
    """A ``started`` row with no result row after it is an attempt that died with the runner or the machine: record it as
    an infrastructure failure so that the resumed check counts it (P-7 item 2)."""
    last_by_check: dict = {}
    for row in read_runlog_lines(out):
        last_by_check[(row["case"], row["arm"], row["twin"])] = row
    recovered = 0
    for (case, arm, twin), row in sorted(last_by_check.items()):
        if row.get("event") == "started":
            append_runlog(out, {
                "event": "result", "case": case, "arm": arm, "twin": twin, "attempt": row.get("attempt", 1),
                "start_utc": row.get("start_utc"), "end_utc": iso(utc_now()), "seconds": None, "exit_code": None,
                "timed_out": False, "has_certificate": False, "infrastructure_failure": True, "cert_sha256": None,
                "study_sha256": row.get("study_sha256"), "gate_tag": row.get("gate_tag"), "gate_commit": row.get("gate_commit"),
                "worktree": row.get("worktree"), "verdict": "INFRASTRUCTURE_FAILURE", "crash": None,
                "note": "started row without a result row: runner or machine crash"})
            recovered += 1
    return recovered


def acquire_lock(out: str):
    """Hold an exclusive lock for the life of the process, so that no second runner writes the run log."""
    os.makedirs(out, exist_ok=True)
    handle = open(os.path.join(out, "RUNLOG.lock"), "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        handle.close()
        raise Refused(f"another runner holds the lock of {out}: only one process may write the run log") from exc
    return handle


# --------------------------------------------------------------------------
# one check
# --------------------------------------------------------------------------

def kill_tree(proc: "subprocess.Popen") -> None:
    """Kill that child's process tree only (``taskkill /T /F /PID`` on Windows)."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    try:
        proc.kill()
    except OSError:
        pass


def run_one(worktree: str, module: str, study: str, cert: str, timeout: float) -> dict:
    """Run one gate check (``python -m <module> check STUDY --out CERT``) as a child process with cwd = worktree."""
    env = dict(os.environ)
    env["PYTHONPATH"] = worktree
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-m", module, "check", study, "--out", cert]
    start = time.perf_counter()
    proc = subprocess.Popen(cmd, cwd=worktree, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    timed_out = False
    try:
        try:
            output, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(proc)
            try:
                output, _ = proc.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                output = ""
    except BaseException:
        if proc.poll() is None:
            kill_tree(proc)
        raise
    seconds = time.perf_counter() - start
    if timed_out:
        output = (output or "") + f"\n[killed after the {timeout:g} s limit]\n"
    return {"exit_code": proc.returncode, "seconds": seconds, "timed_out": timed_out, "output": output or "", "crash": None}


def execute_checks(plan: list, out: str, worktree: str, tag_commit: str, head: str, timeout: float, redo: bool,
                   module: str = GATE_MODULE, tag: str = GATE_TAG, tool_version: str = TOOL_VERSION,
                   verify_head: bool = True, quiet: bool = False) -> dict:
    """The run loop: strictly sequential, one check at a time.  Returns the final rows by (case, arm, twin)."""
    recovered = recover_dangling(out)
    if recovered and not quiet:
        print(f"note: {recovered} earlier attempt(s) left a started row without a result; logged as infrastructure failures")
    last = final_rows(read_runlog_lines(out))
    total = len(plan)
    for index, item in enumerate(plan, start=1):
        case, arm, twin, study = item["case"], item["arm"], item["twin"], item["study"]
        cert = cert_path(out, case, arm, twin)
        attempt = next_attempt(last.get((case, arm, twin)), os.path.isfile(cert), redo)
        if attempt is None:
            if not quiet:
                print(f"{iso(utc_now())}  [{index}/{total}] {arm} {case} {twin}: skip (already done: "
                      f"{last[(case, arm, twin)].get('verdict')})")
            continue
        os.makedirs(os.path.dirname(cert), exist_ok=True)
        os.makedirs(os.path.dirname(log_path(out, case, arm, twin)), exist_ok=True)
        while True:
            if not os.path.isfile(study) or sha256_file(study) != item["study_sha256"]:
                raise Refused(f"study file {study} is missing or changed since it was assembled: refusing to run")
            if verify_head:
                if _git(worktree, "rev-parse", "HEAD")[1] != head:
                    raise Refused(f"the HEAD of {worktree} changed during the run: stopping")
            when = stamp()
            archive_existing(cert, when)                    # never mistake a stale certificate for this run's result
            archive_existing(log_path(out, case, arm, twin, attempt), when)
            started = utc_now()
            base = {"case": case, "arm": arm, "twin": twin, "attempt": attempt, "study_sha256": item["study_sha256"],
                    "gate_tag": tag, "gate_commit": head, "worktree": worktree.replace("\\", "/")}
            append_runlog(out, dict(base, event="started", start_utc=iso(started), redo=bool(redo)))
            try:
                result = run_one(worktree, module, study, cert, timeout)
            except Exception as exc:  # noqa: BLE001 - a crash of the runner is an infrastructure failure
                result = {"exit_code": None, "seconds": time.time() - started.timestamp(), "timed_out": False,
                          "output": f"runner crash: {exc!r}\n", "crash": repr(exc)}
            ended = utc_now()
            status, body = read_certificate(cert)
            has_certificate = os.path.isfile(cert)
            infra = is_infrastructure_failure(has_certificate, result["timed_out"], result["exit_code"], result["crash"])
            if result["timed_out"]:
                verdict = "TIMEOUT"
            elif body:
                verdict = body["verdict"]
            elif infra:
                verdict = "INFRASTRUCTURE_FAILURE"
            elif has_certificate:
                verdict = "INVALID"
            else:
                verdict = "NO_CERTIFICATE"
            with open(log_path(out, case, arm, twin, attempt), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(result["output"])
            row = dict(base, event="result", start_utc=iso(started), end_utc=iso(ended), seconds=round(result["seconds"], 3),
                       exit_code=result["exit_code"], timed_out=result["timed_out"], timeout_limit=timeout,
                       has_certificate=has_certificate, infrastructure_failure=infra, verdict=verdict,
                       cert_sha256=sha256_file(cert) if has_certificate else None, crash=result["crash"],
                       tool_version=body.get("tool_version") if body else None, redo=bool(redo))
            append_runlog(out, row)
            last[(case, arm, twin)] = row
            if not quiet:
                shown = verdict if (body or result["timed_out"]) else f"{verdict} (certificate {status})"
                print(f"{iso(ended)}  [{index}/{total}] {arm} {case} {twin}: {shown} (exit {result['exit_code']}) "
                      f"{result['seconds']:.1f} s"
                      + (" TIMEOUT" if result["timed_out"] else "")
                      + (f" INFRASTRUCTURE FAILURE (attempt {attempt} of {MAX_ATTEMPTS})" if infra else ""))
                sys.stdout.flush()
            if body and body.get("tool_version") != tool_version:
                raise Refused(f"{case} {arm} {twin}: certificate says tool_version {body.get('tool_version')!r}, "
                              f"not {tool_version!r}: the worktree is not the gate under test")
            if infra and attempt < MAX_ATTEMPTS:
                attempt += 1
                continue
            break
    return last


# --------------------------------------------------------------------------
# run command
# --------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace) -> int:
    out = os.path.abspath(args.out)
    worktree = os.path.abspath(args.worktree)
    dry = args.dry_run
    failed: list = []

    def step(name: str, fn):
        print(f"pre-flight {name}")
        try:
            result = fn()
        except Refused as exc:
            print(f"  FAILED: {exc}")
            if not dry:
                raise
            failed.append(name)
            return None
        print(f"  -> OK")
        return result

    step("item 1: freezes verify", lambda: verify_freezes(PHASE_D, FREEZE_FILES, FREEZE_TOOL))
    step("item 2: rule 17 (named commit on origin/main, freeze bytes equal)",
         lambda: verify_rule17(ROOT, NAMED_COMMIT, PUBLIC_REF, PHASE_REL, PHASE_D, FREEZE_FILES))
    wt = step("item 3: worktree at the tag and clean", lambda: verify_worktree(ROOT, GATE_TAG, worktree))

    def assemble_all():
        ids = load_run_set(EXPECTED_PATH)
        studies = build_studies(PHASE_D, ids, load_assembler())
        return ids, studies

    assembled = step("assembly: skeleton + body, differ only in the criterion", assemble_all)
    prepared = None
    if assembled is not None:
        ids, studies = assembled
        prepared = step("item 4: output dir and study files",
                        lambda: prepare_out(out, studies, dry))
        if prepared is not None:
            to_write, identical = prepared
            print(f"  {len(studies)} studies: {to_write} " + ("would be written" if dry else "written")
                  + f", {identical} already present and identical; out = {out}")
    plan = make_plan(ids, studies, out) if assembled is not None else []

    if dry:
        existing = final_rows(read_runlog_lines(out)) if os.path.isfile(runlog_path(out)) else {}
        print(f"plan: {len(plan)} checks (ids {len(ids) if assembled else 0} x arms R, W0, W1 x twins faulty, fixed)")
        for index, item in enumerate(plan, start=1):
            done = existing.get((item["case"], item["arm"], item["twin"]))
            print(f"  [{index}/{len(plan)}] {item['arm']} {item['case']} {item['twin']}"
                  + (f"  (already done: {done.get('verdict')})" if done else ""))
        if failed:
            print(f"DRY RUN: pre-flight FAILED at: {'; '.join(failed)}. Nothing was run, nothing was written.")
            return 1
        print(f"DRY RUN OK: {len(plan)} checks planned. Nothing was run, nothing was written.")
        return 0

    tag_commit, head = wt
    lock = acquire_lock(out)
    try:
        last = execute_checks(plan, out, worktree, tag_commit, head, args.timeout, args.redo)
    finally:
        lock.close()
    rc, porcelain = _git(worktree, "status", "--porcelain")
    if rc != 0 or porcelain:
        print("WARNING: the worktree is not clean after the run (git status --porcelain is not empty)")
    counts: dict = {}
    for row in last.values():
        counts[row.get("verdict")] = counts.get(row.get("verdict"), 0) + 1
    print("run finished: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items(), key=lambda kv: str(kv[0]))))
    return 0


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

FAKE_GATE_MAIN = '''\
import json, os, subprocess, sys, time
EXIT = {"FALSIFIABLE": 0, "WEAK": 1, "NOT_FALSIFIABLE": 2, "UNDEFINED": 3}
args = sys.argv[1:]
assert args[0] == "check"
study = args[1]
cert = args[args.index("--out") + 1]
key = os.path.basename(os.path.dirname(study)) + "/" + os.path.splitext(os.path.basename(study))[0]
script = json.load(open(os.environ["FAKE_GATE_SCRIPT"]))
state = os.environ["FAKE_GATE_STATE"]
safe = key.replace("/", "__")
counter = os.path.join(state, safe + ".count")
n = int(open(counter).read()) if os.path.exists(counter) else 0
open(counter, "w").write(str(n + 1))
plan = script.get(key, ["ok:FALSIFIABLE"])
beh = plan[min(n, len(plan) - 1)]
print("fake gate", key, "attempt", n + 1, beh, "cwd", os.getcwd(), "pp", os.environ.get("PYTHONPATH"))
sys.stdout.flush()
if beh == "crash":
    sys.exit(9)
if beh == "gate4":
    sys.exit(4)
if beh == "sleep":
    gc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    open(os.path.join(state, safe + ".grandchild"), "w").write(str(gc.pid))
    time.sleep(120)
verdict = beh.split(":")[1]
json.dump({"body": {"verdict": verdict, "components": [], "tool_version": "0.5.1", "study_flags": [], "load_error": None}},
          open(cert, "w"))
print(verdict)
sys.exit(EXIT[verdict])
'''

SELF_SKELETON = '''"""skeleton {name}"""
import numpy as np
from truth_gate import Study, Criterion

SCALE = {scale}


def criterion(d):
    raise NotImplementedError


STUDY = Study(criteria=[Criterion("C", criterion)])
'''

SELF_BODY = '''import numpy as np


def criterion(d):
    return {value}
'''


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _make_phase(root: str, ids=("D-001", "D-002")) -> str:
    """A synthetic phase folder with cases and an expected-flags file."""
    phase = os.path.join(root, "phase")
    cases = {}
    for case in ids:
        for arm, arm_name in ARMS:
            cases[f"{case}/{arm_name}"] = {"expected": []}
            sk = SELF_SKELETON.format(name=f"{case} {arm}", scale=len(case) + len(arm))
            _write(os.path.join(phase, skeleton_rel(case, arm)), sk)
        _write(os.path.join(phase, "cases", case, "faulty_body.py"), SELF_BODY.format(value="True"))
        _write(os.path.join(phase, "cases", case, "fixed_body.py"), SELF_BODY.format(value="False"))
    with open(os.path.join(phase, "EXPECTED_FLAGS_D.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"cases": cases}, handle)
    return phase


def _process_alive(pid: int) -> bool:
    if os.name == "nt":
        proc = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return any(tok == str(pid) for tok in proc.stdout.split())
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _git_run(repo: str, *args: str) -> str:
    proc = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid", "-c", "commit.gpgsign=false",
                           "-c", "core.autocrlf=false", *args], cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {args} failed: {proc.stderr}")
    return proc.stdout.strip()


def _expect_refused(fn, fragment: str = "") -> "tuple[bool, str]":
    try:
        fn()
    except Refused as exc:
        return (fragment in str(exc)), str(exc).splitlines()[0]
    return False, "no refusal"


def cmd_selftest(_: argparse.Namespace) -> int:
    import shutil
    import tempfile
    failures: list = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        print(("ok    " if cond else "FAIL  ") + name + (f"  [{detail}]" if detail else ""))
        if not cond:
            failures.append(name)

    tmp = tempfile.mkdtemp(prefix="phase_d_selftest_")
    old_env = {k: os.environ.get(k) for k in ("FAKE_GATE_SCRIPT", "FAKE_GATE_STATE")}
    grandchildren: list = []
    try:
        # ---- pure run-log logic (P-7 item 2)
        check("no certificate, exit 4 is a gate exit: a result", not is_infrastructure_failure(False, False, 4, None))
        check("no certificate, exit 9: infrastructure failure", is_infrastructure_failure(False, False, 9, None))
        check("no certificate, no exit code: infrastructure failure", is_infrastructure_failure(False, False, None, None))
        check("runner crash: infrastructure failure", is_infrastructure_failure(False, False, 0, "OSError"))
        check("timeout is a result", not is_infrastructure_failure(False, True, None, None))
        check("certificate present is never an infrastructure failure", not is_infrastructure_failure(True, False, 9, None))
        check("next attempt: no prior is 1", next_attempt(None, False, False) == 1)
        check("next attempt: infra failure at attempt 1 gives 2",
              next_attempt({"attempt": 1, "infrastructure_failure": True}, False, False) == 2)
        check("next attempt: infra failure at attempt 2 is final",
              next_attempt({"attempt": 2, "infrastructure_failure": True}, False, False) is None)
        check("next attempt: a normal result is final",
              next_attempt({"attempt": 1, "infrastructure_failure": False, "has_certificate": True}, True, False) is None)
        check("next attempt: redo gives 1", next_attempt({"attempt": 2, "infrastructure_failure": False}, True, True) == 1)
        check("next attempt: certificate the log speaks of is gone gives 1",
              next_attempt({"attempt": 1, "has_certificate": True}, False, False) == 1)

        # ---- pre-flight item 1: freezes
        fdir = os.path.join(tmp, "freeze")
        _write(os.path.join(fdir, "a.txt"), "alpha\n")
        import importlib.util
        spec = importlib.util.spec_from_file_location("freeze_tool", FREEZE_TOOL)
        ft = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ft)
        files = {"a.txt": ft.sha256_file(os.path.join(fdir, "a.txt"))}
        _write(os.path.join(fdir, "FREEZE_T.json"), json.dumps(
            {"freeze_format": 1, "created_utc": "2026-01-01T00:00:00Z", "algorithm": "sha256", "files": files,
             "core_sha256": ft.core_hash(files)}))
        try:
            verify_freezes(fdir, ["FREEZE_T.json"], FREEZE_TOOL)
            ok = True
        except Refused:
            ok = False
        check("freeze that verifies passes pre-flight", ok)
        _write(os.path.join(fdir, "a.txt"), "alpha changed\n")
        ok, msg = _expect_refused(lambda: verify_freezes(fdir, ["FREEZE_T.json"], FREEZE_TOOL), "freeze verification")
        check("modified frozen file refuses the run", ok, msg)
        ok, msg = _expect_refused(lambda: verify_freezes(fdir, ["FREEZE_MISSING.json"], FREEZE_TOOL), "missing")
        check("missing freeze manifest refuses the run", ok, msg)

        # ---- pre-flight items 2 and 3 with a temp git repo
        repo = os.path.join(tmp, "repo")
        os.makedirs(repo)
        _git_run(repo, "init", "-q")
        _write(os.path.join(repo, "evaluation", "phase_d", "FREEZE_T.json"), "{\"v\": 1}\n")
        _git_run(repo, "add", "-A")
        _git_run(repo, "commit", "-q", "-m", "c1")
        c1 = _git_run(repo, "rev-parse", "HEAD")
        _git_run(repo, "tag", "v0.5.1")
        _git_run(repo, "update-ref", "refs/remotes/origin/main", c1)
        pdir = os.path.join(repo, "evaluation", "phase_d")
        try:
            verify_rule17(repo, c1, "origin/main", PHASE_REL, pdir, ["FREEZE_T.json"])
            ok = True
        except Refused:
            ok = False
        check("rule 17: named commit on origin/main with equal bytes passes", ok)
        with open(os.path.join(pdir, "FREEZE_T.json"), "ab") as handle:
            handle.write(b"\n")
        ok, msg = _expect_refused(lambda: verify_rule17(repo, c1, "origin/main", PHASE_REL, pdir, ["FREEZE_T.json"]),
                                  "differs from the bytes")
        check("rule 17: a freeze file whose bytes differ from the named commit refuses", ok, msg)
        _git_run(repo, "checkout", "-q", "--", "evaluation/phase_d/FREEZE_T.json")
        _write(os.path.join(repo, "other.txt"), "x\n")
        _git_run(repo, "add", "-A")
        _git_run(repo, "commit", "-q", "-m", "c2")
        c2 = _git_run(repo, "rev-parse", "HEAD")
        ok, msg = _expect_refused(lambda: verify_rule17(repo, c2, "origin/main", PHASE_REL, pdir, ["FREEZE_T.json"]),
                                  "not an ancestor")
        check("rule 17: a named commit that is not an ancestor of origin/main refuses", ok, msg)
        ok, msg = _expect_refused(lambda: verify_rule17(repo, c1, "origin/nowhere", PHASE_REL, pdir, ["FREEZE_T.json"]),
                                  "does not exist")
        check("rule 17: a missing local ref refuses (no fetch)", ok, msg)
        ok, msg = _expect_refused(lambda: verify_rule17(repo, c1, "origin/main", PHASE_REL, pdir, ["NOT_THERE.json"]),
                                  "not in the named commit")
        check("rule 17: a freeze file absent from the named commit refuses", ok, msg)

        # worktree: the repo is at c2 now, the tag at c1
        ok, msg = _expect_refused(lambda: verify_worktree(repo, "v0.5.1", repo), "is at")
        check("worktree at another commit than the tag refuses", ok, msg)
        _git_run(repo, "checkout", "-q", "--detach", "v0.5.1")
        try:
            tc, hd = verify_worktree(repo, "v0.5.1", repo)
            ok = (tc == hd == c1)
        except Refused:
            ok = False
        check("worktree at the tag and clean passes", ok)
        _write(os.path.join(repo, "dirt.txt"), "untracked\n")
        ok, msg = _expect_refused(lambda: verify_worktree(repo, "v0.5.1", repo), "not clean")
        check("dirty worktree refuses", ok, msg)
        os.remove(os.path.join(repo, "dirt.txt"))
        ok, msg = _expect_refused(lambda: verify_worktree(repo, "v0.5.1", os.path.join(tmp, "no_such_worktree")), "does not exist")
        check("missing worktree refuses", ok, msg)
        ok, msg = _expect_refused(lambda: verify_worktree(repo, "v0.5.1", os.path.join(repo, "evaluation")), "top level")
        check("a subfolder of a repo is not a worktree", ok, msg)
        ok, msg = _expect_refused(lambda: verify_worktree(repo, "v9.9.9", repo), "cannot resolve")
        check("unknown tag refuses", ok, msg)

        # ---- run set, assembly (real assembler) and refusal on differ_only_in_criterion False
        phase = _make_phase(tmp)
        ids = load_run_set(os.path.join(phase, "EXPECTED_FLAGS_D.json"))
        check("run set: sorted ids from the expected file", ids == ["D-001", "D-002"], str(ids))
        bad_expected = os.path.join(tmp, "bad_expected.json")
        _write(bad_expected, json.dumps({"cases": {"D-001/reference": {}, "D-001/W0": {}}}))
        ok, msg = _expect_refused(lambda: load_run_set(bad_expected), "arms")
        check("run set: an id without all three arms refuses", ok, msg)
        asm = load_assembler(TOOLS_DIR)
        studies = build_studies(phase, ids, asm)
        check("real assembler: 2 ids x 3 arms x 2 twins = 12 studies", len(studies) == 12, str(len(studies)))
        check("assembled faulty and fixed differ", studies["R/D-001_faulty"]["sha256"] != studies["R/D-001_fixed"]["sha256"])

        class FakeAsm:
            AssembleError = asm.AssembleError
            assemble = staticmethod(asm.assemble)
            differ_only_in_criterion = staticmethod(lambda a, b: False)
        ok, msg = _expect_refused(lambda: build_studies(phase, ids, FakeAsm), "differ outside")
        check("assembly refused when differ_only_in_criterion is False", ok, msg)

        # ---- study files and STUDIES.json (item 4)
        out = os.path.join(tmp, "out_studies")
        n_write, n_same = prepare_out(out, studies, dry_run=True)
        check("dry run writes nothing", not os.path.exists(out) and (n_write, n_same) == (12, 0))
        n_write, n_same = prepare_out(out, studies, dry_run=False)
        check("studies written under OUT/studies/<ARM>/<id>_<twin>.py with STUDIES.json",
              os.path.isfile(os.path.join(out, "studies", "W1", "D-002_fixed.py")) and os.path.isfile(studies_json_path(out))
              and (n_write, n_same) == (12, 0))
        manifest = load_json(studies_json_path(out))["studies"]["W0/D-001_faulty"]
        check("STUDIES.json records the hashes of study, skeleton and body",
              manifest["sha256"] == sha256_file(os.path.join(out, "studies", "W0", "D-001_faulty.py"))
              and manifest["skeleton_sha256"] == sha256_file(os.path.join(phase, skeleton_rel("D-001", "W0")))
              and manifest["body_sha256"] == sha256_file(os.path.join(phase, "cases", "D-001", "faulty_body.py")))
        n_write, n_same = prepare_out(out, studies, dry_run=False)
        check("a second preparation finds everything identical and writes nothing", (n_write, n_same) == (0, 12))
        _write(os.path.join(out, "studies", "R", "D-001_faulty.py"), "# tampered\n")
        ok, msg = _expect_refused(lambda: prepare_out(out, studies, dry_run=False), "never overwritten")
        check("an existing study file with different content is refused, not overwritten", ok, msg)
        check("the tampered file was left as it was", open(os.path.join(out, "studies", "R", "D-001_faulty.py")).read() == "# tampered\n")
        out_b = os.path.join(tmp, "out_manifest")
        prepare_out(out_b, studies, dry_run=False)
        with open(studies_json_path(out_b), "w", encoding="utf-8") as handle:
            handle.write("{}")
        ok, msg = _expect_refused(lambda: prepare_out(out_b, studies, dry_run=False), "STUDIES.json".replace("STUDIES", "STUDIES"))
        check("a STUDIES.json that differs is refused", ok, msg)

        # ---- the run loop with a fake gate in a fake worktree
        worktree = os.path.join(tmp, "fake_worktree")
        _write(os.path.join(worktree, GATE_MODULE, "__init__.py"), "")
        _write(os.path.join(worktree, GATE_MODULE, "__main__.py"), FAKE_GATE_MAIN)
        state = os.path.join(tmp, "gate_state")
        os.makedirs(state)
        script_path = os.path.join(tmp, "fake_script.json")
        scenario = {
            "R/D-001_fixed": ["crash", "ok:FALSIFIABLE"],       # infrastructure failure, then a certificate: one rerun
            "W0/D-001_faulty": ["crash", "crash"],              # two infrastructure failures: no third attempt
            "W0/D-001_fixed": ["gate4"],                        # gate exit 4 without certificate: a result, no rerun
            "W1/D-001_faulty": ["sleep"],                       # timeout: no rerun, child tree killed
            "R/D-001_faulty": ["ok:NOT_FALSIFIABLE"],           # normal verdict: no rerun
        }
        with open(script_path, "w", encoding="utf-8") as handle:
            json.dump(scenario, handle)
        os.environ["FAKE_GATE_SCRIPT"] = script_path
        os.environ["FAKE_GATE_STATE"] = state
        runout = os.path.join(tmp, "run1")
        prepare_out(runout, studies, dry_run=False)
        plan = make_plan(ids, studies, runout)
        check("plan order: ids, then R/W0/W1, then faulty/fixed", [(p["case"], p["arm"], p["twin"]) for p in plan[:7]] == [
            ("D-001", "R", "faulty"), ("D-001", "R", "fixed"), ("D-001", "W0", "faulty"), ("D-001", "W0", "fixed"),
            ("D-001", "W1", "faulty"), ("D-001", "W1", "fixed"), ("D-002", "R", "faulty")])
        lock = acquire_lock(runout)
        ok, msg = _expect_refused(lambda: acquire_lock(runout), "another runner")
        check("a second runner cannot take the lock", ok, msg)
        t0 = time.perf_counter()
        last = execute_checks(plan, runout, worktree, "c" * 40, "c" * 40, 4.0, False, verify_head=False, quiet=True)
        elapsed = time.perf_counter() - t0
        lock.close()
        rows = read_runlog_lines(runout)

        def attempts(arm, case, twin):
            return [r for r in rows if r["event"] == "result" and (r["arm"], r["case"], r["twin"]) == (arm, case, twin)]

        a = attempts("R", "D-001", "faulty")
        check("normal verdict: one attempt, no rerun, certificate hashed",
              len(a) == 1 and a[0]["verdict"] == "NOT_FALSIFIABLE" and a[0]["cert_sha256"] == sha256_file(
                  cert_path(runout, "D-001", "R", "faulty")))
        a = attempts("R", "D-001", "fixed")
        check("infrastructure failure then certificate: exactly one rerun, both attempts logged",
              [(r["attempt"], r["infrastructure_failure"]) for r in a] == [(1, True), (2, False)]
              and a[1]["verdict"] == "FALSIFIABLE" and a[0]["exit_code"] == 9 and not a[0]["has_certificate"])
        check("attempt 1 log in .log and attempt 2 log in .attempt2.log, both kept",
              os.path.isfile(log_path(runout, "D-001", "R", "fixed", 1)) and os.path.isfile(log_path(runout, "D-001", "R", "fixed", 2))
              and log_path(runout, "D-001", "R", "fixed", 2).endswith("D-001_fixed.attempt2.log")
              and "attempt 1" in open(log_path(runout, "D-001", "R", "fixed", 1), encoding="utf-8").read()
              and "attempt 2" in open(log_path(runout, "D-001", "R", "fixed", 2), encoding="utf-8").read())
        a = attempts("W0", "D-001", "faulty")
        check("two infrastructure failures: two attempts, no third, final infrastructure failure",
              [(r["attempt"], r["infrastructure_failure"]) for r in a] == [(1, True), (2, True)]
              and last[("D-001", "W0", "faulty")]["verdict"] == "INFRASTRUCTURE_FAILURE")
        a = attempts("W0", "D-001", "fixed")
        check("gate exit 4 without a certificate: one attempt, a result, not an infrastructure failure",
              len(a) == 1 and a[0]["exit_code"] == 4 and not a[0]["infrastructure_failure"] and a[0]["verdict"] == "NO_CERTIFICATE")
        a = attempts("W1", "D-001", "faulty")
        check("timeout: one attempt, TIMEOUT, not an infrastructure failure, no rerun",
              len(a) == 1 and a[0]["timed_out"] and a[0]["verdict"] == "TIMEOUT" and not a[0]["infrastructure_failure"])
        gc_file = os.path.join(state, "W1__D-001_faulty.grandchild")
        check("timeout: the child started", os.path.isfile(gc_file))
        if os.path.isfile(gc_file):
            gc_pid = int(open(gc_file).read())
            grandchildren.append(gc_pid)
            time.sleep(0.5)
            check("timeout: the child's process tree was killed (grandchild dead)", not _process_alive(gc_pid))
        check("timeout log says the check was killed after the limit",
              "killed after the 4 s limit" in open(log_path(runout, "D-001", "W1", "faulty"), encoding="utf-8").read())
        check("the timeout test took about the limit, not the sleep", elapsed < 60, f"{elapsed:.1f} s")
        started = [r for r in rows if r["event"] == "started"]
        results = [r for r in rows if r["event"] == "result"]
        check("one started row per attempt and one result row per attempt", len(started) == len(results) == 12 + 2,
              f"{len(started)} started, {len(results)} results")
        needed = ("case", "arm", "twin", "attempt", "start_utc", "end_utc", "seconds", "exit_code", "timed_out",
                  "has_certificate", "infrastructure_failure", "cert_sha256", "study_sha256", "gate_tag", "gate_commit", "worktree")
        check("every result row carries the specified fields", all(k in r for r in results for k in needed))
        check("every row carries the study hash of STUDIES.json",
              all(r["study_sha256"] == studies[check_key(r["case"], r["arm"], r["twin"])]["sha256"] for r in rows))
        counts_before = {f: open(os.path.join(state, f)).read() for f in os.listdir(state) if f.endswith(".count")}

        # resume: finished checks are skipped, nothing runs again
        n_rows_before = len(read_runlog_lines(runout))
        execute_checks(plan, runout, worktree, "c" * 40, "c" * 40, 4.0, False, verify_head=False, quiet=True)
        counts_after = {f: open(os.path.join(state, f)).read() for f in os.listdir(state) if f.endswith(".count")}
        check("resume: no check is run again and no row is added", counts_before == counts_after
              and len(read_runlog_lines(runout)) == n_rows_before)

        # the study hash is checked before every check
        victim = plan[0]["study"]
        original = open(victim, encoding="utf-8").read()
        _write(victim, original + "# changed\n")
        runout2 = os.path.join(tmp, "run2")
        ok, msg = _expect_refused(lambda: execute_checks(plan[:1], runout2, worktree, "c" * 40, "c" * 40, 4.0, False,
                                                         verify_head=False, quiet=True), "changed since")
        check("a study file changed after assembly stops the run before the gate", ok, msg)
        _write(victim, original)

        # dangling recovery
        runout3 = os.path.join(tmp, "run3")
        os.makedirs(runout3)
        item = plan[1]                                                  # R D-001 fixed
        append_runlog(runout3, {"event": "started", "case": item["case"], "arm": item["arm"], "twin": item["twin"], "attempt": 1,
                                "start_utc": "2026-01-01T00:00:00Z", "study_sha256": item["study_sha256"], "gate_tag": GATE_TAG,
                                "gate_commit": "c" * 40, "worktree": "w"})
        with open(runlog_path(runout3), "a", encoding="utf-8") as handle:
            handle.write('{"event": "started", "case": "D-0')          # a half-written last line
        for f in os.listdir(state):
            os.remove(os.path.join(state, f))
        with open(script_path, "w", encoding="utf-8") as handle:     # the fake gate now always succeeds
            json.dump({}, handle)
        prepare_out(runout3, studies, dry_run=False)
        plan3 = make_plan(ids, studies, runout3)[:2]
        execute_checks(plan3, runout3, worktree, "c" * 40, "c" * 40, 4.0, False, verify_head=False, quiet=True)
        rows3 = read_runlog_lines(runout3)
        mine = [r for r in rows3 if (r["arm"], r["case"], r["twin"]) == ("R", "D-001", "fixed") and r["event"] == "result"]
        check("dangling started row: recovered as an infrastructure failure, then attempt 2 runs",
              [(r["attempt"], r["infrastructure_failure"]) for r in mine] == [(1, True), (2, False)]
              and "crash" in mine[0]["note"], str([(r["attempt"], r["verdict"]) for r in mine]))
        check("a half-written run-log line does not stop the resume and the next row starts on its own line",
              len(rows3) == len(read_runlog_lines(runout3)) and all(isinstance(r, dict) for r in rows3)
              and not any("D-0" == r.get("case") for r in rows3))
        for f in os.listdir(state):
            os.remove(os.path.join(state, f))

        # redo: every check from attempt 1, earlier files renamed aside, rows kept
        runout4 = os.path.join(tmp, "run4")
        prepare_out(runout4, studies, dry_run=False)
        plan4 = make_plan(ids, studies, runout4)[:2]
        execute_checks(plan4, runout4, worktree, "c" * 40, "c" * 40, 4.0, False, verify_head=False, quiet=True)
        execute_checks(plan4, runout4, worktree, "c" * 40, "c" * 40, 4.0, True, verify_head=False, quiet=True)
        rows4 = [r for r in read_runlog_lines(runout4) if r["event"] == "result"]
        stale = [f for f in os.listdir(os.path.join(runout4, "certs", "R")) if ".stale-" in f]
        check("redo: two result rows per check, earlier certificate renamed aside, current certificate present",
              len(rows4) == 4 and len(stale) == 2 and os.path.isfile(cert_path(runout4, "D-001", "R", "faulty")))

        # wrong tool_version in a certificate stops the run
        wrong_dir = os.path.join(tmp, "run5")
        prepare_out(wrong_dir, studies, dry_run=False)
        ok, msg = _expect_refused(lambda: execute_checks(make_plan(ids, studies, wrong_dir)[:1], wrong_dir, worktree, "c" * 40,
                                                         "c" * 40, 4.0, False, tool_version="9.9.9", verify_head=False,
                                                         quiet=True), "tool_version")
        check("a certificate with another tool_version stops the run", ok, msg)
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for pid in grandchildren:
            if _process_alive(pid):
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)

        def _onerror(func, path, _exc):
            try:
                os.chmod(path, 0o700)
                func(path)
            except OSError:
                pass
        shutil.rmtree(tmp, onerror=_onerror)
    print("selftest: " + ("all passed" if not failures else f"{len(failures)} FAILED: " + "; ".join(failures)))
    return 0 if not failures else 1


# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="pre-flight, assemble the studies, run the gate on every check")
    run.add_argument("--worktree", default=DEFAULT_WORKTREE, help="clean git worktree of tag v0.5.1")
    run.add_argument("--out", default=DEFAULT_OUT, help="output folder (certs, logs, studies, RUNLOG.jsonl)")
    run.add_argument("--timeout", type=float, default=TIME_LIMIT, help="seconds per check (default 3600)")
    run.add_argument("--redo", action="store_true", help="re-run checks that are already done (old files renamed aside)")
    run.add_argument("--dry-run", dest="dry_run", action="store_true", help="pre-flight, assembly and plan only; runs no gate")
    sub.add_parser("selftest", help="synthetic tests with a fake gate")
    return parser


def main(argv: "list | None" = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return {"run": cmd_run, "selftest": cmd_selftest}[args.command](args)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
