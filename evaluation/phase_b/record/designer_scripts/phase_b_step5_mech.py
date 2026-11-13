"""Phase B step 5.1 (designer): mechanical check of the twins (PREREG §5.1, AUTHOR_PHASE2 rules).

For every case: faulty.py and fixed.py equal the frozen skeleton outside the criterion body (docstring kept); no new
imports; no file/network/process access; the criterion reads no module-level name except `np`; randomness only as
np.random.default_rng(<int literal>); default Budget/Targets (the skeleton part is unchanged, so this follows);
comparisons of an input's mean/variance/distribution with a constant are LISTED for the auditor (not failures).
The twins are imported (Study constructed) but no criterion is ever called and the gate is never run.
"""
import ast, importlib.util, json, os, sys, builtins

ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b"
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
idmap = json.load(open(os.path.join(ROOT, "ID_MAP_AND_CLASSES.json"), encoding="utf-8"))
BANNED = {"open", "eval", "exec", "__import__", "compile", "input", "breakpoint", "globals", "locals", "vars",
          "setattr", "delattr", "getattr", "exit", "quit", "print"}
BANNED_ATTR = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
DIST_CALLS = {"mean", "var", "std", "ptp", "allclose", "isclose", "count_nonzero", "unique", "all", "any", "median",
              "nanmean", "nanstd", "nanvar", "array_equal", "sum", "max", "min", "abs"}


def split(src):
    """Return (prefix_lines, criterion_node, body_text, suffix_lines, docstring) around def criterion."""
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


def check_body(fn, modnames, src_lines):
    issues, listed = [], []
    loc = local_names(fn)
    for x in ast.walk(fn):
        if isinstance(x, (ast.Import, ast.ImportFrom)):
            issues.append(f"import inside criterion (line {x.lineno})")
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
            if x.id in BANNED:
                issues.append(f"banned name {x.id} (line {x.lineno})")
            elif x.id not in loc and x.id != "np" and x.id in modnames:
                issues.append(f"reads module-level name {x.id} (line {x.lineno})")
            elif x.id not in loc and x.id != "np" and x.id not in modnames and not hasattr(builtins, x.id):
                issues.append(f"undefined name {x.id} (line {x.lineno})")
        if isinstance(x, ast.Attribute):
            if x.attr in BANNED_ATTR:
                issues.append(f"attribute .{x.attr} (line {x.lineno})")
            if x.attr.startswith("__"):
                issues.append(f"dunder attribute .{x.attr} (line {x.lineno})")
            if isinstance(x.value, ast.Attribute) and isinstance(x.value.value, ast.Name) and x.value.value.id == "np" \
                    and x.value.attr == "random" and x.attr != "default_rng":
                issues.append(f"np.random.{x.attr} (line {x.lineno})")
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


def load(path, tag):
    spec = importlib.util.spec_from_file_location(tag, path)
    mod = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(mod)
    return mod


report, n_ok, n_cases = {}, 0, 0
for a in sorted(idmap, key=lambda z: (z["author_folder"], z["local_id"])):
    n_cases += 1
    case = os.path.join(ROOT, a["author_folder"], "cases", a["local_id"])
    skel_src = open(os.path.join(ROOT, "world", "skeletons", a["world_id"] + ".py"), encoding="utf-8").read()
    sp, sfn, sbody, ss, sdoc, stree = split(skel_src)
    modnames = module_names(stree)
    r = {"world_id": a["world_id"], "class": a["class"], "subtype": a["subtype"], "issues": [], "listed": {}}
    if not os.path.exists(os.path.join(case, "CASE.md")):
        r["issues"].append("CASE.md missing")
    bodies = {}
    for twin in ("faulty", "fixed"):
        p = os.path.join(case, twin + ".py")
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
        if fn.args.args[0].arg != "d" or len(fn.args.args) != 1:
            r["issues"].append(f"{twin}: signature changed")
        if any(isinstance(n, ast.Raise) and isinstance(n.exc, ast.Name) and n.exc.id == "NotImplementedError" for n in fn.body):
            r["issues"].append(f"{twin}: still raises NotImplementedError")
        iss, lst = check_body(fn, modnames, src.splitlines())
        r["issues"] += [f"{twin}: {i}" for i in iss]
        if lst:
            r["listed"][twin] = lst
        bodies[twin] = body
        try:
            mod = load(p, f"chk_{a['local_id']}_{twin}".replace("-", "_"))
            st = mod.STUDY
            if st.name != a["world_id"] or [c.id for c in st.criteria] != ["C"]:
                r["issues"].append(f"{twin}: STUDY name/criteria changed")
        except Exception as e:
            r["issues"].append(f"{twin}: load error {type(e).__name__}: {e}")
    if len(bodies) == 2 and bodies["faulty"] == bodies["fixed"]:
        r["issues"].append("faulty and fixed criterion bodies are identical")
    if len(bodies) == 2:
        fl, xl = bodies["faulty"].splitlines(), bodies["fixed"].splitlines()
        import difflib
        r["diff_lines"] = sum(1 for d in difflib.ndiff(fl, xl) if d[:1] in "+-")
    report[a["local_id"]] = r
    n_ok += not r["issues"]
    print(f"{a['author_folder']:3} {a['local_id']:6} {a['world_id']} {'OK' if not r['issues'] else 'ISSUES'}"
          f" diff={r.get('diff_lines')} listed={sum(len(v) for v in r['listed'].values())}"
          + ("" if not r["issues"] else "\n      - " + "\n      - ".join(r["issues"])))
print(f"\n{n_ok}/{n_cases} cases pass the mechanical check")
json.dump(report, open(os.path.join(ROOT, "STEP5_MECH_CHECK.json"), "w", encoding="utf-8"), indent=2)
