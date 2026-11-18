"""Build ITEMS.json for tools/shuffle_d.py from the five authors' outputs (designer). dims are added per data key from
the brief's sizes (PREREG_PHASE_D section 2.1). designer_id = local_id."""
import json, re
B1 = {"extreme-group-change", "split-by-baseline-compare-change", "select-then-test-same-data"}
RES = {"B2A": lambda i: "-R" in i, "B2B": lambda i: int(i[-2:]) > 10, "B3A": lambda i: int(i[-2:]) > 10,
       "B3B": lambda i: int(i[-2:]) > 10, "DEC": lambda i: "-R" in i}
items = []
for a in ["B2A", "B2B", "B3A", "B3B", "DEC"]:
    B = json.load(open(f"authors/{a}/BRIEFS.json", encoding="utf-8"))
    P = {p["local_id"]: p for p in json.load(open(f"authors/{a}/PRIVATE.json", encoding="utf-8"))}
    for b in B:
        p = P[b["local_id"]]
        keys = []
        for k in b["data_keys"]:
            axes = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(k["shape"]))
            keys.append({**k, "dims": [int(b["sizes"][ax]) for ax in axes]})
        cls = "B-2" if a.startswith("B2") else "B-3" if a.startswith("B3") else ("B-1" if p["mechanism_tag"] in B1 else "B-6")
        items.append({"designer_id": b["local_id"], "class": cls, "half": a[2] if a != "DEC" else None,
                      "source": p["source"], "subtype_or_tag": p["mechanism_tag"], "reserve": RES[a](b["local_id"]),
                      "claim": b["claim"], "data_keys": keys, "sizes": b["sizes"]})
json.dump(items, open("designer/ITEMS.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
from collections import Counter
print(len(items), Counter((x["class"], x["reserve"]) for x in items))
