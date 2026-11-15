# CASE B1-04 (world C05)

## 1. Identification
Case id B1-04; world id C05; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: mean.
Allowed-guard minimum (private note): at least 1 voxel per participant and at least 2 participants with a non-empty region (paired t across participants needs 2).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: KRI10 states no sizes (questions-and-answers paper)).

## 2. Source and documenting passage
Source key: KRI10.
Passage (from the private note of the brief author): Q7 (EV): "to claim that a subject-specific ROI contains a certain effect across the population ('the subject-specific FFA respond more to faces than bodies'), one need only validate with independent data from the same subjects." (PMC2949251, full text of the questions and answers read at the publisher page)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: In each participant's own region of visual cortex that responds more to faces than to houses, the response to faces exceeds the response to bodies: across the 12 participants the mean difference (faces minus bodies) of the response in that region is at least 0.3 percent signal change, and a one-sided paired t test across participants is significant at the 0.05 level.

Data keys:
  * `resp_faces`, float, (subjects, runs, voxels): response to face images (percent signal change) of each visual-cortex voxel in each scanning run of each participant
  * `resp_bodies`, float, (subjects, runs, voxels): response to body images (percent signal change), same layout
  * `resp_houses`, float, (subjects, runs, voxels): response to house images (percent signal change), same layout

Sizes: {"subjects": 12, "runs": 8, "voxels": 300}

## 4. Mapping
Faulty: per participant, voxels with t > 2.0 for faces minus houses over all 8 runs (one-sided, t over runs); faces minus bodies averaged over those voxels and runs (same runs); mean across participants >= 0.3 and one-sided paired t test across participants at 0.05. Fixed: voxels selected from the even-numbered runs (runs 2, 4, 6, 8 = indices 1, 3, 5, 7), faces minus bodies measured in the odd-numbered runs only (indices 0, 2, 4, 6); same t > 2.0 cut, threshold and test (KRI10, Q7 and introduction: independent data from the same subjects).

Estimand line. Claim names the faces-versus-houses region definition because the estimand is the effect in that region. Faulty: mean faces-minus-bodies response in voxels chosen on the faces-vs-houses contrast of the same runs. Fixed: the same quantity with voxels chosen in other runs.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean faces-minus-bodies response in voxels chosen on the faces-vs-houses contrast of the same runs. Fixed: the same quantity with voxels chosen in other runs.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 200, fails 0, None 0, exceptions 0 (n = 200)
  * minus: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * control:swap_face_body_labels_per_run: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000206 s (mean of 30 calls on plus samples), g = 0.001173 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 3.3 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
Numbering convention: runs are numbered from 1, so 'even-numbered' means array indices 1, 3, 5, 7. The cut t > 2.0 is kept as the same constant in both versions, so on 4 selection runs (df 3) it corresponds to a stricter one-sided p than on 8 runs (df 7). A participant with an empty region is left out of the across-participant test, and the criterion returns None when fewer than 2 participants remain (the guard minimum of the note); a voxel with zero variance across the selection runs gives None.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): select-then-test-same-data / mean.
- Allowed-guard minimum (private note): at least 1 voxel per participant and at least 2 participants with a non-empty region (paired t across participants needs 2)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
