"""Structural and data checks of the skeletons (no criterion, no gate run)."""
import ast
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pkg"))
import numpy as np  # noqa: E402

BANNED = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
          "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__"}
NP_FILE = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
STUDY_KW = {"name", "criteria", "worlds", "controls", "premises", "relational"}
IMPORT_1 = "import numpy as np"
IMPORT_2 = "from truth_gate import Study, Criterion, World, Premise, Control"

batch = {b["id"]: b for b in json.loads((ROOT / "BATCH.json").read_text(encoding="utf-8"))}
only = set(sys.argv[1:])
problems = {}


def static_check(path, brief):
    errs = []
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    body = tree.body
    doc = ast.get_docstring(tree, clean=False)
    if doc != f"{brief['id']}: {brief['claim']}" or "\n" in (doc or ""):
        errs.append("docstring mismatch")
    first_line = src.splitlines()[0]
    if first_line != f'"""{brief["id"]}: {brief["claim"]}"""':
        errs.append("first line not exact docstring")
    lines = src.splitlines()
    if IMPORT_1 not in lines or IMPORT_2 not in lines:
        errs.append("import lines")
    for node in body[1:]:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = ast.get_source_segment(src, node)
            if seg not in (IMPORT_1, IMPORT_2):
                errs.append(f"extra import {seg}")
        elif not isinstance(node, (ast.Assign, ast.FunctionDef)):
            errs.append(f"module-level {type(node).__name__} at line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in BANNED:
            errs.append(f"banned name {node.id}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                errs.append(f"dunder attribute {node.attr}")
            if node.attr in NP_FILE:
                errs.append(f"numpy file function {node.attr}")
            if node.attr == "random" and isinstance(node.value, ast.Name) and node.value.id == "np":
                errs.append("np.random used")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "World":
                kws = {k.arg for k in node.keywords}
                if len(node.args) != 1 or not (kws == set() or kws == {"derived_from", "change"}):
                    errs.append("World call form")
            if node.func.id == "Study":
                kws = {k.arg for k in node.keywords}
                if not kws <= STUDY_KW or node.args:
                    errs.append(f"Study keywords {kws - STUDY_KW}")
    return errs


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def expected_shapes(brief):
    return {k["key"]: (tuple(k["dims"]), np.bool_ if k["dtype"] == "bool" else np.float64) for k in brief["data_keys"]}


def check_data(d, exp, label, errs):
    if set(d) != set(exp):
        errs.append(f"{label}: keys {sorted(d)}")
        return
    for k, (shape, dt) in exp.items():
        a = d[k]
        if not isinstance(a, np.ndarray) or a.shape != shape or a.dtype != dt:
            errs.append(f"{label}: {k} shape/dtype {getattr(a, 'shape', None)} {getattr(a, 'dtype', None)}")
        elif dt == np.float64 and not np.all(np.isfinite(a)):
            errs.append(f"{label}: {k} non-finite")
        if a.ndim and max(a.shape) > 2000 or a.size > 2_000_000:
            errs.append(f"{label}: {k} too large")


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, (time.perf_counter() - t0) * 1000


for path in sorted((ROOT / "skeletons").glob("D-*.py")):
    sid = path.stem
    if only and sid not in only:
        continue
    brief = batch[sid]
    errs = static_check(path, brief)
    mod = load(path)
    st = mod.STUDY
    exp = expected_shapes(brief)
    tmax = {}
    for wname, world in st.worlds.items():
        for i in range(4):
            rng = np.random.default_rng([7, i])
            d, ms = timed(world.generate, rng)
            tmax[wname] = max(tmax.get(wname, 0), ms)
            check_data(d, exp, f"{wname}[{i}]", errs)
    # paired identity check as the gate does: minus with plus's generator
    dp = st.worlds["plus"].generate(np.random.default_rng([7, 0]))
    dm = st.worlds["minus"].generate(np.random.default_rng([7, 0]))
    changed = [k for k in dp if not np.array_equal(dp[k], dm[k])]
    if not changed:
        errs.append("minus identical to plus under pairing")
    for c in st.controls:
        for i in range(4):
            dp = st.worlds["plus"].generate(np.random.default_rng([7, i]))
            snapshot = {k: v.copy() for k, v in dp.items()}
            dc, ms = timed(c.transform, dp, np.random.default_rng([9, i]))
            tmax["control:" + c.id] = max(tmax.get("control:" + c.id, 0), ms)
            check_data(dc, exp, f"control {c.id}[{i}]", errs)
            if all(np.array_equal(dc[k], snapshot[k]) for k in snapshot):
                errs.append(f"control {c.id} unchanged")
            if any(not np.array_equal(dp[k], snapshot[k]) for k in snapshot):
                errs.append(f"control {c.id} mutated its input")
    slow = {k: round(v, 1) for k, v in tmax.items()}
    print(f"{sid}: changed-by-minus={changed} max_ms={slow} errors={errs}")
    if errs:
        problems[sid] = errs

print("PROBLEMS:", problems if problems else "none")
