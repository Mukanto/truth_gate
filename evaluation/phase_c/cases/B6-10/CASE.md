# B6-10 (world C23)

## 1. Identification
Case id B6-10; world id C23; class B-6; subtype None; source key LAZ10; mechanism tag `units-not-independent`; statistic family `mean`.

## 2. Source and documenting passage
LAZ10, Introduction/Methods and "How to check reported values": ten rats, three consecutive days of rotarod tests; the reported t28 = 2.1 should have 5 + 5 - 2 = 8 degrees of freedom.

Read by: full text (Europe PMC XML, PMC2817684) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: The drug improves motor coordination: the mean time spent on the rotarod is longer in the treatment group than in the control group, and a two-tailed two-sample t test of the difference between the two group means gives p < 0.05.

Data keys:
  * `latency`, shape (rats, days), float: time in seconds that each rat stayed on the rotarod on each of the consecutive test days
  * `treated`, shape (rats,), bool: whether the rat was in the treatment group (true) or the control group (false)

Sizes: rats = 10; days = 3 (latency: 10 x 3 = 30 values; treated: 10 values)

## 4. Mapping
Faulty: two-tailed pooled two-sample t test on all 30 rat-by-day latencies (df 28, as in the LAZ10 example), treated mean higher, p < 0.05. Fixed: mean latency over the 3 days per rat (LAZ10 summary-measure analysis), the same pooled t test on the 10 rat means (df 8). The only code difference is the two lines that build x and y.

Estimand line. Fixed: difference between group means of rat-level mean latency, rat as replicate. Faulty: difference between group means of rat-by-day latency, observation as replicate.

Allowed-guard minimum (same in both twins): 2 rats per group; non-finite values; zero pooled variance.

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-10 C23  plus 358/400=0.895 (None 0)  minus 5/400=0.013 (None 0)  control(permute_treated_across_rats) 8/400=0.020 (None 0)  noise 10/400=0.025 (None 9)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.048 ms  g=0.010 ms  S=5  estimate=0.14 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-10 C23  plus 915/1000=0.915 (None 0)  minus 24/1000=0.024 (None 0)  control(permute_treated_across_rats) 30/1000=0.030 (None 0)  noise 30/1000=0.030 (None 18)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.050 ms  g=0.012 ms  S=5  estimate=0.15 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.050 ms (mean of 100 calls on plus samples); g = 0.012 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.15 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
No deviation from the private note beyond the points above.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B6-07.
- Mechanism tag / statistic family (private note): units-not-independent / mean.
- Allowed-guard minimum (private note): 2 rats per group (smallest size for a two-sample t statistic); non-finite and zero-variance guards. Same in both twins.
- Size ratio (brief size to source size): rats 10/10 = 1.0; days 3/3 = 1.0.
- The estimand line is in item 4 (criterion author).
