# B6-04 (world C10)

## 1. Identification
Case id B6-04; world id C10; class B-6; subtype None; source key LAZ18; mechanism tag `units-not-independent`; statistic family `mean`.

## 2. Source and documenting passage
LAZ18, section on the three criteria of an experimental unit (cages, drinking-water example): "We expect animals in a cage to influence each other on many relevant variables, from behaviour to microbiomes." Housing 2 per cage maximises "the number of cages (which are now the EUs)".

Read by: full text (PMC5902037 via PMC and Europe PMC) by the part 1 author, see LOG.md 'Sources read and how'. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: Giving the compound in the drinking water reduces body-weight gain: the mean weight gain of animals receiving the compound is lower than that of controls, and a Welch two-sample t test of the difference between the two group means gives two-sided p < 0.05.

Data keys:
  * `weight_gain`, shape (cages, animals), float: body-weight gain in grams over the study of each animal housed in each cage
  * `treated`, shape (cages,), bool: whether the drinking water supplied to the cage contained the compound

Sizes: cages = 40; animals = 2 (weight_gain: 40 x 2 = 80 values; treated: 40 values)

## 4. Mapping
Faulty: Welch two-sample t test on all 80 animal-level weight gains, animals as replicates, two-sided p < 0.05 and treated mean lower. Fixed: mean weight gain per cage (2 animals), the same Welch test on the 40 cage means (cage as experimental unit). The only code difference is the two lines that build x and y.

Estimand line. Fixed: difference in group means of cage-level mean weight gain, cage as replicate. Faulty: difference in group means of animal-level weight gain, animal as replicate.

Allowed-guard minimum (same in both twins): 2 cages per group; non-finite values; zero standard error.

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-04 C10  plus 370/400=0.925 (None 0)  minus 9/400=0.022 (None 0)  control(permute_treatment_across_cages) 12/400=0.030 (None 0)  noise 8/400=0.020 (None 0)  zeros 0/20=0.000 (None 20)
   shuffle(weight_gain,treated) 13/400=0.033 (None 0)
   scipy reference disagreements on 800 samples: 0
   timing t=0.082 ms  g=0.009 ms  S=6  estimate=0.25 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-04 C10  plus 931/1000=0.931 (None 0)  minus 32/1000=0.032 (None 0)  control(permute_treatment_across_cages) 32/1000=0.032 (None 0)  noise 18/1000=0.018 (None 0)  zeros 0/20=0.000 (None 20)
   shuffle(weight_gain,treated) 31/1000=0.031 (None 0)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.059 ms  g=0.009 ms  S=6  estimate=0.19 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.059 ms (mean of 100 calls on plus samples); g = 0.009 ms (mean of 100 plus generations); S = 6 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.19 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
No deviation from the private note beyond the points above.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): units-not-independent / mean.
- Allowed-guard minimum (private note): 2 cages per group (smallest size at which a Welch t statistic on cage means is defined); non-finite and zero-variance guards. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
