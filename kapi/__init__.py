"""Deprecated shim: ``kapi`` is now ``truth_gate`` (spec 0.6, section 2.1).

Every public name is the same object as in ``truth_gate``, and every submodule is aliased in ``sys.modules``
(``kapi.checks`` is ``truth_gate.checks``), so old imports keep working.  No warning is emitted.
The shim stays at least until 1.0.
"""

import importlib
import sys

import truth_gate
from truth_gate import *  # noqa: F401,F403
from truth_gate import SPEC_VERSION, __version__  # noqa: F401

__all__ = list(truth_gate.__all__)

# Keep this tuple in step with the modules of truth_gate/ (a test checks it).
_SUBMODULES = (
    "badge", "certificate", "checks", "ci", "cli", "common", "data_io", "explain", "external", "freeze", "guard", "k8",
    "manifest", "minus", "mutations", "passes", "patterns", "probes", "sampling", "scaffold", "stats", "study",
    "suggest",
)

for _name in _SUBMODULES:
    _module = importlib.import_module("truth_gate." + _name)
    sys.modules[__name__ + "." + _name] = _module
    globals()[_name] = _module
del _name, _module
