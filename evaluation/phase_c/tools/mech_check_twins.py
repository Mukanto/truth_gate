"""Phase C mechanical check of the twins (PREREG_PHASE_C section 5, as PB section 5.1 and AUTHOR_PHASE2_C rules).

Adapted from the Phase B script (evaluation/phase_b/record/designer_scripts/phase_b_step5_mech.py): paths are arguments and
the import line is `from truth_gate import ...`.

For every case folder under --cases-root (a folder holding faulty.py, fixed.py, CASE.md and ASSIGNMENT.json with a
"world_id"; any other ASSIGNMENT.json field, e.g. class/subtype/overlap, is carried into the report):
  * faulty.py and fixed.py equal the frozen skeleton <world_id>.py outside the criterion function (docstring of the
    criterion kept, signature (d) without defaults, annotations or decorators); the skeleton itself imports only
    `from truth_gate import ...`;
  * no import inside the criterion (so no new imports anywhere); no banned names or attributes (open, eval, exec, ...,
    np.load, np.save, ...); no dunder attribute; the criterion reads no module-level name except `np` and no undefined name;
  * randomness only as <numpy>.random.default_rng(<int literal>), `<numpy>.random` never used any other way; <numpy> is
    every name numpy is bound to by the twin's imports (`np`, `numpy`, and the alias of `import numpy as X`), and the
    criterion may read those names (module-level or not). `rng.random(...)` on any other name (a Generator method) is fine;
    an alias assignment inside the criterion (Assign, AnnAssign, AugAssign or NamedExpr whose value, or an element of a
    tuple/list value, is a bare <numpy> name or `<numpy>.random`, e.g. `x = np`, `y = numpy`, `a, b = np, 1`) is an issue;
    passing numpy as a function argument default or in another container is not tracked;
  * exactly one criterion `Criterion("C", criterion)` without components (one Criterion(...) call, STUDY.criteria == [C]);
  * the criterion no longer raises NotImplementedError; STUDY name == world_id; faulty and fixed bodies differ;
  * comparisons of an input's mean/variance/distribution with a constant are LISTED for the auditor (not failures).
A twin is imported (STUDY constructed, so the module body runs) only if it has no issue so far; no criterion is ever
called and the gate is never run.
Package root check: --package-root is inserted first on sys.path and `truth_gate` is imported from it before any case is
looked at. If `truth_gate` was already imported before that, or the imported module's realpath is not under the realpath
of the package root (e.g. an editable install answered instead), the script stops with exit code 2 and a message, and no
case is checked. The imported file is printed on stderr and recorded as the top-level field "truth_gate_file" of the
report.
Report layout (--out JSON): {"truth_gate_file": "<path>", "<case folder>": {...}, ...}: the "truth_gate_file" key is a
string, every other key is a case folder name whose value is {"world_id", "issues": [...], "listed": {twin: [...]}, every
other ASSIGNMENT.json field, and, when both twins parsed, "diff_lines"}.

Usage:
    py mech_check_twins.py --cases-root DIR --skeletons DIR --package-root PKG_DIR --out REPORT.json
PKG_DIR is the sandbox pkg/ folder that holds truth_gate/ and kapi/.
Exit code 0 if every case passes, 1 otherwise, 2 on a usage error or a failed package root check.
"""
import argparse, ast, builtins, difflib, importlib.util, json, os, sys

BANNED = {"open", "eval", "exec", "__import__", "compile", "input", "breakpoint", "globals", "locals", "vars",
          "setattr", "delattr", "getattr", "exit", "quit", "print", "__builtins__"}
BANNED_ATTR = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
DIST_CALLS = {"mean", "var", "std", "ptp", "allclose", "isclose", "count_nonzero", "unique", "all", "any", "median",
              "nanmean", "nanstd", "nanvar", "array_equal", "sum", "max", "min", "abs"}


def split(src):
    """Return (prefix_lines, criterion_node, body_text, suffix_lines, docstring, tree) around def criterion."""
    tree = ast.parse(src)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "criterion"]
    if len(fns) != 1:
        raise ValueError("criterion missing or duplicated")
    fn = fns[0]
    lines = src.splitlines(keepends=True)
    start = fn.lineno - 1 - len(fn.decorator_list)
    end = fn.end_lineno
    return lines[:start], fn, "".join(lines[start:end]), lines[end:], ast.get_docstring(fn, clean=False), tree


