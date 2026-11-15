"""Phase C designer adapter (REVISIONS-post-freeze P-3): copy a batch file for the frozen check script, replacing every
non-string `sizes` by its JSON text. String `sizes` and every other field are copied unchanged.

Usage: py -I sizes_as_text.py BATCH.json OUT.json
"""
import json, sys

src, out = sys.argv[1], sys.argv[2]
briefs = json.load(open(src, encoding="utf-8"))
n = 0
for b in briefs:
    if not isinstance(b.get("sizes"), str):
        b["sizes"] = json.dumps(b["sizes"], ensure_ascii=False)
        n += 1
json.dump(briefs, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"{len(briefs)} briefs, {n} sizes rendered as JSON text -> {out}")
