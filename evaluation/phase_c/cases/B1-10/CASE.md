# CASE B1-10 (world C41)

## 1. Identification
Case id B1-10; world id C41; class B-1; subtype None.
Mechanism tag: split-by-baseline-compare-change. Statistic family: mean.
Allowed-guard minimum (private note): 2 neurons per third for the Welch t statistic.
Size ratio (brief size to source size): source states none (see the sizes note of the private note: MAK19 gives no sizes for the example).

## 2. Source and documenting passage
Source key: MAK19.
Passage (from the private note of the brief author): Circular analysis section: "They therefore split the population to sub-groups, by binning the data based on the activity levels observed at baseline." followed by the significant interaction "a result of the distorting selection criterion and a combination of statistical artefacts (regression to the mean, floor/ceiling effects)". (PMC6785265, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Neurons that are least active at rest increase their firing more with the manipulation than neurons that are most active at rest: ranking the 240 neurons by firing rate in the resting recording, the mean change in rate (post-manipulation minus pre-manipulation) of the lowest third exceeds that of the highest third by at least 1.0 spikes/s, and a one-sided Welch t test of that difference is significant at the 0.05 level.

Data keys:
  * `rate_rest`, float, (neurons,): firing rate (spikes/s) of each neuron in a resting recording
  * `rate_pre`, float, (neurons,): firing rate (spikes/s) of each neuron before the manipulation
  * `rate_post`, float, (neurons,): firing rate (spikes/s) of each neuron after the manipulation

Sizes: {"neurons": 240}

## 4. Mapping
Faulty: ranks the 240 neurons by rate_pre (stable argsort, ties kept in order), takes the lowest and highest thirds (80 each), difference of mean change (rate_post minus rate_pre) lowest minus highest >= 1.0 and one-sided Welch t test at 0.05. Fixed: the same with the ranking by rate_rest (MAK19, circular analysis section: binning on the activity observed at baseline).

Estimand line. Claim names the resting recording because the estimand is the change-by-resting-activity difference. Faulty: difference in mean change between neurons grouped by the pre-manipulation rate itself. Fixed: the same difference with groups by an independent resting recording.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: difference in mean change between neurons grouped by the pre-manipulation rate itself. Fixed: the same difference with groups by an independent resting recording.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 187, fails 13, None 0, exceptions 0 (n = 200)
  * minus: holds 1, fails 199, None 0, exceptions 0 (n = 200)
  * control:permute_rate_rest: holds 4, fails 196, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000086 s (mean of 30 calls on plus samples), g = 0.000071 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.4 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): split-by-baseline-compare-change / mean.
- Allowed-guard minimum (private note): 2 neurons per third for the Welch t statistic
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
