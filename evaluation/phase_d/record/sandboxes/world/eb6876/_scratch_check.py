# Scratch: structural checks of the skeletons (shapes, dtypes, finiteness, timing, module form) and
# descriptive / population-level effect checks. No criterion-like analysis, no gate run.
import ast
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pkg"))
import numpy as np  # noqa: E402

FORBIDDEN = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
             "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__", "load", "save", "savez",
             "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}

batch = json.load(open(os.path.join(HERE, "BATCH.json"), encoding="utf-8"))


def ast_checks(path, brief):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    problems = []
    body = tree.body
    doc = ast.get_docstring(tree, clean=False)
    if doc != f"{brief['id']}: {brief['claim']}":
        problems.append("docstring mismatch")
    if "\n" in (doc or ""):
        problems.append("docstring not one line")
    imports = [n for n in body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if len(imports) != 2:
        problems.append(f"{len(imports)} import lines")
    for n in body[1:]:
        if not isinstance(n, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
            problems.append(f"module-level {type(n).__name__} at line {n.lineno}")
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id in FORBIDDEN:
            problems.append(f"forbidden name {n.id} line {n.lineno}")
        if isinstance(n, ast.Attribute):
            if n.attr in FORBIDDEN:
                problems.append(f"forbidden attribute {n.attr} line {n.lineno}")
            if n.attr.startswith("__"):
                problems.append(f"dunder attribute {n.attr} line {n.lineno}")
            if n.attr == "random" and isinstance(n.value, ast.Name) and n.value.id == "np":
                problems.append(f"np.random used line {n.lineno}")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "World":
            kw = sorted(k.arg for k in n.keywords)
            if not ((len(n.args) == 1 and kw == []) or (len(n.args) == 1 and kw == ["change", "derived_from"])):
                problems.append(f"World call form line {n.lineno}")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Study":
            bad = [k.arg for k in n.keywords if k.arg not in
                   {"name", "criteria", "worlds", "controls", "premises", "relational"}]
            if bad:
                problems.append(f"Study keywords {bad}")
    return problems


def check_data(d, brief, tag):
    problems = []
    keys = [k["key"] for k in brief["data_keys"]]
    if sorted(d) != sorted(keys):
        problems.append(f"{tag}: keys {sorted(d)} != {sorted(keys)}")
        return problems
    for k in brief["data_keys"]:
        a = d[k["key"]]
        if not isinstance(a, np.ndarray):
            problems.append(f"{tag}: {k['key']} not ndarray")
            continue
        if tuple(a.shape) != tuple(k["dims"]):
            problems.append(f"{tag}: {k['key']} shape {a.shape} != {k['dims']}")
        want = np.float64 if k["dtype"] == "float" else np.bool_
        if a.dtype != want:
            problems.append(f"{tag}: {k['key']} dtype {a.dtype}")
        if a.dtype == np.float64 and not np.all(np.isfinite(a)):
            problems.append(f"{tag}: {k['key']} non-finite")
        if max(a.shape) > 2000 or a.size > 2_000_000:
            problems.append(f"{tag}: {k['key']} too large")
    return problems


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, 1000 * (time.perf_counter() - t0)


report = {}
for brief in batch:
    bid = brief["id"]
    path = os.path.join(HERE, "skeletons", f"{bid}.py")
    probs = ast_checks(path, brief)
    spec = importlib.util.spec_from_file_location("sk_" + bid.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    study = mod.STUDY
    tmax = 0.0
    for wname, world in study.worlds.items():
        for i in range(6):
            d, t = timed(world.generate, np.random.default_rng([7, i, len(wname)]))
            tmax = max(tmax, t)
            probs += check_data(d, brief, f"{wname}[{i}]")
    for c in study.controls:
        for i in range(6):
            d = study.worlds["plus"].generate(np.random.default_rng([11, i]))
            out, t = timed(c.transform, d, np.random.default_rng([13, i]))
            tmax = max(tmax, t)
            probs += check_data(out, brief, f"control {c.id}[{i}]")
            if all(np.array_equal(out[k], d[k]) for k in d):
                probs.append(f"control {c.id}[{i}] unchanged")
    report[bid] = (probs, round(tmax, 1))

for bid, (probs, tmax) in report.items():
    print(bid, "max ms", tmax, "OK" if not probs else probs[:6])
