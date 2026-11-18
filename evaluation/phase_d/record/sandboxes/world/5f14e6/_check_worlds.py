"""Author-side check of the skeleton worlds: structure, shapes, dtypes, timing, controls, descriptive effects.
No criterion analysis is computed here."""
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
             "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__"}
NP_FILE = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}


def static_check(path, sid, claim):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    errs = []
    doc = ast.get_docstring(tree, clean=False)
    if doc != f"{sid}: {claim}":
        errs.append("docstring mismatch")
    for i, node in enumerate(tree.body):
        if i == 0 and isinstance(node, ast.Expr):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
            continue
        errs.append(f"module-level node {type(node).__name__} line {node.lineno}")
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if len(imports) != 2:
        errs.append(f"{len(imports)} import lines")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN:
            errs.append(f"forbidden name {node.id} line {node.lineno}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                errs.append(f"dunder attribute {node.attr}")
            if node.attr in NP_FILE:
                errs.append(f"numpy file function {node.attr}")
            if node.attr == "random" and isinstance(node.value, ast.Name) and node.value.id == "np":
                errs.append("np.random used")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "World":
            kws = sorted(k.arg for k in node.keywords)
            if not ((len(node.args) == 1 and kws == []) or (len(node.args) == 1 and kws == ["change", "derived_from"])):
                errs.append("World call form")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Study":
            for k in node.keywords:
                if k.arg not in ("name", "criteria", "worlds", "controls", "premises", "relational"):
                    errs.append(f"Study keyword {k.arg}")
    return errs


def load(path):
    spec = importlib.util.spec_from_file_location("sk_" + os.path.basename(path)[:-3].replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def timed(fn, *a):
    t0 = time.perf_counter()
    out = fn(*a)
    return out, (time.perf_counter() - t0) * 1000.0


def check_data(d, brief, label, errs):
    keys = [k["key"] for k in brief["data_keys"]]
    if sorted(d.keys()) != sorted(keys):
        errs.append(f"{label}: keys {sorted(d.keys())}")
        return
    for k in brief["data_keys"]:
        a = d[k["key"]]
        if not isinstance(a, np.ndarray):
            errs.append(f"{label}: {k['key']} not ndarray")
            continue
        if list(a.shape) != k["dims"]:
            errs.append(f"{label}: {k['key']} shape {a.shape}")
        want = np.float64 if k["dtype"] == "float" else np.bool_
        if a.dtype != want:
            errs.append(f"{label}: {k['key']} dtype {a.dtype}")
        if a.dtype != np.bool_ and not np.all(np.isfinite(a)):
            errs.append(f"{label}: {k['key']} non-finite")


def same(a, b):
    return all(np.array_equal(a[k], b[k]) for k in a)


def describe(sid, d):
    """Descriptive effect summaries (not the criterion)."""
    if sid == "D-052":
        imp = d["post"] - d["pre"]
        return np.mean(imp[d["young"]]) - np.mean(imp[~d["young"]])
    if sid == "D-055":
        return float(np.max(np.abs([np.corrcoef(d["X"][:, j], d["y"])[0, 1] for j in range(6)])))
    if sid == "D-056":
        r = d["oxygen_uptake"] - 6.0 * (d["body_mass"] / 300.0) ** 0.75
        return float(np.ptp(r.mean(axis=1)))
    if sid == "D-062":
        return float(np.mean([np.corrcoef(d["femur"][s], d["humerus"][s])[0, 1] for s in range(12)]))
    if sid == "D-064":
        return float(np.corrcoef(d["response"], d["clinical"][:, 0])[0, 1])
    if sid == "D-066":
        X = (d["X"] - d["X"].mean(0)) / d["X"].std(0)
        return float(np.linalg.norm(X[d["y"]].mean(0) - X[~d["y"]].mean(0)))
    if sid == "D-067":
        return float(np.corrcoef(d["kidney_weight"], d["heart_weight"])[0, 1])
    if sid == "D-068":
        return float(np.mean([np.corrcoef(d["head_width"][p], d["wing_length"][p])[0, 1] for p in range(25)]))
    return float("nan")


def main():
    briefs = json.load(open(os.path.join(HERE, "BATCH.json"), encoding="utf-8"))
    for brief in briefs:
        sid = brief["id"]
        path = os.path.join(HERE, "skeletons", f"{sid}.py")
        errs = static_check(path, sid, brief["claim"])
        mod = load(path)
        st = mod.STUDY
        tmax = 0.0
        shapes = None
        desc = {"plus": [], "minus": []}
        ctl_desc = {c.id: [] for c in st.controls}
        for seed in range(40):
            dp, tp = timed(st.worlds["plus"].generate, np.random.default_rng(seed))
            dm, tm = timed(st.worlds["minus"].generate, np.random.default_rng(seed))
            tmax = max(tmax, tp, tm)
            check_data(dp, brief, f"plus[{seed}]", errs)
            check_data(dm, brief, f"minus[{seed}]", errs)
            sh = {k: v.shape for k, v in dp.items()}
            if shapes is None:
                shapes = sh
            elif sh != shapes:
                errs.append("shape differs between draws")
            if same(dp, dm):
                errs.append(f"minus identical to plus at seed {seed}")
            desc["plus"].append(describe(sid, dp))
            desc["minus"].append(describe(sid, dm))
            for c in st.controls:
                dc, tc = timed(c.transform, dp, np.random.default_rng(1000 + seed))
                tmax = max(tmax, tc)
                check_data(dc, brief, f"control {c.id}[{seed}]", errs)
                if same(dc, dp):
                    errs.append(f"control {c.id} unchanged at seed {seed}")
                ctl_desc[c.id].append(describe(sid, dc))
        mp = np.mean(desc["plus"])
        mm = np.mean(desc["minus"])
        cs = ", ".join(f"{k}={np.mean(v):.3f}" for k, v in ctl_desc.items())
        sys.stdout.write(f"{sid}: errors={errs[:5]} n_err={len(errs)} max_ms={tmax:.1f} "
                         f"desc plus={mp:.3f} minus={mm:.3f} controls: {cs}\n")


if __name__ == "__main__":
    main()
