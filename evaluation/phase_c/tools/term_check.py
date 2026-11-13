"""Phase C term check (PREREG_PHASE_C section 2, "Banned terms as PB section 4, checked by script").

Reports every occurrence of the banned stems in the public fields of every brief: claim, sizes, and for every data key
its key, shape, dtype and meaning. Matching is case-insensitive and by stem, so every inflection is caught
("leak" finds "leakage", "leaky"; "coupl" finds "coupling", "coupled"). Spaces, hyphens or none between the parts of
"double dip", "non-independ", "pseudorepl" and "regression to the mean" are all accepted.

Usage:
    py term_check.py BRIEFS.json [--json REPORT.json]
BRIEFS.json: a list of {"id" (or "local_id"), "claim", "data_keys": [{"key", "shape", "dtype", "meaning"}], "sizes"}
(or an object with such a list under "briefs"). Exit code 0 if there is no hit, 1 if there is any hit, 2 on a usage error.
"""
import argparse, json, re, sys

# (stem as written in the pre-registration, regular expression that implements it)
STEMS = [
    ("circular", r"circular"),
    ("double dip", r"double[\s\-_]*dip"),
    ("double-dip", r"double[\s\-_]*dip"),
    ("leak", r"leak"),
    ("pseudorepl", r"pseudo[\s\-_]*repl"),
    ("coupl", r"coupl"),
    ("spurious", r"spurious"),
    ("non-independ", r"non[\s\-_]*independ"),
    ("nonindepend", r"non[\s\-_]*independ"),
    ("regression to the mean", r"regression[\s\-_]+to[\s\-_]+the[\s\-_]+mean"),
    ("selection bias", r"selection[\s\-_]+bias"),
    ("overfit", r"overfit"),
    ("inflat", r"inflat"),
    ("contaminat", r"contaminat"),
    ("optimis", r"optimis"),
]
# "double dip" and "double-dip" (and the two non-independ spellings) share one pattern: report each pattern once
_seen, PATTERNS = set(), []
for name, rx in STEMS:
    if rx in _seen:
        continue
    _seen.add(rx)
    PATTERNS.append((name, re.compile(rx, re.IGNORECASE)))


def fields_of(brief):
    """Yield (field label, text) for every public text field of a brief."""
    yield "claim", str(brief.get("claim", ""))
    yield "sizes", str(brief.get("sizes", ""))
    for i, k in enumerate(brief.get("data_keys", []) or []):
        for f in ("key", "shape", "dtype", "meaning"):
            if f in k:
                yield f"data_keys[{i}].{f}", str(k[f])


def scan_text(text):
    hits = []
    for name, rx in PATTERNS:
        for m in rx.finditer(text):
            lo, hi = max(0, m.start() - 30), min(len(text), m.end() + 30)
            hits.append({"stem": name, "match": m.group(0), "pos": m.start(), "context": text[lo:hi].replace("\n", " ")})
    return sorted(hits, key=lambda h: h["pos"])


def check(briefs):
    report = []
    for n, b in enumerate(briefs):
        bid = b.get("id", b.get("local_id", f"#{n}"))
        for label, text in fields_of(b):
            for h in scan_text(text):
                report.append({"id": bid, "field": label, **h})
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("briefs")
    ap.add_argument("--json", dest="json_out", default=None, help="write the full hit list as JSON")
    a = ap.parse_args(argv)
    try:
        data = json.load(open(a.briefs, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"cannot read {a.briefs}: {e}", file=sys.stderr)
        return 2
    briefs = data["briefs"] if isinstance(data, dict) and "briefs" in data else data
    if not isinstance(briefs, list):
        print("BRIEFS.json must be a list of briefs", file=sys.stderr)
        return 2
    rep = check(briefs)
    for h in rep:
        print(f"{h['id']}\t{h['field']}\t[{h['stem']}] '{h['match']}'\t...{h['context']}...")
    bad_ids = sorted({h["id"] for h in rep}, key=str)
    print(f"\n{len(rep)} hit(s) in {len(bad_ids)} of {len(briefs)} brief(s)" + (f": {', '.join(map(str, bad_ids))}" if bad_ids else ""))
    if a.json_out:
        json.dump({"n_briefs": len(briefs), "n_hits": len(rep), "ids_with_hits": bad_ids, "hits": rep},
                  open(a.json_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return 1 if rep else 0


if __name__ == "__main__":
    sys.exit(main())
