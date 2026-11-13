"""Phase C skeleton check (PREREG_PHASE_C section 4 item 4), frozen with the pre-registration.

Adapted from the Phase B step-3 script (evaluation/phase_b/record/designer_scripts/phase_b_step3.py): the import line is
`from truth_gate import ...`, the criterion must be exactly one `Criterion("C", criterion)` without components, and the
paths are arguments. Static checks (ast) and construction checks (import the module, build STUDY, call the worlds and the
controls on fixed seeds). It never calls the criterion and never runs the gate.
A skeleton with any banned name, non-allowed import, banned attribute or other module-level statement is NOT loaded or
executed: only the static issues are reported. `<numpy>.random` is a banned attribute for every name that numpy is bound to
by the skeleton's imports (`np`, `numpy`, and the alias of `import numpy as X`): `np.random.rand`, `numpy.random.seed`,
`X.random` are all blocking issues; `rng.random(...)` (a Generator method on a name that is not a numpy binding) is not.
`import numpy.random` and `from numpy import random` stay import issues. An alias assignment (Assign, AnnAssign, AugAssign
or NamedExpr whose value, or an element of a tuple/list value, is a bare numpy binding name or `<numpy binding>.random`,
e.g. `x = np`, `y = numpy.random`, `a, b = np, 1`) is the same blocking issue ("np.random ...: alias assignment x = np").
Passing numpy as a function argument default or in another container is not tracked. Size caps: no array dimension above 1000 and no array above 500000 elements
(worlds, control transforms and control worlds). Worlds, control transforms and control worlds share the 100 ms limit.

Package root check: --package-root is inserted first on sys.path and `truth_gate` is imported from it before any skeleton
is looked at. If `truth_gate` was already imported before that, or the imported module's realpath is not under the realpath
of the package root (e.g. an editable install answered instead), the script stops with exit code 2 and a message, and no
skeleton is checked. The imported file is printed on stderr and recorded as the top-level field "truth_gate_file" of the
report.
Report layout (--out JSON): {"truth_gate_file": "<path>", "<id>": {...}, ...}: the "truth_gate_file" key is a string, every
other key is a skeleton id whose value is {"issues": [...]} (a missing file or a syntax error) or {"issues": [...],
"loaded": bool} plus, when the module was loaded, "worlds", "controls", "control_max_ms", "shapes", "max_ms".

Usage:
    py check_skeletons.py --skeletons DIR --briefs BRIEFS.json --package-root PKG_DIR --out REPORT.json
PKG_DIR is the sandbox pkg/ folder that holds truth_gate/ and kapi/.
BRIEFS.json: a list of {"id", "claim", "data_keys": [{"key", "shape", "dtype", "meaning"}], "sizes"}.
Exit code 0 if every skeleton passes, 1 otherwise, 2 on a usage error or a failed package root check. The report lists, per id, the issues (the error list that PREREG_PHASE_C
section 4 item 4 sends back once to a fresh Fable agent).
"""
import argparse, ast, importlib.util, json, os, re, sys, time
import numpy as np

ALLOWED_TG = {"Study", "Criterion", "World", "Premise", "Control"}
BANNED_NAMES = {"open", "eval", "exec", "__import__", "compile", "input", "breakpoint", "globals", "locals", "vars",
                "setattr", "delattr", "getattr", "exit", "quit", "print", "__builtins__"}
BANNED_NP_ATTR = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
STUDY_KW_OK = {"name", "criteria", "worlds", "controls", "premises", "relational"}
MAX_DIM = 1000       # PREREG_PHASE_C section 2: at most 1000 rows or units (and 500 features)
MAX_ELEMENTS = 500000
BLOCKING_PREFIXES = ("name ", "import ", "from ", "attribute .", "np.random", "dunder attribute", "top-level statement")
MAX_MS = 100.0  # a world call above this is reported (PB section 2 timing; rule 6 of the world instructions asks for < 10 ms)


