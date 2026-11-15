# CASE B1-05 (world C36)

## 1. Identification
Case id B1-05; world id C36; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: mean.
Allowed-guard minimum (private note): at least 1 voxel selected and at least 2 participants in the estimation half (one-sample t needs 2).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: KRI10 states no sizes).

## 2. Source and documenting passage
Source key: KRI10.
Passage (from the private note of the brief author): Q7 (EV): "To claim that an effect exists in a specific anatomic region across the population ... one must validate with independent subjects." Q6 (EV): "Effect sizes should be estimated using unbiased, independent data." (PMC2949251)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: In the cortical voxels where participants respond to the task, the response is at least 0.25 percent signal change: the mean task effect, averaged over those voxels and across participants, is at least 0.25, and a one-sided one-sample t test across participants of the voxel-averaged effect is significant at the 0.05 level.

Data keys:
  * `effect`, float, (subjects, voxels): task effect (task minus rest, percent signal change) of each cortical voxel in each participant

Sizes: {"subjects": 40, "voxels": 1000}

## 4. Mapping
Faulty: voxels with a one-sided one-sample t test across all 40 participants at p < 0.001; effect averaged over those voxels per participant; mean across participants >= 0.25 and one-sided one-sample t test across participants at 0.05, on the same 40 participants. Fixed: voxels selected with the same test on participants 0-19; mean and t test on participants 20-39 only (KRI10, Q6 and Q7: independent subjects).

Estimand line. Claim names the voxels where participants respond to the task because the estimand is the effect size in that region. Faulty: mean effect in voxels chosen on the group-level test of the same participants. Fixed: mean effect in voxels chosen from other participants.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean effect in voxels chosen on the group-level test of the same participants. Fixed: mean effect in voxels chosen from other participants.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 200, fails 0, None 0, exceptions 0 (n = 200)
  * minus: holds 2, fails 107, None 91, exceptions 0 (n = 200)
  * control:scramble_voxels_within_participant: holds 9, fails 171, None 20, exceptions 0 (n = 200)
  * control:random_sign_per_participant: holds 3, fails 93, None 104, exceptions 0 (n = 200)
  * probe:noise: holds 5, fails 110, None 85, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.032644 s (mean of 30 calls on plus samples), g = 0.000610 s (mean plus generation, 30 samples), S = 6 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 93.1 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
The empty-selection guard is reached often in this skeleton's minus world and controls (see pre-check counts: abstentions on 91/200 minus samples, 104/200 random-sign samples, 85/200 noise samples); this follows from the 0.001 cut on 1000 voxels and is an allowed guard, not a change. t on one call is 0.03 s because 1000 tail probabilities are integrated.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): select-then-test-same-data / mean.
- Allowed-guard minimum (private note): at least 1 voxel selected and at least 2 participants in the estimation half (one-sample t needs 2)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
