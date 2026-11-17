import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np

def load(case, twin):
    path = os.path.join(HERE, "cases", case, twin + ".py")
    name = f"{case.replace('-','_')}_{twin}"
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def noise_like(d, rng):
    out = {}
    for k, v in d.items():
        v = np.asarray(v)
        if v.dtype == np.bool_:
            out[k] = rng.random(v.shape) < 0.5
        elif np.issubdtype(v.dtype, np.number):
            out[k] = rng.standard_normal(v.shape)
        else:
            out[k] = v
    return out
