"""Phase B step 3 (designer): mechanical check of the world author's skeletons (PREREG §3, WORLD_INSTRUCTIONS rules).

Static checks (ast) + construction checks (import, build STUDY, call worlds and controls; never run the gate,
never call the criterion). Prints one line per skeleton and a summary; writes a JSON report next to the skeletons' parent.
"""
import ast, importlib.util, json, os, sys, time
import numpy as np

ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b"
WORLD = os.path.join(ROOT, "world")
SK = os.path.join(WORLD, "skeletons")
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")

briefs = {b["id"]: b for b in json.load(open(os.path.join(WORLD, "BRIEFS_SHUFFLED.json"), encoding="utf-8"))}
ALLOWED_KAPI = {"Study", "Criterion", "World", "Premise", "Control"}
BANNED_NAMES = {"open", "eval", "exec", "__import__", "compile", "input", "breakpoint", "globals", "locals", "vars",
                "setattr", "delattr", "getattr", "exit", "quit", "print"}
BANNED_NP_ATTR = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
STUDY_KW_OK = {"name", "criteria", "worlds", "controls", "premises", "relational"}


def static_check(wid, src):
    issues = []
    tree = ast.parse(src)
    # module docstring = "<id>: <claim>"
    doc = ast.get_docstring(tree, clean=False) or ""
    if doc.strip() != f"{wid}: {briefs[wid]['claim']}".strip():
        issues.append("module docstring differs from '<id>: <claim>'")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name != "numpy":
                    issues.append(f"import {a.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module != "kapi" or any(a.name not in ALLOWED_KAPI for a in node.names):
                issues.append(f"from {node.module} import {[a.name for a in node.names]}")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            issues.append(f"name {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr in BANNED_NP_ATTR:
                issues.append(f"attribute .{node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id == "np" and node.attr == "random":
                issues.append("np.random (global random state or module access)")
            if node.attr.startswith("__") and node.attr != "__init__":
                issues.append(f"dunder attribute .{node.attr}")
    # top level: only docstring, imports, defs, constant assignments, STUDY
    for i, node in enumerate(tree.body):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign, ast.AnnAssign)):
            continue
        if i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        issues.append(f"top-level statement {type(node).__name__} at line {node.lineno}")
    # criterion body exactly: docstring + raise NotImplementedError
    crit = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "criterion"]
    if len(crit) != 1:
        issues.append("criterion function missing or duplicated")
    else:
        body = crit[0].body
        ok = (len(body) == 2 and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
              and isinstance(body[0].value.value, str) and isinstance(body[1], ast.Raise)
              and isinstance(body[1].exc, ast.Name) and body[1].exc.id == "NotImplementedError")
        if not ok:
            issues.append("criterion body is not exactly docstring + raise NotImplementedError")
        if [a.arg for a in crit[0].args.args] != ["d"]:
            issues.append("criterion signature is not (d)")
    # STUDY call keywords
    study_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Study"]
    if len(study_calls) != 1:
        issues.append(f"{len(study_calls)} Study(...) calls")
    else:
        kws = {k.arg for k in study_calls[0].keywords}
        if study_calls[0].args:
            issues.append("Study called with positional arguments")
        bad = kws - STUDY_KW_OK
        if bad:
            issues.append(f"Study keywords not allowed: {sorted(bad)}")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "World":
            if any(k.arg not in {"derived_from", "change"} for k in n.keywords) or len(n.args) != 1:
                issues.append("World(...) with unexpected arguments")
    return issues


