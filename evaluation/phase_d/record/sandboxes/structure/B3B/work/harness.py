import sys, os, json, time, glob, importlib.util
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, 'pkg'))
import numpy as np
only = sys.argv[1:]
for cdir in sorted(glob.glob(os.path.join(root, 'cases', 'D-*'))):
    cid = os.path.basename(cdir)
    if only and cid not in only: continue
    brief = json.load(open(os.path.join(cdir, 'brief.json'), encoding='utf-8'))
    note = json.load(open(os.path.join(cdir, 'NOTE.json'), encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('ref_' + cid.replace('-', '_'), os.path.join(cdir, 'reference.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    ns = {'np': np}; exec(note['structure_statistic']['code'], ns); stat = ns['stat']
    av = note['approved_value']; nv = note['structure_statistic']['null_value']
    res = {}
    tmax = 0
    for w, fn in (('plus', m.plus), ('minus', m.minus)):
        vals = []
        for i in range(200):
            rng = np.random.default_rng(7000 + i)
            t0 = time.time(); d = fn(rng); tmax = max(tmax, time.time() - t0)
            if i == 0:
                assert set(d) == {k['key'] for k in brief['data_keys']}, (cid, set(d))
                for k in brief['data_keys']:
                    a = d[k['key']]
                    assert a.shape == tuple(k['dims']), (cid, k['key'], a.shape)
                    assert a.dtype == (np.bool_ if k['dtype'] == 'bool' else np.float64), (cid, k['key'], a.dtype)
                    assert np.all(np.isfinite(a.astype(float)))
            vals.append(stat(d))
        res[w] = np.array(vals)
    mp, mm = res['plus'].mean(), res['minus'].mean()
    sp, sm = res['plus'].std(ddof=1), res['minus'].std(ddof=1)
    tol = 0.2 * abs(av - nv)
    se = np.sqrt(sp**2/200 + sm**2/200)
    ok1 = abs(mp-av) <= tol and abs(mm-av) <= tol
    ok2 = abs(mp-mm) <= 3*se
    # controls
    cok = True
    for c in m.STUDY.controls:
        rng = np.random.default_rng(5); d = m.plus(rng)
        t0 = time.time(); o = c.transform(d, np.random.default_rng(6)); tmax = max(tmax, time.time()-t0)
        assert set(o) == set(d)
        for k in d:
            assert o[k].shape == d[k].shape and o[k].dtype == d[k].dtype, (cid, k, o[k].dtype)
        if all(np.array_equal(o[k], d[k]) for k in d): cok = False
    print(f"{cid} approved={av} null={nv} plus mean={mp:.4f} sd={sp:.4f} | minus mean={mm:.4f} sd={sm:.4f} | tol={tol:.4f} dev_p={mp-av:+.4f} dev_m={mm-av:+.4f} ok_val={ok1} diff={mp-mm:+.4f} 3se={3*se:.4f} ok_eq={ok2} ctrl_changed={cok} tmax_ms={tmax*1000:.0f}")
