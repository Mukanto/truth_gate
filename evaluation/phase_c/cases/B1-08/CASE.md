# CASE B1-08 (world C54)

## 1. Identification
Case id B1-08; world id C54; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: R-squared.
Allowed-guard minimum (private note): at least 1 electrode selected and at least 3 trials in the test half (R-squared of a one-predictor regression needs 3 points), both conditions present.
Size ratio (brief size to source size): source states none (see the sizes note of the private note: KRI09 states no EEG sizes).

## 2. Source and documenting passage
Source key: KRI09.
Passage (from the private note of the brief author): Introduction: "In electro- and magnetoencephalography, an example of selection is the restriction to a subset of sensors or sources that show expected responses." (PMC2841687, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Over the scalp electrodes that respond to the stimulus, the stimulus condition explains at least 10% of the variance of the electrode-averaged post-stimulus amplitude across trials (R-squared of at least 0.10 in a regression of that amplitude on the stimulus condition).

Data keys:
  * `amplitude`, float, (trials, electrodes): mean post-stimulus EEG amplitude (microvolts) at each electrode on each trial
  * `stimulus`, bool, (trials,): True on trials with the stimulus present, False on control trials

Sizes: {"trials": 100, "electrodes": 64}

## 4. Mapping
Faulty: electrodes whose amplitude is larger on stimulus than on control trials (one-sided Welch t test across all 100 trials, p < 0.05); amplitude averaged over those electrodes; R-squared of its regression on the stimulus condition over all 100 trials >= 0.10. Fixed: electrodes selected by the same test on the odd-numbered trials (indices 0, 2, ..., 98); R-squared computed on the even-numbered trials only (indices 1, 3, ..., 99); same threshold (KRI09, introduction: selection of sensors).

Estimand line. Claim names the responsive electrodes because the estimand is the explained variance in that set. Faulty: R-squared of the condition on the average of electrodes chosen for a condition difference on the same trials. Fixed: R-squared of the condition on the average of electrodes chosen on other trials.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: R-squared of the condition on the average of electrodes chosen for a condition difference on the same trials. Fixed: R-squared of the condition on the average of electrodes chosen on other trials.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 179, fails 21, None 0, exceptions 0 (n = 200)
  * minus: holds 3, fails 133, None 64, exceptions 0 (n = 200)
  * control:permute_stimulus_condition_across_trials: holds 3, fails 131, None 66, exceptions 0 (n = 200)
  * probe:noise: holds 9, fails 183, None 8, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.001788 s (mean of 30 calls on plus samples), g = 0.000101 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 4.5 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
R-squared of the one-predictor regression is computed as the squared correlation of the condition (as 0/1) with the electrode average. Guard minima as in the note: 2 trials per condition in the selection half (Welch), at least 3 trials in the estimation half, a stimulus with both conditions present (zero variance gives None). The fixed criterion holds on 89.5% of plus samples (above the 0.8 power target); the abstention (empty selection) rate in minus is 64/200.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): select-then-test-same-data / R-squared.
- Allowed-guard minimum (private note): at least 1 electrode selected and at least 3 trials in the test half (R-squared of a one-predictor regression needs 3 points), both conditions present
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