def load(wid):
    path = os.path.join(SK, f"{wid}.py")
    spec = importlib.util.spec_from_file_location(f"skel_{wid}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def shape_ndim(shape_text):
    import re
    m = re.match(r"\s*\(([^)]*)\)", shape_text)  # first parenthesised group only (axis notes may follow)
    t = (m.group(1) if m else shape_text).strip()
    return 1 if t == "" else len([p for p in t.split(",") if p.strip()])


def dyn_check(wid, mod):
    issues, info = [], {}
    st = mod.STUDY
    b = briefs[wid]
    if st.name != wid:
        issues.append(f"name {st.name!r}")
    if len(st.criteria) != 1 or st.criteria[0].id != "C" or st.criteria[0].fn is not mod.criterion:
        issues.append("criteria is not [Criterion('C', criterion)]")
    c = st.criteria[0]
    if c.regime != "all" or c.components is not None or c.tolerances or c.control_waiver is not None:
        issues.append("criterion has non-default options")
    if st.deterministic or st.allow_paths or st.regimes != ["all"]:
        issues.append("non-default deterministic/allow_paths/regimes")
    from kapi import Study as _S  # noqa
    d0 = _S.__dataclass_fields__
    if repr(st.budget) != repr(d0["budget"].default_factory()) or repr(st.targets) != repr(d0["targets"].default_factory()):
        issues.append("budget or targets not default")
    w = st.worlds
    info["worlds"] = sorted(w)
    if "plus" not in w or "minus" not in w:
        issues.append("plus/minus missing")
        return issues, info
    if w["minus"].derived_from != "plus" or not w["minus"].change.strip():
        issues.append("minus lacks derived_from='plus' or change")
    if len(st.controls) < 1:
        issues.append("no control")
    info["controls"] = [ct.id for ct in st.controls]
    info["premises"] = [p.id for p in st.premises]
    info["relational"] = [list(r) for r in st.relational]
    keys = [k["key"] for k in b["data_keys"]]
    dtypes = {k["key"]: k["dtype"] for k in b["data_keys"]}
    ndims = {k["key"]: shape_ndim(k["shape"]) for k in b["data_keys"]}
    shapes = {}
    times = []
    for name in sorted(w):
        for s in range(3):
            rng = np.random.default_rng(1000 + s)
            t0 = time.perf_counter()
            d = w[name].generate(rng)
            times.append(time.perf_counter() - t0)
            if not isinstance(d, dict) or sorted(d) != sorted(keys):
                issues.append(f"world {name}: keys {sorted(d) if isinstance(d, dict) else type(d)} != brief {sorted(keys)}")
                continue
            for k in keys:
                a = d[k]
                if not isinstance(a, np.ndarray):
                    issues.append(f"world {name}: {k} is not an ndarray"); continue
                want = np.bool_ if dtypes[k].lower().startswith("bool") else np.float64
                if a.dtype != want:
                    issues.append(f"world {name}: {k} dtype {a.dtype} (brief {dtypes[k]})")
                if a.ndim != ndims[k]:
                    issues.append(f"world {name}: {k} ndim {a.ndim} (brief shape {b['data_keys'][keys.index(k)]['shape']})")
                if want is np.float64 and not np.all(np.isfinite(a)):
                    issues.append(f"world {name}: {k} has non-finite values")
                shapes.setdefault(k, set()).add(a.shape)
            # controls on this draw
            if name == "plus":
                for ct in st.controls:
                    if ct.transform is None:
                        continue
                    out = ct.transform(dict(d), np.random.default_rng(7 + s))
                    if not isinstance(out, dict) or sorted(out) != sorted(keys):
                        issues.append(f"control {ct.id}: does not return the full dict")
                        continue
                    for k in keys:
                        if out[k].shape != d[k].shape or out[k].dtype != d[k].dtype:
                            issues.append(f"control {ct.id}: {k} shape/dtype changed")
                    if all(np.array_equal(out[k], d[k]) for k in keys):
                        issues.append(f"control {ct.id}: identity on this draw")
                for p in st.premises:
                    out = p.mutate(dict(d), np.random.default_rng(11 + s))
                    if not isinstance(out, dict) or sorted(out) != sorted(keys):
                        issues.append(f"premise {p.id}: does not return the full dict")
    for k, ss in shapes.items():
        if len(ss) > 1:
            issues.append(f"{k}: shape differs between worlds/draws {sorted(ss)}")
    info["shapes"] = {k: sorted(ss)[0] for k, ss in shapes.items()}
    info["max_ms"] = round(1000 * max(times), 3)
    return issues, info


report = {}
n_ok = 0
for wid in sorted(briefs):
    path = os.path.join(SK, f"{wid}.py")
    if not os.path.exists(path):
        report[wid] = {"issues": ["missing file"]}
        print(wid, "MISSING")
        continue
    src = open(path, encoding="utf-8").read()
    issues = static_check(wid, src)
    info = {}
    try:
        mod = load(wid)
        di, info = dyn_check(wid, mod)
        issues += di
    except Exception as e:  # construction failure is an issue, not a crash
        issues.append(f"load/construct error: {type(e).__name__}: {e}")
    issues = list(dict.fromkeys(issues))
    report[wid] = {"issues": issues, **info}
    n_ok += not issues
    print(f"{wid} {'OK ' if not issues else 'ISSUES'} max_ms={info.get('max_ms')} controls={info.get('controls')} "
          f"worlds={info.get('worlds')} prem={info.get('premises')} rel={info.get('relational')}"
          + ("" if not issues else "\n    - " + "\n    - ".join(issues)))
print(f"\n{n_ok}/{len(briefs)} skeletons pass all mechanical checks")
json.dump(report, open(os.path.join(ROOT, "STEP3_SKELETON_CHECK.json"), "w", encoding="utf-8"), indent=2, default=str)
