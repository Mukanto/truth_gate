"""Static form check of a body file (AST only; nothing is executed).

Used on the fixed bodies. Faulty bodies only get the ast.parse syntax check (see LOG.md).
Usage: py -I check_form.py <file> [<file> ...]
"""
import ast
import builtins
import sys


def check(path):
    errs = []
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    funcs = {}
    first_import_ok = False
    for node in tree.body:
        if isinstance(node, ast.Import):
            if (len(node.names) == 1 and node.names[0].name == "numpy" and node.names[0].asname == "np"
                    and not first_import_ok):
                first_import_ok = True
            else:
                errs.append("bad import at line %d" % node.lineno)
        elif isinstance(node, ast.FunctionDef):
            funcs[node.name] = node
        else:
            errs.append("module-level %s at line %d" % (type(node).__name__, node.lineno))
    if not first_import_ok:
        errs.append("missing 'import numpy as np'")
    if "criterion" not in funcs:
        errs.append("no criterion")
        return errs
    names_ok = set(funcs) | {"np"} | set(dir(builtins))
    for name, fn in funcs.items():
        if fn.decorator_list:
            errs.append("%s: decorator" % name)
        a = fn.args
        if a.vararg or a.kwarg or a.kwonlyargs or a.posonlyargs:
            errs.append("%s: unusual arguments" % name)
        for arg in a.args:
            if arg.annotation is not None:
                errs.append("%s: annotation" % name)
        if fn.returns is not None:
            errs.append("%s: return annotation" % name)
        if name == "criterion":
            if [x.arg for x in a.args] != ["d"] or a.defaults:
                errs.append("criterion signature")
            if ast.get_docstring(fn) is None:
                errs.append("criterion has no docstring")
        for dflt in a.defaults + [x for x in a.kw_defaults if x is not None]:
            ok = False
            if isinstance(dflt, ast.Constant):
                ok = isinstance(dflt.value, (int, float, str, bool, type(None)))
            elif isinstance(dflt, ast.Tuple):
                ok = all(isinstance(e, ast.Constant) for e in dflt.elts)
            if not ok:
                errs.append("%s: non-literal default" % name)
        params = {x.arg for x in a.args}
        local = set(params)
        for sub in ast.walk(fn):
            if isinstance(sub, (ast.Global, ast.Nonlocal)):
                errs.append("%s: global/nonlocal" % name)
            if isinstance(sub, ast.FunctionDef) and sub is not fn:
                errs.append("%s: nested def (not used here)" % name)
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
                local.add(sub.id)
            if isinstance(sub, ast.arg):
                local.add(sub.arg)
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                if sub.id not in local and sub.id not in names_ok:
                    errs.append("%s: free name %s at line %d" % (name, sub.id, sub.lineno))
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "np":
                if sub.attr == "random":
                    errs.append("%s: np.random used" % name)
    return errs


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        e = check(p)
        print(p, "OK" if not e else e)
        bad += bool(e)
    sys.exit(1 if bad else 0)
