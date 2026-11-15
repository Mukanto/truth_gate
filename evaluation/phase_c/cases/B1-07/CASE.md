# CASE B1-07 (world C28)

## 1. Identification
Case id B1-07; world id C28; class B-1; subtype None.
Mechanism tag: select-then-test-same-data. Statistic family: mean.
Allowed-guard minimum (private note): at least 1 neuron selected (a mean is defined from 1) and at least 2 trials per stimulus in each half.
Size ratio (brief size to source size): source states none (see the sizes note of the private note: KRI09 states no recording sizes for the neuron example (its simulations use 30x30x20 voxels, 200 time points and 100 runs, which do not carry over)).

## 2. Source and documenting passage
Source key: KRI09.
Passage (from the private note of the brief author): Introduction: "In single-cell recording, an example of selection is the restriction of in-depth analysis to neurons with certain response properties." Independence is ensured by "an independent data set for the final analysis of the selected channels (e.g. neurons or voxels)". (PMC2841687, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Among the recorded visual neurons that fire more to vertical than to horizontal bars, the mean orientation index, (vertical minus horizontal) / (vertical plus horizontal) computed from trial-averaged firing rates, is at least 0.1.

Data keys:
  * `rate_vertical`, float, (neurons, trials): firing rate (spikes/s) of each neuron on each presentation of a vertical bar
  * `rate_horizontal`, float, (neurons, trials): firing rate (spikes/s) of each neuron on each presentation of a horizontal bar

Sizes: {"neurons": 250, "trials": 15}

## 4. Mapping
Faulty: neurons with a one-sided Welch t test of rate_vertical over rate_horizontal across the 15 presentations each at p < 0.05; orientation index (V-H)/(V+H) of the trial-averaged rates of those neurons from all 15 presentations; mean index >= 0.1. Fixed: neurons selected by the same test on the odd-numbered presentations (indices 0, 2, ..., 14: 8 trials) and the index computed from the even-numbered presentations (indices 1, 3, ..., 13: 7 trials); same threshold (KRI09, introduction: single-cell selection and an independent data set).

Estimand line. Claim names the neurons that fire more to vertical than to horizontal bars because the estimand is the orientation index in that population. Faulty: mean index of neurons chosen for a vertical-over-horizontal difference on the same trials. Fixed: mean index of the same kind of neurons computed on other trials.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean index of neurons chosen for a vertical-over-horizontal difference on the same trials. Fixed: mean index of the same kind of neurons computed on other trials.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 200, fails 0, None 0, exceptions 0 (n = 200)
  * minus: holds 4, fails 196, None 0, exceptions 0 (n = 200)
  * control:shuffle_orientation_labels_within_neuron: holds 8, fails 192, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 99, fails 101, None 0, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.009243 s (mean of 30 calls on plus samples), g = 0.000492 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 23.4 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
The fixed criterion holds on the N(0,1) noise probe in about half the samples (99/200): on noise the trial-averaged rates have positive and negative sums near zero, so the ratio index is heavy-tailed and its mean exceeds 0.1 about as often as not. The index is the claim's own statistic, the allowed guards do not cover a near-zero or negative denominator (only a non-finite one returns None), and I did not change the statistic. A clean pass of the fixed twin may fail on K5_HOLDS_ON_NOISE for this reason, independent of the correction; the faulty twin has the same ratio.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B1-01.
- Mechanism tag / statistic family (private note): select-then-test-same-data / mean.
- Allowed-guard minimum (private note): at least 1 neuron selected (a mean is defined from 1) and at least 2 trials per stimulus in each half
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
