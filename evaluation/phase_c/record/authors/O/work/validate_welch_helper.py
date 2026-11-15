"""Validate the Welch/incomplete-beta helpers inside O3-A fixed.py against scipy (scratch; fixed file only)."""
import ast, os, sys
import numpy as np
from scipy import stats
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pkg"))
src = open(os.path.join(ROOT, "cases", "O3-A", "fixed.py"), encoding="utf-8").read()
tree = ast.parse(src)
ns = {"np": np}
crit = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "criterion"][0]
helpers = [n for n in crit.body if isinstance(n, ast.FunctionDef)]
exec(compile(ast.Module(helpers, []), "<helpers>", "exec"), ns)
welch = ns["welch"]
worst_p = 0.0; worst_rel = 0.0
for i in range(3000):
    rng = np.random.default_rng(i)
    n1, n2 = rng.integers(2, 60, 2)
    a = rng.normal(rng.normal(0, 1.5), rng.uniform(0.1, 3), n1)
    b = rng.normal(0.0, rng.uniform(0.1, 3), n2)
    diff, p = welch(a, b)
    ref = stats.ttest_ind(a, b, equal_var=False)
    worst_p = max(worst_p, abs(p - ref.pvalue))
    if ref.pvalue > 1e-12:
        worst_rel = max(worst_rel, abs(p - ref.pvalue) / ref.pvalue)
print("max abs diff in Welch p vs scipy:", worst_p, " max relative:", worst_rel)
# lgamma
xs = np.linspace(0.05, 100, 400)
print("max abs diff lgamma:", max(abs(ns["log_gamma"](x) - float(__import__('scipy.special', fromlist=['x']).gammaln(x))) for x in xs))
