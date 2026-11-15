# CASE B1-09 (world C19)

## 1. Identification
Case id B1-09; world id C19; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: correlation.
Allowed-guard minimum (private note): at least 1 voxel selected and at least 3 participants (a correlation needs 3 pairs).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: Abstract reports no sample sizes (55 articles surveyed)).

## 2. Source and documenting passage
Source key: VUL09.
Passage (from the private note of the brief author): Abstract: "More than half acknowledged using a strategy that computes separate correlations for individual voxels and reports means of only those voxels exceeding chosen thresholds. We show how this nonindependent analysis inflates correlations while yielding reassuring-looking scattergrams." (abstract via Europe PMC search record; full text not accessible)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Across 16 participants, activation in the brain region whose response relates to the personality trait is correlated with the trait: the mean, over the voxels of that region, of the voxel-wise correlations (across participants) between activation and trait score is at least 0.5.

Data keys:
  * `act_session1`, float, (subjects, voxels): activation of each voxel in each participant, measured in the first scanning session
  * `act_session2`, float, (subjects, voxels): activation of each voxel in each participant, measured in a second scanning session
  * `trait`, float, (subjects,): questionnaire score on the personality trait for each participant

Sizes: {"subjects": 16, "voxels": 1000}

## 4. Mapping
Faulty: sessions averaged; voxel-wise correlation across the 16 participants with the trait; voxels with one-sided p < 0.005 (cut computed from the t distribution with 14 degrees of freedom) kept; mean of their correlations >= 0.5, computed on the same averaged data. Fixed (after the repair round): the two sessions are averaged as in the faulty twin; voxels are chosen with the same one-sided p < 0.005 rule (t distribution with 6 degrees of freedom) on the first 8 participants (indices 0-7), and the mean correlation with the trait of the chosen voxels is computed on the other 8 participants (indices 8-15) and must be >= 0.5 (VUL09, abstract: reporting means of only the voxels exceeding chosen thresholds).

Estimand line. Claim names the region whose response relates to the trait because the estimand is the correlation in that region. Faulty: mean per-voxel correlation across voxels chosen for their correlation with the trait in the same data. Fixed: mean per-voxel correlation measured in other participants across voxels chosen in the first half of the participants.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean per-voxel correlation across voxels chosen for their correlation with the trait in the same data. Fixed: mean per-voxel correlation measured in other participants across voxels chosen in the first half of the participants.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
Final version (after the repair round, see below):
  * plus: holds 193, fails 7, None 0, exceptions 0 (n = 200)
  * minus: holds 6, fails 179, None 15, exceptions 0 (n = 200)
  * control:permute_trait_across_participants: holds 9, fails 182, None 9, exceptions 0 (n = 200)
  * probe:noise: holds 3, fails 197, None 0, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the repaired fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_b09_repair.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 1 (the repair round; the first version below was replaced). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

First version (superseded, kept for the record): voxels chosen on act_session1, mean correlation of act_session2 over those voxels. Pre-check, same 200 samples per stream: plus 199 holds / 1 fails; minus 11 holds / 170 fails / 19 None; control 8 / 171 / 21; noise 1 / 199 / 0; zeros None 5/5; timing t = 0.037231 s, g = 0.000625 s, estimate 90.9 s.

## 6. Timing (final fixed criterion)
t = 0.0351 s (mean of 30 calls on plus samples), g = 0.0006 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 85.6 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
VUL09 was read from the abstract only. The fixed criterion's minus rate (6/200) is close to the nominal 0.05 level of the claim's own threshold and is not repaired further. Skeleton requests: none. Size requests: none.

## Repair (repair round, PREREG_PHASE_C section 5 / PB section 5.3)
Auditor item (b) answered no: the first fixed criterion chose the voxels on session 1 and estimated the correlation on session 2 of the same participants. I agree: in this skeleton the participants' stable subject-by-voxel component is shared by both sessions (the skeleton's own comment says so), so a voxel chosen for a chance correlation in session 1 carries part of it into session 2; session 2 is therefore not independent of the choice (my first CASE.md note recorded the symptom, 11/200 minus holds). What changed: only the body of `criterion` in `fixed.py`. The sessions are averaged (as in the faulty twin), the voxels are chosen on participants 0-7 with the same one-sided p < 0.005 rule (6 degrees of freedom), and the mean voxel-wise correlation is computed on participants 8-15; threshold 0.5, the guards (non-finite, empty selection, at least 3 participants in each half, zero variance) and the p < 0.005 rule are unchanged. `faulty.py` is byte-identical to before (SHA-256 checked before and after). Participants are in no particular order in the skeleton's generator (independent draws), so the first half is an arbitrary half.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B1-04.
- Mechanism tag / statistic family (private note): select-then-test-same-data / correlation.
- Allowed-guard minimum (private note): at least 1 voxel selected and at least 3 participants (a correlation needs 3 pairs)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
