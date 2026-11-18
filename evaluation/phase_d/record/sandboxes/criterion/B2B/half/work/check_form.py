"""Static form check of a body file (own approximation of the form rules in CRITERION_AUTHOR_D.md section 1).
Run on FIXED bodies only (and on text shared by both files); never on a faulty body."""
import ast
import builtins
import sys


def check(path):
    problems = []
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    funcs = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    for node in tree.body:
        if isinstance(node, ast.Import):
            if not (len(node.names) == 1 and node.names[0].name == "numpy" and node.names[0].asname == "np"):
                problems.append("bad import at line %d" % node.lineno)
        elif isinstance(node, ast.FunctionDef):
            if node.decorator_list:
                problems.append("decorator on %s" % node.name)
        else:
            problems.append("module-level statement at line %d: %s" % (node.lineno, type(node).__name__))
    if "criterion" not in funcs:
        problems.append("no criterion")
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        a = node.args
        if node.name == "criterion":
            if [x.arg for x in a.args] != ["d"] or a.defaults or a.vararg or a.kwarg or a.kwonlyargs:
                problems.append("criterion signature")
            if a.args[0].annotation is not None or node.returns is not None:
                problems.append("criterion annotation")
            doc = ast.get_docstring(node)
            if not doc:
                problems.append("criterion has no docstring")
        for dflt in a.defaults + [x for x in a.kw_defaults if x is not None]:
            try:
                ast.literal_eval(dflt)
            except Exception:
                problems.append("non-literal default in %s" % node.name)
        params = {x.arg for x in a.args + a.kwonlyargs}
        stored = set()
        loaded = set()
        for sub in ast.walk(node):
            if isinstance(sub, (ast.Global, ast.Nonlocal)):
                problems.append("global/nonlocal in %s" % node.name)
            if isinstance(sub, ast.Name):
                (stored if isinstance(sub.ctx, (ast.Store, ast.Del)) else loaded).add(sub.id)
            if isinstance(sub, ast.FunctionDef) and sub is not node:
                problems.append("nested def in %s" % node.name)
        allowed = params | stored | set(funcs) | {"np"} | set(dir(builtins))
        for nm in sorted(loaded - allowed):
            problems.append("free name %r in %s" % (nm, node.name))
        # np.random.<function> forbidden; only default_rng allowed
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Attribute):
                if (isinstance(sub.value.value, ast.Name) and sub.value.value.id == "np"
                        and sub.value.attr == "random" and sub.attr != "default_rng"):
                    problems.append("np.random.%s in %s" % (sub.attr, node.name))
    return problems


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        pr = check(p)
        print(p, "OK" if not pr else pr)
        bad += bool(pr)
    sys.exit(1 if bad else 0)
