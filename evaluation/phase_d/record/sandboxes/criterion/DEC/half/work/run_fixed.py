"""Runs ONLY the fixed bodies, on self-generated arrays. Checks helper accuracy vs scipy
(scipy is used only here, in scratch, never in a body)."""
import os, sys, time, importlib.util
import numpy as np
from scipy import stats
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cases')

def load(case):
    p = os.path.join(ROOT, case, 'fixed_body.py')
    spec = importlib.util.spec_from_file_location('fx_' + case.replace('-', '_'), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

# 1. helper accuracy
m = load('D-061')
mx = 0
for df in [1, 2, 4, 8, 9, 12, 19, 37.3, 54, 298, 998]:
    for t in [-6, -2, -0.5, 0.0, 0.3, 1.0, 1.65, 2.5, 5, 12]:
        a = m._t_sf(t, df); b = stats.t.sf(t, df)
        mx = max(mx, abs(a - b))
print('max abs err t_sf vs scipy', mx)
print('t_crit(0.001, 4)', m._t_crit(0.001, 4), stats.t.isf(0.001, 4))
print('t_crit(0.001, 9)', m._t_crit(0.001, 9), stats.t.isf(0.001, 9))
print('t_crit(0.05, 8)', m._t_crit(0.05, 8), stats.t.isf(0.05, 8))

rng = np.random.default_rng(12345)
def timeit(case, d, n=3):
    mod = load(case)
    t0 = time.perf_counter()
    for _ in range(n):
        out = mod.criterion(d)
    dt = (time.perf_counter() - t0) / n
    print(f'{case}: {out!r} ({type(out).__name__}) {dt*1000:.1f} ms/call; repeat equal={mod.criterion(d)==out}')
    return out

# D-061: a world with real A>D structure
V = 1500
mu = np.zeros((V, 4)); mu[:600, 0] = 1.5
resp = mu[:, None, :] + rng.normal(0, 1, (V, 10, 4))
timeit('D-061', {'response': resp})
timeit('D-061', {'response': rng.normal(0, 1, (V, 10, 4))})
# D-028
act = rng.normal(size=(20, 1000)); trait = rng.normal(size=20)
timeit('D-028', {'activation': act, 'trait': trait})
# D-033
b = rng.normal(size=(1000, 60)); inten = rng.normal(size=60)
timeit('D-033', {'betas': b, 'intensity': inten})
# D-047
L = rng.normal(50, 12, 600)
timeit('D-047', {'screening': L + rng.normal(0, 8, 600), 'entry': L + rng.normal(0, 8, 600), 'week12': L - 8 + rng.normal(0, 8, 600)})
# D-069
base = rng.normal(150, 15, 900); tr = rng.random(900) < 0.5
fol = base - 5 * tr + rng.normal(0, 8, 900)
timeit('D-069', {'baseline_sbp': base, 'followup_sbp': fol, 'treated': tr})
# D-032
n = 240
dr = rng.random(n) < 0.5; ca = rng.random(n) < 0.5
resp_ = rng.random(n) < (0.3 + 0.15 * dr)
timeit('D-032', {'responder': resp_, 'drug': dr, 'carrier': ca})
# D-012
occ = rng.random((10, 30)) < 0.4; ex = np.arange(10) % 2 == 0
timeit('D-012', {'occupied': occ, 'exclosure': ex})
# D-021
pr = rng.random((8, 12)) < 0.4; fe = np.arange(8) % 2 == 0
timeit('D-021', {'present': pr, 'fenced': fe})
# D-046
dose = np.linspace(0, 9, 10)
resp = 0.2 * dose[:, None] + rng.normal(0, 1, (10, 1)) + rng.normal(0, 1, (10, 100))
timeit('D-046', {'response': resp, 'dose': dose})
# D-016
exp_ = rng.normal(size=14)
out_ = 0.3 * exp_[:, None] + rng.normal(0, 1, (14, 1)) + rng.normal(0, 1, (14, 4))
timeit('D-016', {'exposure': exp_, 'outcome': out_})
# D-030
pre = rng.gamma(4, 2, (400, 1)) + rng.normal(0, 3, (400, 40))
post = pre.mean(axis=1, keepdims=True) + rng.normal(0, 3, (400, 40))
timeit('D-030', {'pre': pre, 'post': post})
# D-052
pre = rng.normal(50, 10, 40); yg = np.arange(40) < 20
post = pre + np.where(yg, 4, 2) + rng.normal(0, 5, 40)
timeit('D-052', {'pre': pre, 'post': post, 'young': yg})

# cross-check of the fixed statistics against scipy on the same arrays
m6 = load('D-012'); 
a = occ.mean(axis=1)[ex]; bb = occ.mean(axis=1)[~ex]
diff, p = m6._welch(a, bb)
r = stats.ttest_ind(a, bb, equal_var=False, alternative='greater')
print('welch p mine vs scipy', p, r.pvalue)
m7 = load('D-046')
p7 = m7._slope_p(dose, resp.mean(axis=1))
r7 = stats.linregress(dose, resp.mean(axis=1), alternative='greater')
print('slope p mine vs scipy', p7, r7.pvalue)
m8 = load('D-016')
p8 = m8._corr_p(exp_, out_.mean(axis=1))
rr = stats.pearsonr(exp_, out_.mean(axis=1), alternative='greater')
print('corr p mine vs scipy', p8, rr.pvalue)
