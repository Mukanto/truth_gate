import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = {}
for line in open(os.path.join(ROOT, "work", "precheck_repair.txt"), encoding="utf-8"):
    m = re.match(r"(B1-\d\d) (\{.*\})", line.strip())
    if m:
        res[m.group(1)] = json.loads(m.group(2))

OLD = {  # rates before the repair (round 1)
    "B1-04": "plus 0.845, minus 0.015 (None 39/200), control 0.00 (None 53), noise 0.03 (None 2/100)",
    "B1-05": "plus 0.98, minus 0.06 (None 100/200), control 0.11 (None 111), noise 0.02 (None 30/100)",
}
NEWDEV = {
    "B1-04": ("Audit repair (PREREG 5.3, item (a)): the first version selected voxels with r > 0 and two-sided p < 0.05 (my choice among the note's options). "
              "VUL09 Fig. 4 caption documents the selection as 'a positive correlation with p < .01', and the private note says r > 0 and p < 0.01. "
              "Both twins now use r > 0 and two-sided p < 0.01 (critical value `_tq(0.005, df)`); neither the source nor the note states the sidedness, so I kept my original two-sided reading and changed only the level. "
              "Nothing else changed. An empty selection still returns None (allowed guard); with the stricter level this is now much more frequent in minus (see table). "
              "The earlier deviation (single direction in the note, two directions here) stands. The exact threshold of the Fig. 4 simulation was read from the source text by the coordinator/auditor, not by me."),
    "B1-05": ("Audit repair (PREREG 5.3, item (a)): the first version used p < 0.05 two-sided with r > 0 instead of the note's p < 0.01, for a reason about the noise probe (an empty selection in most noise samples). "
              "That is not a reason item (a) accepts: VUL09 Fig. 4 caption documents 'a positive correlation with p < .01' and the note says r > 0 and p < 0.01. "
              "Both twins now use r > 0 and two-sided p < 0.01 (critical value `_tq(0.005, n - 2)`); neither source nor note states the sidedness, so I kept my original two-sided reading and changed only the level. "
              "Nothing else changed. An empty selection returns None (allowed guard), which is now the usual outcome in minus and in the control (see table). "
              "The skeleton's stable subject-by-voxel component still carries session-0 selection into session 1; reported, not changed."),
}

def rows(r):
    def row(name, x):
        return f"| {name} | {x['n']} | {x['holds']} | {x['rate']:.3f} | {x['none']} |"
    out = [row("plus", r["plus"]), row("minus", r["minus"])]
    out += [row(k, r[k]) for k in r if k.startswith("control")]
    out += [row("probe: i.i.d. N(0,1) noise", r["noise"]), row("probe: zeros", r["zeros"])]
    return "\n".join(out)

for cid in ("B1-04", "B1-05"):
    p = os.path.join(ROOT, "cases", cid, "CASE.md")
    s = open(p, encoding="utf-8").read()
    r = res[cid]; tm = r["timing"]
    assert "two-sided p < 0.05" in s
    head, rest = s.split("5. **Pre-checks", 1)
    head = head.replace("two-sided p < 0.05 are kept", "two-sided p < 0.01 are kept")
    assert "p < 0.01" in head, cid
    new5 = f"""5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; generator seeded 12345; `work/precheck.py`; outputs `work/precheck_round1.txt` before the repair and `work/precheck_repair.txt` after it). Revisions of the fixed criterion: 1 (the audit repair, selection level p < 0.01; it mirrors the faulty twin).

   Before the repair (p < 0.05): {OLD[cid]}.

   After the repair (final), 200 samples per world and control, 100 noise, 10 zeros:

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
{rows(r)}

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: {tm['deterministic']}.

6. **Timing** (fixed criterion, after the repair): t = {tm['t']} s per call (mean of 30 plus samples), g = {tm['g']} s per plus generation, S = {tm['S']} (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = {tm['est_s']} s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** {NEWDEV[cid]} Randomness: none (the criterion is deterministic). Skeleton requests: none.
"""
    open(p, "w", encoding="utf-8", newline="\n").write(head + new5)
    print(cid, "CASE.md updated")
