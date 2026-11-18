# Own checks of the skeletons: loading, static rules, shapes/dtypes/finiteness, timing, controls,
# and world-level effect presence (population quantities from the generative design; no criterion).
import ast
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "pkg"))
import numpy as np  # noqa: E402
import truth_gate  # noqa: E402

BATCH = json.load(open(os.path.join(HERE, "BATCH.json"), encoding="utf-8"))
FORBIDDEN = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
             "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__"}
NP_FILE = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}


def static_check(path, brief):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    errs = []
    body = tree.body
    doc = ast.get_docstring(tree, clean=False)
    if doc != f"{brief['id']}: {brief['claim']}":
        errs.append("docstring mismatch")
    for i, node in enumerate(body):
        if i == 0 and isinstance(node, ast.Expr):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            continue
        if isinstance(node, ast.Assign) and all(isinstance(t, ast.Name) for t in node.targets):
            continue
        errs.append(f"module-level node {type(node).__name__} line {node.lineno}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN:
            errs.append(f"forbidden name {node.id}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                errs.append(f"dunder attr {node.attr}")
            if node.attr in NP_FILE:
                errs.append(f"np file fn {node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id == "np" and node.attr == "random":
                errs.append("np.random used")
    return errs


def load(path):
    spec = importlib.util.spec_from_file_location("sk_" + os.path.basename(path)[:-3].replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_data(d, brief, tag):
    errs = []
    keys = [k["key"] for k in brief["data_keys"]]
    if not isinstance(d, dict) or sorted(d) != sorted(keys):
        return [f"{tag}: keys {sorted(d) if isinstance(d, dict) else type(d)} != {sorted(keys)}"]
    for k in brief["data_keys"]:
        a = d[k["key"]]
        want = np.float64 if k["dtype"] == "float" else np.bool_
        if not isinstance(a, np.ndarray) or a.dtype != want:
            errs.append(f"{tag}: {k['key']} dtype {getattr(a, 'dtype', type(a))}")
        if tuple(a.shape) != tuple(k["dims"]):
            errs.append(f"{tag}: {k['key']} shape {a.shape} != {k['dims']}")
        if a.dtype == np.float64 and not np.all(np.isfinite(a)):
            errs.append(f"{tag}: {k['key']} non-finite")
    return errs


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, 1000 * (time.perf_counter() - t0)


def main():
    for brief in BATCH:
        path = os.path.join(HERE, "skeletons", brief["id"] + ".py")
        errs = static_check(path, brief)
        mod = load(path)
        st = mod.STUDY
        assert isinstance(st, truth_gate.Study)
        maxms = 0.0
        for w in ("plus", "minus"):
            for s in range(30):
                rng = np.random.default_rng(1000 + s)
                d, ms = timed(st.worlds[w].generate, rng)
                maxms = max(maxms, ms)
                errs += check_data(d, brief, f"{w}#{s}")
                for c in st.controls:
                    d2, ms2 = timed(c.transform, d, np.random.default_rng(5000 + s))
                    maxms = max(maxms, ms2)
                    errs += check_data(d2, brief, f"ctrl {c.id} {w}#{s}")
                    if all(np.array_equal(d[k], d2[k]) for k in d):
                        errs.append(f"ctrl {c.id} unchanged {w}#{s}")
        print(f"{brief['id']}: errors={len(errs)} max_ms={maxms:.1f}")
        for e in errs[:10]:
            print("   ", e)


if __name__ == "__main__":
    main()
