"""Command line interface (spec section 8)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from .certificate import body_sha256, run_gate

EXIT_CODES = {"FALSIFIABLE": 0, "WEAK": 1, "NOT_FALSIFIABLE": 2, "UNDEFINED": 3, "UNTESTED": 6}
EXIT_USAGE = 4
EXIT_MISMATCH = 5


class _Parser(argparse.ArgumentParser):
    """argparse with the exit code 4 for usage errors (spec section 8)."""

    def error(self, message: str):  # type: ignore[override]
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(EXIT_USAGE)


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="kapi", description="Kapı: falsifiability gate for pre-registered studies.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="run the gate on a study file")
    check.add_argument("study")
    check.add_argument("--out", default=None, help="certificate path (default: next to the study)")
    check.add_argument("--quick", action="store_true", help="quick mode (not certifiable)")
    verify = sub.add_parser("verify", help="re-run a study and compare body_sha256")
    verify.add_argument("certificate")
    verify.add_argument("study")
    return parser


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
    return "\n".join(lines)


def _cmd_check(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.study):
        sys.stderr.write(f"kapi: study file not found: {args.study}\n")
        return EXIT_USAGE
    envelope = run_gate(args.study, quick=args.quick)
    out = args.out if args.out else default_out_path(args.study)
    try:
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(envelope, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
    except OSError as exc:
        sys.stderr.write(f"kapi: cannot write {out}: {type(exc).__name__}\n")
        return EXIT_USAGE
    print(format_table(envelope["body"]))
    print(f"certificate: {out}")
    print(f"body_sha256: {envelope['body_sha256']}")
    return EXIT_CODES[envelope["body"]["verdict"]]


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        with open(args.certificate, "r", encoding="utf-8") as handle:
            stored = json.load(handle)
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"kapi: cannot read certificate: {type(exc).__name__}\n")
        return EXIT_USAGE
    if not os.path.isfile(args.study):
        sys.stderr.write(f"kapi: study file not found: {args.study}\n")
        return EXIT_USAGE
    try:
        mode = stored["body"]["mode"]
        recorded = stored["body_sha256"]
    except (KeyError, TypeError):
        sys.stderr.write("kapi: not a Kapi certificate\n")
        return EXIT_USAGE
    if mode not in ("full", "quick"):
        sys.stderr.write("kapi: unknown mode in certificate\n")
        return EXIT_USAGE
    if body_sha256(stored["body"]) != recorded:
        print("MISMATCH: the certificate body does not match its own body_sha256")
        return EXIT_MISMATCH
    fresh = run_gate(args.study, quick=(mode == "quick"))
    if fresh["body_sha256"] == recorded:
        print(f"OK: body_sha256 reproduced ({recorded})")
        return 0
    print(f"MISMATCH: recorded {recorded}, recomputed {fresh['body_sha256']}")
    return EXIT_MISMATCH


def main(argv: Optional[list] = None) -> int:
    """Entry point; returns the process exit code (spec section 8)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    if args.command == "check":
        return _cmd_check(args)
    return _cmd_verify(args)
