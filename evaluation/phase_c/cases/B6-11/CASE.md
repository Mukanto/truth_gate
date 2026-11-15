# B6-11 (world C03)

## 1. Identification
Case id B6-11; world id C03; class B-6; subtype None; source key LAZ10; mechanism tag `units-not-independent`; statistic family `correlation`.

## 2. Source and documenting passage
LAZ10, Background and Table 1: "If multiple observations are taken from each rat, then observations within each rat are not independent and therefore all of the observations cannot be summed to give a total sample size." Table 1 gives the summary-measure analysis as the solution.

Read by: full text (Europe PMC XML, PMC2817684) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: Across subjects, mean resting heart rate and mean salivary cortisol (each subject's mean over the recording days) are positively correlated: the Pearson correlation between the two subject means is positive, and a test of that correlation gives two-sided p < 0.05.

Data keys:
  * `heart_rate`, shape (subjects, days), float: resting heart rate in beats per minute of each subject on each recording day
  * `cortisol`, shape (subjects, days), float: morning salivary cortisol concentration of each subject on each recording day

Sizes: subjects = 16; days = 10 (heart_rate and cortisol: 16 x 10 = 160 values each)

## 4. Mapping
Faulty: Pearson correlation over all 160 subject-by-day pairs with its t test on df = 158 (each pair a replicate), two-sided p < 0.05 and r positive. Fixed: mean heart rate and mean cortisol per subject over the days, Pearson correlation of the 16 subject means with its t test on df = 14. The only code difference is the two lines that build x and y.

Estimand line. Fixed: between-subject Pearson correlation of subject-level means. Faulty: Pearson correlation over subject-by-day observations (mixing within-subject and between-subject variation), tested with N = subjects x days.

Allowed-guard minimum (same in both twins): 3 subjects; non-finite values; zero variance of either variable.

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-11 C03  plus 363/400=0.907 (None 0)  minus 14/400=0.035 (None 0)  control(permute_cortisol_subjects) 13/400=0.033 (None 0)  noise 6/400=0.015 (None 0)  zeros 0/20=0.000 (None 20)
   shuffle(heart_rate,cortisol) 12/400=0.030 (None 0)
   scipy reference disagreements on 800 samples: 0
   timing t=0.035 ms  g=0.016 ms  S=6  estimate=0.14 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-11 C03  plus 906/1000=0.906 (None 0)  minus 26/1000=0.026 (None 0)  control(permute_cortisol_subjects) 27/1000=0.027 (None 0)  noise 31/1000=0.031 (None 0)  zeros 0/20=0.000 (None 20)
   shuffle(heart_rate,cortisol) 24/1000=0.024 (None 0)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.042 ms  g=0.016 ms  S=6  estimate=0.16 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.042 ms (mean of 100 calls on plus samples); g = 0.016 ms (mean of 100 plus generations); S = 6 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.16 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
No deviation from the private note beyond the points above.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B6-08.
- Mechanism tag / statistic family (private note): units-not-independent / correlation.
- Allowed-guard minimum (private note): 3 subjects (smallest number of pairs for which a Pearson correlation and its t statistic are defined); zero-variance and non-finite guards. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
