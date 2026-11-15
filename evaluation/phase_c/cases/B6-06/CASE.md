# B6-06 (world C52)

## 1. Identification
Case id B6-06; world id C52; class B-6; subtype None; source key NIE11; mechanism tag `significant-here-not-there`; statistic family `regression-slope`.

## 2. Source and documenting passage
NIE11, abstract: "researchers conclude that effects differ when one effect is significant (P < 0.05) but the other is not (P > 0.05)."

Read by: abstract only (Europe PMC record, PMID 21878926; full text not open) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: Reaction times fall more steeply over practice sessions in healthy subjects than in patients: the mean per-subject linear slope of reaction time on session number is more negative in the healthy group, and a two-sample t test of the difference between the two groups' mean slopes gives two-sided p < 0.05.

Data keys:
  * `rt`, shape (subjects, sessions), float: median reaction time in milliseconds of each subject in each practice session, sessions in order
  * `patient`, shape (subjects,), bool: whether the subject belongs to the patient group (true) or the healthy group (false)

Sizes: subjects = 30; sessions = 8 (rt: 30 x 8 = 240 values; patient: 30 values)

## 4. Mapping
Faulty: per-subject least-squares slope of reaction time on session (sessions in order), one-sample t test of the slopes within the healthy group and within the patient group; holds when the healthy mean slope is negative with p < 0.05 and the patient group's p >= 0.05. Fixed: pooled two-sample t test of the per-subject slopes, healthy versus patient, two-sided p < 0.05 and the healthy mean slope more negative. The per-subject slope step is identical in the twins.

Estimand line. Fixed: difference between groups in the mean per-subject slope of reaction time on session. Faulty: the two within-group mean slopes, each tested against zero, compared by the pattern of significance.

Allowed-guard minimum (same in both twins): 2 subjects per group and 2 sessions; non-finite values; zero variance of the slopes (pooled, or within a group for the faulty one-sample tests).

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-06 C52  plus 372/400=0.930 (None 0)  minus 7/400=0.018 (None 0)  control(permute_group_membership_across_subjects) 10/400=0.025 (None 0)  noise 10/400=0.025 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.060 ms  g=0.016 ms  S=5  estimate=0.18 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-06 C52  plus 930/1000=0.930 (None 0)  minus 30/1000=0.030 (None 0)  control(permute_group_membership_across_subjects) 28/1000=0.028 (None 0)  noise 26/1000=0.026 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.056 ms  g=0.016 ms  S=5  estimate=0.17 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.056 ms (mean of 100 calls on plus samples); g = 0.016 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.17 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
The faulty rule does not constrain the direction of the patient group's slope (only p >= 0.05).

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): significant-here-not-there / regression-slope.
- Allowed-guard minimum (private note): 2 subjects per group and 2 sessions (a per-subject slope is defined from 2 points; the two-sample t statistic from 2 per group); zero variance of session numbers is excluded by design. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
