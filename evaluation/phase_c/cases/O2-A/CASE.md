# CASE O2-A

1. **Case id** O2-A; **world id** C18; **class** O; **subtype** O-2 (flexibility outside the criterion).
2. **Source** SIM11, Table 1 note and text, Situation A: "Results for Situation A were obtained by conducting three t tests, one on each of two dependent variables and a third on the average of these two variables." (false-positive rate 9.5 percent at p < .05, r = .50, 20 observations per cell). Read by the brief author in the full text PDF https://pdf.stafforini.com/simmons-2011-falsepositive-psychology-undisclosed.pdf (LOG.md part 1); the part-2 author did not re-read it.
3. **Brief**: claim "Participants in the treatment condition report higher liking of the product than participants in the control condition: the difference in mean liking is positive and a two-sided two-sample t test (equal variances assumed) gives p < .05." Keys: `liking_control`, `liking_treatment`, `willingness_to_pay_control`, `willingness_to_pay_treatment`, each float (participants,). Size: 20 participants per condition.
4. **Mapping.** Faulty: three equal-variance two-sample t tests (liking, willingness to pay, and the raw average (liking + willingness to pay)/2 per participant, as in the source's wording; standardising the variables is not documented), alpha .05 two-sided; the claim is reported as holding when any of the three has a positive treatment-minus-control difference and p < .05. Fixed: the one test on liking, same test, same alpha, same "any over the list of comparisons" code on a list of one. The p value is exact (closed form of Student's t for integer degrees of freedom, Abramowitz and Stegun 26.7.3 and 26.7.4), because only numpy is available.
   **Estimand line.** Faulty: whether at least one of three treatment-control comparisons (liking, willingness to pay, their average) is significant. Fixed: the treatment-minus-control difference in mean liking.
5. **Pre-checks of the fixed criterion**: `plus` 372 of 400 hold (0.93), `minus` 10 of 400 hold (0.025), control `reassign_conditions` 7 of 400, noise probe 7 of 400, zeros probe (20) all None. The helper was validated (scratch `work\validate_p_helper.py`, fixed file only): maximum absolute error of the two-sided p value against `scipy.stats.t` is 2.8e-11 over df 1..59 and 98..198; the fixed criterion's decision disagrees with `scipy.stats.ttest_ind` on 0 of 2000 samples. Revisions: 0.
6. **Timing**: t = 0.000032 s, g = 0.000029 s, S = 2 + 1 + 0 + 0 + 2 = 5; estimate 2 x 200 x 6 x 0.000061 = 0.1 s.
7. **Deviations, problems, skeleton requests.** None. In the world the raw average is dominated by liking (0 to 100 scale, willingness to pay about 8 currency units), which follows the note's instruction to use the raw average. Guards: non-finite values; fewer than 2 per condition; zero pooled variance in any of the tests.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case O2a.
- Mechanism tag / statistic family (private note): O-2 / mean.
- Allowed-guard minimum (private note): 2 participants per condition (smallest size at which a two-sample t statistic is defined); non-finite values and zero pooled variance return None
- Size ratio (brief size to source size): participants per cell 20/20 = 1.0.
- The estimand line is in item 4 (criterion author).
