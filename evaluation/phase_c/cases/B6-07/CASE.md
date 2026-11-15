# B6-07 (world C08)

## 1. Identification
Case id B6-07; world id C08; class B-6; subtype None; source key NIE11; mechanism tag `significant-here-not-there`; statistic family `mean`.

## 2. Source and documenting passage
NIE11, abstract: "In theory, a comparison of two experimental effects requires a statistical test on their difference."

Read by: abstract only (Europe PMC record, PMID 21878926; full text not open) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: The task engages region A more than region B: the task-evoked signal change (task minus rest) is larger in region A than in region B, with the mean across subjects of the within-subject difference of the two signal changes positive, and a paired t test of that difference gives two-sided p < 0.05.

Data keys:
  * `task_a`, shape (subjects,), float: mean signal in region A of each subject during task blocks (percent signal change units)
  * `rest_a`, shape (subjects,), float: mean signal in region A of each subject during rest blocks
  * `task_b`, shape (subjects,), float: mean signal in region B of each subject during task blocks
  * `rest_b`, shape (subjects,), float: mean signal in region B of each subject during rest blocks

Sizes: subjects = 24 (each of the four keys: 24 values)

## 4. Mapping
Faulty: for each region the one-sample t test of the subject-wise task-minus-rest signal change against zero; holds when region A's mean effect is positive with p < 0.05 and region B's effect has p >= 0.05. Fixed: paired t test of the within-subject difference of the two signal changes (one-sample t on (task_a - rest_a) - (task_b - rest_b)), two-sided p < 0.05 and the mean difference positive.

Estimand line. Fixed: mean across subjects of the within-subject difference between the effect in region A and the effect in region B. Faulty: the two region-wise mean effects, each tested against zero, compared by the pattern of significance.

Allowed-guard minimum (same in both twins): 2 subjects; non-finite values; zero variance (of the difference in the fixed criterion; of a region's effect in the faulty one).

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-07 C08  plus 362/400=0.905 (None 0)  minus 13/400=0.033 (None 0)  control(swap_region_labels_in_half_the_subjects) 0/400=0.000 (None 0)  noise 10/400=0.025 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.038 ms  g=0.016 ms  S=5  estimate=0.13 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-07 C08  plus 902/1000=0.902 (None 0)  minus 33/1000=0.033 (None 0)  control(swap_region_labels_in_half_the_subjects) 8/1000=0.008 (None 0)  noise 31/1000=0.031 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.041 ms  g=0.022 ms  S=5  estimate=0.15 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.041 ms (mean of 100 calls on plus samples); g = 0.022 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.15 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
The faulty rule does not constrain the direction of region B's effect (only p >= 0.05).
Observation: the declared control (region labels swapped in half the subjects) makes the fixed criterion hold in 8/1000 samples (0.008); plus 0.902, minus 0.033.
Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B6-01.
- Mechanism tag / statistic family (private note): significant-here-not-there / mean.
- Allowed-guard minimum (private note): 2 subjects (smallest size for a paired t statistic); zero-variance and non-finite guards. Same in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
