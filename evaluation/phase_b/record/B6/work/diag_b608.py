# Diagnostic of the minus world of B6-08 (world function only, fixed-criterion quantities; faulty never touched)
import sys, importlib.util, os
import numpy as np
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("f8", os.path.join(ROOT, "cases", "B6-08", "fixed.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rng = np.random.default_rng(77)
mr, sr = [], []
for _ in range(400):
    s = m.minus(rng)
    rs = np.array([np.corrcoef(s["activity"][i], s["reaction_time"][i])[0, 1] for i in range(12)])
    mr.append(rs.mean()); sr.append(rs.std(ddof=1))
print("minus: mean over samples of mean within-participant r = %.3f, mean sd of r_i = %.3f" % (np.mean(mr), np.mean(sr)))
# same quantity with the trial-position drift removed from both measures (diagnostic only)
mr2 = []
rng = np.random.default_rng(77)
tt = np.arange(25) - 12.0
for _ in range(400):
    s = m.minus(rng)
    ra = s["reaction_time"] - 2.5 * tt[None, :]; aa = s["activity"] - 0.04 * tt[None, :]
    rs = np.array([np.corrcoef(aa[i], ra[i])[0, 1] for i in range(12)]); mr2.append(rs.mean())
print("minus with the known drift terms subtracted: mean r = %.3f" % np.mean(mr2))
