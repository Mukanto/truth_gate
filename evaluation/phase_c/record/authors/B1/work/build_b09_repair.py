"""Scratch (repair round): rewrites ONLY cases/B1-09/fixed.py. Fixed rule: sessions averaged (as in the faulty twin);
voxels chosen on participants 0..n//2-1, correlation estimated on the remaining participants. faulty.py is not touched."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from helpers import SF

cdir = Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B1\cases\B1-09")
MARK = b"    raise NotImplementedError\n"
sk = (cdir / "skeleton.py").read_bytes()
assert sk.count(MARK) == 1
body = SF + '''    s1 = np.asarray(d["act_session1"], dtype=float)
    s2 = np.asarray(d["act_session2"], dtype=float)
    y = np.asarray(d["trait"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (s1, s2, y)):
        return None
    n = y.size
    if n < 3:
        return None
    x = (s1 + s2) / 2.0
    sel = np.arange(n // 2)
    est = np.arange(n // 2, n)
    if sel.size < 3 or est.size < 3:
        return None

    def _corr(rows):
        # correlation of every voxel (columns of x) with the trait over the given participants; None for a zero variance
        yc = y[rows] - y[rows].mean()
        xc = x[rows] - x[rows].mean(axis=0)
        syy = (yc ** 2).sum()
        sxx = (xc ** 2).sum(axis=0)
        if not (syy > 0.0 and np.all(sxx > 0.0)):
            return None
        return (yc @ xc) / np.sqrt(syy * sxx)

    r_sel = _corr(sel)
    if r_sel is None:
        return None
    df = sel.size - 2.0
    chosen = _sf(r_sel * np.sqrt(df) / np.sqrt(1.0 - r_sel ** 2), df) < 0.005
    if not chosen.any():
        return None
    r_est = _corr(est)
    if r_est is None:
        return None
    return bool(r_est[chosen].mean() >= 0.5)
'''
(cdir / "fixed.py").write_bytes(sk.replace(MARK, body.encode("utf-8")))
print("fixed.py rewritten")
