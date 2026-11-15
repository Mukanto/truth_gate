# B6-12 (world C15)

## 1. Identification
Case id B6-12; world id C15; class B-6; subtype None; source key MAK19; mechanism tag `significant-here-not-there`; statistic family `correlation`.

## 2. Source and documenting passage
MAK19, section "Interpreting comparisons between two effects without directly comparing them": the intervention is "significant" in one condition and the control "not significant"; "This type of erroneous inference is very common but incorrect." (Figure 1A: two groups of 20, a correlation significant in one and not in the other.)

Read by: full text (Europe PMC XML, PMC6785265) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: Scores on the task and on the symptom scale are more strongly related in group A than in group B: the Pearson correlation between task score and symptom score is higher in group A than in group B, and a Fisher z test of the difference between the two correlations gives two-sided p < 0.05.

Data keys:
  * `task_score`, shape (participants,), float: score of each participant on the experimental task
  * `symptom_score`, shape (participants,), float: score of each participant on the symptom questionnaire
  * `group_a`, shape (participants,), bool: whether the participant belongs to group A (true) or group B (false)

Sizes: participants = 40 (each of the three keys: 40 values)

## 4. Mapping
Faulty: Pearson correlation and its t test (df = n - 2) separately in group A and in group B; holds when group A's correlation is positive with p < 0.05 and group B's has p >= 0.05. Fixed: Fisher z test of the difference of the two correlations, z = (atanh r_A - atanh r_B) / sqrt(1/(n_A - 3) + 1/(n_B - 3)), two-sided p < 0.05 (|z| > 1.959963984540054) and r_A > r_B. The two group correlations are computed by the same code in the twins.

Estimand line. Fixed: difference between group A's and group B's Pearson correlations. Faulty: the two group-wise correlations each tested against zero, compared by the pattern of significance.

Allowed-guard minimum (same in both twins): 4 participants per group (Fisher z standard error needs n - 3 > 0; the same guard in the faulty twin); non-finite values; zero variance of either score within a group.

No randomness is used by either criterion (no `rng`); both are deterministic. The faulty criterion uses the numpy-only Student t helper (tested as below); the fixed criterion is a z test. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`). Two-sided 5% normal critical value used as a constant: 1.959963984540054.

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-12 C15  plus 370/400=0.925 (None 0)  minus 8/400=0.020 (None 0)  control(permute_group_labels) 18/400=0.045 (None 0)  noise 7/400=0.018 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.031 ms  g=0.012 ms  S=5  estimate=0.10 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-12 C15  plus 921/1000=0.921 (None 0)  minus 24/1000=0.024 (None 0)  control(permute_group_labels) 50/1000=0.050 (None 0)  noise 25/1000=0.025 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.040 ms  g=0.022 ms  S=5  estimate=0.15 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.040 ms (mean of 100 calls on plus samples); g = 0.022 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.15 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
The faulty twin uses the same 4-per-group guard as the fixed one (the note's 'same guards in both twins'), although its own Pearson tests need only 3. Never reached in the skeleton (20 per group).
Observation on the skeleton (no change requested): the fixed criterion holds under the declared control 'permute_group_labels' in 50/1000 samples (0.050), above the one-sided 0.025 expected for a pure null; the permuted groups mix the two correlation structures of plus, so this may reflect the skeleton's control; recorded as is.
Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): significant-here-not-there / correlation.
- Allowed-guard minimum (private note): 4 participants per group (smallest size at which the Fisher z standard error, with n - 3 > 0, is defined; each Pearson correlation needs 3); zero-variance and non-finite guards. Same in both twins.
- Size ratio (brief size to source size): participants 40/40 = 1.0.
- The estimand line is in item 4 (criterion author).
