"""Command line interface (spec section 8)."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from typing import Optional

from . import explain as explain_module
from .badge import BadgeError, badge_payload
from .certificate import TOOL_NAME, TOOL_VERSION, body_sha256, run_gate
from .common import ManifestError
from .freeze import main as freeze_main
from .scaffold import ScaffoldError, write_scaffold
from .suggest import WARNING_LINES, suggest_manifest

EXIT_CODES = {"FALSIFIABLE": 0, "WEAK": 1, "NOT_FALSIFIABLE": 2, "UNDEFINED": 3, "UNTESTED": 6}
EXIT_USAGE = 4
EXIT_MISMATCH = 5
EXIT_VERSION = 7


class _Parser(argparse.ArgumentParser):
    """argparse with the exit code 4 for usage errors (spec section 8)."""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(EXIT_USAGE)


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="truth-gate", description="Truth_Gate: falsifiability gate for pre-registered studies.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run the gate on a study file")
    check.add_argument("study")
    check.add_argument("--out", default=None, help="certificate path (default: next to the study)")
    check.add_argument("--quick", action="store_true", help="quick mode (not certifiable)")
    verify = sub.add_parser("verify", help="re-run a study and compare body_sha256")
    verify.add_argument("certificate")
    verify.add_argument("study")
    suggest = sub.add_parser("suggest", help="write a starter manifest from one dataset (never the real study data)")
    suggest.add_argument("data", metavar="DATA", help="a CSV file: a realistic synthetic or pilot dataset")
    suggest.add_argument("--outcome", default=None, help="the outcome column")
    suggest.add_argument("--group", default=None, help="the group column (with --reference)")
    suggest.add_argument("--reference", default=None, help="the reference group value (with --group)")
    suggest.add_argument("--effect", nargs="+", action="extend", default=None, metavar="COL",
                         help="effect column(s): shuffled in the minus world, negated in a control")
    suggest.add_argument("--exchangeable", action="store_true", help="rows are exchangeable (adds the K8 row check)")
    suggest.add_argument("--out", default="truthgate.toml", help="manifest path (default: truthgate.toml)")
    init = sub.add_parser("init", help="write PREREG.md, truthgate.toml, BLIND_AUDIT_PROMPT.md and run_guarded.py")
    init.add_argument("dir", nargs="?", default=".", metavar="DIR")
    init.add_argument("--ci", action="store_true", help="also write .github/workflows/truth-gate.yml")
    freeze = sub.add_parser("freeze", help="write or verify a freeze manifest (the semantics of protocol/tools/freeze.py)")
    freeze.add_argument("args", nargs=argparse.REMAINDER, help="write FILE... -o FREEZE.json | verify FREEZE.json")
    badge = sub.add_parser("badge", help="write a shields.io endpoint JSON for a full-mode certificate")
    badge.add_argument("certificate")
    badge.add_argument("--out", default=None, help="write the JSON here (default: print it)")
    explain = sub.add_parser("explain", help="explain a flag or study note")
    explain.add_argument("flag", metavar="FLAG")
    return parser


def _reject_constant(name: str):
    raise ValueError(f"non-standard JSON constant {name}")


def load_certificate_file(path: str):
    """Read a certificate file.  NaN, Infinity and -Infinity are not JSON: a certificate containing one is unreadable
    (``ValueError``, so ``verify`` and ``badge`` exit 4 instead of failing later; R-33)."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=_reject_constant)


def default_out_path(study_path: str) -> str:
    """``STUDY.kapi.json`` next to the study (spec section 8)."""
    root, _ = os.path.splitext(study_path)
    return root + ".kapi.json"


