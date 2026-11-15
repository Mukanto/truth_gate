# B6-09 (world C35)

## 1. Identification
Case id B6-09; world id C35; class B-6; subtype None; source key HUR84; mechanism tag `units-not-independent`; statistic family `other`.

## 2. Source and documenting passage
HUR84, pp. 204-205 (temporal pseudoreplication): "... the multiple samples from each experimental unit are not taken simultaneously but rather sequentially over each of several dates. Dates are then taken to represent replicated treatments and significance tests are applied."

Read by: full PDF text (extracted in memory with pypdf) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: The treatment raises invertebrate abundance in the field plots: abundance is higher in treated plots than in control plots, and a two-sided Mann-Whitney U test comparing the abundances of the two groups gives p < 0.05.

Data keys:
  * `abundance`, shape (plots, dates), float: number of individuals counted in a sample from each plot on each weekly sampling date, dates in order
  * `treated`, shape (plots,), bool: whether the plot received the treatment

Sizes: plots = 12; dates = 12 (abundance: 12 x 12 = 144 values; treated: 12 values)

## 4. Mapping
Faulty: two-sided Mann-Whitney U test (normal approximation with tie correction and continuity correction) on all 144 plot-by-date abundances, each a replicate of its treatment. Fixed: abundance averaged over dates per plot, the same Mann-Whitney test on the 12 plot means. Holds when the treated rank sum is higher and |z| exceeds the two-sided 5% critical value 1.959963984540054. The only code difference is the two lines that build x and y.

Estimand line. Fixed: location shift (Mann-Whitney probability) of plot-level time-averaged abundance between treated and control plots, plot as replicate. Faulty: the same shift tested on plot-by-date observations, date-sample as replicate.

Allowed-guard minimum (same in both twins): 1 plot per group (the rank-sum statistic is defined from 1 per group); non-finite values; zero rank variance (all values equal).

No randomness is used by either criterion (no `rng`); both are deterministic. The test is a z test (normal approximation), so no t-distribution helper is needed; Two-sided 5% normal critical value used as a constant: 1.959963984540054.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-09 C35  plus 373/400=0.932 (None 0)  minus 9/400=0.022 (None 0)  control(reassign_plots_to_treatment) 8/400=0.020 (None 0)  noise 8/400=0.020 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.037 ms  g=0.057 ms  S=5  estimate=0.22 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-09 C35  plus 932/1000=0.932 (None 0)  minus 20/1000=0.020 (None 0)  control(reassign_plots_to_treatment) 23/1000=0.023 (None 0)  noise 19/1000=0.019 (None 1)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.040 ms  g=0.074 ms  S=5  estimate=0.28 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.040 ms (mean of 100 calls on plus samples); g = 0.074 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.28 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
The note's guard minimum 'at least 2 plots per group' is lowered to 1 plot per group, because PREREG_PHASE_C section 2 allows no more than the smallest size at which the statistic is defined (the rank-sum statistic exists from 1 per group). Never reached in the skeleton (6 plots per group). Both twins use the normal approximation with tie and continuity corrections (6 versus 6 plot means in the fixed criterion).

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): units-not-independent / other.
- Allowed-guard minimum (private note): 2 plots per group (smallest size at which the rank-sum statistic is defined for the plot means); non-finite and all-values-equal guards. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
