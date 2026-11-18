import ast, os, re
B = r"E:\Claude Projects\Kapi\phase_d_work\structure\B2B\cases"
for cid in sorted(os.listdir(B)):
    src = open(B + "\\" + cid + r"\reference.py", encoding="utf-8").read()
    t = ast.parse(src)
    bad = []
    for i, n in enumerate(t.body):
        if i == 0 and isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant): continue
        if isinstance(n, (ast.Assign, ast.FunctionDef)): continue
        if isinstance(n, ast.ImportFrom) and n.module == "truth_gate": continue
        if isinstance(n, ast.Import) and n.names[0].name == "numpy": continue
        bad.append(type(n).__name__)
    print(cid, "module-level issues:", bad, "| np.random:", "np.random" in src, "| lines", src.count("\n"))
