import json, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for cid in sorted(os.listdir(os.path.join(root, "cases"))):
    bp = os.path.join(root, "work", "body", cid + ".py")
    if not os.path.exists(bp):
        continue
    brief = json.load(open(os.path.join(root, "cases", cid, "brief.json"), encoding="utf-8"))
    body = open(bp, encoding="utf-8").read()
    doc = '"""%s: %s"""\n' % (brief["id"], brief["claim"])
    open(os.path.join(root, "cases", cid, "reference.py"), "w", encoding="utf-8", newline="\n").write(doc + body)
    print("built", cid)
