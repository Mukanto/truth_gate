"""Auditor helper (B-6, Phase C). Reads only ASSIGNMENT.json briefs; never imports or calls a criterion.
1. Banned-term scan (PB section 4 list, case-insensitive, with hyphen/space variants).
2. Negation / 'claim false' scan: prints every brief sentence containing words that could describe the null.
3. Size scan: numbers per axis and values per array against the Phase C caps (1000 per axis, 500000 per array).
"""
import json, re, sys, pathlib

root = pathlib.Path(sys.argv[1])
banned = ["circular", "double dip", "double-dip", "doubledip", "leak", "pseudorepl", "pseudo-repl", "coupl",
          "spurious", "non-independ", "nonindepend", "non independ", "regression to the mean", "selection bias",
          "overfit", "over-fit", "inflat", "contaminat", "optimis", "optimiz"]
neg_words = ["false", "null", "no effect", "not ", "none", "zero", "absent", "no difference", "no relation",
             "would", "otherwise", "if the", "independent", "shared", "same ", "duplicate", "selected", "random",
             "paired", "nested", "litter", "within"]
for case in sorted(root.glob("B6-*")):
    a = json.loads((case / "ASSIGNMENT.json").read_text(encoding="utf-8"))
    b = a["brief"]
    text = json.dumps(b, ensure_ascii=False)
    low = text.lower()
    hits = [t for t in banned if t in low]
    print(f"== {case.name} ({b['id']}) banned hits: {hits}")
    keys_brief = sorted(b.keys())
    print("   brief keys:", keys_brief)
    parts = [("claim", b["claim"])] + [(f"key {k['key']}", k["meaning"]) for k in b["data_keys"]] + [("sizes", b["sizes"])]
    for name, s in parts:
        sl = s.lower()
        found = [w.strip() for w in neg_words if w in sl]
        if found:
            print(f"   [{name}] words {found}: {s}")
    # sizes
    nums = dict(re.findall(r"(\w+) = (\d+)", b["sizes"]))
    print("   axis sizes:", nums, "max axis", max(int(v) for v in nums.values()))
    for k in b["data_keys"]:
        axes = [x.strip() for x in k["shape"].strip("()").split(",") if x.strip()]
        vals = 1
        for ax in axes:
            vals *= int(nums[ax])
        print(f"   {k['key']} shape {k['shape']} -> {vals} values; cap ok: {vals <= 500000 and all(int(nums[ax]) <= 1000 for ax in axes)}")
