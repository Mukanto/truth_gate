"""Text-only check: faulty.py and fixed.py equal skeleton.py outside the criterion body, and the docstring is kept.
Executes nothing from the case files."""
import os, re

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")
for case in ["O1a", "O1b", "O2a", "O2b", "O3a", "O3b"]:
    sk = open(os.path.join(root, case, "skeleton.py"), encoding="utf-8", newline="").read()
    pre, post = sk.split("    raise NotImplementedError")
    for kind in ["faulty", "fixed"]:
        t = open(os.path.join(root, case, kind + ".py"), encoding="utf-8", newline="").read()
        ok = t.startswith(pre) and t.endswith(post) and "NotImplementedError" not in t
        print(case, kind, "outside-body identical:", ok)
    # imports unchanged
    for kind in ["faulty", "fixed"]:
        t = open(os.path.join(root, case, kind + ".py"), encoding="utf-8", newline="").read()
        imps = re.findall(r"^\s*(?:import|from)\s.*$", t, flags=re.M)
        print("   imports", kind, imps)