def numpy_names(tree):
    """Names numpy is bound to: np, numpy, and the alias of every `import numpy [as X]` in the module."""
    names = {"np", "numpy"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "numpy":
                    names.add(a.asname or "numpy")
    return names


def verify_package_root(package_root):
    """Import truth_gate from package_root (first on sys.path). Return (file, None) or (None, message)."""
    root = os.path.abspath(package_root)
    if "truth_gate" in sys.modules:
        return None, "truth_gate was already imported before the package root was inserted; refusing to reuse it"
    sys.path.insert(0, root)
    try:
        import truth_gate
    except Exception as e:
        return None, f"cannot import truth_gate with package root {root}: {type(e).__name__}: {e}"
    f = getattr(truth_gate, "__file__", None)
    if not f:
        return None, f"truth_gate imported with package root {root} has no __file__ (namespace package?)"
    real, rroot = os.path.normcase(os.path.realpath(f)), os.path.normcase(os.path.realpath(root))
    try:
        inside = os.path.commonpath([real, rroot]) == rroot
    except ValueError:  # different drives
        inside = False
    if not inside:
        return None, f"truth_gate was imported from {f}, which is not under the package root {root}"
    return f, None


def is_numpy_ref(v, npn):
    """True if v is a bare numpy binding name or `<numpy binding>.random`."""
    return (isinstance(v, ast.Name) and v.id in npn) or            (isinstance(v, ast.Attribute) and v.attr == "random" and isinstance(v.value, ast.Name) and v.value.id in npn)


def alias_assignments(root, npn):
    """Assign / AnnAssign / AugAssign / NamedExpr nodes under root whose value (or, for a tuple/list value, any element) is
    a numpy reference (see is_numpy_ref): `x = np`, `x = np.random`, `a, b = np, 1`, `(x := numpy)`, `x += np`."""
    out = []
    for n in ast.walk(root):
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)) and n.value is not None:
            vals = list(n.value.elts) if isinstance(n.value, (ast.Tuple, ast.List)) else [n.value]
            if any(is_numpy_ref(e, npn) for e in vals):
                out.append(n)
    return out


