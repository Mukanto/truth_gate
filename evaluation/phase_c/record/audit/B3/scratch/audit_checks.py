"""Auditor helper (B-3, Phase C). Reads only the class folder; imports no case file; calls no criterion.
1. Banned-term scan of every brief (PB section 4 list, inflections via stems).
2. Twins vs skeleton outside the criterion body (text comparison only).
3. Import lines and file/network/process tokens in the twins.
4. Accuracy of the Student-t tail routine copied from B3-01/B3-12 on known critical values (helper computation)."""
import json, re, os, sys
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "class", "cases")
BANNED = [r"circular", r"double[\s\-_]*dip", r"leak", r"pseudo[\s\-_]*repl", r"coupl", r"spurious",
          r"non[\s\-_]*independ", r"regression[\s\-_]+to[\s\-_]+the[\s\-_]+mean", r"selection[\s\-_]+bias",
          r"over[\s\-_]*fit", r"inflat", r"contaminat", r"optimis", r"optimiz"]

def brief_text(b):
    parts = [b["claim"], b["sizes"]]
    for k in b["data_keys"]:
        parts += [k["key"], k["shape"], k["dtype"], k["meaning"]]
    return " | ".join(parts)

cases = sorted(os.listdir(ROOT))
print("== 1. banned terms ==")
for c in cases:
    a = json.load(open(os.path.join(ROOT, c, "ASSIGNMENT.json"), encoding="utf-8"))
    txt = brief_text(a["brief"])
    hits = [p for p in BANNED if re.search(p, txt, re.I)]
    extra = [w for w in ["false", "null", "no relation", "not hold", "fails"] if re.search(r"\b" + w + r"\b", txt, re.I)]
    print(c, "banned hits:", hits or "none", "| negation-like words:", extra or "none")

print("== 2. twins vs skeleton outside body ==")
for c in cases:
    sk = open(os.path.join(ROOT, c, "skeleton.py"), encoding="utf-8").read().split("\n")
    i = [k for k, l in enumerate(sk) if l.strip() == "raise NotImplementedError"]
    assert len(i) == 1, c
    i = i[0]
    pre, post = sk[:i], sk[i + 1:]
    for v in ["faulty.py", "fixed.py"]:
        tw = open(os.path.join(ROOT, c, v), encoding="utf-8").read().split("\n")
        ok_pre = tw[:len(pre)] == pre
        ok_post = tw[len(tw) - len(post):] == post
        body = tw[len(pre):len(tw) - len(post)]
        print(c, v, "prefix_equal", ok_pre, "suffix_equal", ok_post, "body_lines", len(body))

print("== 3. imports and access tokens ==")
TOK = [r"\bopen\(", r"\bos\.", r"\bsys\.", r"subprocess", r"socket", r"urllib", r"requests", r"__import__",
       r"\beval\(", r"\bexec\(", r"\brandom\b", r"default_rng", r"np\.random", r"pathlib", r"\bglobals\(", r"STUDY"]
for c in cases:
    for v in ["faulty.py", "fixed.py"]:
        src = open(os.path.join(ROOT, c, v), encoding="utf-8").read()
        imps = [l.strip() for l in src.split("\n") if re.match(r"\s*(import|from)\s", l)]
        sk = open(os.path.join(ROOT, c, "skeleton.py"), encoding="utf-8").read().split("\n")
        i = [k for k, l in enumerate(sk) if l.strip() == "raise NotImplementedError"][0]
        tw = src.split("\n")
        body = "\n".join(tw[i:len(tw) - (len(sk) - i - 1)])
        toks = [t for t in TOK if re.search(t, body)]
        print(c, v, "imports:", imps, "| body tokens:", toks or "none")

print("== 4. t tail routine (copied text) ==")
def t_sf(t, df):
    top = np.pi / 2.0
    def tail(a):
        th = np.linspace(a, top, 4001)
        f = np.cos(th) ** (df - 1.0)
        return float(np.sum(f[:-1] + f[1:]) * (top - a) / 8000.0)
    p = tail(float(np.arctan(abs(t) / np.sqrt(df)))) / (2.0 * tail(0.0))
    return p if t >= 0 else 1.0 - p
# one-sided 5% critical values from standard tables
known = [(1, 6.3138), (2, 2.9200), (5, 2.0150), (10, 1.8125), (30, 1.6973), (45, 1.6794), (46, 1.6787),
         (60, 1.6706), (117, 1.6580), (120, 1.6577)]
for df, tc in known:
    print("df", df, "t", tc, "p(T>t) =", round(t_sf(tc, df), 5), "| p(T>-t) =", round(t_sf(-tc, df), 5))
try:
    from scipy import stats
    err = 0.0
    for df in [1, 2, 3, 5, 10, 45, 46, 116, 117]:
        for t in np.linspace(-4, 8, 49):
            err = max(err, abs(t_sf(t, df) - stats.t.sf(t, df)))
    print("max abs error vs scipy:", err)
except Exception as e:
    print("scipy not available:", type(e).__name__)
