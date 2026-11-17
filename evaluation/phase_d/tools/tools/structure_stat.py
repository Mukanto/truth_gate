"""Phase D structure statistic (PREREG_PHASE_D sections 2.1, 2.2 and 5; TOOLS_SPEC_D section 2).

Runs the private note's structure statistic ``stat(d)`` on samples of one world of a study file.  The samples of world
``plus`` or ``minus`` are drawn with ``truth_gate.sampling.stream_rng(seed, "structure:<world>", i)``, i = 0..samples-1
(a stream name the gate never uses).

``PRIVATE.json["structure_statistic"]``::

    {"code": "def stat(d):\\n    ...\\n    return float(value)", "direction": "greater" | "less",
     "null_value": 0.0, "note_value": 0.4, "set_by_brief": false}

``code`` is executed with ``numpy`` (as ``np``) as its only global and must define ``stat(d)`` returning a finite float.

Result: ``{"mean", "sd", "values_head" (first 5), "share_beyond_half"}``.  The share counts samples at or beyond
``null + 0.5 * (note_value - null)`` in the stated direction (``>=`` for greater, ``<=`` for less).  With
``set_by_brief`` true the result is ``{"set_by_brief": true, "mean"}`` and has no share.  ``sd`` is the sample standard
deviation (ddof = 1; 0.0 for one sample).

Usage:
    py structure_stat.py --study FILE --private PRIVATE.json --world minus --samples 200 --seed 20261117 --package-root DIR
prints the result as JSON.  Exit code 0 on success, 1 when the statistic cannot be computed (message on stderr), 2 on a
usage error or a failed package root check.

``import_truth_gate`` and ``load_study_module`` are shared with ``validity_check.py``.
"""
import argparse
import itertools
import json
import math
import os
import sys
import types
import uuid

import numpy as np

_COUNTER = itertools.count()


class PackageRootError(Exception):
    """truth_gate cannot be imported from the package root (or resolves elsewhere)."""


class StatisticError(Exception):
    """The structure statistic cannot be computed."""


def import_truth_gate(package_root):
    """Import ``truth_gate`` with ``package_root`` first on ``sys.path``; refuse if it resolves elsewhere.

    As ``evaluation/phase_c/tools/check_skeletons.py``, with one difference for use as a library: a ``truth_gate`` that
    is already imported is accepted when its file lies under ``package_root`` (a fresh process never has one).
    Returns the module.  Raises ``PackageRootError``.
    """
    root = os.path.abspath(package_root)
    rroot = os.path.normcase(os.path.realpath(root))

    def inside(f):
        real = os.path.normcase(os.path.realpath(f))
        try:
            return os.path.commonpath([real, rroot]) == rroot
        except ValueError:  # different drives
            return False

    mod = sys.modules.get("truth_gate")
    if mod is not None:
        f = getattr(mod, "__file__", None)
        if f and inside(f):
            return mod
        raise PackageRootError(f"truth_gate was already imported from {f}, which is not under the package root {root}")
    sys.path.insert(0, root)
    try:
        import truth_gate
    except Exception as e:
        raise PackageRootError(f"cannot import truth_gate with package root {root}: {type(e).__name__}: {e}") from e
    f = getattr(truth_gate, "__file__", None)
    if not f:
        raise PackageRootError(f"truth_gate imported with package root {root} has no __file__ (namespace package?)")
    if not inside(f):
        raise PackageRootError(f"truth_gate was imported from {f}, which is not under the package root {root}")
    return truth_gate


def load_study_module(src, path="<study>", role="study"):
    """Execute study source text as a module with a name that is unique per call; return the module.

    Like ``truth_gate.study.load_study``: compiled from the given text (no import machinery, no ``__pycache__``), the
    module is registered in ``sys.modules`` while it executes and removed afterwards.  The leak guard is not armed.
    """
    name = f"kapi_phase_d_{role}_{next(_COUNTER)}_{uuid.uuid4().hex[:8]}"
    module = types.ModuleType(name)
    module.__file__ = path
    code = compile(src, path, "exec")
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)  # noqa: S102 - executing the study file is the purpose
    finally:
        sys.modules.pop(name, None)
    return module


