"""Validate the t-distribution helper that sits inside fixed.py (O2-A, O2-B) against scipy (scratch; fixed files only)."""
import ast, os, sys
import numpy as np
from scipy import stats
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def extract(case, name):
    src = open(os.path.join(ROOT, "cases", case, "fixed.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            ns = {"np": np}
            exec(compile(ast.Module([node], []), "<helper>", "exec"), ns)
            return ns[name]
    raise SystemExit("not found")

for case in ("O2-A", "O2-B"):
    f = extract(case, "p_two_sided")
    worst = 0.0
    for df in list(range(1, 60)) + [98, 99, 100, 150, 198]:
        for t in np.concatenate([np.linspace(0, 8, 81), [0.01, 1e-6, 12.0]]):
            ref = 2 * stats.t.sf(t, df)
            got = f(t, df)
            worst = max(worst, abs(got - ref))
    print(case, "max abs error of p over grid:", worst)

# decision agreement of the full fixed criterion with scipy on random samples (O2-A on liking, O2-B on score)
import importlib.util
sys.path.insert(0, os.path.join(ROOT, "pkg"))
for case, kc, kt in (("O2-A", "liking_control", "liking_treatment"), ("O2-B", "score_control", "score_treatment")):
    spec = importlib.util.spec_from_file_location("fx_" + case.replace("-", "_"), os.path.join(ROOT, "cases", case, "fixed.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    dis = 0; N = 2000
    for i in range(N):
        rng = np.random.default_rng(300 + i)
        d = (m.plus if i % 2 == 0 else m.minus)(rng)
        r = m.criterion(d)
        tt = stats.ttest_ind(d[kt], d[kc], equal_var=True)
        ref = bool(tt.statistic > 0 and tt.pvalue < 0.05)
        dis += (r != ref)
    print(case, "disagreements with scipy.ttest_ind:", dis, "of", N)
