"""``truth-gate init [DIR] [--ci]``: the scaffold of a new study (spec 0.6, section 9).

Writes ``PREREG.md``, ``truthgate.toml`` (a minimal example), ``BLIND_AUDIT_PROMPT.md``, ``run_guarded.py`` and, with
``--ci``, ``.github/workflows/truth-gate.yml``.  The files come from ``truth_gate/templates/``; the first three are
byte-identical copies of ``protocol/templates/`` (a test asserts it), kept inside the package so that an installed
copy can write them.  An existing file is never overwritten: nothing is written and the existing files are listed.
"""

from __future__ import annotations

import os

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
FILES = (  # (path inside DIR, template file)
    ("PREREG.md", "PREREG.md"),
    ("truthgate.toml", "truthgate.toml"),
    ("BLIND_AUDIT_PROMPT.md", "BLIND_AUDIT_PROMPT.md"),
    ("run_guarded.py", "run_guarded.py"),
)
CI_FILE = (os.path.join(".github", "workflows", "truth-gate.yml").replace(os.sep, "/"), "truth-gate.yml")


class ScaffoldError(Exception):
    """Existing files (``existing``) or an I/O problem; the CLI turns it into exit code 4."""

    def __init__(self, message: str, existing: tuple = ()) -> None:
        super().__init__(message)
        self.existing = tuple(existing)


def planned_files(ci: bool) -> list:
    return list(FILES) + ([CI_FILE] if ci else [])


def read_template(name: str) -> bytes:
    with open(os.path.join(TEMPLATES, name), "rb") as handle:
        return handle.read()


def write_scaffold(directory: str, ci: bool) -> list:
    """Write the files into ``directory`` (created if needed); return the paths written.

    Raises :class:`ScaffoldError` listing the existing files, without writing anything, if any target exists.
    The files are created in exclusive mode, so even a race cannot overwrite one.
    """
    plan = planned_files(ci)
    existing = [rel for rel, _ in plan if os.path.lexists(os.path.join(directory, *rel.split("/")))]
    if existing:
        raise ScaffoldError("refusing to overwrite existing files: " + ", ".join(existing), existing)
    contents = [(rel, read_template(template)) for rel, template in plan]
    written = []
    try:
        for rel, content in contents:
            target = os.path.join(directory, *rel.split("/"))
            os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
            with open(target, "xb") as handle:
                handle.write(content)
            written.append(target)
    except FileExistsError as exc:
        raise ScaffoldError(f"refusing to overwrite an existing file: {exc.filename}", (str(exc.filename),)) from None
    except OSError as exc:
        raise ScaffoldError(f"cannot write the scaffold: {type(exc).__name__}: {exc}") from None
    return written