def module_names(tree):
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        names.add(x.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            names.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                names.add((a.asname or a.name).split(".")[0])
    return names


def local_names(fn):
    loc = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    for x in ast.walk(fn):
        if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del)):
            loc.add(x.id)
        elif isinstance(x, (ast.FunctionDef, ast.Lambda)) and x is not fn:
            if isinstance(x, ast.FunctionDef):
                loc.add(x.name)
            for a in x.args.args + x.args.kwonlyargs:
                loc.add(a.arg)
            if x.args.vararg: loc.add(x.args.vararg.arg)
            if x.args.kwarg: loc.add(x.args.kwarg.arg)
        elif isinstance(x, ast.arg):
            loc.add(x.arg)
        elif isinstance(x, ast.ExceptHandler) and x.name:
            loc.add(x.name)
    return loc


def call_name(c):
    f = c.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def numpy_bindings(tree):
    """Names bound to numpy by the module's imports (`import numpy` -> numpy, `import numpy as X` -> X)."""
    names = set()
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


def is_np_random(x, npn):
    return isinstance(x, ast.Attribute) and x.attr == "random" and isinstance(x.value, ast.Name) and x.value.id in npn


def signature_issues(fn):
    a = fn.args
    out = []
    if [p.arg for p in a.args] != ["d"] or a.vararg or a.kwarg or a.kwonlyargs or getattr(a, "posonlyargs", []):
        out.append("signature is not (d)")
    if a.defaults or a.kw_defaults:
        out.append("signature has default values")
    if fn.decorator_list:
        out.append("criterion has decorators")
    if fn.returns is not None or any(p.annotation is not None for p in a.args):
        out.append("signature has annotations")
    return out


def check_body(fn, modnames, src_lines, tree):
    issues, listed = [], []
    loc = local_names(fn)
    bound = numpy_bindings(tree)
    npn = bound | {"np", "numpy"}   # names whose `.random` is checked
    npok = bound | {"np"}           # names the criterion may read without being a module-level/undefined name
    alias_nodes = alias_assignments(fn, npn)
    ok_random = set()  # <numpy>.random nodes used only as <numpy>.random.default_rng
    for x in ast.walk(fn):
        if isinstance(x, ast.Attribute) and x.attr == "default_rng" and is_np_random(x.value, npn):
            ok_random.add(id(x.value))
    for x in ast.walk(fn):
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            issues.append(f"import inside criterion (line {x.lineno})")
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
            if x.id in BANNED:
                issues.append(f"banned name {x.id} (line {x.lineno})")
            elif x.id not in loc and x.id not in npok and x.id in modnames:
                issues.append(f"reads module-level name {x.id} (line {x.lineno})")
            elif x.id not in loc and x.id not in npok and x.id not in modnames and not hasattr(builtins, x.id):
                issues.append(f"undefined name {x.id} (line {x.lineno})")
        if isinstance(x, ast.Attribute):
            if x.attr in BANNED_ATTR:
                issues.append(f"attribute .{x.attr} (line {x.lineno})")
            if x.attr.startswith("__"):
                issues.append(f"dunder attribute .{x.attr} (line {x.lineno})")
            if is_np_random(x, npn) and id(x) not in ok_random:
                issues.append(f"{x.value.id}.random used other than as {x.value.id}.random.default_rng (line {x.lineno})")
        if x in alias_nodes:
            issues.append(f"numpy alias assignment `{ast.unparse(x)}` (line {x.lineno})")
        if isinstance(x, ast.Call) and call_name(x) == "default_rng":
            ok = len(x.args) == 1 and isinstance(x.args[0], ast.Constant) and type(x.args[0].value) is int and not x.keywords
            if not ok:
                issues.append(f"default_rng without a single int literal seed (line {x.lineno})")
        if isinstance(x, ast.Compare):
            sides = [x.left] + list(x.comparators)
            has_const = any(isinstance(s, ast.Constant) or (isinstance(s, ast.UnaryOp) and isinstance(s.operand, ast.Constant)) for s in sides)
            calls = {call_name(c) for s in sides for c in ast.walk(s) if isinstance(c, ast.Call)}
            if has_const and calls & DIST_CALLS:
                listed.append(f"line {x.lineno}: {src_lines[x.lineno - 1].strip()}")
    return issues, listed


