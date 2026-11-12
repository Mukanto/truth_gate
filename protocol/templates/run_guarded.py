#!/usr/bin/env python3
"""Guarded runner: executes a study script only if the freeze manifest verifies.  Standard library only.

Usage::

    python run_guarded.py FREEZE.json ENTRY.py [ARGS...]

Steps:

1. Load the manifest written by ``freeze.py write`` and verify it: the manifest's own core hash, and the SHA-256 of
   every listed file.  Any missing or modified file means the runner refuses to start (exit 3).
2. Refuse (exit 3) if ``ENTRY.py`` is not itself listed in the manifest.  Otherwise unfrozen code could run
   under a valid freeze.
3. Run ``ENTRY.py`` in this process (``runpy``, as ``__main__``) with ``sys.argv = [ENTRY.py, ARGS...]``.
4. Verify the manifest again after the run.  If a frozen file changed while the study ran, the run is reported as
   invalid (exit 3), even if the script itself succeeded.

Exit codes: 0 verified, ran and verified again; 2 usage error; 3 freeze check failed (before or after); any other
code is the entry script's own non-zero exit status (``SystemExit``) or 1 for an uncaught exception.

This file is a template.  Copy it next to your study, and add it to the manifest too if you want the runner itself
frozen.  The verification code is repeated here (instead of imported from ``freeze.py``) so that the runner works
when copied on its own.
"""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import sys

CHUNK = 1 << 20


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _core_hash(files):
    text = "\n".join(f"{path}:{files[path]}" for path in sorted(files))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify(manifest_path):
    """Return ``(problems, files, base_dir)``.  An empty problem list means the freeze holds."""
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return ["manifest has no 'files' table"], {}, ""
    base = os.path.dirname(os.path.abspath(manifest_path))
    problems = []
    if _core_hash(files) != manifest.get("core_sha256"):
        problems.append("MANIFEST EDITED: core_sha256 does not match the file table")
    for rel in sorted(files):
        target = os.path.join(base, *rel.split("/"))
        if not os.path.isfile(target):
            problems.append(f"MISSING: {rel}")
        elif _sha256_file(target) != files[rel]:
            problems.append(f"MODIFIED: {rel}")
    return problems, files, base


def _refuse(problems, when):
    print(f"refusing: freeze check failed {when}", file=sys.stderr)
    for line in problems:
        print("  " + line, file=sys.stderr)
    return 3


def main(argv):
    if len(argv) < 3:
        print("usage: run_guarded.py FREEZE.json ENTRY.py [ARGS...]", file=sys.stderr)
        return 2
    manifest_path, entry, args = argv[1], argv[2], argv[3:]
    try:
        problems, files, base = verify(manifest_path)
    except (OSError, ValueError) as exc:
        print(f"cannot read manifest: {type(exc).__name__}", file=sys.stderr)
        return 3
    if problems:
        return _refuse(problems, "before the run")
    entry_rel = os.path.relpath(os.path.abspath(entry), base).replace(os.sep, "/")
    if entry_rel not in files:
        return _refuse([f"ENTRY NOT FROZEN: {entry_rel} is not listed in the manifest"], "before the run")

    status = 0
    old_argv = sys.argv
    sys.argv = [entry] + list(args)
    try:
        runpy.run_path(entry, run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            status = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv

    problems, _, _ = verify(manifest_path)
    if problems:
        return _refuse(problems, "after the run (the run is invalid)")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
