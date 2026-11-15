"""Scratch text/AST check (never executes a case file): twins equal the skeleton outside the criterion body; the
criterion body reads no module-level name except np; no import or np.random in the body; no rng needed."""
import ast, pathlib, builtins
ROOT = pathlib.Path(__file__).resolve().parent.parent
MARK = "    raise NotImplementedError"
for case in sorted(p.name for p in (ROOT / "cases").iterdir() if p.is_dir()):
    sk = (ROOT / "cases" / case / "skeleton.py").read_text(encoding="utf-8")
    pre, post = sk.split(MARK)
    for name in ("faulty.py", "fixed.py"):
        t = (ROOT / "cases" / case / name).read_text(encoding="utf-8")
        assert t.startswith(pre) and t.endswith(post), (case, name, "outside-body mismatch")
        body = t[len(pre):len(t) - len(post)]
        tree = ast.parse(t)
        fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "criterion"][0]
        assigned, loads = set(), set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Name):
                (assigned if isinstance(n.ctx, (ast.Store, ast.Del)) else loads).add(n.id)
            elif isinstance(n, ast.FunctionDef) and n is not fn:
                assigned.add(n.name); assigned.update(a.arg for a in n.args.args)
            elif isinstance(n, ast.arg):
                assigned.add(n.arg)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                raise AssertionError((case, name, "import in body"))
        # lambda args / comprehension vars are Store/arg, covered above
        free = loads - assigned - set(dir(builtins))
        assert free <= {"np"}, (case, name, free)
        assert "np.random" not in body and "default_rng" not in body
        assert "scipy" not in body and "math" not in body
    # twins differ only inside the body
    a = (ROOT / "cases" / case / "faulty.py").read_text(encoding="utf-8")
    b = (ROOT / "cases" / case / "fixed.py").read_text(encoding="utf-8")
    assert a != b
    print(case, "ok; faulty/fixed body lines", a.count("\n") - pre.count("\n") - post.count("\n"), b.count("\n") - pre.count("\n") - post.count("\n"))
