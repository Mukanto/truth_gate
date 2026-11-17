"""Check FREEZE_VALIDITY.json against the validity log (R3-2, R3B-3, R3B-4; D-R4-4, D-R5-3, D-R5-4).

The validity results that are frozen must be the results of the decisive runs: the first standard run of
``validity_check.py`` on the case files as they are now, in a history that holds no final drop.  This tool confirms it, pair
by pair, and (with ``--timing-arms``) confirms the per-arm timing entries.  It needs no gate.

Inputs
------
``--freeze FREEZE_VALIDITY.json`` (written by the designer) and ``--cases DIR`` (the folder that holds one case folder per
neutral id).  The log is ``<cases>/validity_log.jsonl``: ``validity_check.py`` writes to ``<parent of the case folder>/
validity_log.jsonl`` and nowhere else.  ``--log`` is optional and, if given, must be that path (anything else is refused).
``--timing-arms TIMING_ARMS.json`` (optional, written by the designer) lists the per-arm timing results.

``FREEZE_VALIDITY.json`` has the form::

    {"pairs": [{"id": "<neutral id>",
                "result": {...the RESULT.json that validity_check.py wrote for the decisive run...},
                "repairs": [{"file": "<file name>", "reason": "<text>", "after_run_sha256": "<sha256 of the file after the repair>"}, ...]},
               ...]}

``repairs`` is optional (a missing list is an empty list), one entry per repair that the pair went through; the designer may add
other keys (they are ignored).  ``result`` is the whole JSON output of the run.  It carries, besides the outcome fields,
``input_sha256`` (the SHA-256 of the five input files ``brief.json``, ``PRIVATE.json``, ``faulty_body.py``, ``fixed_body.py``,
``reference.py``) and ``decisive`` (true when the run was the first standard run on those hashes); both are written by
``validity_check.py``.

``TIMING_ARMS.json`` is a list of ``{"id", "arm", "skeleton_sha256", "body_sha256", "estimate_s", "redo": bool}``.

For every pair the tool confirms
--------------------------------
1. ``hashes``: ``result["input_sha256"]`` equals the SHA-256 of the five files currently in ``<cases>/<id>/``.
2. ``run_logged``: the log holds at least one standard run (mode "validity", ``samples`` 1000, ``seed`` 20261117, not dev) with
   ``case`` equal to the id and those five hashes.
3. ``first_is_decisive``: the first such run in the log has ``"decisive": true`` (and no later one claims it).
4. ``cites_decisive``: the result itself says ``"decisive": true`` (a result that comes from a non-decisive run is refused).
5. ``outcomes``: the logged outcome fields of that first run (``valid``, ``v1``, ``v2``, ``mech_a``, ``mech_b``, ``timing_ok``,
   ``v1_label``) equal the ones in the freeze.
6. ``no_earlier_final_drop`` (D-R5-3): the history of the id.  The tool lists every standard run with ``case == id``, in log
   order (``runs`` in the report).  The *earlier decisive runs on other hashes* are the decisive runs of the id that come before
   the pair's first run on its hashes and have other hashes.  If one of them ended in a final drop the pair is refused ("earlier
   final drop").  A final drop is a non-null ``v1_final_drop_label``, or a V1, V2 or timing failure that was computed without an
   error in that stage (``v1``, ``v2`` or ``timing_ok`` false, with no entry for the stage in ``error_stages``, its reason not
   "error", and its counts or timing present).
7. ``repairs_listed`` (D-R5-3): the number of earlier decisive runs on other hashes must not exceed the number of the pair's
   ``repairs`` ("unlisted repair"): each such run is a repaired state of the pair.

For every ``--timing-arms`` entry (key ``timing_arms`` in the report) it confirms
--------------------------------------------------------------------------------
``run_logged``: exactly one decisive ``timing_arm`` run in the log (mode "timing_arm", not dev, ``decisive`` true) has ``case`` equal
to the id, the arm, the skeleton hash and the fixed-body hash of the entry; ``estimate_equal``: that run's ``estimate_s`` equals the
entry's; ``redo_correct``: ``redo`` is true exactly when that estimate is above 1800 s.

Output: a JSON report ``{"pairs": [{"id", "pass", "checks": {...}, "problems": [...], "runs": [...]}], "timing_arms": [...],
"n_pairs", "n_pass", "all_pass"}`` (printed, and written with ``--out``).  Exit code 0 if everything passes, 1 if not, 2 on a
usage error (an unreadable or malformed input, a log path other than ``<cases>/validity_log.jsonl``, a log or freeze that does
not exist).  A pair whose case folder or files are missing fails ``hashes``.
"""
import argparse
import hashlib
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from validity_check import (INPUT_FILES, LOG_NAME, TIMING_LIMIT_S, is_standard_entry, read_log,  # noqa: E402
                            same_path)

