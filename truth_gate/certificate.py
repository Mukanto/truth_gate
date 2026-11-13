"""Certificate construction, validation and the gate orchestration (spec sections 5.6, 7)."""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import platform
from typing import Any, Optional

import numpy as np

from . import guard
from .checks import VERDICTS, evaluate, study_verdict
from .external import ExternalSession
from .k8 import K8Result, k8_pass
from .manifest import Manifest, build_study, compiled_invariances, compiled_patterns, parse_manifest
from .passes import SUGGESTED_UNREVIEWED, add_component_flags, add_flags_by_component, pattern_stats
from .study import Study, StudyError, load_study

TOOL_NAME = "truth-gate"
TOOL_VERSION = "0.4.1"
SPEC_VERSION = "0.6"

NON_CLAIMS = [
    "A FALSIFIABLE certificate does not mean the hypothesis is true or that the study is well designed in every respect.",
    "All checks are relative to the synthetic worlds, premise mutators and controls that the study declares. "
    "Weak declarations give weak certificates; the certificate lists them so a reviewer can judge.",
    "The gate does not modify or repair criteria. It only reports.",
    "Generated mutations and suggested declarations are generic; they do not know your domain.",
    "A file world is only as independent as its provenance; a plus world built from the real data makes the plus and "
    "minus checks circular.",
    "The leak guard does not cover external programs; a study note lists them.",
]

KNOWN_LIMITATIONS = [
    "allow_paths are declared by the user and cannot be audited for content beyond hashing. "
    "A reviewer must inspect them.",
    "Studies are single files in v0. Importing local helper modules is not supported, "
    "because the study's directory is not on the allow-list.",
    "The identical-minus check (K2_MINUS_IDENTICAL) detects only exact identity: a minus world that changes data in an "
    "irrelevant way, below float resolution, in the wrong direction, or by too little is not detected. In stochastic "
    "mode it depends on pairing: a minus world that ignores its declared change but consumes the generator differently "
    "from plus is not detected. Read-key recording is shallow: only top-level keys are recorded. UNTESTED can hide a "
    "criterion defect: with an identical minus the criterion's own falsifiability is unknown, which is why UNTESTED does "
    "not pass the gate.",
    "External programs are hashed by executable and `uses` files only; the libraries they load are not hashed.",
    "On Windows, killing an external program does not kill programs it started.",
]

INPUT_KINDS = ("python", "manifest")
MANIFEST_EXTENSIONS = (".toml", ".json")
MANIFEST_BODY_FIELDS = ("manifest", "mutations", "pattern_stats", "suggested_unreviewed", "k8", "m_k8")

BODY_FIELDS = (
    "tool", "tool_version", "spec_version", "input_kind", "python_version", "numpy_version", "mode", "study",
    "m_comparisons", "alpha_per_bound", "components", "premise_map", "study_flags", "study_notes", "leak_log",
    "verdict", "non_claims",
)


# --------------------------------------------------------------------------
# Canonical JSON and hashing (spec section 7)
# --------------------------------------------------------------------------

