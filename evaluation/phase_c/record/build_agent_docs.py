"""Phase C item 0(a): remove evaluation content from the agent document set; log every removal (designer)."""
import io, os, re
D = "agent_docs"
log = io.StringIO()
log.write("# Removals from the agent document set (PREREG_PHASE_C section 4 item 0(a))\n\n"
          "Source: docs/GATE.md, docs/MANIFEST.md, docs/SPEC.md and the tool parts of README.md at tag v0.5.0 "
          "(README_TOOL.md keeps the sections: title, Who it is for, Getting started, Run the gate, Quick start without "
          "Python code, The command line, In CI, A study in Python, Limits). Each block below was removed by the designer "
          "before the two-reader triage, because it states an evaluation, its results, its cases or its process.\n\n")

def section_end(lines, i):
    for j in range(i + 1, len(lines)):
        if lines[j].startswith("## ") or lines[j].startswith("# ") or lines[j].strip() == "---":
            return j
    return len(lines)

def bullet_end(lines, i):
    j = i + 1
    while j < len(lines) and lines[j].startswith("  ") and not lines[j].startswith("- "):
        j += 1
    return j

def apply(fname, rules):
    p = os.path.join(D, fname)
    lines = open(p, encoding="utf-8").read().split("\n")
    drop = set()
    for kind, pat in rules:
        hits = [i for i, l in enumerate(lines) if l.startswith(pat)]
        assert hits, (fname, pat)
        for i in hits:
            if kind == "section":
                rng = range(i, section_end(lines, i))
            elif kind == "bullet":
                rng = range(i, bullet_end(lines, i))
            elif kind == "line":
                rng = range(i, i + 1)
            elif kind.startswith("until:"):
                end = next(j for j in range(i, len(lines)) if lines[j].startswith(kind[6:]))
                rng = range(i, end + 1)
            log.write(f"## {fname}, lines {rng.start + 1}-{rng.stop} ({kind} `{pat[:60]}`)\n\n```\n")
            log.write("\n".join(lines[k] for k in rng) + "\n```\n\n")
            drop.update(rng)
    out = [l for k, l in enumerate(lines) if k not in drop]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
    open(p, "w", encoding="utf-8", newline="\n").write(text)

apply("README_TOOL.md", [("line", "<!-- Agent document set")])
apply("GATE.md", [("bullet", "* Tiny denominators:")])
apply("SPEC.md", [
    ("until:> The released package", "> **This is an edited copy for publication.**"),
    ("line", "- **Freeze rule:**"), ("line", "- **Roles:**"),
    ("section", "## 11. D4 pre-freeze smoke test"), ("section", "## 12. Evaluation"),
    ("line", "- E1 is self-authored"), ("section", "## 14. Change log"),
    ("bullet", "- **Why v0.2:**"), ("section", "## Δ4 — Evaluation of v0.2"), ("section", "## Δ6 — Change log"),
    ("bullet", "- **Why v0.3:**"), ("line", "  - E5 author:"), ("section", "## Δ4 — Evaluation of v0.3"),
])
open("SCAN_REMOVALS.md", "w", encoding="utf-8", newline="\n").write(log.getvalue())
print("ok")
