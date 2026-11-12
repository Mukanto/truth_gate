"""``python -m truth_gate.ci``: the logic of the GitHub Action (spec 0.6, section 10).

The composite action in ``action.yml`` passes its inputs as environment variables (never spliced into a shell line)::

    TG_TARGET    the study or manifest to check (required)
    TG_FREEZE    a freeze manifest to verify (optional)
    TG_QUICK     "true" or "false" (default "false"; quick mode is not certifiable)
    TG_FAIL_ON   comma-separated verdicts that fail the job (default NOT_FALSIFIABLE,UNDEFINED,UNTESTED)

What it does, in this order: runs ``check`` on the target (the same code path as ``truth-gate check``, so the table
reaches the job log), runs ``freeze verify`` if a freeze manifest is given, appends the result table and the study notes
to ``$GITHUB_STEP_SUMMARY``, writes ``certificate=<absolute path>`` to ``$GITHUB_OUTPUT`` and returns the exit code.

Exit code: 0 when nothing fails.  Otherwise the first of: 4 (inputs or manifest rejected, no certificate, or freeze
verify could not run), 5 (the freeze does not hold), the CLI's code for the study verdict (1 WEAK, 2 NOT_FALSIFIABLE, 3 UNDEFINED, 6 UNTESTED) when the
verdict is in ``fail-on``, and 1 when any component carries ``SUGGESTED_UNREVIEWED`` (whatever ``fail-on`` says).
The summary and the output are written before the exit code is returned, also on failure.

``python -m truth_gate.ci --pre-commit FILE...`` is the pre-commit wrapper (R-27): it checks every file in quick mode,
writes the certificates to a temporary folder that is deleted afterwards (never next to a manifest, so a commit cannot
pick one up), prints one line per file and exits with the most severe code (4, then 5, then the worst verdict; see
:func:`most_severe`).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shlex
import shutil
import sys
import tempfile
from typing import Mapping, Optional

from . import cli
from .checks import VERDICTS
from .freeze import main as freeze_main
from .passes import SUGGESTED_UNREVIEWED

DEFAULT_FAIL_ON = "NOT_FALSIFIABLE,UNDEFINED,UNTESTED"
EXIT_USAGE = cli.EXIT_USAGE
EXIT_FREEZE = cli.EXIT_MISMATCH
EXIT_UNREVIEWED = 1


class CiInputError(Exception):
    """An input of the action is not valid (exit code 4)."""


def severity(code: int) -> tuple:
    """Order of exit codes for the pre-commit wrapper, as in R-26: 4 (input or manifest error) beats 5 (a broken
    freeze), which beats the verdict codes, ordered by the severity order of the verdicts (UNDEFINED worst, then
    NOT_FALSIFIABLE, UNTESTED, WEAK); 0 is the least severe.  Any code that is none of these ranks with 4."""
    if code == 0:
        return (0, 0)
    verdict_by_code = {v: k for k, v in cli.EXIT_CODES.items()}
    if code in verdict_by_code:
        return (1, VERDICTS.index(verdict_by_code[code]))
    if code == EXIT_FREEZE:
        return (2, 0)
    return (3, 0)


def most_severe(codes) -> int:
    """The most severe exit code of ``codes`` (0 for none)."""
    return max(codes, key=severity, default=0)


def parse_bool(text: Optional[str], name: str) -> bool:
    value = (text or "").strip().lower()
    if value in ("", "false"):
        return False
    if value == "true":
        return True
    raise CiInputError(f"{name} must be \"true\" or \"false\", not {text!r}")


def parse_fail_on(text: Optional[str]) -> tuple:
    """The verdict names of ``fail-on``.  An empty list is allowed (only SUGGESTED_UNREVIEWED then fails the job)."""
    names = tuple(part.strip() for part in (DEFAULT_FAIL_ON if text is None else text).split(",") if part.strip())
    unknown = [n for n in names if n not in VERDICTS]
    if unknown:
        raise CiInputError(f"fail-on has unknown verdict(s) {', '.join(unknown)}; known: {', '.join(VERDICTS)}")
    return names


def has_unreviewed(body: dict) -> bool:
    """True when any component carries SUGGESTED_UNREVIEWED (or the body counts unreviewed declarations)."""
    for comp in body.get("components") or []:
        if SUGGESTED_UNREVIEWED in (comp.get("flags") or []):
            return True
    count = body.get("suggested_unreviewed")
    return isinstance(count, int) and not isinstance(count, bool) and count > 0


def decide(body: dict, fail_on: tuple) -> tuple:
    """``(exit_code, reasons)`` for a certificate body: the CLI's code for a verdict in ``fail_on``, 1 for an unreviewed
    suggestion, 0 otherwise."""
    code = 0
    reasons = []
    verdict = body.get("verdict")
    if verdict in fail_on:
        code = cli.EXIT_CODES.get(verdict, 1)
        reasons.append(f"the verdict {verdict} is in fail-on")
    if has_unreviewed(body):
        reasons.append(f"{SUGGESTED_UNREVIEWED}: a declaration still carries origin = \"suggested\" "
                       "(fails the job whatever fail-on says)")
        code = code or EXIT_UNREVIEWED
    return code, reasons


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_summary(body: Optional[dict], *, target: str, quick: bool, certificate: Optional[str], sha: Optional[str],
                   check_code: int, freeze_target: Optional[str], freeze_code: Optional[int], freeze_text: str,
                   reasons: list, exit_code: int) -> str:
    """The markdown written to ``$GITHUB_STEP_SUMMARY``."""
    lines = ["## Truth_Gate", ""]
    lines.append(f"Target: `{_cell(target)}`   Mode: {'quick (not certifiable)' if quick else 'full'}")
    lines.append("")
    if body is None:
        lines.append(f"The check did not produce a certificate (exit code {check_code}). Read the job log for the reason.")
        lines.append("")
    else:
        lines.append(f"**Verdict: {body['verdict']}**")
        lines.append("")
        lines.append("| Component | Verdict | Flags |")
        lines.append("|---|---|---|")
        for comp in body.get("components") or []:
            flags = ", ".join(f"`{_cell(f)}`" for f in comp.get("flags") or []) or "-"
            lines.append(f"| {_cell(comp['id'])} | {comp['verdict']} | {flags} |")
        lines.append("")
        study_flags = body.get("study_flags") or []
        lines.append("Study flags: " + (", ".join(f"`{_cell(f)}`" for f in study_flags) or "-"))
        if body.get("load_error"):
            lines.append("")
            lines.append(f"The study failed to load: `{_cell(body['load_error'].get('type'))}`")
        notes = body.get("study_notes") or []
        if notes:
            lines.append("")
            lines.append("Study notes:")
            lines.append("")
            for note in notes:
                commands = "; ".join(f"`{_cell(shlex.join(argv))}`" for argv in note.get("commands", []))
                lines.append(f"* `{_cell(note['note'])}`" + (f": {commands}" if commands else ""))
        lines.append("")
        if certificate:
            lines.append(f"Certificate: `{_cell(certificate)}`   body_sha256: `{sha}`")
            lines.append("")
    if freeze_target is not None:
        state = {0: "FREEZE OK", 1: "FREEZE BROKEN"}.get(freeze_code, f"freeze verify failed to run (exit code {freeze_code})")
        lines.append(f"Freeze `{_cell(freeze_target)}`: **{state}**")
        details = [ln for ln in freeze_text.splitlines() if ln.strip() and ln not in ("FREEZE OK", "FREEZE BROKEN")]
        if details:
            lines.append("")
            lines.extend(f"* {_cell(ln)}" for ln in details)
        lines.append("")
    if exit_code == 0:
        lines.append("Result: passed.")
    else:
        lines.append(f"Result: **failed** (exit code {exit_code}).")
        lines.extend(f"* {r}" for r in reasons)
    return "\n".join(lines) + "\n"


def _append(path: Optional[str], text: str) -> None:
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as exc:
        sys.stderr.write(f"truth-gate ci: cannot write {path}: {type(exc).__name__}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m truth_gate.ci", description="The logic of the Truth_Gate GitHub Action.")
    parser.add_argument("--target", default=None, help="study or manifest (default: $TG_TARGET)")
    parser.add_argument("--freeze", default=None, help="freeze manifest to verify (default: $TG_FREEZE)")
    parser.add_argument("--quick", default=None, help='"true" or "false" (default: $TG_QUICK)')
    parser.add_argument("--fail-on", default=None, help=f"verdicts that fail the job (default: $TG_FAIL_ON, else {DEFAULT_FAIL_ON})")
    parser.add_argument("--pre-commit", action="store_true",
                        help="the pre-commit wrapper: check each FILE in quick mode, one line per file")
    parser.add_argument("files", nargs="*", metavar="FILE", help="the files of --pre-commit")
    return parser


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def pre_commit(files: list) -> int:
    """Check each file in quick mode (R-27).  Certificates go to a temporary folder that is removed afterwards; the
    table of ``check`` is not printed: one line per file, ``FILE: VERDICT (exit N)`` or the reason there is none."""
    folder = tempfile.mkdtemp(prefix="truth_gate_precommit_")
    codes = []
    try:
        for number, path in enumerate(files):
            out = os.path.join(folder, f"{number}.kapi.json")
            captured_out, captured_err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
                code = cli.main(["check", path, "--quick", "--out", out])
            verdict = None
            if code in cli.EXIT_CODES.values():
                try:
                    verdict = cli.load_certificate_file(out)["body"]["verdict"]
                except (OSError, ValueError, KeyError, TypeError):
                    verdict = None
            if verdict is not None:
                line = f"truth-gate pre-commit: {path}: {verdict} (exit {code})"
            else:
                reason = _first_line(captured_err.getvalue()) or "no certificate"
                line = f"truth-gate pre-commit: {path}: not checked (exit {code}): {reason}"
            print(line)
            codes.append(code)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    return most_severe(codes)


def main(argv: Optional[list] = None, environ: Optional[Mapping] = None) -> int:
    """Run the action's logic; returns the exit code.  ``environ`` defaults to ``os.environ`` (tests pass a fake).

    As in the CLI (R-33), an exception nobody expected exits with 4 and a one-line message, never with a verdict code.
    """
    try:
        return _main(argv, environ)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(cli.internal_error_line(exc) + chr(10))
        return EXIT_USAGE


def _main(argv: Optional[list], environ: Optional[Mapping]) -> int:
    env = os.environ if environ is None else environ
    try:
        args = build_parser().parse_args(sys.argv[1:] if argv is None else list(argv))
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    if args.pre_commit:
        if any(value is not None for value in (args.target, args.freeze, args.quick, args.fail_on)):
            sys.stderr.write("truth-gate ci: --pre-commit takes only FILE arguments\n")
            return EXIT_USAGE
        if not args.files:
            return 0  # pre-commit passes no files when none matched
        return pre_commit(args.files)
    if args.files:
        sys.stderr.write("truth-gate ci: FILE arguments are only valid with --pre-commit\n")
        return EXIT_USAGE
    summary_path = env.get("GITHUB_STEP_SUMMARY")
    output_path = env.get("GITHUB_OUTPUT")
    target = args.target if args.target is not None else env.get("TG_TARGET", "")
    freeze = args.freeze if args.freeze is not None else env.get("TG_FREEZE", "")
    quick_text = args.quick if args.quick is not None else env.get("TG_QUICK", "")
    fail_text = args.fail_on if args.fail_on is not None else env.get("TG_FAIL_ON")
    try:
        quick = parse_bool(quick_text, "quick")
        fail_on = parse_fail_on(fail_text)
        if not target.strip():
            raise CiInputError("target is required")
    except CiInputError as exc:
        sys.stderr.write(f"truth-gate ci: {exc}\n")
        _append(summary_path, f"## Truth_Gate\n\nInvalid input: {exc}\n")
        return EXIT_USAGE
    freeze = freeze.strip() or None

    # 1. check (the CLI's own code path; its table goes to the job log)
    certificate = os.path.abspath(cli.default_out_path(target))
    check_args = ["check", target, "--out", certificate] + (["--quick"] if quick else [])
    check_code = cli.main(check_args)
    body = sha = None
    if check_code in cli.EXIT_CODES.values():  # 4 and the other non-verdict codes mean there is no certificate of this run
        try:
            with open(certificate, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
            body, sha = stored["body"], stored["body_sha256"]
        except (OSError, ValueError, KeyError, TypeError):
            body = sha = None
    if body is None:
        certificate = None

    # 2. freeze verify (output is captured for the summary and echoed to the log)
    freeze_code = None
    freeze_text = ""
    if freeze is not None:
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            freeze_code = cli.main(["freeze", "verify", freeze])
        freeze_text = captured.getvalue()
        sys.stdout.write(freeze_text)

    # 3. decide: 4 (no certificate, or freeze verify could not run), then 5 (freeze broken), then the verdict codes
    if body is None:
        exit_code = EXIT_USAGE
        reasons = [f"the check produced no certificate (exit code {check_code})"]
    else:
        exit_code, reasons = decide(body, fail_on)
    if freeze_code == 1:
        reasons.append("the freeze does not hold")
        if exit_code != EXIT_USAGE:
            exit_code = EXIT_FREEZE
    elif freeze_code not in (None, 0):
        reasons.append(f"freeze verify failed to run (exit code {freeze_code})")
        exit_code = EXIT_USAGE
    for reason in reasons:
        print(f"truth-gate ci: {reason}")

    _append(summary_path, render_summary(
        body, target=target, quick=quick, certificate=certificate, sha=sha, check_code=check_code,
        freeze_target=freeze, freeze_code=freeze_code, freeze_text=freeze_text, reasons=reasons, exit_code=exit_code))
    if certificate:
        _append(output_path, f"certificate={certificate}\n")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
