# CASE B3-05

## 1. Identity
Case id B3-05; world id C12; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key PEA97. Passage (as recorded in the part-1 private note): Section (1): 'a biologist takes the triplet femur, tibia, humerus, and seeks the correlation between the indices femur/humerus and tibia/humerus ... there would be ... a correlation of about 0.4 to 0.5 between these indices had the bones been sorted absolutely at random.' (OCR text of Proc. R. Soc. 60:489, archive.org philtrans00847732.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: Across adult skeletons, femur length and tibia length are positively associated after accounting for humerus length: the partial correlation between femur length and tibia length, given humerus length, is at least 0.3.
Data keys:
  * `femur_length` (skeletons,) float: Maximum length of the femur of each skeleton, in mm.
  * `tibia_length` (skeletons,) float: Maximum length of the tibia of each skeleton, in mm.
  * `humerus_length` (skeletons,) float: Maximum length of the humerus of each skeleton, in mm.
Sizes: skeletons = 1000; femur_length, tibia_length and humerus_length each have shape (1000,).

## 4. Mapping
Documented error (note): Pearson correlation across skeletons between femur_length/humerus_length and tibia_length/humerus_length; claim holds when r >= 0.3. Documented parameter: equal coefficients of variation of the three lengths give r about 0.5 (Pearson's example 0.45) when the lengths are otherwise uncorrelated.
Documented correction (note): Partial correlation of femur_length and tibia_length given humerus_length; claim holds when >= 0.3.
As implemented. Faulty: Pearson correlation of femur_length / humerus_length with tibia_length / humerus_length, holds when r >= 0.3. Fixed: partial correlation of femur_length and tibia_length given humerus_length, holds when >= 0.3.
Guards as coded: Faulty n >= 3, fixed n >= 4; zero variance -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: correlation between femur and tibia length at fixed humerus length. Faulty: correlation between the two quotients over the same humerus length, which contains the shared humerus term.
Mechanism tag ratio-shared-denominator, statistic family correlation (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 300/300, fails 0/300, None 0/300 (rate 1.000)
* minus: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control permute_tibia_within_humerus_blocks: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.061 ms, g = 0.055 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.3 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B3-05.
- Mechanism tag / statistic family (private note): ratio-shared-denominator / correlation.
- Allowed-guard minimum (private note): 4 skeletons (partial correlation with 1 covariate); zero variance of any variable or residual -> None; non-finite -> None.
- Size ratio (brief size to source size): skeletons 1000/'some thousand' = about 1.0.
- The estimand line is in item 4 (criterion author).
