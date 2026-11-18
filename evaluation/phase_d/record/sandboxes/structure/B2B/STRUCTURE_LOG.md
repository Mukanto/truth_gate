# Structure log, Phase D, sandbox B2B (15 cases)

## General

- Files written: `cases\<id>\reference.py` for D-003, D-007, D-011, D-013, D-018, D-024, D-034, D-035, D-043, D-049,
  D-058, D-059, D-064, D-065, D-070 (15 reference worlds). Scratch scripts: `work\build.py` (writes the 15 files from
  five family templates), `work\verify.py`, `work\scan.py`, `work\oracle.py`.
- No source was fetched online. Every structure value is the note's `approved_value`; every other size is my own choice
  and is justified below. No URL was visited.
- `minus` uses the same random draws as `plus`, in the same order. Both build the full data, then `minus` replaces only
  the quantity that the claim is about by a null version of it (a label, outcome or series taken from other units, or
  a series driven by an independent copy of the drivers). The structure carriers (counts, clusters, autocorrelation,
  correlations, scales) are therefore the same in both worlds. For the label and outcome cases the feature data
  distribution is identical in both worlds, so the structure statistic is equal in distribution by construction.
- The null label of a case with iid units is the label of a different unit (a derangement, so no unit keeps its own
  value). Fixed class counts and the small fixed-count subject groups use a plain permutation.
- Measured statistics: 200 samples of each world (generators seeded `default_rng([7, world, i])`) through the note's
  `stat` code. All 15 cases meet `|mean - approved| <= 0.2 |approved - null|` in both worlds and the
  3-standard-error equality between worlds. Largest call time 10 ms.
- Effects: set by the generator parameters below, not estimated from samples. The "oracle" values are computed from the
  parameters (population formulas or the exact Mahalanobis distance of the generator's covariance for random parameter
  draws), in `work\oracle.py`. No sample of any world was analysed beyond the note's `stat`, shapes, dtypes, finiteness,
  timing, and a check that each control changes the data.
- Controls: each case has one control with the case id, listing criterion `C`. It permutes the carrier of the claim
  across units within the study's own structure (labels across records, samples, subjects; outcomes across patients;
  cover across sites; the walking sequence across subjects) or, for the series, shifts the series circularly in time by
  a lag of a quarter to three quarters of its length, which keeps its autocorrelation. The transform returns the full
  data dict; it redraws until the data differ.
- Keys the error needs: in no case does the error need a key beyond the brief's keys. The grouping the faulty
  analysis uses is the array axis (subject, site, time order); the duplicated or synthesised rows are made by the
  analysis, not the world.
- Dtypes: every `float` key is float64, every `bool` key is bool.
- Realism choices common to the high-dimensional cases: log-expression = gene mean (8 + 2 z) + K = 8 co-expression
  factors (each loaded by 10% of the genes, loading sd 0.5; about 200 genes per factor) + a sample-level normalisation
  offset (sd 0.15) + gene-level residual (sd about 0.45 times exp(0.25 z)), the residual being measurement error plus
  biological noise. Factor share of gene variance about half. The class or prognostic signal acts on the first
  factors, as a pathway-level difference, so it is carried by hundreds of genes with moderate per-gene effect.

## Family A: imbalanced tabular records (D-003, D-035, D-043, D-049)

Common design: p measured variables in blocks of 4 or 5 with within-block correlation 0.30 (correlated measurements),
variable-specific mean and scale (fixed deterministic pattern), measurement error inside the unit-variance variables;
a Bernoulli(0.10) label; the label shifts a subset of variables by a Mahalanobis distance `DPRIME` (the shift vector is
scaled with the exact block covariance). Minus: label replaced by that of another record.