def jsonable(value: Any) -> Any:
    """Convert to JSON-native types; non-finite floats become strings (allow_nan=False)."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        items = sorted(value, key=str) if isinstance(value, (set, frozenset)) else value
        return [jsonable(v) for v in items]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    return str(value)


def canonical_json(body: dict) -> str:
    """Canonical serialisation of the body (spec section 7)."""
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def body_sha256(body: dict) -> str:
    """SHA-256 of the canonical body, UTF-8 encoded (spec section 7)."""
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def make_envelope(body: dict) -> dict:
    """``{body, body_sha256, created_utc}``; the timestamp is outside the hash (spec section 7)."""
    created = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"body": body, "body_sha256": body_sha256(body), "created_utc": created}


def validate_envelope(envelope: Any) -> list:
    """Structural validation against spec section 7; returns a list of problems (empty if valid)."""
    problems: list = []
    if not isinstance(envelope, dict):
        return ["envelope is not an object"]
    if set(envelope) != {"body", "body_sha256", "created_utc"}:
        problems.append("envelope keys must be exactly body, body_sha256, created_utc")
    body = envelope.get("body")
    if not isinstance(body, dict):
        return problems + ["body is not an object"]
    for key in BODY_FIELDS:
        if key not in body:
            problems.append(f"body is missing {key!r}")
    if "created_utc" in body:
        problems.append("timestamp must not be inside the hashed body")
    if problems:
        return problems
    try:
        recomputed = body_sha256(body)
    except (TypeError, ValueError) as exc:
        return problems + [f"body is not canonicalisable: {type(exc).__name__}"]
    if recomputed != envelope.get("body_sha256"):
        problems.append("body_sha256 does not match the body")
    if body["verdict"] not in VERDICTS:
        problems.append("unknown verdict")
    if body["mode"] not in ("full", "quick"):
        problems.append("unknown mode")
    if body["tool"] != TOOL_NAME:
        problems.append("unknown tool")
    if body["input_kind"] not in INPUT_KINDS:
        problems.append("unknown input_kind")
    if not isinstance(body["study_notes"], list):
        problems.append("study_notes is not a list")
    if body["input_kind"] == "manifest":
        for key in MANIFEST_BODY_FIELDS:
            if key not in body:
                problems.append(f"body is missing {key!r}")
    for comp in body["components"]:
        for key in ("id", "regime", "verdict", "flags", "counts", "bounds"):
            if key not in comp:
                problems.append(f"component is missing {key!r}")
        if comp.get("verdict") not in VERDICTS:
            problems.append("component has an unknown verdict")
    return problems


# --------------------------------------------------------------------------
# Body assembly
# --------------------------------------------------------------------------

def describe_study(study: Study, module_sha: str, allowed_files: list) -> dict:
    """Declarations of the study, as recorded in the certificate (spec section 7, ``study``)."""
    return jsonable(
        {
            "name": study.name,
            "module_sha256": module_sha,
            "allowed_files": allowed_files,
            "deterministic": study.deterministic,
            "budget": vars(study.budget),
            "targets": vars(study.targets),
            "regimes": study.regimes,
            "worlds": {k: {"derived_from": w.derived_from, "change": w.change} for k, w in study.worlds.items()},
            "premises": [
                {"id": p.id, "role": p.role, "criteria": p.criteria, "magnitude": p.magnitude}
                for p in study.premises
            ],
            "controls": [
                {"id": c.id, "kind": "transform" if c.transform is not None else "world", "criteria": c.criteria}
                for c in study.controls
            ],
            "criteria": [
                {
                    "id": c.id,
                    "regime": c.regime,
                    "components": c.components,
                    "tolerances": c.tolerances,
                    "control_waiver": c.control_waiver,
                }
                for c in study.criteria
            ],
            "relational": [list(pair) for pair in study.relational],
        }
    )


def assemble_body(
    mode: str,
    study_desc: dict,
    result: Optional[dict],
    leak_log: list,
    load_error: Optional[dict],
    extra_study_flags=(),
    input_kind: str = "python",
    extra: Optional[dict] = None,
) -> dict:
    """Build the canonical body from an evaluation result (spec section 7).

    ``extra`` holds the fields that only a manifest run has (spec 0.6, section 11); a Python study passes none.
    """
    flags = set(extra_study_flags)
    if leak_log:
        flags.add("K6_LEAK_ATTEMPT")
    body: dict = {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "spec_version": SPEC_VERSION,
        "input_kind": input_kind,
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "mode": mode,
        "study": study_desc,
        "leak_log": leak_log,
        "study_notes": [],
        "non_claims": NON_CLAIMS,
        "known_limitations": KNOWN_LIMITATIONS,
        "load_error": load_error,
    }
    if extra:
        body.update(extra)
    if result is None:
        body.update(
            m_comparisons=0, alpha_per_bound=None, components=[], premise_map={},
            study_flags=sorted(flags), study_flag_details={}, probe_unchanged_keys={}, verdict="UNDEFINED",
        )
        return jsonable(body)
    flags.update(result["study_flags"])
    verdicts = [c["verdict"] for c in result["components"]]
    body.update(
        m_comparisons=result["m_comparisons"],
        alpha_per_bound=result["alpha_per_bound"],
        components=result["components"],
        premise_map=result["premise_map"],
        study_flags=sorted(flags),
        study_flag_details=result["study_flag_details"],
        probe_unchanged_keys=result["probe_unchanged_keys"],
        verdict=study_verdict(verdicts, flags),
    )
    return jsonable(body)


# --------------------------------------------------------------------------
# Gate orchestration
# --------------------------------------------------------------------------

def _error_record(exc: BaseException) -> dict:
    """Exception type name only; the message is kept only for StudyError (spec section 3)."""
    record = {"type": type(exc).__name__}
    if isinstance(exc, StudyError):
        record["message"] = str(exc)
    return record


def _hash_allowed_files(study: Study, study_dir: str) -> list:
    """Add ``allow_paths`` to the allow-list and hash them (spec section 5.6).

    Relative paths are resolved against the study file's directory.  The
    recorded ``path`` is the path as declared.
    """
    entries = []
    for declared in sorted(study.allow_paths):
        resolved = declared if os.path.isabs(declared) else os.path.join(study_dir, declared)
        resolved = os.path.realpath(resolved)
        guard.allow_file(resolved)
        if not os.path.isfile(resolved):
            raise StudyError(f"allow_paths entry is not an existing file: {declared}")
        with open(resolved, "rb") as handle:
            entries.append({"path": declared, "sha256": hashlib.sha256(handle.read()).hexdigest()})
    return entries


def _merge_logs(*logs: list) -> list:
    merged, seen = [], set()
    for log in logs:
        for event in log:
            key = (event["event"], event["target"])
            if key not in seen:
                seen.add(key)
                merged.append(dict(event))
    return merged


def run_gate(study_path: str, quick: bool = False) -> dict:
    """Run the gate on a study file and return the certificate envelope (spec sections 5-8).

    The leak guard is armed from before the study is loaded until after the
    second evaluation.  Raises ``FileNotFoundError`` if the file is missing.
    A ``.toml`` or ``.json`` target is a manifest (spec 0.6, section 1.2): see :func:`run_manifest_gate`.
    """
    if os.path.splitext(study_path)[1].lower() in MANIFEST_EXTENSIONS:
        return run_manifest_gate(study_path, quick)
    path = os.path.realpath(study_path)
    with open(path, "rb") as handle:
        source = handle.read()
    module_sha = hashlib.sha256(source).hexdigest()
    mode = "quick" if quick else "full"
    outcome = _guarded_run(path, source, quick)
    if outcome["study"] is None:
        desc = {"name": None, "module_sha256": module_sha, "allowed_files": []}
        body = assemble_body(mode, jsonable(desc), None, outcome["load_log"], outcome["load_error"])
        return make_envelope(body)
    desc = describe_study(outcome["study"], module_sha, outcome["allowed"])
    log1 = _merge_logs(outcome["load_log"], outcome["log1"])
    log2 = _merge_logs(outcome["load_log"], outcome["log2"])
    body1 = assemble_body(mode, desc, outcome["run1"], log1, None)
    body2 = assemble_body(mode, desc, outcome["run2"], log2, None)
    if canonical_json(body1) != canonical_json(body2):
        body1 = assemble_body(mode, desc, outcome["run1"], log1, None, ("K6_NONREPRODUCIBLE",))
    return make_envelope(body1)


def _guarded_run(path: str, source: bytes, quick: bool) -> dict:
    """Load the study and evaluate it twice under the armed guard (spec sections 5.6)."""
    out: dict = {"study": None, "load_error": None, "allowed": [], "run1": None, "run2": None,
                 "load_log": [], "log1": [], "log2": []}
    with guard.armed(path):
        try:
            study = load_study(path, source)
            out["allowed"] = _hash_allowed_files(study, os.path.dirname(path))
            out["study"] = study
        except Exception as exc:
            out["load_error"] = _error_record(exc)
        out["load_log"] = guard.take_log()
        if out["study"] is not None:
            out["run1"] = evaluate(out["study"], quick)
            out["log1"] = guard.take_log()
            out["run2"] = evaluate(out["study"], quick)
            out["log2"] = guard.take_log()
    return out


# --------------------------------------------------------------------------
# Manifest orchestration (spec 0.6, section 1.2)
# --------------------------------------------------------------------------

def run_manifest_gate(manifest_path: str, quick: bool = False) -> dict:
    """Run the gate on a manifest and return the certificate envelope.

    Step 1 (before the guard): parse and validate, read and hash the data files.  A problem there raises
    :class:`~truth_gate.common.ManifestError` (exit code 4, no certificate).  Step 2 (under the armed guard): build and
    validate the ``Study`` (an error is a load error, exit code 3), evaluate twice and compare, then run the passes.
    """
    path = os.path.realpath(manifest_path)
    with open(path, "rb") as handle:
        source = handle.read()
    mode = "quick" if quick else "full"
    spec = parse_manifest(path, source)
    # Command criteria (spec section 5): the external processes are started and shaken hands with before the guard is
    # armed (a failure there is a ManifestError, exit 4) and are closed after it is disarmed, whatever happens.
    session = ExternalSession(spec) if ExternalSession.needed(spec) else None
    try:
        notes: list = []
        if session is not None:
            session.start()
            spec.uses_files = session.uses_record
            spec.commands = session.commands_record()
        outcome = _guarded_manifest_run(spec, quick, session)
        if session is not None:
            notes = session.notes()
    finally:
        if session is not None:
            session.close()
    extra = {
        "manifest": spec.record(),
        "mutations": spec.mutation_ops(),
        "suggested_unreviewed": spec.suggested_count,
        "study_notes": notes,
    }
    if outcome["study"] is None:
        desc = {"name": None, "module_sha256": spec.sha256, "allowed_files": []}
        body = assemble_body(mode, jsonable(desc), None, outcome["load_log"], outcome["load_error"],
                             input_kind="manifest", extra={**extra, "pattern_stats": {}, "k8": {}, "m_k8": 0})
        return make_envelope(body)
    desc = describe_study(outcome["study"], spec.sha256, outcome["allowed"])
    capping = [SUGGESTED_UNREVIEWED] if spec.suggested_count else []
    run1 = add_component_flags(outcome["run1"], capping)
    run2 = add_component_flags(outcome["run2"], capping)
    log1 = _merge_logs(outcome["load_log"], outcome["log1"])
    log2 = _merge_logs(outcome["load_log"], outcome["log2"])
    body1 = assemble_body(mode, desc, run1, log1, None, input_kind="manifest", extra=extra)
    body2 = assemble_body(mode, desc, run2, log2, None, input_kind="manifest", extra=extra)
    reproducible = canonical_json(body1) == canonical_json(body2)
    # The passes come after the reproducibility comparison; their guard log is appended to the leak log.  The K8 flags
    # are added after the 0.3 suppression rules and are never suppressed (spec section 1.1, item 3).
    k8: K8Result = outcome["k8"]
    add_flags_by_component(run1, k8.flags)
    final_log = _merge_logs(log1, outcome["log3"])
    body = assemble_body(
        mode, desc, run1, final_log, None, () if reproducible else ("K6_NONREPRODUCIBLE",),
        input_kind="manifest", extra={**extra, "pattern_stats": outcome["pattern_stats"], **k8.body_fields()},
    )
    return make_envelope(body)


def _guarded_manifest_run(spec: Manifest, quick: bool, session: Optional[ExternalSession] = None) -> dict:
    """Build the study from a manifest, evaluate twice and run the passes under the armed guard (spec section 1.2)."""
    out: dict = {"study": None, "load_error": None, "allowed": [], "run1": None, "run2": None, "pattern_stats": {},
                 "k8": K8Result({}, 0, {}, False), "load_log": [], "log1": [], "log2": [], "log3": []}
    with guard.armed(spec.path):
        for real in spec.python_files:
            guard.allow_file(real)
        try:
            study = build_study(spec, session)
            invariances = compiled_invariances(spec, study)
            out["allowed"] = _hash_allowed_files(study, spec.directory)
            out["study"] = study
        except Exception as exc:
            out["load_error"] = _error_record(exc)
        out["load_log"] = guard.take_log()
        if out["study"] is not None:
            out["run1"] = evaluate(out["study"], quick)
            out["log1"] = guard.take_log()
            out["run2"] = evaluate(out["study"], quick)
            out["log2"] = guard.take_log()
            out["k8"] = k8_pass(out["study"], quick, invariances)
            out["pattern_stats"] = pattern_stats(out["study"], quick, compiled_patterns(spec))
            out["log3"] = guard.take_log()
    return out
