# B6-08 (world C22)

## 1. Identification
Case id B6-08; world id C22; class B-6; subtype None; source key HUR84; mechanism tag `units-not-independent`; statistic family `mean`.

## 2. Source and documenting passage
HUR84, section on types of pseudoreplication, p. 205 (sacrificial pseudoreplication): "... where the two or more samples or measurements taken from each experimental unit are treated as independent replicates (Fig. 5B)."

Read by: full PDF text (extracted in memory with pypdf) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: The insecticide lowers invertebrate density: the mean density in treated tanks is lower than in control tanks, and a Welch two-sample t test of the difference between the two group means gives two-sided p < 0.05.

Data keys:
  * `density`, shape (tanks, samples), float: invertebrates per litre counted in each of the water samples taken from each tank
  * `treated`, shape (tanks,), bool: whether the tank received the insecticide

Sizes: tanks = 8; samples = 10 (density: 8 x 10 = 80 values; treated: 8 values)

## 4. Mapping
Faulty: Welch two-sample t test on all 80 sample densities, samples as replicates, two-sided p < 0.05 and treated mean lower. Fixed: mean density per tank, the same Welch test on the 8 tank means (tank as experimental unit). The only code difference is the two lines that build x and y.

Estimand line. Fixed: difference in group means of tank-level mean density, tank as replicate. Faulty: difference in group means of sample-level density, sample as replicate.

Allowed-guard minimum (same in both twins): 2 tanks per group; non-finite values; zero standard error.

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-08 C22  plus 369/400=0.922 (None 0)  minus 8/400=0.020 (None 0)  control(permute_treated_across_tanks) 2/400=0.005 (None 0)  noise 10/400=0.025 (None 24)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.049 ms  g=0.017 ms  S=5  estimate=0.16 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-08 C22  plus 911/1000=0.911 (None 0)  minus 23/1000=0.023 (None 0)  control(permute_treated_across_tanks) 6/1000=0.006 (None 0)  noise 27/1000=0.027 (None 83)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.053 ms  g=0.022 ms  S=5  estimate=0.18 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.053 ms (mean of 100 calls on plus samples); g = 0.022 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.18 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
No deviation from the private note beyond the points above.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B6-04.
- Mechanism tag / statistic family (private note): units-not-independent / mean.
- Allowed-guard minimum (private note): 2 tanks per group (smallest size for the Welch t statistic on tank means); non-finite and zero-variance guards. Same in both twins.
- Size ratio (brief size to source size): tanks per treatment 4/2 = 2.0 (Hurlbert: twofold replication in such examples); samples per tank: source states none.
- The estimand line is in item 4 (criterion author).
