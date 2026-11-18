import sys, json, glob, os, time, importlib.util, re
sys.path.insert(0, os.path.abspath('pkg'))
import numpy as np
root = os.path.abspath('.')
only = sys.argv[1:]
for d in sorted(glob.glob('cases/D-*')):
    cid = os.path.basename(d)
    if only and cid not in only: continue
    b = json.load(open(d + '/brief.json', encoding='utf-8')); n = json.load(open(d + '/NOTE.json', encoding='utf-8'))
    p = d + '/reference.py'
    s = open(p, encoding='utf-8').read()
    doc = '"""%s: %s"""' % (cid, b['claim'])
    s = re.sub(r'^""".*?"""', lambda m: doc, s, count=1, flags=re.S)
    open(p, 'w', encoding='utf-8').write(s)
    spec = importlib.util.spec_from_file_location('ref_' + cid.replace('-', '_'), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    ns = {'np': np}; exec(n['structure_statistic']['code'], ns); stat = ns['stat']
    sv = n['structure_statistic']; av = n['approved_value'] if 'approved_value' in n else sv['note_value']; nv = sv['null_value']
    res = {}; tmax = 0
    for w in ('plus', 'minus'):
        vals = []
        for i in range(200):
            rng = np.random.default_rng(1000 + i)
            t0 = time.time(); dd = getattr(m, w)(rng); tmax = max(tmax, time.time() - t0)
            if i == 0:
                assert set(dd) == {k['key'] for k in b['data_keys']}, (cid, set(dd))
                for k in b['data_keys']:
                    a = dd[k['key']]; assert tuple(a.shape) == tuple(k['dims']), (cid, k['key'], a.shape)
                    assert a.dtype == (np.bool_ if k['dtype'] == 'bool' else np.float64), (cid, k['key'], a.dtype)
                    if a.dtype != np.bool_ and cid not in ('D-014', 'D-041'): assert np.isfinite(a).all()
                    if a.dtype != np.bool_ and cid in ('D-014', 'D-041'): assert not np.isinf(a).any()
            vals.append(stat(dd))
        res[w] = (np.mean(vals), np.std(vals, ddof=1))
    (mp, sp), (mm, sm) = res['plus'], res['minus']
    tol = 0.2 * abs(av - nv)
    ok1 = abs(mp - av) <= tol and abs(mm - av) <= tol
    se = 3 * np.sqrt(sp**2 / 200 + sm**2 / 200); ok2 = abs(mp - mm) <= se
    # control
    rng = np.random.default_rng(5); dd = m.plus(rng)
    c = m.STUDY.controls[0].transform(dd, np.random.default_rng(6))
    changed = any(not np.array_equal(c[k], dd[k]) for k in dd)
    print(cid, 'plus %.4f(%.4f) minus %.4f(%.4f) target %.4f tol %.4f ok1=%s ok2=%s ctrl_changed=%s tmax=%.0fms' % (mp, sp, mm, sm, av, tol, ok1, ok2, changed, tmax * 1000), flush=True)
