import sys, json, time, importlib.util, math
sys.path.insert(0, 'pkg')
import numpy as np
ids = sys.argv[1:] or sorted(__import__('os').listdir('cases'))
for cid in ids:
    note = json.load(open(f'cases/{cid}/NOTE.json')); brief = json.load(open(f'cases/{cid}/brief.json'))
    ns = {'np': np}; exec(note['structure_statistic']['code'], ns); stat = ns['stat']
    spec = importlib.util.spec_from_file_location('ref_'+cid.replace('-','_'), f'cases/{cid}/reference.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    assert m.__doc__ == cid + ': ' + brief['claim'], 'docstring'
    appr = note['approved_value']; null = note['structure_statistic']['null_value']
    res = {}; tmax = 0
    for wname, fn in (('plus', m.plus), ('minus', m.minus)):
        vals = []
        for i in range(200):
            rng = np.random.default_rng(np.random.SeedSequence([4242, 1 if wname=='plus' else 2, i]))
            t0 = time.perf_counter(); d = fn(rng); tmax = max(tmax, time.perf_counter()-t0)
            if i == 0:
                assert set(d) == {k['key'] for k in brief['data_keys']}, 'keys'
                for k in brief['data_keys']:
                    a = d[k['key']]
                    assert a.shape == tuple(k['dims']), (k['key'], a.shape)
                    assert a.dtype == (np.bool_ if k['dtype']=='bool' else np.float64), (k['key'], a.dtype)
            for a in d.values(): assert np.all(np.isfinite(a.astype(float)))
            vals.append(stat(d))
        res[wname] = (float(np.mean(vals)), float(np.std(vals, ddof=1)))
    (mp, sp), (mm, sm) = res['plus'], res['minus']
    tol = 0.2*abs(appr-null)
    ok1 = abs(mp-appr) <= tol and abs(mm-appr) <= tol
    se3 = 3*math.sqrt(sp**2/200+sm**2/200)
    ok2 = abs(mp-mm) <= se3
    # control timing / change
    rng = np.random.default_rng(5); d = m.plus(rng)
    c = m.STUDY.controls[0]
    t0=time.perf_counter(); d2 = c.transform(d, np.random.default_rng(6)); tc=time.perf_counter()-t0
    changed = any(not np.array_equal(d[k], d2[k]) for k in d); same_keys = set(d)==set(d2) and all(d[k].shape==d2[k].shape and d[k].dtype==d2[k].dtype for k in d)
    print(f"{cid} approved={appr} plus={mp:.4f}(sd {sp:.4f}) minus={mm:.4f}(sd {sm:.4f}) tol={tol:.4f} meanok={ok1} eqok={ok2} diff={mp-mm:+.4f} 3se={se3:.4f} tmax={tmax*1000:.0f}ms ctrl={tc*1000:.0f}ms changed={changed} keys_ok={same_keys}")
