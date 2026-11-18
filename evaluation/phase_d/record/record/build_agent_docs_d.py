"""Phase D item 0(a): build the agent document set from tag v0.5.1 and remove evaluation content (designer).

PREREG_PHASE_D section 3 item 0, as PC section 4 item 0(a). Source: docs/GATE.md, docs/MANIFEST.md, docs/SPEC.md and
the tool parts of README.md at tag v0.5.1. README_TOOL.md keeps the same sections as Phase C's copy: the title block,
"Who it is for", "Getting started" with "Run the gate", "Quick start without Python code", "The command line", "In CI"
and "A study in Python", and "Limits". The removal rules are Phase C's (evaluation/phase_c/record/build_agent_docs.py),
applied to the v0.5.1 text, plus any rule added below. Every removed block is logged in SCAN_REMOVALS.md.
Run from this folder: py -I build_agent_docs_d.py <path to kapi-oss>
"""
import io
import os
import re
import subprocess
import sys

REPO = sys.argv[1]
TAG = "v0.5.1"
D = "agent_docs"
os.makedirs(D, exist_ok=False)


def show(path):
    return subprocess.run(["git", "-C", REPO, "show", f"{TAG}:{path}"], capture_output=True, check=True).stdout.decode("utf-8")


for name in ("GATE.md", "MANIFEST.md", "SPEC.md"):
    open(os.path.join(D, name), "w", encoding="utf-8", newline="\n").write(show("docs/" + name).replace("\r\n", "\n"))

# README_TOOL.md: section selection
readme = show("README.md").replace("\r\n", "\n").split("\n")
heads = [(i, l) for i, l in enumerate(readme) if l.startswith("## ") or l.startswith("### ")]


def block(title):
    """Lines of the section or subsection with this exact heading, up to the next heading of the same or higher level."""
    idx = [i for i, l in heads if l == title]
    assert len(idx) == 1, title
    i = idx[0]
    level = len(title) - len(title.lstrip("#"))
    for j, l in heads:
        if j > i and (len(l) - len(l.lstrip("#"))) <= level:
            return readme[i:j]
    return readme[i:]


first_h2 = min(i for i, l in heads if l.startswith("## "))
out = readme[:first_h2]
out += block("## Who it is for")
gs = [i for i, l in heads if l == "## Getting started"][0]
out += [readme[gs], ""]
for sub in ("### Run the gate", "### Quick start without Python code", "### The command line", "### In CI",
            "### A study in Python"):
    out += block(sub)
out += block("## Limits")
open(os.path.join(D, "README_TOOL.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out).rstrip("\n") + "\n")

# removals (Phase C's rules on the v0.5.1 text)
log = io.StringIO()
log.write("# Removals from the agent document set (PREREG_PHASE_D section 3 item 0, as PC section 4 item 0(a))\n\n"
          f"Source: docs/GATE.md, docs/MANIFEST.md, docs/SPEC.md and the tool parts of README.md at tag {TAG} "
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


RULES = {
    # Phase C's README rule ("<!-- Agent document set" line) is dropped: no such line exists in README.md at v0.5.1.
    "GATE.md": [("bullet", "* Tiny denominators:")],
    "SPEC.md": [
        ("until:> The released package", "> **This is an edited copy for publication.**"),
        ("line", "- **Freeze rule:**"), ("line", "- **Roles:**"),
        ("section", "## 11. D4 pre-freeze smoke test"), ("section", "## 12. Evaluation"),
        ("line", "- E1 is self-authored"), ("section", "## 14. Change log"),
        ("bullet", "- **Why v0.2:**"), ("section", "## Δ4 — Evaluation of v0.2"), ("section", "## Δ6 — Change log"),
        ("bullet", "- **Why v0.3:**"), ("line", "  - E5 author:"), ("section", "## Δ4 — Evaluation of v0.3"),
    ],
}
for fname, rules in RULES.items():
    apply(fname, rules)

# Phase D addition (designer, before the triage): the README's CI sentences report test results of the tool's own
# workflows (a result); they are removed, and the instruction that follows them is kept.
CI_SENTENCES = (
    "The Action runs on GitHub in this repository's own workflows\n"
    "([`.github/workflows/`](.github/workflows/)): from the same commit on a study that passes and on one that must fail, and\n"
    "as released (exactly as `init --ci` writes it; `@v0.5.0` on the first run). All three passed from their first run on 2026-11-17\n"
    "([CI](https://github.com/Mukanto/truth_gate/actions/runs/43980474228),\n"
    "[must fail](https://github.com/Mukanto/truth_gate/actions/runs/43980475889),\n"
    "[released](https://github.com/Mukanto/truth_gate/actions/runs/43980474292)). ")
p = os.path.join(D, "README_TOOL.md")
text = open(p, encoding="utf-8").read()
assert text.count(CI_SENTENCES) == 1
open(p, "w", encoding="utf-8", newline="\n").write(text.replace(CI_SENTENCES, ""))
log.write("## README_TOOL.md (sentences; designer, Phase D addition)\n\n```\n" + CI_SENTENCES + "\n```\n\n")
open("SCAN_REMOVALS.md", "w", encoding="utf-8", newline="\n").write(log.getvalue())
print("ok")
