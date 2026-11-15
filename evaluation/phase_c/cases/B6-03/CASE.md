# B6-03 (world C17)

## 1. Identification
Case id B6-03; world id C17; class B-6; subtype None; source key LAZ18; mechanism tag `units-not-independent`; statistic family `regression-slope`.

## 2. Source and documenting passage
LAZ18, section "Slice preparations and histological samples": "The EU is the animal and the sample size (N) is the number of animals. Multiple histological sections, neurons per section, spines per neuron, and so on, are all subsamples as they have been randomised together ..."

Read by: full text (PMC5902037 via PMC and Europe PMC) by the part 1 author, see LOG.md 'Sources read and how'. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: Spine density on hippocampal CA1 pyramidal neurons rises with the dose of the drug the animal received: the regression slope of spine density on dose is positive, and a test of the slope gives two-sided p < 0.05.

Data keys:
  * `spine_density`, shape (animals, sections, neurons), float: spines per 10 micrometres of dendrite on each sampled neuron, in each histological section, of each animal
  * `dose`, shape (animals,), float: dose of the drug (mg/kg) that each animal received

Sizes: animals = 12; sections = 4; neurons = 25 (spine_density: 12 x 4 x 25 = 1200 values; dose: 12 values)

## 4. Mapping
Faulty: ordinary least squares slope of all 1200 neuron-level spine densities on the dose of the animal (dose repeated for the 100 neurons of an animal), slope t test with df = 1198, two-sided p < 0.05 and slope positive. Fixed: spine density averaged over sections and neurons per animal, slope of the 12 animal means on dose, t test with df = 10. The only code difference is the two lines that build x and y.

Estimand line. Fixed: slope of animal-level mean spine density on dose, animal as replicate. Faulty: slope of neuron-level spine density on dose, neuron as replicate.

Allowed-guard minimum (same in both twins): 3 animals; non-finite values; zero variance of dose; zero residual variance.

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-03 C17  plus 368/400=0.920 (None 0)  minus 9/400=0.022 (None 0)  control(permute_dose_across_animals) 8/400=0.020 (None 0)  noise 4/400=0.010 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.034 ms  g=0.025 ms  S=5  estimate=0.14 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-03 C17  plus 935/1000=0.935 (None 0)  minus 22/1000=0.022 (None 0)  control(permute_dose_across_animals) 32/1000=0.032 (None 0)  noise 28/1000=0.028 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.033 ms  g=0.025 ms  S=5  estimate=0.14 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.033 ms (mean of 100 calls on plus samples); g = 0.025 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.14 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
No deviation from the private note beyond the points above.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): units-not-independent / regression-slope.
- Allowed-guard minimum (private note): 3 animals (smallest size at which a slope t statistic with 1 df is defined); positive variance of dose; non-finite guard. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