def format_table(body: dict) -> str:
    """Human-readable table: component, verdict, flags."""
    rows = [("COMPONENT", "VERDICT", "FLAGS")]
    for comp in body["components"]:
        rows.append((comp["id"], comp["verdict"], ", ".join(comp["flags"]) or "-"))
    widths = [max(len(r[i]) for r in rows) for i in range(2)]
    lines = [f"{r[0].ljust(widths[0])}  {r[1].ljust(widths[1])}  {r[2]}" for r in rows]
    if body.get("load_error"):
        lines.append(f"study failed to load: {body['load_error']['type']}")
    lines.append(f"study flags: {', '.join(body['study_flags']) or '-'}")
    lines.append(f"mode: {body['mode']}   verdict: {body['verdict']}")
    notes = body.get("study_notes") or []
    if notes:  # spec 0.6 section 9: the table ends with the study notes
        lines.append("study notes:")
        for note in notes:
            commands = "; ".join(shlex.join(argv) for argv in note.get("commands", []))
            lines.append(f"  {note['note']}" + (f": {commands}" if commands else ""))
    return "\n".join(lines)


def _cmd_check(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.study):
        sys.stderr.write(f"truth-gate: study file not found: {args.study}\n")
        return EXIT_USAGE
    try:
        envelope = run_gate(args.study, quick=args.quick)
    except ManifestError as exc:  # spec 0.6, section 1.2: exit 4, no certificate
        sys.stderr.write(f"truth-gate: manifest error: {exc}\n")
        return EXIT_USAGE
    out = args.out if args.out else default_out_path(args.study)
    try:
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
    except OSError as exc:
        sys.stderr.write(f"truth-gate: cannot write {out}: {type(exc).__name__}\n")
        return EXIT_USAGE
    print(format_table(envelope["body"]))
    print(f"certificate: {out}")
    print(f"body_sha256: {envelope['body_sha256']}")
    return EXIT_CODES[envelope["body"]["verdict"]]


def _version_mismatch(body: dict) -> int:
    """Exit 7 (spec 0.6, section 2.4): the certificate was made by another version; never re-run the study."""
    if "tool" not in body:  # a Kapi 0.3 certificate has kapi_version instead of tool/tool_version
        made_by = f"Kapi {body['kapi_version']}" if isinstance(body.get("kapi_version"), str) else "an unknown Kapi version"
        version = body.get("kapi_version")
    else:
        made_by = f"{body['tool']} {body.get('tool_version')}"
        version = body.get("tool_version")
    tag = f"v{version}" if isinstance(version, str) and version else "of that version"
    print(
        f"VERSION MISMATCH: this certificate was made by {made_by}; this is {TOOL_NAME} {TOOL_VERSION}. "
        f"Use the matching git tag ({tag}) to verify it. The study was not re-run."
    )
    return EXIT_VERSION


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        stored = load_certificate_file(args.certificate)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"truth-gate: cannot read certificate: {type(exc).__name__}\n")
        return EXIT_USAGE
    if not os.path.isfile(args.study):
        sys.stderr.write(f"truth-gate: study file not found: {args.study}\n")
        return EXIT_USAGE
    try:
        mode = stored["body"]["mode"]
        recorded = stored["body_sha256"]
    except (KeyError, TypeError):
        sys.stderr.write("truth-gate: not a Truth_Gate certificate\n")
        return EXIT_USAGE
    body = stored["body"]
    if not isinstance(body, dict):
        sys.stderr.write("truth-gate: not a Truth_Gate certificate\n")
        return EXIT_USAGE
    # Integrity first (post-freeze revision R-2): an altered certificate reads as altered, whatever version it claims.
    if body_sha256(body) != recorded:
        print("MISMATCH: the certificate body does not match its own body_sha256")
        return EXIT_MISMATCH
    if body.get("tool") != TOOL_NAME or body.get("tool_version") != TOOL_VERSION:
        return _version_mismatch(body)
    if mode not in ("full", "quick"):
        sys.stderr.write("truth-gate: unknown mode in certificate\n")
        return EXIT_USAGE
    try:
        fresh = run_gate(args.study, quick=(mode == "quick"))
    except ManifestError as exc:
        sys.stderr.write(f"truth-gate: manifest error: {exc}\n")
        return EXIT_USAGE
    if fresh["body_sha256"] == recorded:
        print(f"OK: body_sha256 reproduced ({recorded})")
        return 0
    print(f"MISMATCH: recorded {recorded}, recomputed {fresh['body_sha256']}")
    return EXIT_MISMATCH


