"""Form check and runs of the FIXED bodies only, on self-generated arrays (shapes and dtypes from the briefs).
Never opens or imports a faulty body."""
import ast
import builtins
import json
import os
import sys
import time
import importlib.util

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HALF = os.path.dirname(HERE)
BRIEFS = {b['local_id']: b for b in json.load(open(os.path.join(HALF, 'BRIEFS.json'), encoding='utf-8'))}
IDS = json.load(open(os.path.join(HALF, 'CASE_IDS.json'), encoding='utf-8'))
BUILTINS = set(dir(builtins))


def form_check(path):
    src = open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    errs = []
    funcs = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            if not (len(node.names) == 1 and node.names[0].name == 'numpy' and node.names[0].asname == 'np'):
                errs.append('bad import')
        elif isinstance(node, ast.FunctionDef):
            funcs.append(node.name)
        else:
            errs.append('module-level %s' % type(node).__name__)
    if 'criterion' not in funcs:
        errs.append('no criterion')
    for node in ast.walk(tree):
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            errs.append('global/nonlocal')
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list:
                errs.append('decorator on ' + node.name)
            if node.name == 'criterion':
                a = node.args
                if [x.arg for x in a.args] != ['d'] or a.defaults or a.kwonlyargs or a.vararg or a.kwarg:
                    errs.append('criterion signature')
                if a.args[0].annotation is not None or node.returns is not None:
                    errs.append('annotation')
                if ast.get_docstring(node) is None:
                    errs.append('no docstring')
            for dflt in node.args.defaults:
                if not isinstance(dflt, ast.Constant):
                    errs.append('non-literal default')
            if node.name != 'criterion':
                pass
    # name resolution per top-level function
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            params = {a.arg for a in node.args.args}
            stores = set()
            loads = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Name):
                    (stores if isinstance(sub.ctx, ast.Store) else loads).add(sub.id)
            free = loads - params - stores - set(funcs) - {'np'} - BUILTINS
            if free:
                errs.append('free names in %s: %s' % (node.name, sorted(free)))
    # no random module use except default_rng
    if 'np.random' in src:
        errs.append('np.random used')
    return errs


def load(path):
    spec = importlib.util.spec_from_file_location('body_mod', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_arrays(lid, seed=0):
    rng = np.random.default_rng(seed)
    b = BRIEFS[lid]
    sizes = b['sizes']
    out = {}
    for k in b['data_keys']:
        dims = [sizes[s.strip()] for s in k['shape'].strip('()').split(',') if s.strip()]
        if k['dtype'] == 'bool':
            out[k['key']] = rng.random(dims) < 0.5
        else:
            out[k['key']] = rng.normal(10.0, 2.0, dims)
    return out


if __name__ == '__main__':
    for lid in sorted(BRIEFS):
        cid = IDS[lid]
        path = os.path.join(HALF, 'cases', cid, 'fixed_body.py')
        errs = form_check(path)
        mod = load(path)
        d = make_arrays(lid)
        t0 = time.perf_counter()
        r1 = mod.criterion(d)
        dt = time.perf_counter() - t0
        r2 = mod.criterion({k: v.copy() for k, v in d.items()})
        print(lid, cid, 'form:', errs or 'ok', '| result', r1, type(r1).__name__, '| repeat equal', r1 == r2,
              '| %.4f s' % dt)