def compile_statistic(spec):
    """``stat`` function of a ``structure_statistic`` record; numpy (as ``np``) is its only global."""
    ns = {"np": np}
    try:
        exec(compile(spec["code"], "<structure_statistic>", "exec"), ns)  # noqa: S102
    except Exception as e:
        raise StatisticError(f"the statistic's code does not run: {type(e).__name__}: {e}") from e
    stat = ns.get("stat")
    if not callable(stat):
        raise StatisticError("the statistic's code does not define stat(d)")
    return stat


def _as_private(private):
    if isinstance(private, (str, os.PathLike)):
        with open(private, encoding="utf-8") as f:
            return json.load(f)
    return private


def structure_stat(study_module, private, world, samples, seed, package_root):
    """The statistic of ``private`` on ``samples`` samples of ``world`` ("plus" or "minus") of ``study_module``.

    ``private`` is the parsed PRIVATE.json (a path is accepted too).  Raises ``StatisticError`` when a sample cannot be
    generated or the statistic raises or returns something that is not a finite real number.
    """
    if world not in ("plus", "minus"):
        raise ValueError("world must be 'plus' or 'minus'")
    if samples < 1:
        raise ValueError("samples must be >= 1")
    tg = import_truth_gate(package_root)
    from truth_gate.sampling import stream_rng, copy_data, validate_data
    del tg
    spec = _as_private(private)["structure_statistic"]
    stat = compile_statistic(spec)
    generate = study_module.STUDY.worlds[world].generate
    values = []
    for i in range(samples):
        rng = stream_rng(seed, f"structure:{world}", i)
        try:
            data = validate_data(generate(rng))
            v = stat(copy_data(data))
        except Exception as e:
            raise StatisticError(f"sample {i} of world {world}: {type(e).__name__}: {e}") from e
        if isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, float, np.integer, np.floating)):
            raise StatisticError(f"sample {i} of world {world}: stat returned {type(v).__name__}, not a float")
        v = float(v)
        if not math.isfinite(v):
            raise StatisticError(f"sample {i} of world {world}: stat returned a non-finite value")
        values.append(v)
    arr = np.asarray(values, dtype=np.float64)
    mean = float(arr.mean())
    if spec.get("set_by_brief"):
        return {"set_by_brief": True, "mean": mean}
    null, note = float(spec["null_value"]), float(spec["note_value"])
    half = null + 0.5 * (note - null)
    if spec["direction"] == "greater":
        beyond = arr >= half
    elif spec["direction"] == "less":
        beyond = arr <= half
    else:
        raise StatisticError(f"direction must be 'greater' or 'less', not {spec['direction']!r}")
    return {
        "mean": mean,
        "sd": float(arr.std(ddof=1)) if samples > 1 else 0.0,
        "values_head": [float(x) for x in arr[:5]],
        "share_beyond_half": float(beyond.mean()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Structure statistic of a private note on a world's samples (Phase D).")
    ap.add_argument("--study", required=True)
    ap.add_argument("--private", required=True)
    ap.add_argument("--world", required=True, choices=["plus", "minus"])
    ap.add_argument("--samples", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20261117)
    ap.add_argument("--package-root", required=True, metavar="DIR")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    try:
        import_truth_gate(a.package_root)
    except PackageRootError as e:
        print(f"package root check failed: {e}", file=sys.stderr)
        return 2
    try:
        with open(a.study, encoding="utf-8") as f:
            src = f.read()
        private = _as_private(a.private)
        private["structure_statistic"]  # noqa: B018 - a missing record is a usage error
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"cannot read input: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if a.samples < 1:
        print("--samples must be >= 1", file=sys.stderr)
        return 2
    try:
        module = load_study_module(src, a.study, "study")
        result = structure_stat(module, private, a.world, a.samples, a.seed, a.package_root)
    except StatisticError as e:
        print(f"structure_stat: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"structure_stat: cannot load the study: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
