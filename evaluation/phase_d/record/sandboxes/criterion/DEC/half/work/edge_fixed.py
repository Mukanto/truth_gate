"""Edge runs of the FIXED bodies only (guards)."""
import os, importlib.util
import numpy as np
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cases')
def load(case):
    p = os.path.join(ROOT, case, 'fixed_body.py')
    spec = importlib.util.spec_from_file_location('fx_' + case.replace('-', '_'), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
rng = np.random.default_rng(7)
print('D-047 none flagged', load('D-047').criterion({'screening': np.full(10, 30.), 'entry': np.full(10, 30.), 'week12': np.full(10, 20.)}))
print('D-069 empty cell', load('D-069').criterion({'baseline_sbp': rng.normal(150, 10, 30), 'followup_sbp': rng.normal(140, 10, 30), 'treated': np.ones(30, bool)}))
print('D-012 one fenced plot', load('D-012').criterion({'occupied': rng.random((10, 30)) < .5, 'exclosure': np.arange(10) == 0}))
print('D-012 zero variance', load('D-012').criterion({'occupied': np.ones((10, 30), bool), 'exclosure': np.arange(10) % 2 == 0}))
print('D-032 empty cell', load('D-032').criterion({'responder': rng.random(20) < .5, 'drug': np.ones(20, bool), 'carrier': rng.random(20) < .5}))
print('D-032 zero var', load('D-032').criterion({'responder': np.ones(40, bool), 'drug': np.arange(40) % 2 == 0, 'carrier': np.arange(40) % 4 < 2}))
print('D-046 const dose', load('D-046').criterion({'response': rng.normal(size=(10, 5)), 'dose': np.ones(10)}))
print('D-016 const exposure', load('D-016').criterion({'exposure': np.ones(14), 'outcome': rng.normal(size=(14, 4))}))
print('D-052 group of 1', load('D-052').criterion({'pre': np.zeros(5), 'post': rng.normal(size=5), 'young': np.array([1, 0, 0, 0, 0], bool)}))
print('D-030 empty bin', load('D-030').criterion({'pre': np.full((10, 6), 20.) + rng.normal(size=(10, 6)), 'post': rng.normal(20, 1, (10, 6))}))
print('D-028 nan', load('D-028').criterion({'activation': np.full((20, 50), np.nan), 'trait': rng.normal(size=20)}))
print('D-028 const voxel', load('D-028').criterion({'activation': np.ones((20, 50)), 'trait': rng.normal(size=20)}))
print('D-061 nothing kept', load('D-061').criterion({'response': rng.normal(size=(20, 10, 4)) * 0 + np.tile(rng.normal(size=(20, 10, 1)), (1, 1, 4)) * 0 + rng.normal(size=(20, 10, 4)) * 1e-0 - 5 * np.eye(1)[0, 0] * 0}))
