# B6-01 (world C27)

## 1. Identification
Case id B6-01; world id C27; class B-6; subtype None; source key LAZ18; mechanism tag `units-not-independent`; statistic family `mean`.

## 2. Source and documenting passage
LAZ18, section "Animal experiments": "animals in the same litter are randomised together, the treatment is applied to all animals simultaneously, and it is unreasonable to assume that animals in a womb do not influence each other."

Read by: full text (PMC5902037 via PMC and Europe PMC) by the part 1 author, see LOG.md 'Sources read and how'. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: Prenatal exposure raises adult open-field activity: the mean activity score of offspring of exposed dams is higher than that of offspring of control dams, and a two-sample t test of the difference between the two group means gives two-sided p < 0.05.

Data keys:
  * `activity`, shape (dams, pups), float: open-field activity score (distance travelled, arbitrary units) measured in adulthood on each pup of each dam
  * `exposed`, shape (dams,), bool: whether the dam received the exposure during pregnancy

Sizes: dams = 20; pups = 8 (activity: 20 x 8 = 160 values; exposed: 20 values)

## 4. Mapping
Faulty: Student two-sample t test (pooled variance, df = 158) on all 160 pup values, each pup a replicate (N = dams x pups); two-sided p < 0.05 and exposed mean higher. Fixed: one value per dam (mean over the pups of the dam, LAZ18 'reduce the data to a single value for each EU'), the same pooled two-sample t test on the 20 dam means (df = 18). The only code difference is the two lines that build x and y (`.ravel()` versus `.mean(axis=1)`).

Estimand line. Fixed: difference between the exposed and control groups in the mean of dam-level mean activity, dam as replicate. Faulty: difference between group means of pup-level activity, pup as replicate.

Allowed-guard minimum (same in both twins): 2 dams per group; non-finite values; zero pooled variance (zero standard error).

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-01 C27  plus 361/400=0.902 (None 0)  minus 15/400=0.037 (None 0)  control(permute_exposed_across_dams) 11/400=0.028 (None 0)  noise 5/400=0.013 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.052 ms  g=0.011 ms  S=5  estimate=0.15 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-01 C27  plus 900/1000=0.900 (None 0)  minus 29/1000=0.029 (None 0)  control(permute_exposed_across_dams) 23/1000=0.023 (None 0)  noise 28/1000=0.028 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.051 ms  g=0.011 ms  S=5  estimate=0.15 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.051 ms (mean of 100 calls on plus samples); g = 0.011 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.15 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
No deviation from the private note beyond the points above.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): units-not-independent / mean.
- Allowed-guard minimum (private note): 2 dams per group (smallest size at which the two-sample t statistic on dam means is defined); also non-finite and zero-variance guards. Same guards in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
