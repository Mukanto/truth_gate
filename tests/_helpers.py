"""Shared helpers for the Kapi test suite (unittest only)."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import kapi  # noqa: E402

TOYS = os.path.join(ROOT, "tests", "toy_studies")
_CACHE: dict = {}


def toy_path(name: str) -> str:
    return os.path.join(TOYS, name + ".py")


def run_toy(name: str, quick: bool = False) -> dict:
    """Run the gate on a toy study once per process and cache the envelope."""
    key = (name, quick)
    if key not in _CACHE:
        _CACHE[key] = kapi.run_gate(toy_path(name), quick=quick)
    return _CACHE[key]


def body(name: str, quick: bool = False) -> dict:
    return run_toy(name, quick)["body"]


def component(name: str, comp_id: str = None) -> dict:
    comps = body(name)["components"]
    if comp_id is None:
        assert len(comps) == 1, "toy has several components; name one"
        return comps[0]
    return next(c for c in comps if c["id"] == comp_id)


def raised(name: str, flag: str) -> bool:
    """True if the flag (or flag family ``PREFIX:*``) is raised by any component or at study level."""
    b = body(name)
    flags = set(b["study_flags"])
    for comp in b["components"]:
        flags.update(comp["flags"])
    if flag.endswith(":*"):
        return any(f.startswith(flag[:-1]) for f in flags)
    return flag in flags
