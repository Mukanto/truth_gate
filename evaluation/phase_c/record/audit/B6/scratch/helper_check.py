"""Auditor helper (B-6, Phase C): checks the shared numpy-only Student-t p-value helper in isolation.
The helper text is extracted from one case file as text (lines from 'def lgam' to the end of 'p2t') and exec'd
on its own; no criterion and no study is imported or called, and no world data is generated.
Known two-sided 5% critical values of Student's t (standard tables) should give p = 0.05.
"""
import sys, re, pathlib
import numpy as np

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
start = src.index("    def lgam(x):")
end = src.index("return float(1.0 - np.exp(lb) * betacf(b, a, 1.0 - x) / b)") + len("return float(1.0 - np.exp(lb) * betacf(b, a, 1.0 - x) / b)")
block = src[start:end]
# dedent by 4
block = "\n".join(line[4:] if line.startswith("    ") else line for line in block.splitlines())
ns = {"np": np}
exec(block, ns)
p2t = ns["p2t"]
known = [(1, 12.706205), (2, 4.302653), (8, 2.306004), (10, 2.228139), (14, 2.144787), (18, 2.100922),
         (19, 2.093024), (28, 2.048407), (38, 2.024394), (78, 1.990847), (158, 1.975092), (1198, 1.961941)]
for df, tc in known:
    print(f"df={df:5d} t={tc:.6f}  p2t={p2t(tc, float(df)):.6f}  p2t(-t)={p2t(-tc, float(df)):.6f}")
print("t=0 ->", p2t(0.0, 10.0), " t=1e6 ->", p2t(1e6, 10.0))
# non-integer (Welch) df: t critical for df=17.5 lies between df 17 (2.109816) and 18 (2.100922)
print("df=17.5 at t=2.105 ->", p2t(2.105, 17.5))