| id | n x p | structure statistic and source | informative vars, `DPRIME` | oracle effect | measured statistic (plus / minus) |
|---|---|---|---|---|---|
| D-003 | 1000 x 15 | majority/minority ratio, approved 9.0 (note: a 90/10 split proposed as typical; source states none) | 6 of 15, 1.6 | AUC 0.871 | 9.04 +- 0.95 / 9.19 +- 1.05 |
| D-035 | 1500 x 20 | same statistic, approved 9.0 | 8 of 20, 1.7 | AUC 0.885; balanced accuracy at a balanced threshold 0.802 | 8.99 +- 0.78 / 9.16 +- 0.84 |
| D-043 | 400 x 8 | positive share, approved 0.1 (null 0.5) | 4 of 8, 2.8 | AUC 0.976; sensitivity at the prior-based threshold 0.73 | 0.1013 +- 0.0142 / 0.1008 +- 0.0164 |
| D-049 | 600 x 12 | positive share, approved 0.1 | 5 of 12, 2.4 | AUC 0.955; F1 at the prior-based threshold 0.69 | 0.1011 +- 0.0120 / 0.0993 +- 0.0135 |

Other dependencies: within-block correlation 0.30, in both worlds; no cluster or time structure (records are
exchangeable). Binomial variation of the positive count is kept, identical in distribution in both worlds. The positive count is about 100 (D-003), 150 (D-035), 40
(D-043), 60 (D-049). The effects were chosen so that the claimed value is met with a clear margin by a classifier that
handles the imbalance (claimed 0.75 AUC, 0.65 balanced accuracy, 0.60 sensitivity, 0.50 F1) and not by the null.
Note: the shift defines a hidden two-component mixture in the variables in both worlds; in `minus` its membership is
unrelated to the reported label.

## Family B: high-dimensional expression, binary class (D-011, D-013, D-024, D-070)

Structure statistic: genes / samples, from the shape; it equals the approved value in every draw (the note's value is
set by the brief). Class counts are fixed (counts of the setting). The class shifts the means of `KC` of the 8
factors by `DPRIME / sqrt(KC)` each; with 2000 genes the factors are measured almost exactly, so the Mahalanobis
distance in expression space equals `DPRIME` (checked on three parameter draws, within 0.01). Minus: labels randomly
reassigned among samples, class counts kept.

| id | n x genes | class counts (source) | `KC`, `DPRIME` | oracle (from the Mahalanobis distance) | measured statistic (plus / minus) |
|---|---|---|---|---|---|
| D-011 | 72 x 2000 | 25 AML, 47 ALL (AMB02 leukaemia counts, from the note) | 3, 3.4 | AUC 0.992, balanced error 0.045 | 27.7778 (sd 0) / 27.7778 (sd 0) |
| D-013 | 40 x 2000 | 20 / 20 (VAR06 design, from the note) | 3, 2.4 | AUC 0.955, balanced error 0.115 | 50.0000 / 50.0000 |
| D-024 | 62 x 2000 | 40 tumour, 22 normal (AMB02 colon counts, from the note) | 3, 2.8 | AUC 0.976, balanced error 0.081 | 32.2581 / 32.2581 |
| D-070 | 120 x 2000 | 42 relapse (35%; my choice) | 2, 1.4 | AUC 0.838, balanced error 0.242 | 16.6667 / 16.6667 |

Justification of the sizes: the leukaemia classes are known to separate strongly (corrected error about 5% in the
source), so D-011 has `DPRIME` 3.4 (oracle error 4.5%); the colon classes are harder (corrected error about 15% for a
few genes), so D-024 has 2.8; D-013 claims error at most 0.40 and has 2.4 (oracle error 11.5%); a prognostic relapse
signature is modest, D-070 has 1.4 (oracle AUC 0.84 against a claim of 0.70). The oracle values are for a classifier
that knows the structure; a classifier learned from 40 to 120 samples will be below them; the margins to the claimed
values were chosen with that loss in mind.
Other dependencies: gene co-expression (factors), sample offset, gene scale differences, all in both worlds.

## Family C: high-dimensional expression, continuous outcome (D-007, D-064)