OUTCOME_FIELDS = ("valid", "v1", "v2", "mech_a", "mech_b", "timing_ok", "v1_label")
CHECKS = ("hashes", "run_logged", "first_is_decisive", "cites_decisive", "outcomes", "no_earlier_final_drop",  # D-R5-3
          "repairs_listed")


def current_hashes(case_dir):
    """``{file: sha256}`` of the five input files of a case folder, or ``None`` for a file that is missing."""
    out = {}
    for n in INPUT_FILES:
        path = os.path.join(case_dir, n)
        if os.path.isfile(path):
            h = hashlib.sha256()
            with open(path, "rb") as f:
                h.update(f.read())
            out[n] = h.hexdigest()
        else:
            out[n] = None
    return out


def _hashes_of(entry):  # D-R5-3
    return {n: (entry.get("sha256") or {}).get(n) for n in INPUT_FILES}


def computed_failure(result, ok_key, stage, reason_key, evidence_key):  # D-R5-3
    """A stage that failed although it was computed: ``ok_key`` is false, the stage has no error, and its data is there."""
    if result.get(ok_key) is not False:
        return False
    errored = stage in (result.get("error_stages") or {}) or (result.get("reasons") or {}).get(reason_key) == "error"
    computed = "setup" not in (result.get("reasons") or {}) and bool(result.get(evidence_key))
    return computed and not errored


def is_final_drop(result):  # D-R5-3
    """A final drop: a non-null ``v1_final_drop_label``, or a V1, V2 or timing failure computed without an error in that stage."""
    if not isinstance(result, dict):
        return False
    if result.get("v1_final_drop_label"):
        return True
    counts = result.get("counts") or {}
    return (computed_failure({**result, "counts_v1": counts.get("v1")}, "v1", "V1", "v1", "counts_v1")
            or computed_failure({**result, "counts_v2": counts.get("v2")}, "v2", "V2", "v2", "counts_v2")
            or computed_failure(result, "timing_ok", "timing", "timing", "timing"))


