# CASE O2-B

1. **Case id** O2-B; **world id** C20; **class** O; **subtype** O-2 (flexibility outside the criterion, optional stopping).
2. **Source** SIM11, text on Figure 1: a researcher who has collected 10 (or 20) observations per condition "and then tests for significance every 1, 5, 10, or 20 per-condition observations" stops once significance is obtained or at 50 per condition; starting at 10 and testing after every new observation finds a significant effect 22 percent of the time. Read by the brief author in the full-text PDF https://pdf.stafforini.com/simmons-2011-falsepositive-psychology-undisclosed.pdf (LOG.md part 1); the part-2 author did not re-read it.
3. **Brief**: claim "The mean score of the treatment condition exceeds that of the control condition: the difference in means is positive and a two-sided two-sample t test (equal variances assumed) on all participants gives p < .05." Keys: `score_control`, `score_treatment`, float (participants,). Size: 50 participants per condition.
4. **Mapping.** Faulty: equal-variance two-sample t test after the first 10 observations per condition and after every additional observation up to the maximum (n = 10, 11, ..., 50, the first n entries of each array); the claim holds when any of these tests has a positive difference and p < .05 (documented parameters: minimum 10, step 1, maximum 50, alpha .05; the maximum is the array length, 50). Fixed: the same test on all observations only; the same loop over a list of sizes, a list of one. Exact p value as in O2-A.
   **Estimand line.** Faulty: whether the treatment-control difference reaches significance at any of the sample sizes 10 to 50. Fixed: the treatment-minus-control difference in mean score over all 50 participants per condition (the analysis at the full planned size).
5. **Pre-checks of the fixed criterion**: `plus` 376 of 400 hold (0.94), `minus` 12 of 400 (0.03), control `reassign_conditions` 11 of 400, noise probe 8 of 400, zeros probe all None. Helper validation as in O2-A (same helper text; 0 disagreements with `scipy.stats.ttest_ind` on 2000 samples). Revisions: 0.
6. **Timing**: t = 0.000037 s, g = 0.000016 s, S = 5; estimate 2 x 200 x 6 x 0.000053 = 0.1 s.
7. **Deviations, problems, skeleton requests.** None. The brief does not say that rows are in recruitment order; as the note states, the faulty criterion takes the first n entries of each array. Guards: non-finite values; fewer than 2 per condition; zero pooled variance in any look.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case O2a.
- Mechanism tag / statistic family (private note): O-2 / mean.
- Allowed-guard minimum (private note): 2 participants per condition; non-finite values and zero pooled variance return None
- Size ratio (brief size to source size): maximum participants per condition 50/50 = 1.0.
- The estimand line is in item 4 (criterion author).