def static_check(wid, src, claim):
    issues = []
    tree = ast.parse(src)
    npn = numpy_names(tree)
    doc = ast.get_docstring(tree, clean=False) or ""
    if doc.strip() != f"{wid}: {claim}".strip():
        issues.append("module docstring differs from '<id>: <claim>'")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name != "numpy":
                    issues.append(f"import {a.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module != "truth_gate" or any(a.name not in ALLOWED_TG for a in node.names):
                issues.append(f"from {node.module} import {[a.name for a in node.names]}")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            issues.append(f"name {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr in BANNED_NP_ATTR:
                issues.append(f"attribute .{node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id in npn and node.attr == "random":
                issues.append(f"np.random (global random state or module access): {node.value.id}.random")
            if node.attr.startswith("__") and node.attr != "__init__":
                issues.append(f"dunder attribute .{node.attr}")
    for node in alias_assignments(tree, npn):
        issues.append(f"np.random (global random state or module access): alias assignment {ast.unparse(node)}")
    for i, node in enumerate(tree.body):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign, ast.AnnAssign)):
            continue
        if i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        issues.append(f"top-level statement {type(node).__name__} at line {node.lineno}")
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
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Study"]
    if len(calls) != 1:
        issues.append(f"{len(calls)} Study(...) calls")
    else:
        if calls[0].args:
            issues.append("Study called with positional arguments")
        bad = {k.arg for k in calls[0].keywords} - STUDY_KW_OK
        if bad:
            issues.append(f"Study keywords not allowed: {sorted(bad)}")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "World":
            if any(k.arg not in {"derived_from", "change"} for k in n.keywords) or len(n.args) != 1:
                issues.append("World(...) with unexpected arguments")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Criterion":
            if n.keywords or len(n.args) != 2 or not (isinstance(n.args[0], ast.Constant) and n.args[0].value == "C"):
                issues.append("Criterion(...) is not Criterion(\"C\", criterion)")
    return issues


def is_blocking(issue):
    """A static issue that forbids loading the module (it would execute banned code)."""
    return issue.startswith(BLOCKING_PREFIXES)


def shape_ndim(shape_text):
    m = re.match(r"\s*\(([^)]*)\)", shape_text)
    t = (m.group(1) if m else shape_text).strip()
    return 1 if t == "" else len([p for p in t.split(",") if p.strip()])


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dyn_check(wid, mod, brief):
    issues, info = [], {}
    st = mod.STUDY
    if st.name != wid:
        issues.append(f"name {st.name!r}")
    if len(st.criteria) != 1 or st.criteria[0].id != "C" or st.criteria[0].fn is not mod.criterion:
        issues.append("criteria is not [Criterion('C', criterion)]")
    c = st.criteria[0]
    if c.regime != "all" or c.components is not None or c.tolerances or c.control_waiver is not None:
        issues.append("criterion has non-default options")
    if st.deterministic or st.allow_paths or st.regimes != ["all"]:
        issues.append("non-default deterministic/allow_paths/regimes")
    d0 = type(st).__dataclass_fields__
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
    keys = [k["key"] for k in brief["data_keys"]]
    dtypes = {k["key"]: k["dtype"] for k in brief["data_keys"]}
    ndims = {k["key"]: shape_ndim(k["shape"]) for k in brief["data_keys"]}
    shapes, times = {}, []
    ctimes = {}

    def check_data(label, d):
        """Keys, types, dtypes, ndim, finiteness, size caps and shapes of one generated dict. True if it is a usable dict."""
        if not isinstance(d, dict) or sorted(d) != sorted(keys):
            issues.append(f"{label}: keys {sorted(d) if isinstance(d, dict) else type(d).__name__} != brief {sorted(keys)}")
            return False
        for k in keys:
            a = d[k]
            if not isinstance(a, np.ndarray):
                issues.append(f"{label}: {k} is not an ndarray"); continue
            want = np.bool_ if dtypes[k].lower().startswith("bool") else np.float64
            if a.dtype != want:
                issues.append(f"{label}: {k} dtype {a.dtype} (brief {dtypes[k]})")
            if a.ndim != ndims[k]:
                issues.append(f"{label}: {k} ndim {a.ndim} (brief shape {brief['data_keys'][keys.index(k)]['shape']})")
            if want is np.float64 and not np.all(np.isfinite(a)):
                issues.append(f"{label}: {k} has non-finite values")
            if any(n > MAX_DIM for n in a.shape) or a.size > MAX_ELEMENTS:
                issues.append(f"{label}: {k} shape {a.shape} exceeds the size cap (dimension {MAX_DIM}, {MAX_ELEMENTS} elements)")
            shapes.setdefault(k, set()).add(a.shape)
        return True

    for name in sorted(w):
        for s in range(3):
            rng = np.random.default_rng(1000 + s)
            t0 = time.perf_counter()
            try:
                d = w[name].generate(rng)
            except Exception as e:
                issues.append(f"world {name}: raises {type(e).__name__}")
                continue
            times.append(time.perf_counter() - t0)
            if not check_data(f"world {name}", d):
                continue
            if name == "plus":
                for ct in st.controls:
                    if ct.transform is None:
                        continue
                    t0 = time.perf_counter()
                    try:
                        out = ct.transform(dict(d), np.random.default_rng(7 + s))
                    except Exception as e:
                        issues.append(f"control {ct.id}: raises {type(e).__name__}"); continue
                    ctimes.setdefault(ct.id, []).append(time.perf_counter() - t0)
                    if not isinstance(out, dict) or sorted(out) != sorted(keys):
                        issues.append(f"control {ct.id}: does not return the full dict"); continue
                    for k in keys:
                        if out[k].shape != d[k].shape or out[k].dtype != d[k].dtype:
                            issues.append(f"control {ct.id}: {k} shape/dtype changed")
                        if any(n > MAX_DIM for n in out[k].shape) or out[k].size > MAX_ELEMENTS:
                            issues.append(f"control {ct.id}: {k} shape {out[k].shape} exceeds the size cap")
                    if all(np.array_equal(out[k], d[k]) for k in keys):
                        issues.append(f"control {ct.id}: identity on this draw")
                for p in st.premises:
                    out = p.mutate(dict(d), np.random.default_rng(11 + s))
                    if not isinstance(out, dict) or sorted(out) != sorted(keys):
                        issues.append(f"premise {p.id}: does not return the full dict")
    for ct in st.controls:
        if ct.world is None:
            continue
        for s in range(3):
            t0 = time.perf_counter()
            try:
                d = ct.world.generate(np.random.default_rng(2000 + s))
            except Exception as e:
                issues.append(f"control world {ct.id}: raises {type(e).__name__}")
                continue
            ctimes.setdefault(ct.id, []).append(time.perf_counter() - t0)
            check_data(f"control world {ct.id}", d)
    for cid, tl in sorted(ctimes.items()):
        if 1000 * max(tl) > MAX_MS:
            issues.append(f"control {cid} takes {1000 * max(tl):.1f} ms (> {MAX_MS} ms)")
    info["control_max_ms"] = {cid: round(1000 * max(tl), 3) for cid, tl in sorted(ctimes.items())}
    for k, ss in shapes.items():
        if len(ss) > 1:
            issues.append(f"{k}: shape differs between worlds/draws {sorted(ss)}")
    info["shapes"] = {k: sorted(ss)[0] for k, ss in shapes.items()}
    info["max_ms"] = round(1000 * max(times), 3) if times else None
    if times and 1000 * max(times) > MAX_MS:
        issues.append(f"world call takes {1000 * max(times):.1f} ms (> {MAX_MS} ms)")
    txt = brief["sizes"] + " " + " ".join(k["shape"] + " " + k["meaning"] for k in brief["data_keys"]) + " " + brief["claim"]
    nums = set(int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", txt) if n.replace(",", "").isdigit())
    miss = sorted({dim for s in info["shapes"].values() for dim in s} - nums)
    if miss:
        issues.append(f"array dimensions not found in the brief text: {miss}")
    return issues, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skeletons", required=True)
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--package-root", required=True, metavar="PKG_DIR",
                    help="the sandbox pkg/ folder that holds truth_gate/ and kapi/")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.dont_write_bytecode = True
    tg_file, err = verify_package_root(a.package_root)
    if err:
        print(f"package root check failed: {err}", file=sys.stderr)
        return 2
    print(f"truth_gate: {tg_file}", file=sys.stderr)
    briefs = {b["id"]: b for b in json.load(open(a.briefs, encoding="utf-8"))}
    report, n_ok = {"truth_gate_file": tg_file}, 0
    for wid in sorted(briefs):
        path = os.path.join(a.skeletons, f"{wid}.py")
        if not os.path.exists(path):
            report[wid] = {"issues": ["missing file"]}
            print(wid, "MISSING"); continue
        src = open(path, encoding="utf-8").read()
        try:
            issues = static_check(wid, src, briefs[wid]["claim"])
        except SyntaxError as e:
            report[wid] = {"issues": [f"syntax error: {e}"]}
            print(wid, "SYNTAX ERROR"); continue
        if any(is_blocking(i) for i in issues):
            issues = list(dict.fromkeys(issues))
            report[wid] = {"issues": issues, "loaded": False}
            print(f"{wid} ISSUES (static only, module not loaded)\n    - " + "\n    - ".join(issues)); continue
        info = {}
        try:
            mod = load(path, f"skel_{wid}")
            di, info = dyn_check(wid, mod, briefs[wid])
            issues += di
        except Exception as e:
            issues.append(f"load/construct error: {type(e).__name__}: {e}")
        issues = list(dict.fromkeys(issues))
        report[wid] = {"issues": issues, "loaded": True, **info}
        n_ok += not issues
        print(f"{wid} {'OK' if not issues else 'ISSUES'}" + ("" if not issues else "\n    - " + "\n    - ".join(issues)))
    print(f"\n{n_ok}/{len(briefs)} skeletons pass")
    json.dump(report, open(a.out, "w", encoding="utf-8"), indent=2, default=str)
    return 0 if n_ok == len(briefs) else 1


if __name__ == "__main__":
    sys.exit(main())
