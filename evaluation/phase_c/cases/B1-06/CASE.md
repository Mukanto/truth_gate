# CASE B1-06 (world C06)

## 1. Identification
Case id B1-06; world id C06; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: regression-slope.
Allowed-guard minimum (private note): at least 1 voxel selected and at least 3 trials in the test half (a slope p value needs 3 points).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: KRI10 gives no sizes).

## 2. Source and documenting passage
Source key: KRI10.
Passage (from the private note of the brief author): Introduction: effect estimates and tests "based on selected data need to be independent of the selection process", ensured "by using independent data for selection (e.g., using half of the data to select signal-carrying voxels, and the other half to estimate the signal)". (PMC2949251, introduction)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: In the voxels of this participant's visual cortex whose responses follow stimulus contrast, the response rises with contrast: the regression slope of the voxel-averaged response (percent signal change) on stimulus contrast across the 240 trials is at least 0.2 percent signal change per unit of contrast, with a one-sided p value below 0.05.

Data keys:
  * `response`, float, (trials, voxels): response of each visual-cortex voxel on each trial, in percent signal change
  * `contrast`, float, (trials,): stimulus contrast shown on each trial, in units where full contrast equals 1

Sizes: {"trials": 240, "voxels": 500}

## 4. Mapping
Faulty: voxels whose response correlates positively with contrast across all 240 trials (one-sided p < 0.01), average of those voxels regressed on contrast over all 240 trials; slope >= 0.2 and one-sided p < 0.05. Fixed: voxels selected on the even-numbered trials (indices 1, 3, ..., 239), slope estimated on the odd-numbered trials only (indices 0, 2, ..., 238); same p < 0.01 rule, threshold and test (KRI10, introduction: half of the data to select, the other half to estimate).

Estimand line. Claim names the voxels whose responses follow stimulus contrast because the estimand is the slope in that set. Faulty: slope of the average of voxels chosen for correlation with contrast, on the same trials. Fixed: the same slope on trials not used to choose the voxels.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: slope of the average of voxels chosen for correlation with contrast, on the same trials. Fixed: the same slope on trials not used to choose the voxels.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 200, fails 0, None 0, exceptions 0 (n = 200)
  * minus: holds 4, fails 187, None 9, exceptions 0 (n = 200)
  * control:permute_contrast_across_trials: holds 4, fails 182, None 14, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 199, None 1, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * probe:shuffle:response,contrast: holds 4, fails 186, None 10, exceptions 0 (n = 200)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.018114 s (mean of 30 calls on plus samples), g = 0.001424 s (mean plus generation, 30 samples), S = 6 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 54.7 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
Numbering convention as in B1-04 (trials numbered from 1). The correlation p value of each voxel is that of a t statistic with n - 2 degrees of freedom (n = 240 in the faulty, 120 in the fixed); the cut p < 0.01 is the same in both.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): select-then-test-same-data / regression-slope.
- Allowed-guard minimum (private note): at least 1 voxel selected and at least 3 trials in the test half (a slope p value needs 3 points)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
