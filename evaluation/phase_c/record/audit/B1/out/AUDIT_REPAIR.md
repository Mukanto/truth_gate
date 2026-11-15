# Post-repair fidelity audit, Phase C, class B-1: pair B1-09

This is the repair round under PREREG_PHASE_C §5 and PB §5.3, judged by `AUDIT_PHASE_C.md` on all nine items under the
same rules as the first audit. `AUDIT.json` and `AUDIT.md` are unchanged.

I called no criterion on any data and ran no world and no Truth_Gate. I read the files as text only, using the same
diff helper (`scratch\show_case.py`) and a byte comparison of `faulty.py` with `prerepair\faulty.py`.

**Verdict: B1-09 passes. All nine items are "yes".**

## What changed

* `faulty.py` is byte-identical to `prerepair\faulty.py` (checked with `cmp`).
* `fixed.py`: only the criterion body changed. Both twins still match the frozen skeleton outside the body; the helper
  confirms this and `MECH_CHECK.json` lists no issues.
* The new fixed rule works in three steps:
  1. Average the two sessions, as the faulty twin does.
  2. Choose voxels on participants 0–7 with the same one-sided p < 0.005 rule (6 df).
  3. Require the mean correlation of the chosen voxels with the trait, computed on participants 8–15, to be at least 0.5.

  The guards are: non-finite input; fewer than 3 participants per half; zero variance of the trait in a half or of any
  voxel; and an empty selection. Each returns `None`.
* `CASE.md`: §1–3 are unchanged (compared with `prerepair\CASE.md`). The mapping, the estimand line, §5–7 and a
  "Repair" paragraph are updated.
* `class\LOG.md` has a "Repair round" section. It records that the author agreed (no dispute) and lists the pre-check of
  the fixed twin:
  * plus 193/200;
  * minus 6/200 (None 15);
  * control 9/200;
  * noise 3/200.

## Items

* **(a) yes.** The faulty twin is unchanged and is the VUL09 strategy: voxel-wise correlations across all 16
  participants, voxels above p < 0.005 kept, and the mean of their correlations reported on the same data.
* **(b) yes.** Voxels are now chosen and the correlation estimated on disjoint participants. KRI10 Q7 asks for exactly
  this when the inference is at the group level (TN, ML, RP; EV says a group-level region effect must be validated
  "with independent subjects"). The threshold, the p rule, the session averaging and the guards are the same as in the
  faulty twin, so the repair adds nothing else.
* **(c) yes.** The only difference is which participants are used for choosing and for estimating. To compute the
  correlation on a subset, the helper now takes a set of participant rows, computes the trait variance per half and
  uses df = half size − 2. That restructuring belongs to the correction.
* **(d) yes.**
  * MECH_CHECK line 99 compares the claim's statistic with its threshold (0.5).
  * The minimum of 3 participants per half is the smallest size at which a correlation is defined, and it is the
    note's minimum.
  * The zero-variance, non-finite and empty-selection guards are on the allowed list.
  * No branch inspects whether the input looks like noise, zeros or a shuffle.
* **(e) yes.** The brief is unchanged (`ASSIGNMENT.json` equals the brief in `MECH_CHECK.json`). It contains no banned
  term and no negation of the claim.
* **(f) yes.** The sizes are unchanged at 16 × 1000. VUL09's abstract states no sizes. Sixteen participants is of the
  order of the brain–trait studies VUL09 surveys, and 1000 voxels is the cap. The halves of 8 come from the correction,
  not from a size change. The pair stays on the list of sizes "not documented by the source".
* **(g) yes.** Both twins use the same statistic, threshold and decision rule. The fixed twin's cost is comparable: its
  timing estimate is 85.6 s, against 90.9 s for the first version.
* **(h) yes.** The brief is unchanged and keeps to the "what a brief may state" text.
* **(i) yes.** The claim's quantity is the mean voxel-wise trait correlation in the trait-related region. The fixed
  twin now estimates it on participants not used to choose the voxels, and CASE.md's estimand line says so. The
  fixed-estimand wording in `PRIVATE.json` (the brief author's note, which is not part of the repair) still describes
  the superseded session split; it names the same quantity.

**Return-value check (no yes/no).** The fixed criterion returns True exactly when the mean correlation of the chosen
voxels, measured in independent participants, is at least 0.5. As in B1-05, the estimate uses half the sample.

## What I read in this round

`class\LOG.md` (the "Repair round" section); the `MECH_CHECK.json` entry for B1-09; and in `class\cases\B1-09\`:
`ASSIGNMENT.json` (checked unchanged), `faulty.py`, `fixed.py`, `skeleton.py` (through the diff helper), `CASE.md`
(§4 to the end, and §1–3 compared with `prerepair\CASE.md`), and `prerepair\faulty.py` (byte comparison).

I fetched no URL and called no `ctx_*` tool in this round. For KRI10 Q7 I relied on the class extract
(`class\src\kri10.txt`), which I had already searched in the first audit.
