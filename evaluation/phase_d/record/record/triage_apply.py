"""Phase D item 0(a): apply the two-reader triage (designer READER1.json, fresh agent READER2.json) to agent_docs/.
A sentence is removed if either reader says remove (including 'other_sentences'); the kept hits are listed in
agent_docs/SCAN_REVIEW.json, which scan_docs_d.py reads with --allow."""
import json, os
R1 = json.load(open("READER1.json", encoding="utf-8"))
R2 = json.load(open("READER2.json", encoding="utf-8"))
hits = json.load(open("scan_initial.json", encoding="utf-8"))["hits"]
removals = {}  # (file, sentence) -> who
for who, r in (("designer", R1), ("reader 2", R2)):
    for d in r["decisions"]:
        if d["decision"] == "remove":
            removals.setdefault((d["file"], d["sentence"]), []).append(f"{who} (hit {d['hit']})")
    for o in r.get("other_sentences", []):
        removals.setdefault((o["file"], o["sentence"]), []).append(f"{who} (other sentence, {o['file']}:{o['line']})")
applied = set()
log = ["", "## Two-reader triage (designer READER1.json, fresh agent READER2.json): sentences removed", ""]
for (f, sent), who in removals.items():
    p = os.path.join("agent_docs", f)
    text = open(p, encoding="utf-8").read()
    s = sent.strip()
    done = [x for (ff, x) in removals if ff == f and x.strip() != s and s in x and (ff, x) in applied]
    if text.count(s) == 0 and done:
        log.append(f"* `{f}` ({' and '.join(who)}): {s} (inside a sentence already removed)")
        continue
    assert text.count(s) == 1, (f, s[:60], text.count(s))
    # remove the sentence; drop a whole bullet line if the sentence is the entire line
    lines = text.split("\n")
    out = []
    for l in lines:
        if l.strip() == s:
            continue
        out.append(l.replace(" " + s, "").replace(s + " ", "").replace(s, ""))
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    log.append(f"* `{f}` ({' and '.join(who)}): {s}")
    applied.add((f, sent))
open("SCAN_REMOVALS.md", "a", encoding="utf-8", newline="\n").write("\n".join(log) + "\n")
removed_hits = {d["hit"] for r in (R1, R2) for d in r["decisions"] if d["decision"] == "remove"}
listed = [{"file": h["file"], "text": h["text"], "tokens": h["tokens"],
           "reason": "tool vocabulary: kept by both readers (READER1.json, READER2.json)"}
          for i, h in enumerate(hits) if i not in removed_hits]
json.dump({"note": "Scan hits kept as tool vocabulary after the two-reader triage (PREREG_PHASE_D section 3 item 0, as "
                   "PC section 4 item 0(a)); removed sentences are listed in SCAN_REMOVALS.md.", "listed": listed},
          open(os.path.join("agent_docs", "SCAN_REVIEW.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(removals), "sentences removed;", len(listed), "hits listed")

# Lines that keep a scanned word after a sentence was removed from them: the remaining sentences were kept by both
# readers (each reader removed only the sentence it quoted), so the remaining line is listed with that reason.
import subprocess, sys
TOOL = sys.argv[1] if len(sys.argv) > 1 else None
if TOOL:
    subprocess.run([sys.executable, "-I", "-B", TOOL, "agent_docs", "--allow", os.path.join("agent_docs", "SCAN_REVIEW.json"),
                    "--json", "scan_after_removal.json"], capture_output=True)
    rest = json.load(open("scan_after_removal.json", encoding="utf-8"))
    rest_hits = rest["hits"] if isinstance(rest, dict) else rest
    listed_texts = {(x["file"], x["text"]) for x in listed}
    extra = [h for h in rest_hits if (h["file"], h["text"]) not in listed_texts]
    for h in extra:
        listed.append({"file": h["file"], "text": h["text"], "tokens": h["tokens"],
                       "reason": "remaining sentences of a line from which one sentence was removed; kept by both readers"})
    json.dump({"note": "Scan hits kept as tool vocabulary after the two-reader triage (PREREG_PHASE_D section 3 item 0, as "
                       "PC section 4 item 0(a)); removed sentences are listed in SCAN_REMOVALS.md.", "listed": listed},
              open(os.path.join("agent_docs", "SCAN_REVIEW.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(extra), "remaining line(s) listed")
