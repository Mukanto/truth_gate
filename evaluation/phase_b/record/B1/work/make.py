import sys, os, ast
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bodies import CASES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "    raise NotImplementedError"
only = sys.argv[1:]
for cid, c in CASES.items():
    if only and cid not in only:
        continue
    cdir = os.path.join(ROOT, "cases", cid)
    if os.path.exists(os.path.join(cdir, "CASE.md")):
        print(cid, "has CASE.md, skipped")
        continue
    skel = open(os.path.join(cdir, "skeleton.py"), encoding="utf-8").read()
    assert skel.count(MARK) == 1
    helpers = "".join(c["helpers"]).strip("\n")
    for which in ("faulty", "fixed"):
        body = c["body"].strip("\n").replace("@@V@@", c[which])
        text = (helpers + "\n\n" + body) if helpers else body
        out = skel.replace(MARK, text)
        ast.parse(out)
        with open(os.path.join(cdir, which + ".py"), "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
    print(cid, "written")
