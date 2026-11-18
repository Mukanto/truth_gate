import ast,glob
bad={'open','eval','exec','compile','__import__','getattr','setattr','globals','locals','vars','print','input'}
for f in sorted(glob.glob('cases/D-*/reference.py')):
    t=ast.parse(open(f).read())
    for n in t.body:
        ok=isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.Assign)) or (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant))
        if not ok: print(f,'module-level',type(n).__name__)
    for n in ast.walk(t):
        if isinstance(n,ast.Name) and n.id in bad: print(f,'name',n.id)
        if isinstance(n,ast.Attribute) and n.attr=='random' and isinstance(n.value,ast.Name) and n.value.id=='np': print(f,'np.random')
print('scan done')