def check_pair(pair, entries, cases_dir):
    """The report of one pair (``entries``: the parsed log)."""
    pid = pair.get("id")
    res = pair.get("result")
    checks = {k: False for k in CHECKS}
    problems = []
    if not isinstance(pid, str) or not isinstance(res, dict):
        return {"id": pid, "pass": False, "checks": checks, "problems": ["the pair needs a string id and an object result"],
                "runs": []}
    now = current_hashes(os.path.join(cases_dir, pid))
    claimed = res.get("input_sha256")
    if not isinstance(claimed, dict):
        problems.append("the result has no input_sha256")
    elif any(v is None for v in now.values()):
        problems.append("missing case file(s): " + ", ".join(n for n, v in now.items() if v is None))
    elif {n: claimed.get(n) for n in INPUT_FILES} != now:
        problems.append("input hashes differ from the current files: " + ", ".join(n for n in INPUT_FILES if claimed.get(n) != now[n]))
    else:
        checks["hashes"] = True
    want = {n: (claimed or {}).get(n) if isinstance(claimed, dict) else None for n in INPUT_FILES}
    # D-R5-3: every standard run of this id, in log order
    runs = [(i, e) for i, e in enumerate(entries)
            if is_standard_entry(e) and e.get("case") == pid and isinstance(e.get("sha256"), dict)]
    run_list = [{"log_line": i + 1, "decisive": e.get("decisive"), "same_hashes": _hashes_of(e) == want,
                 "valid": (e.get("result") or {}).get("valid"), "final_drop": is_final_drop(e.get("result"))} for i, e in runs]
    standard = [(i, e) for i, e in runs if _hashes_of(e) == want]
    if not standard:
        problems.append("no standard run (1000 samples, seed 20261117, not dev) of this id with these hashes is logged")
        return {"id": pid, "pass": False, "checks": checks, "problems": problems, "runs": run_list}
    checks["run_logged"] = True
    first_idx, first = standard[0]
    if first.get("decisive") is True and not any(e.get("decisive") is True for _, e in standard[1:]):
        checks["first_is_decisive"] = True
    elif first.get("decisive") is not True:
        problems.append("the first standard run with these hashes is not marked decisive")
    else:
        problems.append("a later run with these hashes is also marked decisive")
    if res.get("decisive") is True:
        checks["cites_decisive"] = True
    else:
        problems.append("the frozen result is not from a decisive run (decisive = %r)" % (res.get("decisive"),))
    logged = first.get("result") or {}
    diff = [f for f in OUTCOME_FIELDS if logged.get(f) != res.get(f) or (f in logged) != (f in res)]
    if diff:
        problems.append("outcome fields differ from the first standard run: " + ", ".join(
            f"{f} (log {logged.get(f)!r}, freeze {res.get(f)!r})" for f in diff))
    else:
        checks["outcomes"] = True
    # D-R5-3: the earlier decisive runs on other hashes
    earlier = [(i, e) for i, e in runs if i < first_idx and _hashes_of(e) != want and e.get("decisive") is True]
    drops = [i + 1 for i, e in earlier if is_final_drop(e.get("result"))]
    if drops:
        problems.append("earlier final drop: the decisive run(s) at log line(s) " + ", ".join(map(str, drops))
                        + " on other hashes ended in a final drop")
    else:
        checks["no_earlier_final_drop"] = True
    repairs = pair.get("repairs", [])
    if not isinstance(repairs, list) or not all(
            isinstance(r, dict) and all(isinstance(r.get(k), str) and r.get(k) for k in ("file", "reason", "after_run_sha256"))
            for r in repairs):
        problems.append('"repairs" must be a list of {"file", "reason", "after_run_sha256"} objects')
    elif len(earlier) > len(repairs):
        problems.append(f"unlisted repair: {len(earlier)} earlier decisive run(s) on other hashes, {len(repairs)} repair(s) listed")
    else:
        checks["repairs_listed"] = True
    return {"id": pid, "pass": all(checks.values()), "checks": checks, "problems": problems, "runs": run_list}


