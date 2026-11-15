# B6-05 (world C45)

## 1. Identification
Case id B6-05; world id C45; class B-6; subtype None; source key NIE11; mechanism tag `significant-here-not-there`; statistic family `mean`.

## 2. Source and documenting passage
NIE11, abstract: "researchers conclude that effects differ when one effect is significant (P < 0.05) but the other is not (P > 0.05)."

Read by: abstract only (Europe PMC record, PMID 21878926; full text not open) by the part 1 author, see LOG.md. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: The training programme improves task accuracy more than the control activity: the mean change in accuracy (post minus pre) is larger in the trained group than in the control group, and a two-sample t test of the difference between the two groups' mean changes gives two-sided p < 0.05.

Data keys:
  * `pre`, shape (subjects,), float: task accuracy (proportion correct) of each subject before the programme
  * `post`, shape (subjects,), float: task accuracy (proportion correct) of each subject after the programme
  * `trained`, shape (subjects,), bool: whether the subject took part in the training programme (true) or in the control activity (false)

Sizes: subjects = 40 (pre, post and trained: 40 values each)

## 4. Mapping
Faulty: within-group paired t tests of post minus pre (one-sample t test of the change scores) in the trained group and in the control group; the claim is taken to hold when the trained group's mean change is positive with p < 0.05 and the control group's change has p >= 0.05 (the NIE11 'significant here, not there' rule). Fixed: two-sample (pooled) t test of the difference between the groups' mean change scores, two-sided p < 0.05 and trained mean change larger (the test of the interaction).

Estimand line. Fixed: difference between groups in mean change (post minus pre). Faulty: the pair of within-group mean changes, each tested against zero, with the decision based on the pattern of their significance.

Allowed-guard minimum (same in both twins): 2 subjects per group; non-finite values; zero variance (of the change scores in the pooled test; of a group's change scores in the faulty one-sample tests).

No randomness is used by either criterion (no `rng`); both are deterministic. The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`).

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
B6-05 C45  plus 369/400=0.922 (None 0)  minus 9/400=0.022 (None 0)  control(permute_trained) 13/400=0.033 (None 0)  noise 11/400=0.028 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 800 samples: 0
   timing t=0.049 ms  g=0.036 ms  S=5  estimate=0.20 s  (calls 100)
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
B6-05 C45  plus 928/1000=0.928 (None 0)  minus 26/1000=0.026 (None 0)  control(permute_trained) 19/1000=0.019 (None 0)  noise 28/1000=0.028 (None 0)  zeros 0/20=0.000 (None 20)
   scipy reference disagreements on 2000 samples: 0
   timing t=0.048 ms  g=0.036 ms  S=5  estimate=0.20 s  (calls 100)
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = 0.048 ms (mean of 100 calls on plus samples); g = 0.036 ms (mean of 100 plus generations); S = 5 (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = 0.20 s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
The faulty rule does not constrain the direction of the control group's change (only p >= 0.05), as NIE11 describes the pattern.

Skeleton requests: none. SIZE REQUEST: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B6-01.
- Mechanism tag / statistic family (private note): significant-here-not-there / mean.
- Allowed-guard minimum (private note): 2 subjects per group (smallest size for two-sample t on change scores); each within-group paired test is also defined at 2. Same guards in both twins.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