def criterion_calls(tree):
    return [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Criterion"]


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    return mod


def check_case(case_dir, skel_dir):
    """Return (report dict, printable header)."""
    r = {"world_id": None, "issues": [], "listed": {}}
    ap = os.path.join(case_dir, "ASSIGNMENT.json")
    if not os.path.exists(ap):
        r["issues"].append("ASSIGNMENT.json missing")
        return r
    try:
        asg = json.load(open(ap, encoding="utf-8"))
        wid = asg["world_id"]
    except Exception as e:
        r["issues"].append(f"ASSIGNMENT.json unreadable or without world_id: {type(e).__name__}: {e}")
        return r
    r.update({k: v for k, v in asg.items() if k != "issues"})
    r["world_id"] = wid
    sp_path = os.path.join(skel_dir, f"{wid}.py")
    if not os.path.exists(sp_path):
        r["issues"].append(f"skeleton {wid}.py missing")
        return r
    skel_src = open(sp_path, encoding="utf-8").read()
    try:
        sp, sfn, sbody, ss, sdoc, stree = split(skel_src)
    except Exception as e:
        r["issues"].append(f"skeleton: parse error {e}")
        return r
    modnames = module_names(stree)
    for n in ast.walk(stree):
        if isinstance(n, ast.ImportFrom) and n.module != "truth_gate":
            r["issues"].append(f"skeleton imports from {n.module}, not truth_gate")
        elif isinstance(n, ast.Import) and any(a.name != "numpy" for a in n.names):
            r["issues"].append("skeleton has a non-numpy import")
    if not os.path.exists(os.path.join(case_dir, "CASE.md")):
        r["issues"].append("CASE.md missing")
    bodies = {}
    for twin in ("faulty", "fixed"):
        p = os.path.join(case_dir, twin + ".py")
        if not os.path.exists(p):
            r["issues"].append(f"{twin}: file missing"); continue
        n_before = len(r["issues"])
        src = open(p, encoding="utf-8").read()
        try:
            pp, fn, body, sf, doc, tree = split(src)
        except Exception as e:
            r["issues"].append(f"{twin}: parse error {e}"); continue
        if pp != sp:
            r["issues"].append(f"{twin}: text before the criterion differs from the skeleton")
        if sf != ss:
            r["issues"].append(f"{twin}: text after the criterion differs from the skeleton")
        if doc != sdoc:
            r["issues"].append(f"{twin}: criterion docstring changed")
        r["issues"] += [f"{twin}: {i}" for i in signature_issues(fn)]
        if any(isinstance(n, ast.Raise) and isinstance(n.exc, ast.Name) and n.exc.id == "NotImplementedError" for n in fn.body):
            r["issues"].append(f"{twin}: still raises NotImplementedError")
        iss, lst = check_body(fn, modnames, src.splitlines(), tree)
        r["issues"] += [f"{twin}: {i}" for i in iss]
        if lst:
            r["listed"][twin] = lst
        cc = criterion_calls(tree)
        if len(cc) != 1 or cc[0].keywords or len(cc[0].args) != 2 or not (isinstance(cc[0].args[0], ast.Constant) and cc[0].args[0].value == "C"):
            r["issues"].append(f"{twin}: not exactly one Criterion(\"C\", criterion) without components")
        bodies[twin] = body
        if len(r["issues"]) > n_before:
            r["issues"].append(f"{twin}: module not loaded (static issues above)")
            continue
        try:
            mod = load(p, f"chk_{os.path.basename(case_dir)}_{twin}".replace("-", "_").replace(" ", "_"))
            st = mod.STUDY
            if st.name != wid or [c.id for c in st.criteria] != ["C"]:
                r["issues"].append(f"{twin}: STUDY name/criteria changed")
            elif st.criteria[0].components is not None or st.criteria[0].fn is not mod.criterion:
                r["issues"].append(f"{twin}: criterion C has components or is not the module's criterion function")
        except Exception as e:
            r["issues"].append(f"{twin}: load error {type(e).__name__}: {e}")
    if len(bodies) == 2:
        if bodies["faulty"] == bodies["fixed"]:
            r["issues"].append("faulty and fixed criterion bodies are identical")
        fl, xl = bodies["faulty"].splitlines(), bodies["fixed"].splitlines()
        r["diff_lines"] = sum(1 for d in difflib.ndiff(fl, xl) if d[:1] in "+-")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases-root", required=True)
    ap.add_argument("--skeletons", required=True)
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
    cases = sorted(d for d in os.listdir(a.cases_root) if os.path.isdir(os.path.join(a.cases_root, d)))
    report, n_ok = {"truth_gate_file": tg_file}, 0
    for c in cases:
        r = check_case(os.path.join(a.cases_root, c), a.skeletons)
        r["issues"] = list(dict.fromkeys(r["issues"]))
        report[c] = r
        n_ok += not r["issues"]
        print(f"{c:12} {r['world_id']} {'OK' if not r['issues'] else 'ISSUES'}"
              f" diff={r.get('diff_lines')} listed={sum(len(v) for v in r['listed'].values())}"
              + ("" if not r["issues"] else "\n      - " + "\n      - ".join(r["issues"])))
    print(f"\n{n_ok}/{len(cases)} cases pass the mechanical check")
    json.dump(report, open(a.out, "w", encoding="utf-8"), indent=2, default=str)
    return 0 if n_ok == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
