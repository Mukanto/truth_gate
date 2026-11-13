import json, os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from casetext import T

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
priv = {p["local_id"]: p for p in json.load(open(os.path.join(ROOT, "PRIVATE.json"), encoding="utf-8"))}

# last precheck line per case
pre = {}
for line in open(os.path.join(ROOT, "work", "precheck_round1.txt"), encoding="utf-8"):
    m = re.match(r"(B1-\d\d) (\{.*\})", line.strip())
    if m:
        pre[m.group(1)] = json.loads(m.group(2))

READ = {
 "KRI09": "Read by the earlier author (phase 1) as the full text on PMC (PMC2841687, stripped HTML). I did not re-read it.",
 "VUL09": "Read by the earlier author as a PDF converted to text (sections on the nonindependence error, survey, Fig. 4, reliability, gradations of nonindependence). I did not re-read it; my attempt to fetch the PDF failed.",
 "MAK19": "Read by the earlier author as the Europe PMC full-text XML (PMC6785265), section 'Circular analysis'. I did not re-read it.",
 "BAR05": "Only the abstract was read (by the earlier author, via Europe PMC); the full text was not accessible. I did not re-read it. Everything beyond the abstract (setting, remedy) is NOT VERIFIED against the paper.",
}
REVS = {"B1-02": 1}
REV_TEXT = {"B1-02": ("Revision 1: first version had an unbounded index ratio; pre-check on 100 N(0,1) noise samples: holds 37/100. "
                      "Reason: with N(0,1) probe data the denominator (r_pref + r_orth) is near zero or negative and the ratio explodes. Added a clip of the index to [-1, 1] (no effect on non-negative rates); "
                      "the faulty body mirrors it. Result after revision: noise 20/100 (see table). The remaining noise rate comes from the mean being taken over the few (about 7 of 150) neurons that pass the ANOVA at p < 0.05 "
                      "with a bounded index; I left the guard (at least one tuned neuron) and p unchanged.")}

for cid in sorted(priv):
    cdir = os.path.join(ROOT, "cases", cid)
    out = os.path.join(cdir, "CASE.md")
    if os.path.exists(out):
        print(cid, "CASE.md exists, skipped")
        continue
    a = json.load(open(os.path.join(cdir, "ASSIGNMENT.json"), encoding="utf-8"))
    p = priv[cid]
    r = pre[cid]
    tm = r["timing"]
    br = a["brief"]
    keys = "\n".join(f"  * `{k['key']}` {k['shape']} {k['dtype']}: {k['meaning']}" for k in br["data_keys"])
    def row(name, x):
        return f"| {name} | {x['n']} | {x['holds']} | {x['rate']:.3f} | {x['none']} |"
    ctl = [k for k in r if k.startswith("control")]
    rows = [row("plus", r["plus"]), row("minus", r["minus"])] + [row(k, r[k]) for k in ctl] + [row("probe: i.i.d. N(0,1) noise", r["noise"]), row("probe: zeros", r["zeros"])]
    s = f"""# {cid} ({a['world_id']})

1. **Case**: {cid}; world id {a['world_id']}; class {a['class']}; subtype: {a['subtype'] or '(none)'}; source key {a['source']}.

2. **Documented error** ({p['source']}): {p['passage']}
   Reading: {READ[p['source']]}

3. **Brief (exactly as in ASSIGNMENT.json)**
   * claim: {br['claim']}
   * data keys:
{keys}
   * sizes: {br['sizes']}

4. **Mapping.** {T[cid]['map']}

5. **Pre-checks of the fixed criterion** (plain Python, `fixed.py` only; samples drawn with a generator seeded 12345; `work/precheck.py`, output in `work/precheck_round1.txt`). Revisions of the fixed criterion: {REVS.get(cid, 0)}.

   | stream | samples | holds | rate | undefined (None) |
   |---|---|---|---|---|
""" + "\n".join(rows) + f"""

   Controls are the skeleton's own transforms applied to `plus` samples. The noise probe replaces every array by i.i.d. N(0,1) (bool arrays by fair coin flips: my reading of the probe, not the gate's code); the zero probe uses all-zero arrays. The criterion gave the same answer on repeated calls: {tm['deterministic']}.
""" + (f"\n   {REV_TEXT[cid]}\n" if cid in REV_TEXT else "") + f"""
6. **Timing** (fixed criterion): t = {tm['t']} s per call (mean of 30 plus samples), g = {tm['g']} s per plus generation, S = {tm['S']} (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = {tm['est_s']} s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests.** {T[cid]['dev']} Randomness: none (the criterion is deterministic). Skeleton requests: none.
"""
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print(cid, "CASE.md written")
