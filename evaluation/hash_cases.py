"""Hash an evaluation case set before its first run (spec 12.2, step 4).

Usage (from the project root)::

    py -B evaluation/hash_cases.py evaluation/cases/E1E3

Writes ``CASES_SHA256.json`` into the set directory: the SHA-256 of every file in the directory (recursively, relative
POSIX paths, sorted) except the hash file itself and ``__pycache__`` directories.  An existing hash file is never
overwritten.  ``verify_set`` is used by ``run_eval.py`` to check a set against its recorded hashes.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

HASH_FILE = "CASES_SHA256.json"
ALGORITHM = "sha256"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def list_set_files(set_dir: str) -> list:
    """Relative POSIX paths of all files in ``set_dir`` except the hash file and bytecode caches, sorted."""
    out = []
    for dirpath, dirnames, filenames in os.walk(set_dir):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), set_dir).replace(os.sep, "/")
            if rel == HASH_FILE:
                continue
            out.append(rel)
    return sorted(out)


def compute_hashes(set_dir: str) -> dict:
    return {rel: sha256_file(os.path.join(set_dir, *rel.split("/"))) for rel in list_set_files(set_dir)}


def write_hashes(set_dir: str) -> str:
    """Write ``CASES_SHA256.json``; refuse to overwrite.  Returns the path written."""
    if not os.path.isdir(set_dir):
        raise FileNotFoundError(f"not a directory: {set_dir}")
    target = os.path.join(set_dir, HASH_FILE)
    if os.path.exists(target):
        raise FileExistsError(f"refusing to overwrite {target}")
    files = compute_hashes(set_dir)
    if not files:
        raise ValueError(f"no files to hash in {set_dir}")
    payload = {"algorithm": ALGORITHM, "files": files}
    with open(target, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return target


def verify_set(set_dir: str) -> list:
    """Compare a set directory with its recorded hashes.  Returns a list of problem strings (empty if intact)."""
    target = os.path.join(set_dir, HASH_FILE)
    if not os.path.isfile(target):
        return [f"{HASH_FILE} is missing in {set_dir}"]
    try:
        with open(target, "r", encoding="utf-8") as fh:
            recorded = json.load(fh)
        files = recorded["files"]
        if recorded.get("algorithm") != ALGORITHM or not isinstance(files, dict):
            return [f"{target} is malformed"]
    except (OSError, ValueError, KeyError):
        return [f"{target} cannot be read"]
    actual = compute_hashes(set_dir)
    problems = []
    for rel in sorted(set(files) | set(actual)):
        if rel not in actual:
            problems.append(f"missing file: {rel}")
        elif rel not in files:
            problems.append(f"unrecorded file: {rel}")
        elif files[rel] != actual[rel]:
            problems.append(f"hash mismatch: {rel}")
    return problems


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: py -B evaluation/hash_cases.py SET_DIR", file=sys.stderr)
        return 4
    try:
        target = write_hashes(argv[0])
    except (OSError, ValueError) as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.exit(main())
