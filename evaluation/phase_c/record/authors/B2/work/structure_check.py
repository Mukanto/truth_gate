"""Static checks only (text/AST); nothing is executed."""
import ast, pathlib
ROOT = pathlib.Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\cases")
MARK = "    raise NotImplementedError\n"
for cdir in sorted(ROOT.glob("B2-*")):
    skel = (cdir / "skeleton.py").read_text(encoding="utf-8")
    pre, post = skel.split(MARK)
    out = []
    mods = {}
    for v in ("faulty", "fixed"):
        s = (cdir / (v + ".py")).read_text(encoding="utf-8")
        ok = s.startswith(pre) and s.endswith(post)
        body = s[len(pre):len(s) - len(post)]
        mods[v] = body
        tree = ast.parse(s)
        modnames = set()
        for node in tree.body:
            if isinstance(node, (ast.Assign,)):
                for t in node.targets:
                    if isinstance(t, ast.Name): modnames.add(t.id)
            elif isinstance(node, (ast.FunctionDef,)): modnames.add(node.name)
        crit = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "criterion"][0]
        local = {a.arg for a in crit.args.args}
        for n in ast.walk(crit):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store): local.add(n.id)
            if isinstance(n, ast.FunctionDef):
                local.add(n.name); local |= {a.arg for a in n.args.args}
            if isinstance(n, (ast.comprehension,)):
                for t in ast.walk(n.target):
                    if isinstance(t, ast.Name): local.add(t.id)
        used = {n.id for n in ast.walk(crit) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        skel_hit = sorted((used & modnames) - local - {"np", "criterion"})
        rnd = [l.strip() for l in body.splitlines() if "np.random" in l]
        out.append((v, ok, skel_hit, rnd))
    same_head = mods["faulty"].split("    def ")[0] if False else None
    print(cdir.name, out)
