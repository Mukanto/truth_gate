#!/usr/bin/env python3
"""Freeze manifest tool: write and verify a SHA-256 manifest of the files that define a study.

Standard library only.  Two commands::

    python freeze.py write FILE_OR_DIR... -o FREEZE.json [--no-readonly]
    python freeze.py verify FREEZE.json [--require-readonly]

``write`` hashes every listed file (directories are walked recursively), records the paths relative to the folder
that holds the manifest, writes the manifest and marks the frozen files and the manifest read-only.  Marking
read-only is best effort: it uses ``os.chmod`` (the read-only attribute on Windows, permission bits elsewhere) and
a failure is only a warning, because read-only is a safeguard against accidents, not a security boundary.
The manifest is never overwritten: ``write`` refuses if the output file exists.

``verify`` recomputes every hash and compares it with the manifest.  It also recomputes the manifest's own
``core_sha256`` (a hash over the sorted ``path:hash`` lines), so an edited manifest is detected too.

Exit codes: 0 all good, 1 verification failed (a file is missing or modified, or the manifest was edited),
2 usage or I/O error.

Hashes are over the raw bytes.  A tool that rewrites line endings (for example a git checkout with autocrlf)
changes the hash; freeze the files in the form in which they will be run.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import stat
import sys

FORMAT = 1
CHUNK = 1 << 20


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def core_hash(files: dict) -> str:
    """Hash of the sorted ``path:sha256`` lines.  Detects an edited manifest."""
    text = "\n".join(f"{path}:{files[path]}" for path in sorted(files))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _expand(paths):
    found = []
    for item in paths:
        if os.path.isdir(item):
            for folder, dirs, names in os.walk(item):
                dirs[:] = sorted(d for d in dirs if d != "__pycache__")
                for name in sorted(names):
                    if not name.endswith((".pyc", ".pyo")):
                        found.append(os.path.join(folder, name))
        elif os.path.isfile(item):
            found.append(item)
        else:
            raise FileNotFoundError(item)
    return found


def _make_readonly(path: str) -> bool:
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        return True
    except OSError:
        return False


def _is_writable(path: str) -> bool:
    return bool(os.stat(path).st_mode & stat.S_IWUSR)


def cmd_write(args) -> int:
    out = os.path.abspath(args.output)
    if os.path.exists(out):
        print(f"refusing to overwrite {args.output}", file=sys.stderr)
        return 2
    base = os.path.dirname(out)
    try:
        listed = _expand(args.files)
    except FileNotFoundError as exc:
        print(f"no such file or directory: {exc}", file=sys.stderr)
        return 2
    files = {}
    for path in listed:
        absolute = os.path.abspath(path)
        if absolute == out:
            continue
        try:
            rel = os.path.relpath(absolute, base)
        except ValueError:
            print(f"{path} is on another drive than the manifest", file=sys.stderr)
            return 2
        files[rel.replace(os.sep, "/")] = sha256_file(absolute)
    if not files:
        print("no files to freeze", file=sys.stderr)
        return 2
    manifest = {
        "freeze_format": FORMAT,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "algorithm": "sha256",
        "files": dict(sorted(files.items())),
        "core_sha256": core_hash(files),
    }
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=False)
        handle.write("\n")
    failed = []
    if not args.no_readonly:
        for rel in files:
            target = os.path.join(base, *rel.split("/"))
            if not _make_readonly(target):
                failed.append(rel)
        if not _make_readonly(out):
            failed.append(os.path.basename(out))
    print(f"froze {len(files)} file(s) -> {args.output}")
    print(f"core_sha256 {manifest['core_sha256']}")
    if failed:
        print("warning: could not mark read-only: " + ", ".join(failed), file=sys.stderr)
    return 0


def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise ValueError("manifest has no 'files' table")
    return manifest


def verify_manifest(path: str, require_readonly: bool = False):
    """Return ``(problems, warnings)``; both are lists of strings.  No problems means the freeze holds."""
    problems, warnings = [], []
    manifest = load_manifest(path)
    files = manifest["files"]
    base = os.path.dirname(os.path.abspath(path))
    if core_hash(files) != manifest.get("core_sha256"):
        problems.append("MANIFEST EDITED: core_sha256 does not match the file table")
    for rel in sorted(files):
        target = os.path.join(base, *rel.split("/"))
        if not os.path.isfile(target):
            problems.append(f"MISSING: {rel}")
            continue
        if sha256_file(target) != files[rel]:
            problems.append(f"MODIFIED: {rel}")
        elif _is_writable(target):
            (problems if require_readonly else warnings).append(f"WRITABLE: {rel}")
    return problems, warnings


def cmd_verify(args) -> int:
    try:
        problems, warnings = verify_manifest(args.manifest, args.require_readonly)
    except (OSError, ValueError) as exc:
        print(f"cannot read manifest: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    for line in warnings:
        print("warning: " + line)
    for line in problems:
        print(line)
    if problems:
        print("FREEZE BROKEN")
        return 1
    print("FREEZE OK")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="freeze.py", description="Write and verify a SHA-256 freeze manifest.")
    sub = parser.add_subparsers(dest="command", required=True)
    w = sub.add_parser("write", help="hash files and write a manifest")
    w.add_argument("files", nargs="+", help="files or directories to freeze")
    w.add_argument("-o", "--output", required=True, help="manifest path (must not exist)")
    w.add_argument("--no-readonly", action="store_true", help="do not mark the files read-only")
    w.set_defaults(func=cmd_write)
    v = sub.add_parser("verify", help="check a manifest against the files on disk")
    v.add_argument("manifest")
    v.add_argument("--require-readonly", action="store_true", help="treat a writable file as a failure")
    v.set_defaults(func=cmd_verify)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
