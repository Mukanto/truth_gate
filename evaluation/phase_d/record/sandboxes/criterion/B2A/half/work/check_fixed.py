"""Form check and smoke run of the FIXED bodies only, on arrays generated here.

The faulty bodies are never imported, executed or analysed by this script.
Usage: py check_fixed.py            (from any folder; paths are relative to this file)
"""
import ast
import builtins
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "..", "cases")

LITERAL = (ast.Constant, ast.Tuple)


def form_errors(src):
    errs = []
    tree = ast.parse(src)
    body = tree.body
    if not body or not (isinstance(body[0], ast.Import) and len(body[0].names) == 1
                        and body[0].names[0].name == "numpy" and body[0].names[0].asname == "np"):
        errs.append("first statement is not 'import numpy as np'")
    funcs = []
    for node in body[1:]:
        if isinstance(node, ast.FunctionDef):
            funcs.append(node)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            errs.append("module-level docstring/expression")
        else:
            errs.append("module-level statement: " + type(node).__name__)
    names = {f.name for f in funcs}
    if "criterion" not in names:
        errs.append("no criterion")
    for f in funcs:
        if f.decorator_list:
            errs.append(f.name + ": decorator")
        if f.name == "criterion":
            a = f.args
            if [x.arg for x in a.args] != ["d"] or a.defaults or a.vararg or a.kwarg or a.kwonlyargs:
                errs.append("criterion signature")
            if any(x.annotation for x in a.args) or f.returns:
                errs.append("criterion annotation")
            if not ast.get_docstring(f):
                errs.append("criterion has no docstring")
        for n in ast.walk(f):
            if isinstance(n, (ast.Global, ast.Nonlocal)):
                errs.append(f.name + ": global/nonlocal")
            if isinstance(n, ast.FunctionDef):
                for dflt in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                    if not isinstance(dflt, LITERAL) or (
                            isinstance(dflt, ast.Tuple) and not all(isinstance(e, ast.Constant) for e in dflt.elts)):
                        errs.append(n.name + ": non-literal default")
                if n.decorator_list:
                    errs.append(n.name + ": decorator")
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Attribute):
                if isinstance(n.value.value, ast.Name) and n.value.value.id == "np" and n.value.attr == "random":
                    if n.attr != "default_rng":
                        errs.append(f.name + ": np.random." + n.attr)
        # scope check (approximate: names stored anywhere inside the function count as local)
        local = set()
        for n in ast.walk(f):
            if isinstance(n, ast.arg):
                local.add(n.arg)
            elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                local.add(n.id)
            elif isinstance(n, ast.FunctionDef):
                local.add(n.name)
        ok = local | names | {"np"} | set(dir(builtins))
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in ok:
                errs.append(f.name + ": free name " + n.id)
    return errs


def make(case_id, rng):
    """Self-generated arrays with the brief's keys, shapes, dtypes (pure noise unless stated)."""
    if case_id == "D-005":
        return {"X": rng.normal(size=(100, 150)), "y": rng.normal(size=100)}
    if case_id == "D-022":
        return {"X": rng.normal(size=(300, 10)), "y": rng.normal(size=300)}
    if case_id == "D-014":
        X = rng.normal(size=(250, 20))
        X[rng.random(X.shape) < 0.25] = np.nan
        return {"X": X, "y": rng.normal(size=250)}
    if case_id == "D-010":
        n, c = 1200, 150
        cat = np.zeros((n, c), dtype=bool)
        cat[np.arange(n), rng.integers(0, c, n)] = True
        return {"category": cat, "covariates": rng.normal(size=(n, 3)), "y": rng.normal(size=n)}
    if case_id == "D-054":
        return {"X": rng.normal(size=(80, 1000)), "y": np.arange(80) % 2 == 0}
    if case_id == "D-029":
        X = rng.normal(size=(600, 8))
        X[420:] = X[:180]
        return {"X": X, "y": rng.normal(size=600)}
    if case_id == "D-042":
        return {"X": rng.normal(size=(1200, 20)), "y": rng.normal(size=1200)}
    if case_id == "D-055":
        return {"X": np.cumsum(rng.normal(size=(1000, 6)), axis=0), "y": rng.normal(size=1000)}
    if case_id == "D-004":
        return {"X": rng.normal(size=(40, 250, 5)), "y": rng.normal(size=(40, 250))}
    if case_id == "D-044":
        return {"X": rng.normal(size=(60, 30, 25)), "y": rng.normal(size=(60, 30))}
    if case_id == "D-027":
        return {"X": rng.normal(size=(60, 25)), "y": rng.normal(size=60)}
    if case_id == "D-041":
        X = rng.normal(size=(1400, 25))
        X[rng.random(X.shape) < 0.3] = np.nan
        return {"X": X, "y": rng.random(1400) < 0.08}
    if case_id == "D-060":
        return {"X": rng.normal(size=(100, 500)), "y": rng.normal(size=100)}
    if case_id == "D-066":
        return {"X": rng.normal(size=(1000, 15)), "y": rng.random(1000) < 0.08}
    if case_id == "D-039":
        return {"X": np.cumsum(rng.normal(size=(400, 3)), axis=0), "y": rng.normal(size=400)}
    raise KeyError(case_id)


def main(ids):
    bad = 0
    for cid in ids:
        path = os.path.join(CASES, cid, "fixed_body.py")
        src = open(path, encoding="utf-8").read()
        errs = form_errors(src)
        ns = {}
        exec(compile(src, path, "exec"), ns)
        crit = ns["criterion"]
        rng = np.random.default_rng(12345)
        out = []
        times = []
        for rep in range(2):
            d = make(cid, rng)
            t0 = time.perf_counter()
            r1 = crit(d)
            times.append(time.perf_counter() - t0)
            r2 = crit(d)
            out.append((r1, r2))
        ok_type = all(isinstance(a, (bool, np.bool_)) and a == b for a, b in out)
        print(cid, "form:", errs or "ok", "| returns:", [o[0] for o in out], "| bool & deterministic:", ok_type,
              "| time/run s: %.3f %.3f" % tuple(times))
        if errs or not ok_type:
            bad += 1
    print("problems:", bad)


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(d for d in os.listdir(CASES) if d.startswith("D-"))
    main(ids)
