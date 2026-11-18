# Phase D post-run audit, part 1

This file was written before `part2\` was opened. It covers 20 pairs: B-2 has 10 (D-007, D-010, D-011, D-022, D-027,
D-035, D-042, D-055, D-064, D-066), B-3 has 7 (D-008, D-023, D-040, D-056, D-062, D-067, D-068), and the decoys are 3
(D-012 B-6, D-047 B-1, D-052 B-6).

**Method.**
- I read the files that the instruction lists.
- I parsed all 120 certificates with `scratch\summ.py`. It extracts the verdicts, the flags and the per-stream counts,
  maps rate flags to streams as PREREG §5 says, and applies the §5 attribution rule with a one-sided Fisher test.
- I checked `RUNLOG.jsonl` against the certificates: 120 results, all attempt 1, no redo, timeout, infrastructure
  failure or crash. Every certificate SHA-256 and every verdict matches the log, and every study file's SHA-256 matches
  `module_sha256` in its certificate.
- I ran no gate and started no agent.

My recount, used only to answer the questions:

| Class | Arm | Faulty NOT_FALSIFIABLE | Attributable (declared / generic-only) | Clean pass |
|---|---|---|---|---|
| B-2 | R | 10/10 | 10 (10 / 0) | 10/10 |
| B-2 | W0 | 9/10 | 9 (9 / 0) | 9/10 |
| B-2 | W1 | 9/10 | 9 (9 / 0) | 10/10 |
| B-3 | R | 7/7 | 7 (7 / 0) | 7/7 |
| B-3 | W0 | 6/7 | 6 (5 / 1) | 7/7 |
| B-3 | W1 | 6/7 | 6 (5 / 1) | 7/7 |
| decoys | R | 3/3 | 3 (3 / 0) | 3/3 |
| decoys | W0 | 2/3 | 1 (1 / 0) | 3/3 |
| decoys | W1 | 3/3 | 2 (2 / 0) | 3/3 |

Counts below are written "faulty vs fixed", out of 200. Awareness levels are the higher of the two readers. "First"
means `WORLD_LOG.md` alone; "second" means W1 with `CHECKLIST_LOG.md`.

## 1. Answers per pair

### B-2

**D-007** (L1.1, ridge R^2 by resubstitution vs 5-fold CV)
- R: (i) yes. world:minus 200 vs 3, control 200 vs 0, noise 200 vs 0. (ii) n/a: fixed WEAK; K2_LOW_POWER is capping,
  with plus 134/200.
- W0: (i) yes. The faulty twin holds everywhere (K2 on world:minus 200 vs 2; HIGH_RATE/K4 on the control 200 vs 3;
  HIGH_RATE/K5 on the shuffle 200 vs 3; noise 200 vs 0), and the fixed twin carries no rate flag. Several streams,
  not only noise. (ii) n/a. (iii) no. The claim names out-of-sample R^2. 50 x 2000 is a realistic size, and the
  statistic is set by the brief. The noise probe detects without any world.
- W1: (i) yes: world:minus 200 vs 2, control 200 vs 1, noise 200 vs 0. (ii) n/a: WEAK; K2_LOW_POWER, plus 96/200.
  (iii) no.

**D-010** (L1.2, target encoding from all rows)
- R: (i) yes: world:minus 200 vs 0, control 200 vs 0, noise 112 vs 0. (ii) n/a.
- W0: (i) yes: world:minus 200 vs 0, control 200 vs 0, shuffle 200 vs 0, noise 112 vs 0. (ii) n/a. (iii) no. The
  claim names the district, and 150 districts for 1200 rows are the sizes. The small-category structure is set mostly
  by those sizes.
- W1: (i) yes: world:minus 200 vs 0, control 200 vs 0, noise 112 vs 0. (ii) n/a. (iii) no.

**D-011** (L1.3, gene selection on all samples)
- R: (i) yes: world:minus 88 vs 0, control 85 vs 0, noise 200 vs 0. (ii) n/a.
- W0: (i) yes: world:minus 157 vs 0, control 144 vs 0, shuffle 149 vs 0, noise 200 vs 0. (ii) n/a. (iii) no: 72 x
  2000 is set by the brief, and the noise probe detects.
- W1: (i) yes: world:minus 120 vs 0, control 123 vs 0, noise 200 vs 0. (ii) n/a. (iii) no.

**D-022** (L1.1, 66-term OLS by resubstitution)
- R: (i) yes: world:minus, control and noise all 200 vs 0. (ii) n/a.
- W0: (i) yes: world:minus, control, shuffle and noise all 200 vs 0. (ii) n/a. (iii) no: the model is the claim's
  estimand, and the noise probe detects.
- W1: (i) yes: world:minus 200 vs 3, control 200 vs 0, shuffle 200 vs 0, noise 200 vs 0. (ii) n/a. (iii) no.

**D-027** (L1.1, OLS MAE skill in-sample)
- R: (i) yes: world:minus 197 vs 0, control 198 vs 0, noise 196 vs 0. (ii) n/a.
- W0: (i) yes: world:minus 199, control 198, shuffle 196, noise 196, each vs 0. (ii) n/a. (iii) no.
- W1: (i) yes: world:minus 198, control 199, noise 196, each vs 0. (ii) n/a. (iii) no.

**D-035** (L1.2, SMOTE before the folds)
- R: (i) yes: world:minus 200 vs 0, control 200 vs 0; no noise. (ii) n/a: fixed plus 158/200.
- W0:
  - (i) yes. On world:minus, K2_HIGH_SIZE and K2_FAILS_UNREACHABLE: 200 vs 0, and the fixed twin has no rate flag
    there.
  - The faulty HIGH_RATE flags on the control and the shuffle (200 vs 0) do not qualify. The fixed twin carries
    K4_CONTROL_ALSO_HOLDS and K5_HOLDS_ON_SHUFFLE on those streams, which comes from its own plus rate of 2/200: the
    same flag names, for a different reason.
  - The detection rests on world:minus only, not on noise.
  - (ii) yes, from the skeleton (low power in plus). The fixed twin is NOT_FALSIFIABLE with plus 2/200 and 0/200 on
    minus, noise, control and shuffle. Every flag it has is relative to that plus rate.
  - The W0 effect is Mahalanobis 1.2 on 7 of 20 variables; the log puts the optimal balanced accuracy at about 0.73.
    That was sized for an optimal classifier, not for the 5-NN + SMOTE pipeline that both twins use and the brief does
    not name.
  - The same fixed body passes in R (158/200) and in W1 (29/200).
  - (iii) no. Balanced accuracy is the claim's statistic and cues imbalance (12%).
- W1: (i) yes: world:minus 200 vs 0, control 200 vs 0. (ii) n/a: a clean pass, but weak (K2_LOW_POWER, plus 29/200).
  (iii) no. The log says the 15% prevalence is "not given in the brief".

**D-042** (L1.4, duplicate records split across folds)
- R: (i) yes: world:minus 128 vs 0 only. (ii) n/a.
- W0:
  - (i) yes: world:minus 200 vs 0, control 200 vs 0; noise and shuffle 0. (ii) n/a.
  - **(iii) yes.** The key meanings ("for each compound record") and the axis "records", set against the claim's "new
    compounds", made the author build 600 compounds with repeat records and identical descriptor rows. The log calls
    this its main judgement call: "the brief distinguishes compound records from new compounds".
  - The detection rests entirely on those duplicates.
- W1: (i) yes: world:minus 95 vs 0, control 141 vs 0. (ii) n/a. **(iii) yes.** The log says: "'records' vs 'new
  compounds' read as replicate measurements of some compounds" (300 replicate records). The checklist also points to
  repeated measurements, but the world log names the brief's wording.

**D-055** (L3.1, random folds on a daily series)
- R: (i) yes: world:minus 45 vs 3, control 65 vs 2. (ii) n/a.
- W0: (i) n/a. The faulty twin is WEAK, at 0/200 on every stream. What was needed is world:minus with an outcome as
  persistent as the predictors: the W0 outcome noise is AR 0.3, while R used 0.92. The structure statistic, the
  predictors' autocorrelation, does not capture this. (ii) n/a. (iii) no.
- W1: (i) n/a: WEAK (world:minus 1/200). world:minus was needed; outcome AR 0.6 with a 10% drift was not enough.
  (ii) n/a. (iii) no.

**D-064** (L1.1, ridge correlation by resubstitution)
- R: (i) yes: world:minus 200 vs 0, control 200 vs 2, noise 200 vs 1. (ii) n/a.
- W0: (i) yes: world:minus 200 vs 1, control 200 vs 3, noise 200 vs 1. (ii) n/a: WEAK; K2_LOW_POWER, plus 119/200.
  (iii) no.
- W1: (i) yes: world:minus 200 vs 4, control 200 vs 2, shuffle 200 vs 2, noise 200 vs 1. (ii) n/a. (iii) no.

**D-066** (L1.4, upsampling copies before the folds)
- R: (i) yes: world:minus 200 vs 0, control 200 vs 0. (ii) n/a.
- W0: (i) yes: world:minus, control and shuffle all 200 vs 0; noise 0 vs 0. (ii) n/a. (iii) no, but borderline. The
  claim sentence calls y "the rare outcome", and the author set prevalence to 8%, which equals the note value and is
  what the copying exploits. Because the word is in the claim, and the claim's balanced accuracy cues imbalance anyway
  (compare D-035), I do not count it.
- W1: (i) yes: world:minus, control and shuffle all 200 vs 0. (ii) n/a. (iii) no, borderline as in W0 (log: "'rare'
  was taken as 8%").

### B-3

**D-008** (shared measured component, Fick VO2 vs DO2)
- R: (i) yes: world:minus 96 vs 0, control 200 vs 0, noise 200 vs 0. (ii) n/a.
- W0:
  - (i) yes. On world:minus, K2_HIGH_SIZE: 25 vs 0.
  - Control and shuffle: 200 vs 0. The faulty twin never reads `vo2_expired_gas`, because it substitutes Fick VO2,
    which is the error.
  - Noise: 200 vs 0, from the coupling.
  - Not noise only.
  - (ii) n/a.
  - (iii) no. `venous_o2_content` is read only by the faulty body, but it is a routine measurement and decides no world
    structure. The coupling in minus comes from the author's own 7% CO error.
- W1: (i) yes: world:minus 18 vs 0, control 200 vs 0, noise 200 vs 0. (ii) n/a. (iii) no.

**D-023** (shared denominator, beetles)
- R: (i) yes: world:minus 197 vs 0, control 200 vs 0, noise 66 vs 0. (ii) n/a.
- W0: (i) yes, **probe:noise only**: 66 vs 0. On N(0,1) data the denominator crosses zero, so the ratios co-move.
  world:minus, control and shuffle are all 0 vs 0. The worlds are near-isometric, with a body-length CV of about
  0.08. (ii) n/a. (iii) no.
- W1: (i) yes, **probe:noise only**: 66 vs 0, the same as W0 because the noise probe does not depend on the arm.
  world:minus 0 vs 0. (ii) n/a. (iii) no.

**D-040** (shared denominator, skulls)
- R: (i) yes: world:minus 200 vs 0, control 200 vs 1, noise 87 vs 0. (ii) n/a.
- W0: (i) yes: world:minus 192 vs 0, control 195 vs 0, shuffle 200 vs 0, noise 87 vs 0. (ii) n/a. (iii) no.
- W1: (i) yes: world:minus 74 vs 0, control 124 vs 1, noise 87 vs 0. (ii) n/a. (iii) no.

**D-056** (ratio vs ANCOVA)
- R: (i) yes: world:minus 53 vs 10 only. (ii) n/a.
- W0: (i) yes, world:minus only: 22 vs 6 (p 0.001). Group masses differ and uptake scales as mass^0.75. (ii) n/a.
  (iii) no. The group mass differences follow from the claim's "once body mass is accounted for".
- W1: (i) yes, world:minus only: 47 vs 10. (ii) n/a. (iii) no.

**D-062** (shared denominator, 12 species)
- R: (i) yes: world:minus 149 vs 0, control 176 vs 1. (ii) n/a.
- W0: (i) n/a: WEAK (world:minus 0/200).
  - world:minus was needed. W0 makes the bones proportional to body length, so the indices carry no spurious
    correlation, while R draws them independent of body length.
  - The structure statistic is Pearson's approximation from the three CVs. It assumes uncorrelated numerators, so it
    does not register this.
  - (ii) n/a. (iii) no.
- W1: (i) n/a: WEAK (world:minus 1/200), with near-isometric log slopes of 0.95 and 0.90. (ii) n/a. (iii) no.

**D-067** (shared denominator, rat organs)
- R: (i) yes: world:minus 121 vs 6, control 123 vs 5, noise 64 vs 8. (ii) n/a.
- W0: (i) yes: world:minus 200 vs 15, controls 200 vs 6 and 200 vs 2, shuffle 200 vs 1, noise 64 vs 8. Organ
  elasticity on mass is about 0.4, so both indices share a 1/mass term. (ii) n/a. (iii) no.
- W1: (i) yes, **without world:minus**.
  - Streams: control `heart_permuted_across_rats` 33 vs 3, shuffle 20 vs 2, noise 64 vs 8. Permuting heart breaks
    its scaling with each rat's mass, which is the documented mechanism.
  - world:minus is 6 vs 8, because the allometry is near-isometric (exponents 0.90 and 0.85).
  - (ii) n/a. (iii) no.

**D-068** (shared denominator, 25 populations)
- R: (i) yes: world:minus 200 vs 0, control 200 vs 3, noise 20 vs 0. (ii) n/a.
- W0: (i) yes: world:minus 200 vs 0, controls 175 vs 0 and 197 vs 0, noise 20 vs 0. (ii) n/a. (iii) no.
- W1: (i) yes: world:minus 125 vs 1, controls 124 vs 0 and 121 vs 0, noise 20 vs 0. (ii) n/a. (iii) no.

### Decoys

**D-012** (B-6, pseudoreplication)
- R: (i) yes: world:minus 57 vs 14, control 60 vs 2. (ii) n/a.
- W0: (i) yes, world:minus only: K2_HIGH_SIZE 19 vs 4 (p 0.001), with no fixed rate flag. (ii) n/a. (iii) no. The
  claim defines plot occupancy and the plot-level test. The plot effects are the author's, who named pseudoreplication
  from the claim's form.
- W1: (i) yes: world:minus 53 vs 11, control 50 vs 10 (the fixed twin stays near 5%). (ii) n/a. (iii) no.

**D-047** (B-1, regression to the mean)
- R: (i) yes: world:minus 148 vs 0, control 136 vs 0. (ii) n/a.
- W0: (i) n/a: WEAK (world:minus 0/200).
  - world:minus was needed. The screening-to-entry regression (about 5.9 points) is too small to push the share of
    drops of 10 or more past 0.5 without an effect.
  - A control that keeps the screening reference, like W1's random swap, would also have served. W0's full time
    reversal gave 1/200.
  - (ii) n/a.
  - (iii) no. The author inferred regression to the mean from the claim's form.
- W1: (i) yes, **control only**: the random entry/week-12 swap gives 135 vs 0.
  - The faulty twin measures change from screening, which the swap leaves in place. It scores the screening-to-entry
    drop (regression to the mean) on the swapped patients.
  - world:minus 3 vs 0 has no flag.
  - (ii) n/a. (iii) no.

**D-052** (B-6, significant here, not there)
- R: (i) yes: world:minus 95 vs 13, control 49 vs 6. (ii) n/a.
- W0: (i) yes, by the weakness route, and not attributable.
  - The faulty verdict comes from K2_LOW_POWER, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS, K5_HOLDS_ON_NOISE and
    K5_HOLDS_ON_DEGENERATE.
  - The faulty twin holds in only 8/200 plus samples, because the old group's real gain is also significant.
  - No faulty count is raised: minus 9 vs 11, noise 6 vs 6, controls 0 vs 14 and 0 vs 0.
  - The fixed twin carries none of these flags. They come from the faulty rule's failure in plus, not from the
    documented false support in minus.
  - W0 has equal improvement SDs.
  - (ii) n/a. (iii) no.
- W1: (i) yes, by the same weakness route: plus 2/200; minus 0 vs 6, control 1 vs 11, shuffle 1 vs 10, noise 6 vs 6.
  (ii) n/a. (iii) no.

## 2. Summary: counts per class and arm

| Class | Arm | (i) yes / no / n/a | (ii) yes / no / n/a | (iii) yes / no / n/a |
|---|---|---|---|---|
| B-2 (10) | R | 10 / 0 / 0 | 0 / 0 / 10 | n/a (10) |
| B-2 (10) | W0 | 9 / 0 / 1 | 1 / 0 / 9 | 1 / 9 / 0 |
| B-2 (10) | W1 | 9 / 0 / 1 | 0 / 0 / 10 | 1 / 9 / 0 |
| B-3 (7) | R | 7 / 0 / 0 | 0 / 0 / 7 | n/a (7) |
| B-3 (7) | W0 | 6 / 0 / 1 | 0 / 0 / 7 | 0 / 7 / 0 |
| B-3 (7) | W1 | 6 / 0 / 1 | 0 / 0 / 7 | 0 / 7 / 0 |
| decoys (3) | R | 3 / 0 / 0 | 0 / 0 / 3 | n/a (3) |
| decoys (3) | W0 | 2 / 0 / 1 | 0 / 0 / 3 | 0 / 3 / 0 |
| decoys (3) | W1 | 3 / 0 / 0 | 0 / 0 / 3 | 0 / 3 / 0 |

The (i) n/a cases are D-055 W0/W1, D-062 W0/W1 and D-047 W0. The only (ii) yes is D-035 W0.

## 3. Pair-arms where (i) or (ii) is "no", or (iii) is "yes"

- (i) "no": none.
- (ii) "no": none.
- (iii) "yes":
  - **D-042 W0** and **D-042 W1** (B-2, L1.4). The brief's key meanings and axis ("compound record", "records"), set
    against the claim's "new compounds", led both authors to build duplicate records with identical descriptors.
  - The detection rests entirely on those duplicates.
  - Both logs cite the brief's wording as the reason.

## 4. Other points the designer may want to check

- **Detections that §5 does not count as attributable: D-052 W0 and W1.** The faulty verdict comes from the faulty
  twin's low plus rate (8 and 2 of 200). Its counts are not raised anywhere.
- **Detections through probe:noise only: D-023 W0 and W1.** The declared worlds carried no index correlation.
- **Detections without world:minus:**
  - D-047 W1 rests on its control only.
  - D-067 W1 rests on a control, the shuffle and noise.
- **Borderline (iii) cases, answered no:**
  - D-066 ("rare" in the claim fixes the low prevalence, 8% in both arms).
  - D-035 (balanced accuracy cues imbalance).
  - D-008 (`venous_o2_content` is read only by the faulty body).
- **Ratio cases (D-023, D-062, D-067 W1).** The declared worlds use realistic near-isometric allometry, under which
  the index correlation nearly vanishes. The reference worlds draw numerators independent of the denominator. The
  structure statistics of D-040, D-062 and D-067 (Pearson's CV formula) assume uncorrelated numerators, so they can
  read "structure present" where the error cannot appear. The same gap applies to D-055, whose statistic ignores the
  outcome's persistence.
- **Weak clean passes.** Three fixed twins pass clean but carry K2_LOW_POWER: D-064 W0 (plus 119/200), D-007 W1
  (96/200) and D-035 W1 (29/200).