def check_timing_arm(item, entries):  # D-R5-4
    """The report of one ``--timing-arms`` entry."""
    checks = {k: False for k in ("run_logged", "estimate_equal", "redo_correct")}
    problems = []
    need = ("id", "arm", "skeleton_sha256", "body_sha256", "estimate_s", "redo")
    if not isinstance(item, dict) or any(k not in item for k in need) or not isinstance(item["redo"], bool) \
            or isinstance(item["estimate_s"], bool) or not isinstance(item["estimate_s"], (int, float)):
        return {"id": item.get("id") if isinstance(item, dict) else None, "arm": item.get("arm") if isinstance(item, dict) else None,
                "pass": False, "checks": checks,
                "problems": ['an entry needs {"id", "arm", "skeleton_sha256", "body_sha256", "estimate_s", "redo": bool}']}
    found = [e for e in entries if e.get("mode") == "timing_arm" and not e.get("dev") and e.get("decisive") is True
             and e.get("case") == item["id"] and e.get("arm") == item["arm"]
             and (e.get("sha256") or {}).get("skeleton") == item["skeleton_sha256"]
             and (e.get("sha256") or {}).get("fixed_body.py") == item["body_sha256"]]
    est = item["estimate_s"]
    if len(found) == 1:
        checks["run_logged"] = True
        logged = (found[0].get("result") or {}).get("estimate_s")
        if logged == item["estimate_s"]:
            checks["estimate_equal"] = True
        else:
            problems.append(f"the estimate differs from the decisive run (log {logged!r}, entry {item['estimate_s']!r})")
        if isinstance(logged, (int, float)):
            est = logged
    elif not found:
        problems.append("no decisive timing_arm run with this id, arm and these hashes is logged")
    else:
        problems.append(f"{len(found)} decisive timing_arm runs with these hashes are logged")
    if item["redo"] is (est > TIMING_LIMIT_S):
        checks["redo_correct"] = True
    else:
        problems.append(f"redo is {item['redo']} but the estimate {est!r} is {'above' if est > TIMING_LIMIT_S else 'not above'} "
                        f"{TIMING_LIMIT_S:.0f} s")
    return {"id": item["id"], "arm": item["arm"], "pass": all(checks.values()), "checks": checks, "problems": problems}


def check_freeze(freeze, entries, cases_dir, timing_arms=None):
    """The report of a parsed freeze file (and, if given, of a parsed ``TIMING_ARMS.json`` list)."""
    pairs = freeze["pairs"]
    if not isinstance(pairs, list):
        raise ValueError('"pairs" must be a list')
    reports = [check_pair(p if isinstance(p, dict) else {}, entries, cases_dir) for p in pairs]
    seen = {}
    for r in reports:
        seen[r["id"]] = seen.get(r["id"], 0) + 1
    for r in reports:
        if seen[r["id"]] > 1:
            r["pass"] = False
            r["problems"].append("the id occurs more than once in the freeze")
    n_pass = sum(r["pass"] for r in reports)
    out = {"pairs": reports, "n_pairs": len(reports), "n_pass": n_pass, "all_pass": n_pass == len(reports)}
    if timing_arms is not None:
        if not isinstance(timing_arms, list):
            raise ValueError("TIMING_ARMS.json must be a list")
        out["timing_arms"] = [check_timing_arm(t, entries) for t in timing_arms]
        out["all_pass"] = out["all_pass"] and all(t["pass"] for t in out["timing_arms"])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check FREEZE_VALIDITY.json against validity_log.jsonl (Phase D).")
    ap.add_argument("--freeze", required=True, metavar="FREEZE_VALIDITY.json")
    ap.add_argument("--cases", required=True, metavar="DIR")
    ap.add_argument("--log", metavar="validity_log.jsonl", help="optional; must be <cases>/validity_log.jsonl")  # D-R5-3
    ap.add_argument("--timing-arms", metavar="TIMING_ARMS.json")  # D-R5-4
    ap.add_argument("--out", metavar="REPORT.json")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    log = os.path.join(a.cases, LOG_NAME)  # D-R5-3
    if a.log is not None and not same_path(a.log, log):  # D-R5-3
        print(f"the log is {log}; --log {a.log} is not it", file=sys.stderr)  # D-R5-3
        return 2  # D-R5-3
    try:
        if not os.path.isdir(a.cases):
            raise OSError(f"{a.cases} is not a folder")
        if not os.path.isfile(log):
            raise OSError(f"{log} does not exist")
        with open(a.freeze, encoding="utf-8") as f:
            freeze = json.load(f)
        timing_arms = None
        if a.timing_arms:
            with open(a.timing_arms, encoding="utf-8") as f:
                timing_arms = json.load(f)
        entries = read_log(log)
        report = check_freeze(freeze, entries, a.cases, timing_arms)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"check_validity_log_d: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    print(text)
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