def _cmd_suggest(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.data):
        sys.stderr.write(f"truth-gate: data file not found: {args.data}\n")
        return EXIT_USAGE
    if os.path.lexists(args.out):
        sys.stderr.write(f"truth-gate: refusing to overwrite {args.out}\n")
        return EXIT_USAGE
    try:
        with open(args.data, "rb") as handle:
            raw = handle.read()
        out_dir = os.path.dirname(os.path.abspath(args.out))
        try:
            data_ref = os.path.relpath(os.path.abspath(args.data), out_dir)
        except ValueError:  # another drive
            data_ref = os.path.abspath(args.data)
        text = suggest_manifest(raw, data_ref.replace(os.sep, "/"), outcome=args.outcome, group=args.group,
                                reference=args.reference, effects=args.effect, exchangeable=args.exchangeable)
    except ManifestError as exc:
        sys.stderr.write(f"truth-gate: suggest: {exc}\n")
        return EXIT_USAGE
    except OSError as exc:
        sys.stderr.write(f"truth-gate: cannot read {args.data}: {type(exc).__name__}\n")
        return EXIT_USAGE
    for line in WARNING_LINES:
        print(line)
    try:
        with open(args.out, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        sys.stderr.write(f"truth-gate: cannot write {args.out}: {type(exc).__name__}\n")
        return EXIT_USAGE
    print(f"wrote {args.out}: every declaration carries origin = \"suggested\" (verdict capped at WEAK until reviewed).")
    print("Next: set provenance (it says TODO), write a criterion from a template, then run `truth-gate check`.")
    return 0


def _cmd_init(args: argparse.Namespace) -> int:
    try:
        written = write_scaffold(args.dir, args.ci)
    except ScaffoldError as exc:
        sys.stderr.write(f"truth-gate: init: {exc}\n")
        return EXIT_USAGE
    for path in written:
        print(f"wrote {path}")
    return 0


def _cmd_badge(args: argparse.Namespace) -> int:
    try:
        stored = load_certificate_file(args.certificate)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"truth-gate: cannot read certificate: {type(exc).__name__}\n")
        return EXIT_USAGE
    try:
        payload = badge_payload(stored)
    except BadgeError as exc:
        if exc.code == EXIT_MISMATCH:
            print(str(exc))
        else:
            sys.stderr.write(f"truth-gate: badge: {exc}\n")
        return exc.code
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.out is None:
        sys.stdout.write(text)
        return 0
    try:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        sys.stderr.write(f"truth-gate: cannot write {args.out}: {type(exc).__name__}\n")
        return EXIT_USAGE
    return 0


def _cmd_explain(args: argparse.Namespace) -> int:
    text = explain_module.explain(args.flag)
    if text is None:
        sys.stderr.write(f"truth-gate: unknown flag or note {args.flag!r}; known: {', '.join(explain_module.known_names())}\n")
        return EXIT_USAGE
    print(text)
    return 0


def _run(argv: Optional[list]) -> int:
    """Dispatch one command line (the body of :func:`main`)."""
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "freeze":  # the freeze tool keeps its own arguments and exit codes (0, 1, 2)
        try:
            return freeze_main(argv[1:])
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 2
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    handlers = {
        "check": _cmd_check, "verify": _cmd_verify, "suggest": _cmd_suggest, "init": _cmd_init,
        "badge": _cmd_badge, "explain": _cmd_explain,
    }
    return handlers[args.command](args)


def internal_error_line(exc: BaseException) -> str:
    """One line, whatever the exception says (R-33): the type and the first line of its message, shortened."""
    text = (str(exc).strip().splitlines() or [""])[0]
    if len(text) > 200:
        text = text[:197] + "..."
    return f"truth-gate: internal error ({type(exc).__name__})" + (f": {text}" if text else "")


def main(argv: Optional[list] = None) -> int:
    """Entry point; returns the process exit code (spec section 8).

    R-33: any exception that no handler expected exits with 4 and a one-line message.  Exit 1 means WEAK, so an internal
    error must never look like a verdict.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    try:
        return _run(argv)
    except Exception as exc:  # noqa: BLE001 - the point is to catch everything that was not expected
        sys.stderr.write(internal_error_line(exc) + "\n")
        return EXIT_USAGE