Structure statistic: genes / patients from the shape (40.0 and 18.75), equal to the approved value in every draw.

- D-007 (50 x 2000). A prognostic index (fixed mix 0.8/0.6/0.4 of the first 3 factors, unit variance) correlates
  0.70 with the log survival time; survival = 30 months x exp(0.70 z), lognormal (median 30 months, log-sd 0.70, mean
  about 38 months; heavy right tail; observed for every patient). Oracle R-squared 0.49 on the log scale and 0.429 on
  the raw months. Generator parameters: `RHO = 0.70`, `SIG = 0.70`, `MEDIAN = 30`, `GAM = (0.8, 0.6, 0.4)`. The signal is
  on factors, not on single genes: ridge-type fits can use it, a handful of genes is not needed. Minus: survival times
  replaced by those of other patients. Measured: 40.0000 (sd 0) / 40.0000 (sd 0).
- D-064 (80 x 1500, clinical 80 x 8). Clinical covariates standardised, equicorrelated 0.25. Response = 40 + 20 z,
  clipped to [-50, 100] (percent shrinkage, clipping affects about 1% of values), z = sqrt(0.25) x expression index
  (same factor mix) + sqrt(0.12) x clinical index (weights 0.6, 0.4, 0.3, 0, 0, 0.2, -0.2, 0) + noise (share 0.63).
  Oracle correlation 0.61 (R-squared 0.37). Parameters: `R2E = 0.25`, `R2C = 0.12`, `RC = 0.25`. Minus: response
  replaced by that of other patients (so neither expression nor clinical covariates carry information). Measured:
  18.7500 (sd 0) / 18.7500 (sd 0).

## Family D: time series (D-034, D-059)

Structure statistic: mean lag-k autocorrelation of the drivers. The drivers are stationary AR(1) series with unit
variance, persistence differing by driver, innovations correlated across drivers. Series = centre + spread x
(linear response to the drivers of variance share `RSQ`, an AR(1) residual, white measurement error). Minus: the
series is built from an independent copy of the driver paths (same law), with the same residual and white
error, so its variance, autocorrelation and residual dependence are unchanged and the drivers carry no information.
The drivers are returned unchanged in both worlds. No seasonal cycle was put in, because a deterministic cycle common
to drivers and series would make a null series impossible to define.

- D-034 (1500 days x 6 drivers; statistic lag-7, approved 0.6, a proposed typical value). Persistence
  `(0.966, 0.951, 0.935, 0.920, 0.907, 0.893)` (lag-7 values 0.78 to 0.45), innovation correlation 0.3. Level = 3.0 +
  0.9 x (response share `RSQ = 0.75` + AR(1) residual share 0.20 with persistence 0.85 + white share 0.05). Oracle
  R-squared 0.75, oracle RMSE 0.50 sd (claimed at most 0.70 sd). Weights `(0.8, -0.5, 0.6, 0.3, -0.4, 0.2)`, scaled
  with the exact stationary covariance of the drivers. Measured: 0.5936 +- 0.0234 / 0.5949 +- 0.0250.
- D-059 (600 months x 10 variables; statistic lag-1, approved 0.7). Persistence 0.60 to 0.85, innovation correlation
  0.25. Abundance = 2.0 + 0.8 x (response share `RSQ = 0.55` + AR(1) residual share 0.40 with persistence 0.70 + white
  share 0.05); the residual models population carry-over. Oracle R-squared 0.55 (claimed at least 0.30). Weights
  `(0.7, -0.5, 0.6, 0.3, -0.4, 0.2, 0, 0.4, -0.3, 0.2)`. Measured: 0.7114 +- 0.0111 / 0.7107 +- 0.0116.

Control: the series is shifted circularly in time (lag a quarter to three quarters of its length).

## Family E: clustered records (D-018, D-058, D-065)

Structure statistic: mean over variables of the one-way ANOVA intraclass correlation of the note's code.

