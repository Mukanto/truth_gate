"""PREREG_PHASE_D section 6 (descriptive) and AWARENESS_RULE_D.md: sandboxes of the awareness readers (designer).

Valid world-author batches only (WORLD_RUN.md orders 3, 4, 5, 7). Each WORLD_LOG.md is split at its "## D-" headings into
one entry per case. The log's general notes (the text between its title line and the first case heading) are given with
each of its entries; the title line, which holds the sandbox label, is dropped. No sentence names the checklist or
CHECKLIST_LOG.md in any W-1 WORLD_LOG.md (checked here; the script stops if one does), so nothing is removed.

  first   both arms, 40 entries, one shuffled set, labels E01..E40, no arm or batch label -> awareness/r1, awareness/r2
  second  W-1 only (WORLD_LOG.md entry + the CHECKLIST_LOG.md section of the same case, with that log's general notes),
          20 entries, labels F01..F20 -> awareness/r3, awareness/r4 (built with `second`, after the first reading is frozen)

Each reader sandbox holds READER_RULE.md (the "## Rule" section of AWARENESS_RULE_D.md, verbatim) and ENTRIES.md.
Private map: AWARENESS_MAP_<first|second>.json in the work folder. Inputs read-only. Usage: build_awareness.py first|second"""
import hashlib, json, os, re, secrets, stat, sys
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
PD = r"E:\Claude Projects\kapi-oss\evaluation\phase_d"
VALID = {"eb6876": "W0", "c13bd2": "W1", "5f14e6": "W0", "d5f53a": "W1"}
mode = sys.argv[1]
assert mode in ("first", "second")


def split(path):
    lines = open(path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    starts = [k for k, l in enumerate(lines) if l.startswith("## D-")]
    general = "\n".join(lines[1:starts[0]]).strip()
    out = {}
    for n, k in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        cid = re.match(r"## (D-\d{3})", lines[k]).group(1)
        out[cid] = "\n".join(["#" + lines[k]] + lines[k + 1:end]).strip()
    return general, out


rule = open(os.path.join(PD, "AWARENESS_RULE_D.md"), encoding="utf-8").read().replace("\r\n", "\n")
rule = rule[rule.index("## Rule"):].strip()
entries = []
for label, arm in VALID.items():
    wl = os.path.join(WORK, "world", label, "WORLD_LOG.md")
    if arm == "W1":
        assert not re.search(r"checklist|CHECKLIST_LOG", open(wl, encoding="utf-8").read(), re.I), f"{label}: names the checklist"
    g, ents = split(wl)
    if mode == "second" and arm != "W1":
        continue
    if mode == "second":
        cg, cents = split(os.path.join(WORK, "world", label, "CHECKLIST_LOG.md"))
    for cid, text in ents.items():
        body = f"General notes of the log this entry comes from:\n\n{g}\n\nEntry:\n\n{text}"
        if mode == "second":
            body += f"\n\nSecond log of the same author, general notes:\n\n{cg}\n\nSecond log, entry for {cid}:\n\n{cents[cid]}"
        entries.append({"id": cid, "arm": arm, "label_src": label, "body": body})
order = list(range(len(entries)))
for k in range(len(order) - 1, 0, -1):  # Fisher-Yates with a CSPRNG
    j = secrets.randbelow(k + 1)
    order[k], order[j] = order[j], order[k]
prefix = "E" if mode == "first" else "F"
amap, doc = {}, [f"# Entries ({len(entries)})\n"]
for n, k in enumerate(order, start=1):
    lab = f"{prefix}{n:02d}"
    e = entries[k]
    amap[lab] = {"id": e["id"], "arm": e["arm"], "sandbox": e["label_src"]}
    doc.append(f"\n---\n\n# {lab}\n\n{e['body']}\n")
readers = ("r1", "r2") if mode == "first" else ("r3", "r4")
manifest = {}
for r in readers:
    d = os.path.join(WORK, "awareness", r)
    assert not os.path.exists(d), f"{d} exists"
    os.makedirs(d)
    open(os.path.join(d, "READER_RULE.md"), "w", encoding="utf-8", newline="\n").write(
        "# Classification rule\n\nApply this rule to every entry of ENTRIES.md, to the text of the entry only.\n\n" + rule + "\n")
    open(os.path.join(d, "ENTRIES.md"), "w", encoding="utf-8", newline="\n").write("".join(doc))
    for f in ("READER_RULE.md", "ENTRIES.md"):
        q = os.path.join(d, f)
        os.chmod(q, stat.S_IREAD)
        manifest[os.path.relpath(q, WORK)] = hashlib.sha256(open(q, "rb").read()).hexdigest()
json.dump(amap, open(os.path.join(WORK, f"AWARENESS_MAP_{mode}.json"), "w"), indent=1, sort_keys=True)
mp = os.path.join(WORK, "MANIFEST_awareness.json")
old = json.load(open(mp)) if os.path.exists(mp) else {}
old.update(manifest)
json.dump(old, open(mp, "w"), indent=1, sort_keys=True)
print(mode, len(entries), "entries ->", ", ".join(readers))
