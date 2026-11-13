"""Exploration on FIXED copies only: vary one numeric constant, count True in plus/minus (200 samples each)."""
import importlib.util, os, re, sys
import numpy as np
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
HERE = os.path.dirname(os.path.abspath(__file__))
case, pattern, values = sys.argv[1], sys.argv[2], sys.argv[3:]
src = open(os.path.join(HERE, "..", "cases", case, "fixed.py"), encoding="utf-8").read()
for v in values:
    new = src.replace(pattern, pattern.split("=")[0] + "= " + v, 1)
    assert new != src or pattern.endswith(v)
    p = os.path.join(HERE, "explore", "tmp_%s.py" % case.replace("-", "_"))
    open(p, "w", encoding="utf-8").write(new)
    spec = importlib.util.spec_from_file_location("tmp_" + case.replace("-", "_") + v.replace(".", "_"), p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    out = []
    for name in ("plus", "minus"):
        rng = np.random.default_rng(77)
        r = [m.criterion(getattr(m, name)(rng)) for _ in range(200)]
        out.append("%s True %.3f None %.3f" % (name, np.mean([x is True for x in r]), np.mean([x is None for x in r])))
    print(case, pattern, "->", v, " | ", " | ".join(out))
