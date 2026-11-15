# CASE B1-11 (world C31)

## 1. Identification
Case id B1-11; world id C31; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: mean.
Allowed-guard minimum (private note): 2 participants per group in the test half (Welch t needs 2 per group).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: MAK19 states no sizes for this example).

## 2. Source and documenting passage
Source key: MAK19.
Passage (from the private note of the brief author): Circular analysis section: "Most commonly, circular analysis is used to divide (e.g. sub-grouping, binning) or reduce (e.g. defining a region of interest, removing 'outliers') the complete dataset using a selection criterion that is retrospective and inherently relevant to the statistical outcome." (PMC6785265, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Patients show a larger evoked response than controls in the time window in which the two groups' responses differ: the mean amplitude over a window of 10 consecutive samples is at least 0.5 microvolts greater for patients than for controls, and a one-sided Welch t test of that difference is significant at the 0.05 level.

Data keys:
  * `erp`, float, (participants, time): evoked-response amplitude (microvolts) of each participant at each time sample after stimulus onset, time samples in order
  * `patient`, bool, (participants,): True for a patient, False for a control participant

Sizes: {"participants": 60, "time": 200}

## 4. Mapping
Faulty: mean amplitude in each window of 10 consecutive samples (191 windows, cumulative sums); the window with the largest patient-minus-control difference of group means over all 60 participants is picked and its mean amplitude difference is tested on the same participants (difference >= 0.5 and one-sided Welch t test at 0.05). Fixed: the window is picked on the even-indexed participants (indices 0, 2, ..., 58), the difference is tested on the odd-indexed participants (indices 1, 3, ..., 59); same width, threshold and test (MAK19, circular analysis section: defining a region of interest).

Estimand line. Claim names the window in which the groups differ because the estimand is the group difference in that window. Faulty: mean difference over a window chosen for the largest group difference in the same participants. Fixed: mean difference over a window chosen on other participants.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean difference over a window chosen for the largest group difference in the same participants. Fixed: mean difference over a window chosen on other participants.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 177, fails 23, None 0, exceptions 0 (n = 200)
  * minus: holds 10, fails 190, None 0, exceptions 0 (n = 200)
  * control:permute_patient: holds 9, fails 191, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000162 s (mean of 30 calls on plus samples), g = 0.000654 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 2.0 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
Here the note says 'even-indexed', which I read as array indices 0, 2, ...; this differs from the 1-based 'even-numbered' reading used in B1-04, B1-06, B1-07 and B1-08, as the notes word it. Guard: at least 1 participant per group in the selection half (a mean is defined from 1), at least 2 per group in the test half (Welch); the note's parenthetical 'at least 2 per group' for the selection half was read as the test-half minimum only, so that the guard does not exceed the smallest defined size. The fixed criterion holds on 88.5% of plus samples and on 10/200 minus samples.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B1-07.
- Mechanism tag / statistic family (private note): select-then-test-same-data / mean.
- Allowed-guard minimum (private note): 2 participants per group in the test half (Welch t needs 2 per group)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