- D-018 (16 subjects x 60 records x 10 variables; approved 0.3, a proposed share). Subject effect share 0.30 of each
  variable; within subject: AR(1) drift over the records (share 0.20, persistence 0.70), a shared record factor
  (share 0.15, signs alternating by variable), white measurement error (0.35). Half of the subjects are diseased (8 of
  16). Disease acts through the subject effect of 6 of 10 variables: the subject effect of variable j is
  `r_j * (+-1 for disease status) + sqrt(1 - r_j^2) * noise`, with `r = (0.8, 0, 0.8, 0.7, 0, 0, 0.7, 0, 0.7, 0)`,
  so the total between-subject share (and the statistic) is the same with or without the disease link. Oracle
  record-level AUC 0.892 (Mahalanobis distance 1.75), subject-mean level AUC about 1.0. Minus: disease status
  replaced by a random reassignment among the subjects (8 diseased kept); the measurements are identical in
  distribution to plus. Measured: 0.3103 +- 0.0219 / 0.3092 +- 0.0230.
- D-058 (30 subjects x 30 windows x 40 features; approved 0.3, a proposed share). Subject effect, slow within-subject
  drift (AR(1) over windows, persistence 0.90, share 0.40), a shared window factor (0.10), white error (0.37), in 40
  features. Walking comes in bouts (stay probability 0.85) with a subject-specific walking share Beta(2.4, 9.6)
  (mean 0.2), so that adjacent windows are alike in features and in label, as in overlapping activity windows.
  Walking shifts 20 of the features, by a Mahalanobis distance 3.6 in the exact within covariance (oracle error about
  0.027 at walking share 0.2; majority-class error 0.2; claimed at most 0.10). The subject-effect share parameter is
  `ICC = 0.13`: the ANOVA statistic reads higher than the parameter because the persistent drift is partly absorbed by
  the 30-window subject means, so `ICC` was set so that the statistic itself is at 0.3 (0.13 gave 0.29). Minus: each
  subject gets the walking sequence of another subject. Features are identical in distribution to plus. Measured:
  0.2945 +- 0.0100 / 0.2939 +- 0.0099.
- D-065 (40 sites x 20 plots x 6 variables; approved 0.3, a proposed share). Habitat = site effect (share 0.30,
  variables correlated 0.30 across sites with alternating signs) + plot variation (variables correlated 0.25 across
  variables within a plot). Cover (percent, 45 + 18 z, clipped to [0, 100]) = linear response to the habitat (variance
  share `R2 = 0.35`, weights `(0.7, 0.4, 0.5, 0, -0.3, 0.3)` scaled with the exact covariance) + a site-level
  residual (share 0.20, unexplained by habitat) + plot noise (share 0.45). Oracle correlation 0.59 (claimed at least
  0.40). Minus: each site gets the cover values of another site. Measured: 0.2969 +- 0.0247 / 0.2925 +- 0.0250.

## Notes on the briefs and notes

- No case's brief or approved value made a realistic world impossible.
- D-007, D-011, D-013, D-024, D-064, D-070: the statistic (genes / samples) is fixed by the shape; its value is the
  approved one in every draw, with zero spread. The equality check between worlds is then exact.
- D-043 and D-049 have a positive share of 0.1 (null 0.5); the briefs do not say the class is rare, so I made it
  rare, as the notes propose, in all four SAN18-type cases.
- Controls and minus use only the rng passed in; no `np.random` is used.
- Reads: STRUCTURE_AUTHOR_D.md, SOURCES_D.md, the 15 `brief.json` and `NOTE.json`, `pkg\truth_gate\study.py`,
  `pkg\truth_gate\guard.py`, `pkg\truth_gate\sampling.py`, and (by search) `agent_docs\SPEC.md`, `GATE.md`,
  `README_TOOL.md`, `MANIFEST.md`. Truth_Gate was imported for `Study`, `Criterion`, `World`, `Premise`, `Control`
  only; no check was run. No criterion was seen or run.
