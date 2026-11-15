"""Auditor helper: print the criterion body of faulty.py and the faulty->fixed diff for one case.
Reads text only; never imports or executes the study files."""
import sys, difflib, pathlib

case = sys.argv[1]
base = pathlib.Path(__file__).resolve().parent.parent / "class" / "cases" / case
sk = (base / "skeleton.py").read_text(encoding="utf-8").splitlines()
fa = (base / "faulty.py").read_text(encoding="utf-8").splitlines()
fi = (base / "fixed.py").read_text(encoding="utf-8").splitlines()

# locate the stub line in the skeleton
idx = [i for i, l in enumerate(sk) if l.strip() == "raise NotImplementedError"]
assert len(idx) == 1, idx
i = idx[0]
pre, post = sk[:i], sk[i + 1:]
for name, f in (("faulty", fa), ("fixed", fi)):
    ok = f[:len(pre)] == pre and f[len(f) - len(post):] == post
    print(f"{name}: skeleton prefix/suffix identical = {ok}; body lines = {len(f) - len(pre) - len(post)}")

body = fa[len(pre):len(fa) - len(post)]
print("==== faulty body ====")
for k, l in enumerate(body):
    print(f"{len(pre) + k + 1:4d}| {l}")
print("==== diff faulty -> fixed ====")
for l in difflib.unified_diff(fa, fi, "faulty.py", "fixed.py", n=0, lineterm=""):
    print(l)
