"""Form check of the bodies by AST only (no import/exec of either body)."""
import ast, glob, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cases')
bad = 0
for p in sorted(glob.glob(os.path.join(ROOT, 'D-*', '*_body.py'))):
    t = ast.parse(open(p, encoding='utf-8').read())
    ok = True
    first = t.body[0]
    if not (isinstance(first, ast.Import) and first.names[0].name == 'numpy' and first.names[0].asname == 'np'):
        ok = False
    for n in t.body[1:]:
        if not isinstance(n, ast.FunctionDef) or n.decorator_list:
            ok = False
    crit = [n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == 'criterion']
    if len(crit) != 1 or [a.arg for a in crit[0].args.args] != ['d'] or crit[0].args.defaults or not ast.get_docstring(crit[0]):
        ok = False
    for n in ast.walk(t):
        if isinstance(n, (ast.Global, ast.Nonlocal)):
            ok = False
    # names read must be params/locals/functions/np/builtins : crude check on free names
    import builtins
    funcs = {n.name for n in t.body if isinstance(n, ast.FunctionDef)}
    for f in [n for n in t.body if isinstance(n, ast.FunctionDef)]:
        local = {a.arg for a in f.args.args}
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                local.add(n.id)
            if isinstance(n, ast.arg):
                local.add(n.arg)
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                if n.id not in local and n.id not in funcs and n.id != 'np' and not hasattr(builtins, n.id):
                    print('free name', p, f.name, n.id); ok = False
    print(('OK  ' if ok else 'BAD ') + os.path.relpath(p, ROOT))
    bad += (not ok)
print('bad', bad)
