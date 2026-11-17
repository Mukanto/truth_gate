# Validity audit of the B-2 and B-3 cases, Phase C

Independent auditor. Part 1 was written before anything in `after_part1/` was opened.

## Part 1: own audit

### Method

* **Inputs read:** `INSTRUCTIONS.md`, `PREREG_PHASE_C.md`, `EXPECTED_FLAGS.json`, `SOURCES_ADDENDUM.md`,
  `SOURCES_PHASE_B.md`, `WORLD_INSTRUCTIONS.md`, `docs/GATE.md`, `RESULTS.json` (pair records of B-2 and B-3),
  every `cases/<id>/` file and every `certs/<id>/` certificate of the 22 B-2/B-3 pairs, and `truth_gate/probes.py`,
  `stats.py` and `sampling.py`. Line numbers below refer to `cases/<id>/fixed.py` unless `faulty.py` is named; the twins
  are identical outside the criterion body (checked with `diff`).
* **Samples.** For every pair I drew the gate's own 200 `minus` samples: `stream_rng(20261105, "world:minus", i)`,
  i = 0..199 (base seed from the certificates' `budget`), from scratch copies of the case files
  (`scratch/stats_run.py`, output `scratch/stats_out.json`). I evaluated copies of `faulty.py` and `fixed.py` whose last
  line returns the statistic together with the original decision. On these samples the holds counts reproduce the
  `world:minus` count of all 44 certificates exactly, so every statistic below is computed on the samples the gate used.
* **Flag threshold.** At n = 200 and the per-bound levels of these certificates (0.005 or 0.00625), a rate flag
  (`K2_HIGH_SIZE`, `HIGH_RATE:*`) needs at least **18/200** holds (`truth_gate.stats.wilson_lower`, `scratch/kmin.py`).
  The criterion's declared alpha is 0.05.
* **Counterfactual (only for pairs whose fixed twin is not clean, `scratch/cf_run.py`):** the faulty twin's `minus`
  rate at the threshold where the fixed twin holds in 5% of the same `minus` samples (its 95th percentile). It is an
  in-sample, descriptive check of whether the error alone would have been flagged under a size-controlled rule.
* **Attribution labels.** As defined in the instructions. I read `case-size` ("the structure is there but the data are
  too small to show it") as: the structure is present and the error measurably moves the statistic, but at the declared
  sizes and effect sizes the movement does not change the decision often enough to be flagged (the pre-registration's
  "error too small in the declared worlds at this size"). Where the detection side and the clean-pass side of one pair
  have different causes, the JSON gives both (`attribution_by_outcome`); the class summary counts those.

### Overview

| id | source, subtype | detected | clean | W2 | R1 | R2 | C1 | fixed clean? | attribution |
|---|---|---|---|---|---|---|---|---|---|
| B2-01 | KAP23 L1.1 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-02 | KAP23 L1.4 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-03 | KAP23 L1.4 | no | yes | yes | yes | n/a | yes | clean | case-size |
| B2-04 | KAP23 L3.1 | no | yes | weak | yes | n/a | yes | clean | case-world |
| B2-05 | KAP23 L3.1 | no | yes | yes (autocorrelation) / weak for this model | partly | n/a | yes | clean | mixed (case-error + case-world) |
| B2-06 | KAP23 L3.2 | no | yes | yes | yes | n/a | yes | clean | case-size |
| B2-07 | KAP23 L3.2 | no | yes | yes | yes | n/a | yes | clean | case-size |
| B2-08 | VAR06 L1.3 | yes | no | yes | yes | no | yes | not clean | case-fixed |
| B2-09 | VAR06 L1.3 | yes | no | yes (small effect) | yes | no | yes | not clean | case-fixed |
| B2-10 | VAR06 L1.3 | yes | no | yes | yes | no | yes | not clean | case-fixed |
| B2-11 | VAR06 L1.3 | yes | no | yes | yes | no | yes | not clean | case-fixed |
| B2-12 | AMB02 L1.3 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-01 | CUR13 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-02 | CUR13 | no | yes | weak | yes | n/a | yes | clean | case-world |
| B3-03 | CUR13 | no | yes | no | yes | n/a | yes | clean | case-world |
| B3-04 | CUR13 | yes | no | weak | yes | no | yes | not clean | case-fixed |
| B3-05 | PEA97 | yes (noise probe only) | yes | weak | yes | yes | yes | clean | tool |
| B3-06 | PEA97 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-08 | ARC81 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-09 | ARC81 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-11 | KRO93 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-12 | KRO93 | yes | no | no | yes | no | yes | not clean | mixed (case-fixed + case-world) |

Counts are holds out of 200 from the certificates (`certs/<id>/<twin>.json`, `components[0].counts`) unless stated.
"zeros" is 0/200 with 200 abstentions in every certificate (all-zero labels or zero variance return `None`).

---

### B-2: procedure-level leakage

#### B2-01 (KAP23, L1.1 no test set). Detected yes, clean pass yes.

* **W1.** An apparent (in-sample) AUC rewards a 31-parameter logistic fit for fitting noise; it inflates when the model
  has many parameters per onset, even if the indicators carry no information.
* **W2: yes.** `minus` (L28-42, L50-52) draws onsets from an unrelated panel; the fit still has 30 indicators. Onsets
  per `minus` draw: mean 47.1 (sd 6.4), i.e. 1.6 onsets per indicator. Faulty statistic (apparent AUC) in `minus`: mean
  0.797, 5th percentile 0.736, against the threshold 0.75; fixed CV AUC mean 0.632, 95th percentile 0.728.
  (200 gate `minus` samples, seeds as in Method.)
* **W3.** 896 country-years x 30 indicators. Source (CASE.md §2): "test set of 896 rows with 19 positives"; designer
  line: "country-years 896/896 = 1.0; indicators 30/90 = 0.33". The world has about 47 onsets per 896 (5%) against
  19 in the source test set, and a third of the source's indicators; the inflation is large anyway.
* **R1: yes.** `faulty.py` L126 `score = fit_predict(X, y, X)` against the 5-fold loop of `fixed.py` L126-130; same
  classifier, AUC routine and threshold. The guard lines differ (L80) but never bind here (at least 37 onsets).
* **R2: yes.** Faulty against fixed: `minus` 178 vs 5 (`K2_HIGH_SIZE`), control `permute_onset_across_country_years`
  47 vs 0, control `permute_onset_histories_across_countries` 186 vs 6.
* **C1: yes.** Stratified 5-fold CV with pooled held-out scores (L82-90, L126-131).
* **C2.** Fixed: `minus` 5, controls 0 and 6, noise 0, zeros 0 (200 abstentions), `plus` 179. **Clean.**
* **C3.** n/a. Caveat: the folds are random over rows, not grouped by country (CASE.md §7). In `minus` the fixed AUC is
  centred at 0.63, not 0.5: the country-level indicator levels (L19) and onsets clustered by country leak through
  row-level folds. The threshold 0.75 absorbs this here.
* **Attribution: tool.** Adequate structure, faithful single-difference error, clean fixed twin; the gate flagged
  `minus` and both controls.

#### B2-02 (KAP23, L1.4 oversampling before the split). Detected yes, clean pass yes.

* **W1.** Copying minority rows before the split puts exact copies of training rows into the held-out folds, and the
  fit scores those copies in the direction of their training label.
* **W2: yes.** The copies come from the criterion's own procedure; the world supplies the imbalance (L7, prevalence
  0.22). Minority share in `minus`: 0.221. Share of held-out minority rows in the faulty CV that have an exact copy in
  the training folds (replicating `faulty.py` L98-99 with its seed 20260202): mean 0.943. Faulty sensitivity in
  `minus`: mean 0.555 (95th percentile 0.609), fixed 0.437; threshold 0.60.
* **W3.** 400 x 12; source states none.
* **R1: yes.** `faulty.py` L98-106 oversamples the whole data, then folds; `fixed.py` L98-106 oversamples each
  training fold. Same classifier, guard, threshold.
* **R2: yes.** `minus` 25 vs 0, control `permute_outcome` 29 vs 1.
* **C1: yes.** Oversampling inside the training folds, scoring on untouched held-out rows (L103-106).
* **C2.** Fixed: `minus` 0, control 1, noise 0, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: tool.** The error lifts `minus` sensitivity by 0.12 and the gate flagged it.

#### B2-03 (KAP23, L1.4 oversampling before the split). Detected no, clean pass yes.

* **W1.** As B2-02: copies of training rows in the held-out folds.
* **W2: yes.** Defect rate 15% (L21); minority share in `minus` 0.150; held-out minority rows with a training copy in
  the faulty CV (seed 20260203): mean 0.993. The error acts: faulty balanced accuracy in `minus` mean 0.597 (sd 0.021,
  95th percentile 0.629) against the fixed 0.502 (sd 0.027), threshold 0.65.
* **W3.** 1000 units x 50 features; source states none.
* **R1: yes.** `faulty.py` L94-103 against `fixed.py` L94-103, the same single change as B2-02. Remark: the
  classifier is a ridge logistic regression; CASE.md §7 records that the brief note asked for a classifier able to use
  exact copies (1-NN or a flexible fit) and that 5-NN was dropped because the fixed twin then failed in `plus`.
* **R2.** n/a. Faulty: `minus` 2, control 2, noise 0, `plus` 200.
* **C1: yes.** As B2-02.
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: case-size.** The error raises `minus` balanced accuracy by 0.095, but with a ridge logistic fit on
  1000 x 50 it stays 2.5 sd below the claim's 0.65; the faulty twin held 2/200, so there was nothing for the gate to
  flag.

#### B2-04 (KAP23, L3.1 shuffled folds on a time series). Detected no, clean pass yes.

* **W1.** Shuffled folds let a held-out day be predicted from its temporal neighbours in the training folds; that helps
  only if the labels are serially dependent and neighbouring days are close in indicator space.
* **W2: weak.** `minus` drives `rises` from an independent copy of the indicator process (L33), so the labels keep
  only the serial dependence of that copy. Lag-1 autocorrelation of `rises` in `minus`: mean 0.086 (5th-95th
  percentile 0.010-0.174); of the indicators: mean 0.54. Faulty accuracy in `minus`: mean 0.512 (95th percentile
  0.554) against the fixed 0.499; threshold 0.58.
* **W3.** 500 days x 10 indicators; source states none.
* **R1: yes.** `faulty.py` L84 `fold = rng.permutation(n) % K` against the forward blocks of `fixed.py` L84-97; same
  15-NN classifier and accuracy.
* **R2.** n/a. Faulty: `minus` 1, control `shift_rises_in_time` 1, noise 0, `plus` 188.
* **C1: yes.** Forward evaluation on later blocks only (L88-94).
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 166. **Clean.**
* **C3.** n/a.
* **Attribution: case-world.** A flexible classifier is used, but the labels carry almost no serial dependence
  (lag-1 0.086), so shuffling leaks only +0.013 accuracy.

#### B2-05 (KAP23, L3.1 shuffled folds on a time series). Detected no, clean pass yes.

* **W1.** Shuffled folds let a held-out week borrow from neighbouring training weeks; with a linear regression on
  non-informative drivers this works only through a spurious driver-demand relation shared by interleaved weeks, which
  needs strong persistence of drivers and demand.
* **W2: yes for serial dependence, weak for this model.** `minus` (L40-46): demand from an independent realisation
  of the drivers plus AR(1) noise (L12, rho 0.5). Lag-1 autocorrelation in `minus`: demand 0.49, drivers 0.35 (mean
  over columns); no trend or season. Faulty R-squared in `minus`: mean -0.024 (95th percentile 0.010), fixed -0.123;
  threshold 0.30. The faulty value is what an unbiased CV gives for 9 parameters on 320 rows (about -0.03).
* **W3.** 400 weeks x 8 drivers; source states none.
* **R1: partly.** The shuffled folds (`faulty.py` L86) are the only difference, but an ordinary least-squares fit on
  drivers unrelated to demand has no route to the neighbouring weeks, so the documented "data from the future" cannot
  act. CASE.md §7: "shuffled folds can hardly leak"; "Linear regression is what the note names."
* **R2.** n/a. Faulty: `minus` 0, control 0, noise 0, `plus` 200.
* **C1: yes.** Chronological blocks (L86-103).
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 199. **Clean.**
* **C3.** n/a.
* **Attribution: mixed (case-error + case-world).** The model cannot exploit the leak, and the persistence is too weak
  for spurious regression to substitute; the faulty statistic is unbiased in `minus`.

#### B2-06 (KAP23, L3.2 patches of one patient on both sides). Detected no, clean pass yes.

* **W1.** Patch-level folds put patches of one patient on both sides; patient-specific feature levels and the
  patient's shared label let the fit score held-out patches of known patients.
* **W2: yes.** Patient shift sd 0.8 and slide stain (L13, L21-22) against patch noise sd 1. Within-patient intraclass
  correlation of the features in `minus`: mean 0.399 (one-way ANOVA ICC, mean over 20 features). The error acts:
  faulty AUC in `minus` mean 0.643 (95th percentile 0.703), fixed 0.499; threshold 0.75.
* **W3.** 80 patients x 10 patches x 20 features; source states none (the setting named in CASE.md §2 is
  histopathology, Oner et al. 2020).
* **R1: yes.** `faulty.py` L108 folds over patch rows against `fixed.py` L108-109 folds over patients; same guard
  (repaired), classifier, AUC and threshold.
* **R2.** n/a. Faulty: `minus` 0, control 0, noise 0, `plus` 200.
* **C1: yes.** Patient-level folds.
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 197. **Clean.**
* **C3.** n/a.
* **Attribution: case-size.** The leak is real (+0.14 AUC), but with 20 features, 10 patches per patient and a ridge
  logistic fit it does not reach 0.75; image settings have many more features per patch.

#### B2-07 (KAP23, L3.2 sessions of one participant on both sides). Detected no, clean pass yes.

* **W1.** Session-level folds put sessions of one participant on both sides; stable participant-level parts of the
  measurements and of the score let the fit predict held-out sessions of known participants.
* **W2: yes.** Trait sd 0.8 against state 0.6 (L8-9), participant level share 0.25 of the score (L13). ICC in
  `minus`: measurements 0.547, score 0.476. The error acts: faulty r in `minus` mean 0.115 (95th percentile 0.318),
  fixed -0.042; threshold 0.30.
* **W3.** 40 participants x 4 sessions x 10 measurements; source states none.
* **R1: yes.** `faulty.py` L86 folds over rows against `fixed.py` L86-87 folds over participants.
* **R2.** n/a. Faulty: `minus` 12, control 8, noise 0, `plus` 200; the gate needs 18/200 for a flag.
* **C1: yes.** Participant-level folds.
* **C2.** Fixed: `minus` 2, control 2, noise 0, zeros 0 (200 abstentions), `plus` 198. **Clean.**
* **C3.** n/a.
* **Attribution: case-size.** The faulty twin holds 6% in `minus`, near the declared 5%; the leak through an OLS fit
  with 10 measurements is too small to be flagged at n = 200 (12 against the 18 needed).

#### B2-08 (VAR06, L1.3 best CV accuracy over a tuning grid). Detected yes, clean pass no.

* **W1.** Reporting the best cross-validated performance over a grid of tuning values selects on the estimate's own
  noise, which inflates it when the class signal is null.
* **W2: yes.** Null genes in `minus` (L40, shift 0), 20 shrinkage values (L67). Faulty best CV accuracy in `minus`:
  mean 0.563 (sd 0.090), fixed nested CV 0.508 (sd 0.101). Optimism 0.055, about half the source's (next item).
* **W3.** 40 samples x 1000 genes. Source line (CASE.md §2): "shrunken centroid, null data, mean CV error 37.8%
  against a true error of 50.0%"; designer line "samples 40/40 = 1.0; genes 1000/6000 = 0.17". Here the faulty CV error
  is 43.7% on average, against 37.8% in the source.
* **R1: yes.** `faulty.py` L104-106 (max over the grid of one CV) against the nested loop `fixed.py` L104-113. The
  guard lines differ (L55) but cannot bind with 20 per class.
* **R2: no.** Both twins carry the same expected flags (`K2_HIGH_SIZE`, `HIGH_RATE:control:permute_class_across_samples`,
  `HIGH_RATE:probe:noise`): `minus` 86 vs 47, control 94 vs 48, noise 130 vs 65. The fixed twin alone would have been
  scored as a detection.
* **C1: yes.** Nested CV, inner loop tunes delta, outer loop estimates (L104-113).
* **C2.** Fixed: `minus` 47, control 48, noise 65, zeros 0 (200 abstentions), `plus` 200. **Not clean.**
* **C3.** The rule compares a point estimate with 0.60 at n = 40. The fixed accuracy in `minus` has mean 0.508 and sd
  0.101 and exceeds 0.60 in 47/200; even a binomial count at p = 0.5 exceeds 24/40 with probability 0.13. Under the
  noise probe the labels are Bernoulli(0.5) and unbalanced, and the class priors let accuracy pass 0.60 by predicting
  the majority (CASE.md §5). The correction is right; the claim's threshold lies inside the null distribution at this n.
  Counterfactual: at the fixed twin's 95th percentile (0.651) the faulty twin holds 27/200, which would be flagged.
* **Attribution: case-fixed.** The fixed twin is flagged the same way, so neither the detection nor the failed clean
  pass separates the error.

#### B2-09 (VAR06, L1.3 best CV AUC over a tuning grid). Detected yes, clean pass no.

* **W1.** As B2-08.
* **W2: yes, with a small effect.** 20 shrinkage values (L83), no responder difference in `minus` (L38). Faulty best
  CV AUC in `minus`: mean 0.507 (sd 0.120), fixed nested 0.476 (sd 0.127). The optimism over the nested estimate is
  0.031, and the nested AUC itself sits below 0.5 under the null.
* **W3.** 40 patients x 1000 genes; as B2-08 (the AUC variant is the brief's extension, CASE.md §7).
* **R1: yes.** `faulty.py` L123-124 against `fixed.py` L123-131; the guard lines differ but cannot bind (16/24).
* **R2: no.** Same expected flags on both: `minus` 26 vs 18, control `permute_responder` 23 vs 20, noise 67 vs 25.
* **C1: yes.** Nested CV.
* **C2.** Fixed: `minus` 18, control 20, noise 25, zeros 0 (200 abstentions), `plus` 199. **Not clean** (18 is exactly
  the flag threshold).
* **C3.** The threshold 0.65 is 1.6 null-sd above 0.5 for a fixed score (sd 0.094 for 16 vs 24; P = 0.055), and nested
  CV adds variance (sd 0.127), so the fixed twin holds 9% in `minus`. Counterfactual: at the fixed twin's 95th
  percentile (0.690) the faulty twin holds 10/200, not flagged: the error is also small here.
* **Attribution: case-fixed** (with a small error effect).

#### B2-10 (VAR06, L1.3 best LOO accuracy over a (C, gamma) grid). Detected yes, clean pass no.

* **W1.** As B2-08.
* **W2: yes.** 5 x 5 grid (L81-82), genes reselected inside every fit, no class difference in `minus` (L35-37). Faulty
  best LOO accuracy in `minus`: mean 0.582 (sd 0.118), fixed 0.489 (sd 0.106). Optimism 0.093.
* **W3.** 40 x 1000; CASE.md §2 gives the source's grid "2^-5 to 2^15, 2^-15 to 2^3" with leave-one-out tuning; kernel
  ridge replaces the SVM, as the note allows (CASE.md §4).
* **R1: yes.** `faulty.py` L121 against `fixed.py` L121-129 (and the guard, which cannot bind).
* **R2: no.** Same expected flags on both: `minus` 89 vs 31, control 85 vs 41, noise 122 vs 50.
* **C1: yes.** Nested: outer 10-fold, inner leave-one-out tuning (L121-129).
* **C2.** Fixed: `minus` 31, control 41, noise 50, zeros 0 (200 abstentions), `plus` 177. **Not clean.**
* **C3.** As B2-08 (point estimate against 0.60 at n = 40; sd 0.106). Counterfactual: at the fixed twin's 95th
  percentile (0.70) the faulty twin holds 28/200, which would be flagged.
* **Attribution: case-fixed.**

#### B2-11 (VAR06, L1.3 best CV balanced accuracy over the panel size). Detected yes, clean pass no.

* **W1.** As B2-08 (the tuning parameter is the number of top genes).
* **W2: yes.** Grid k = 1..100 (L72), no group difference in `minus` (L27-29). Faulty best CV balanced accuracy in
  `minus`: mean 0.620 (sd 0.096), fixed 0.514 (sd 0.110). Optimism 0.106.
* **W3.** 40 x 1000; as B2-08.
* **R1: yes.** `faulty.py` L103-104 against `fixed.py` L103-110; gene ranking is inside every fold in both.
* **R2: no.** Same expected flags on both: `minus` 132 vs 46, control 110 vs 44, shuffle 102 vs 46, noise 122 vs 39.
* **C1: yes.** Nested CV.
* **C2.** Fixed: `minus` 46, control 44, shuffle 46, noise 39, zeros 0 (200 abstentions), `plus` 199. **Not clean.**
* **C3.** As B2-08: CASE.md §5 already reports mean 0.506, sd 0.106, P(>= 0.6) = 0.21 in `minus`. Counterfactual: at
  the fixed twin's 95th percentile (0.675) the faulty twin holds 48/200, which would be flagged.
* **Attribution: case-fixed.**

#### B2-12 (AMB02, L1.3 genes chosen on all tissues). Detected yes, clean pass yes.

* **W1.** Choosing the 3 genes with the largest |t| on all tissues before CV selects genes that correlate with the
  labels by chance among many null genes, the held-out tissues included.
* **W2: yes.** 1000 null genes in `minus` (L28-30). Faulty CV accuracy in `minus`: mean 0.744, fixed 0.519; threshold
  0.70.
* **W3.** 62 x 1000. Designer line: "source states none (as read; the author's 62 x 2000 from memory is unverified)".
* **R1: yes.** `faulty.py` L83 ranks genes once on all tissues; `fixed.py` L88 ranks inside each fold.
* **R2: yes.** `minus` 165 vs 5, control 173 vs 6, shuffle 166 vs 5, noise 188 vs 6.
* **C1: yes.** Selection repeated inside every training fold.
* **C2.** Fixed: `minus` 5, control 6, shuffle 5, noise 6, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: tool.**

### B-3: coupling by construction

#### B3-01 (CUR13, ratio with a non-zero intercept). Detected yes, clean pass yes.

* **W1.** Dividing heart weight by body mass misrepresents the adjusted effect when the heart-weight line has a non-zero
  intercept and the groups differ in body mass.
* **W2: yes.** Intercept 240 mg (L20) and treated animals 25 g lighter in both worlds (L18). In `minus`: body-mass
  difference treated minus untreated -25.2 g; correlation of the quotient with treatment 0.122 (sd 0.135); faulty t
  mean 0.86 against the fixed 0.08.
* **W3.** 48 animals; source states none.
* **R1: yes.** `faulty.py` L84-89 (OLS of the quotient on treatment) against `fixed.py` L84-89 (OLS on treatment and
  body mass); same t routine.
* **R2: yes.** `minus` 33 vs 13 (only the faulty twin gets `K2_HIGH_SIZE`); control 10 vs 10, noise 3 vs 10.
* **C1: yes.** Analysis of covariance.
* **C2.** Fixed: `minus` 13, control 10, noise 10, zeros 0 (200 abstentions), `plus` 188. **Clean** (13 < 18).
* **C3.** n/a.
* **Attribution: tool.**

#### B3-02 (CUR13, albumin/creatinine quotient against age). Detected no, clean pass yes.

* **W1.** Correlating age with the albumin/creatinine quotient carries the age dependence of creatinine into the
  quotient when albumin is not proportional to creatinine.
* **W2: weak.** Albumin follows creatinine with exponent 0.7 (L12, L30), creatinine falls with age (L9, L24).
  In `minus`: correlation of creatinine with age -0.40; faulty r(age, quotient) mean 0.071 (sd 0.035, 95th percentile
  0.125), fixed partial r 0.001; threshold 0.15. The induced correlation is about half the threshold and does not grow
  with n.
* **W3.** 800 participants; source states none.
* **R1: yes.** `faulty.py` L84 `partial_r(age, quotient, [])` against `fixed.py` L80 `partial_r(alb, age, [cre])`.
* **R2.** n/a. Faulty: `minus` 2, control 0, noise 0, `plus` 200.
* **C1: yes.** Partial correlation given creatinine (regression with the denominator).
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: case-world.** The structure exists but induces r of about 0.07 against a 0.15 claim.

#### B3-03 (CUR13, LV-mass/BSA quotient as the only predictor). Detected no, clean pass yes.

* **W1.** The LV-mass/BSA quotient keeps part of the BSA information when LV mass is not proportional to BSA, so it can
  explain systolic pressure through BSA.
* **W2: no.** In `minus` systolic pressure depends on BSA by 3 mmHg per SD against a total sd of about 19 (L11-14):
  R-squared of pressure on BSA mean 0.027, below the 0.05 threshold even for a perfect proxy of BSA. LV mass is close to
  proportional to BSA (fitted intercept -24 g), and the quotient correlates 0.066 with BSA. Faulty R-squared mean 0.003
  (95th percentile 0.012).
* **W3.** 300 patients; source states none.
* **R1: yes.** `faulty.py` L77-85 against `fixed.py` L77-84.
* **R2.** n/a. Faulty: `minus` 0, both controls 0, noise 0, `plus` 200.
* **C1: yes.** R-squared gain over BSA.
* **C2.** Fixed: `minus` 0, controls 0 and 0, noise 0, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: case-world.**

#### B3-04 (CUR13, organ weights both divided by body mass). Detected yes, clean pass no.

* **W1.** Two organ weights divided by the same body mass share a 1/body-mass term when they are not proportional to
  body mass, which adds a spurious slope between the quotients.
* **W2: weak.** Intercepts 0.05 g (liver, 4% of its mean) and 0.10 g (kidney, 26%), body-mass CV 11% (L8-11). In
  `minus`: correlation of the two quotients 0.018; faulty slope mean 0.059 (sd 0.288), fixed coefficient -0.023 (sd
  0.290); threshold 0.25.
* **W3.** 150 mice; source states none.
* **R1: yes.** `faulty.py` L60-66 against `fixed.py` L60-61.
* **R2: no.** On the declared streams both twins are flagged the same way (`K2_HIGH_SIZE`, `HIGH_RATE:control:…`):
  `minus` 46 vs 32, control 53 vs 42. The faulty twin's extra flag is the noise probe (65 vs 0), where quotients of
  zero-mean noise are heavy-tailed; it is not the intercept mechanism of the source.
* **C1: yes.** Coefficient of kidney weight with body mass as covariate.
* **C2.** Fixed: `minus` 32, control 42, noise 0, zeros 0 (200 abstentions), `plus` 200. **Not clean.**
* **C3.** The rule is a point estimate against 0.25 while its standard error is 0.29 (sd over `minus` samples; CASE.md
  §7 says "about 0.3"), so the fixed twin holds 16% in `minus`. Counterfactual: at the fixed twin's 95th percentile
  (0.45) the faulty twin holds 16/200, not flagged: the ratio's own bias here is small.
* **Attribution: case-fixed** (with weak structure).

#### B3-05 (PEA97, femur/humerus against tibia/humerus). Detected yes (noise probe only), clean pass yes.

* **W1.** Two lengths divided by the same humerus length share a 1/humerus term, which correlates the indices when
  the lengths are not proportional to the humerus.
* **W2: weak.** In `minus` femur and tibia scale with the humerus (L12-13; fitted intercepts 106 mm and 62 mm), so the
  quotient removes most of the shared size. Faulty r of the indices in `minus`: mean 0.115 (95th percentile 0.169)
  against the threshold 0.3 and against Pearson's "about 0.4 to 0.5 ... had the bones been sorted absolutely at
  random" (CASE.md §2).
* **W3.** 1000 skeletons; designer line "skeletons 1000/'some thousand' = about 1.0".
* **R1: yes.** `faulty.py` L64-70 against `fixed.py` L64-65.
* **R2: yes**, through the noise probe only: noise 67 vs 0; `minus` 0 vs 0, control 0 vs 0. On i.i.d. N(0, 1) data the
  shared denominator dominates both quotients; the declared worlds never showed the error.
* **C1: yes.** Partial correlation given the humerus.
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: tool.** The gate's own noise probe made the detection; the declared worlds would have missed it
  (W2 weak). The probe responds to any correlation of two quotients with a shared denominator, whether or not the
  source's condition holds in the setting.

#### B3-06 (PEA97, observers' errors divided by the true value). Detected yes, clean pass yes.

* **W1.** Dividing each observer's error by the common true value adds a shared 1/true-value term (from the observers'
  non-zero offsets) to every relative error.
* **W2: yes.** Offsets from range compression and bias (L9-10): fitted estimate at true value 0 averages 7.9. Faulty
  mean pairwise r of relative errors in `minus`: mean 0.142 (95th percentile 0.331), fixed 0.000; threshold 0.2.
* **W3.** 200 trials x 3 observers; designer line "observers 3/3 = 1.0; trials: source states none".
* **R1: yes.** `faulty.py` L70-78 against `fixed.py` L70-74.
* **R2: yes.** `minus` 61 vs 0, control 62 vs 0, noise 38 vs 0.
* **C1: yes.** Partial correlation given the true value.
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: tool.**

#### B3-08 (ARC81, fall correlated with its own baseline reading). Detected yes, clean pass yes.

* **W1.** The fall (first reading minus week 12) contains the first reading's error, so it correlates with that same
  reading without any true dependence.
* **W2: yes.** Visit and reading error sd 3 and 6 against usual pressure sd 12 (L15-27). In `minus`:
  r(fall, first reading) mean 0.265 (95th percentile 0.416); threshold 0.3.
* **W3.** 120 patients; source states none.
* **R1: yes.** `faulty.py` L74 uses `first`; `fixed.py` L74 uses `second`.
* **R2: yes.** `minus` 72 vs 0, control 200 vs 0, noise 200 vs 0. The control permutes `sbp_baseline_second`, which the
  faulty criterion does not read (that is the error itself), and on noise r(first - week12, first) is 0.71.
* **C1: yes.** An independent baseline reading.
* **C2.** Fixed: `minus` 0, control 0, noise 0, zeros 0 (200 abstentions), `plus` 188. **Clean.**
* **C3.** n/a. Note: the second reading still shares the visit term (L17, L25-26), so the fixed r in `minus` has mean
  0.060; harmless at 0.3.
* **Attribution: tool.**

#### B3-09 (ARC81, delivery against uptake calculated from the same cardiac output). Detected yes, clean pass yes.

* **W1.** Calculated uptake and delivery both contain the measured cardiac output, whose error correlates them.
* **W2: yes.** 10% thermodilution error (L15). In `minus`: r(delivery, calculated uptake) mean 0.165 (95th percentile
  0.388), r(delivery, expired-gas uptake) 0.008; threshold 0.3.
* **W3.** 60 patients; source states none.
* **R1: yes.** `faulty.py` L68-69 against `fixed.py` L68.
* **R2: yes.** `minus` 34 vs 4, control 200 vs 3 (the control permutes a key the faulty twin does not read), noise
  199 vs 2.
* **C1: yes.** Uptake measured independently.
* **C2.** Fixed: `minus` 4, control 3, noise 2, zeros 0 (200 abstentions), `plus` 200. **Clean.**
* **C3.** n/a.
* **Attribution: tool.**

#### B3-11 (KRO93, gene A/C against gene B/C). Detected yes, clean pass yes.

* **W1.** Two expression signals divided by the same gene C signal share a 1/C term when they are not proportional to
  C.
* **W2: yes.** Intercepts 20 + 30 and 30 + 40 on gene C (L19-21; fitted 50 and 70). In `minus`: correlation of the
  quotients 0.61; faulty R-squared mean 0.376 (5th percentile 0.220); threshold 0.05.
* **W3.** 96 samples; source states none.
* **R1: yes.** `faulty.py` L63-72 against `fixed.py` L63-70.
* **R2: yes.** `minus` 200 vs 0, control 200 vs 0, noise 155 vs 9.
* **C1: yes.** R-squared gain over gene C.
* **C2.** Fixed: `minus` 0, control 0, noise 9, zeros 0 (200 abstentions), `plus` 182. **Clean.**
* **C3.** n/a.
* **Attribution: tool.**

#### B3-12 (KRO93, admissions per population against time). Detected yes, clean pass no.

* **W1.** A per-population rate as the dependent variable misrepresents the trend at fixed population only when
  admissions are not proportional to population (a non-zero intercept), so the rate also moves with population.
* **W2: no.** `admissions = 8.0 * population + trend * time + season + waves + noise` (L31): proportional, no
  intercept, so the rate has no population-driven trend in `minus`. The worlds instead carry autocorrelated waves
  (L29, AR(1) 0.6, sd 55): lag-1 autocorrelation of the residuals in `minus` 0.66 for the fixed model and 0.67 for the
  faulty one. Faulty t mean -0.03, fixed 0.02.
* **W3.** 120 months; source states none.
* **R1: yes.** `faulty.py` L97-102 (OLS of the rate on time) against `fixed.py` L97-98 (OLS on time and population).
* **R2: no.** Both twins get `K2_HIGH_SIZE`: `minus` 25 vs 23; controls 10 vs 11 and 0 vs 0; noise 11 vs 4.
* **C1: yes.** Regression with the denominator as covariate.
* **C2.** Fixed: `minus` 23, controls 11 and 0, noise 4, zeros 0 (200 abstentions), `plus` 192. **Not clean.**
* **C3.** The claim's ordinary one-sided t test assumes independent months; with residual lag-1 autocorrelation 0.66
  it holds 11.5% in `minus` (CASE.md §7 says the same). Counterfactual: at the fixed twin's 95th percentile the faulty
  twin holds 10/200: the error adds nothing in these worlds.
* **Attribution: mixed (case-fixed + case-world).** The failed clean pass is case-fixed; the detection is not the
  error's, because the worlds lack the intercept and both twins share the oversized test.

---

### Class summary (post hoc; it does not change the pre-registered result)

Per-outcome attributions (from `attribution_by_outcome` in the JSON).

**B-2 (12 pairs: 7 detected, 8 clean passes, as `RESULTS.json`).**

| outcome | pairs | attribution counts |
|---|---|---|
| misses (5) | B2-03, B2-04, B2-05, B2-06, B2-07 | case-size 3 (B2-03, B2-06, B2-07); case-world 1 (B2-04); mixed 1 (B2-05: case-error + case-world); tool 0 |
| failed clean passes (4) | B2-08, B2-09, B2-10, B2-11 | case-fixed 4 |
| detections not attributable to the error (4) | B2-08, B2-09, B2-10, B2-11 | case-fixed 4 |
| attributed to the tool | B2-01, B2-02, B2-12 | tool 3 |

Without every pair attributed to the case (B2-03 to B2-11 left out): 3 pairs, **detections 3/3, clean passes 3/3**
(one-sided 95% Wilson lower bound 0.53 for 3/3; fewer than the 10 pairs a class verdict needs, so no verdict).
Counterfactual remark: under a size-controlled threshold the faulty twins of B2-08, B2-10 and B2-11 would still be
flagged on `minus` (27, 28 and 48 of 200); that of B2-09 would not (10/200).

**B-3 (10 pairs: 8 detected, 8 clean passes).**

| outcome | pairs | attribution counts |
|---|---|---|
| misses (2) | B3-02, B3-03 | case-world 2 |
| failed clean passes (2) | B3-04, B3-12 | case-fixed 2 |
| detections not attributable to the error (2) | B3-04, B3-12 | case-fixed 1 (B3-04, structure weak); mixed 1 (B3-12: case-fixed + case-world) |
| attributed to the tool | B3-01, B3-05, B3-06, B3-08, B3-09, B3-11 | tool 6 (B3-05 detected only through the noise probe) |

Without every pair attributed to the case (B3-02, B3-03, B3-04, B3-12 left out): 6 pairs, **detections 6/6, clean
passes 6/6** (Wilson lower bound 0.69; fewer than 10 pairs, no verdict).

**Reading.** In this audit no miss and no failed clean pass of B-2 or B-3 is due to the gate's behaviour. Each miss
comes from a faulty criterion that, in the declared worlds, held where the claim is false at about the nominal rate
(at most 12/200), because the worlds carry the structure weakly or the error's effect stays below the claim's threshold
at these sizes. Each failed clean pass comes from a fixed criterion whose decision rule (a point estimate against a
threshold at small n, or an ordinary t test on autocorrelated months) is not size-controlled in the declared worlds;
those same pairs are the detections that do not come from the error. Two qualifiers: B3-05's detection rests on the
generic noise probe alone, and the remaining sets (3 and 6 pairs) are small.

---

## Part 2: comparison with the report (written after opening `after_part1/`)

Read: `after_part1/REPORT.md` (sections 7.1, 7.3, 7.4 and 9 for these pairs) and `after_part1/POSTRUN_AUDIT.md`
(B-2 and B-3 entries and summary). Part 1 above was not changed. One extra computation was made for Part 2
(`scratch/season_check.py`, item W4 below); every other number is from Part 1.

### Pairs where my attribution or explanation differs

| pair | report (REPORT §7, POSTRUN_AUDIT) | this audit | better supported |
|---|---|---|---|
| B2-03 | §7.1: "error too small"; what the error exploits "was not present in the declared worlds strongly enough"; the ridge logistic model "lets little leak". POSTRUN: "at this size the copies carry almost no weight". | case-size: the copies are there (99.3% of held-out minority rows have a training copy) and they lift `minus` balanced accuracy from 0.502 to 0.597; the claim's 0.65 lies above the faulty twin's 95th percentile (0.629). | This audit. The leak is moderate, not negligible; the miss comes from where the claim's threshold sits relative to the inflated statistic. The report is right that the model choice limits the leak. |
| B2-06 | §7.1: worlds not strong enough. Not in the list of model-dependent misses. POSTRUN: "the declared offsets (SD 0.8 on 20 features) gave no lift". | case-size: within-patient ICC 0.40; the leak lifts `minus` AUC from 0.499 to 0.643 (95th percentile 0.703 against 0.75). | This audit: "no lift" is contradicted by the gate's own `minus` samples. B2-06 uses the same ridge logistic regression as B2-03 and belongs with the model-dependent misses that §7.1 lists. |
| B2-07 | §7.1: worlds, and OLS "lets little leak". | case-size: ICC 0.55 (measurements) and 0.48 (score); faulty r mean 0.115 against fixed -0.042; 12/200 against the 18 the gate needs. | Same cause in substance. "Little leak" understates it: the faulty twin holds six times as often as the fixed twin, but stays near the declared 5%. |
| B2-04 | §7.1: worlds. POSTRUN "needed": indicators and next-day outcome sharing a slow common component. | case-world: label lag-1 autocorrelation 0.086. | Same attribution. The suggested world is doubtful under the fixed `minus` rule (WORLD_INSTRUCTIONS rule 3): a slow component shared by the indicators and the outcome would carry over to later days, so the indicators would predict the outcome. The leak path the rule allows is persistence of the labels alone, with uninformative but persistent indicators. |
| B2-05 | §7.1: worlds and the OLS model. | mixed (case-error + case-world); faulty R-squared in `minus` -0.024, the value of an unbiased CV. | Agree. |
| B2-08, B2-10, B2-11 | §7.3: threshold without a test at n = 40; "their detections stand". POSTRUN (i): "yes, qualified". §9: under a strict reading they count as detected without the error. | R2 no (the fixed twin carries the same expected flags), attribution case-fixed. Counterfactual: under a size-controlled threshold the faulty twin would still be flagged in `minus` (27, 28, 48 of 200). | Same cause. On R2 this audit applies the instruction's test ("would the fixed twin have been flagged in the same way?"), which the report gives only as its strict reading. The counterfactual supports the report's view that these errors are large enough to show. |
| B2-09 | As above, "qualified yes"; POSTRUN notes the near-equal declared rates. | R2 no, case-fixed; counterfactual 10/200 (not flagged); optimism +0.031 AUC; the nested AUC sits below 0.5 under the null. | This audit. "Their detections stand" (§7.3) is weak for B2-09: the error separates the twins only on the noise probe (67 against 25), not in the declared worlds. |
| B3-04 | §7.3: coefficient threshold against sampling sd about 0.3 (same as here). §9 and POSTRUN (ii): the failed clean pass comes "from the skeleton" (little kidney variation against liver noise). POSTRUN (i): "qualified yes", following from the error through the noise flag. | case-fixed: the point estimate against 0.25 with SE 0.29. R2 no. The noise-flag difference (65 against 0) comes from quotients of zero-mean noise, not from the intercept mechanism. Counterfactual 16/200 (not flagged). | Mixed. The world's noise ratio does set the SE, so "skeleton" is not wrong, but the report puts the same mechanism (a threshold without a test, null sd comparable to the threshold) under "the claim's rule" for B2-08 to B2-11 and under "the skeleton" for B3-04. Its own §7.3 explains B3-04 by the threshold. On (i), the declared streams do not separate the twins; this audit's "no" is better supported. |
| B3-12 | §7.3 and POSTRUN (i): the detection does not show the error (agree). §9 and POSTRUN (ii): "autocorrelated, seasonal residuals" inflate the size of the t test. | mixed (case-fixed + case-world). The worlds lack the intercept the error needs (admissions proportional to population, L31). | This audit on the cause (item W4): the season term does not inflate the size; it lowers it. |

### Report claims about these pairs that I find unsupported or wrong

* **W1. B2-03, POSTRUN (i): "at this size the copies carry almost no weight".** Contradicted. On the gate's 200 `minus`
  samples the faulty balanced accuracy has mean 0.597 against the fixed 0.502; 99.3% of held-out minority rows have a
  copy in training.
* **W2. B2-06, POSTRUN (i): "the declared offsets (SD 0.8 on 20 features) gave no lift".** Contradicted. Faulty AUC
  in `minus` mean 0.643 against the fixed 0.499. The lift exists and stays below the claim's 0.75.
* **W3. REPORT §7.1, for B2-03, B2-06 and B2-07: "What the error exploits was not present in the declared worlds
  strongly enough to show at this size", and the model "lets little leak".** Not supported as stated. The structure is
  present (copies 99.3%; ICC 0.40; ICC 0.55 and 0.48), and the error moves the statistic by 0.095, 0.14 and 0.16. The
  miss comes from the claim's threshold sitting above the inflated distribution. B2-06 uses the same low-capacity model
  as B2-03 but is missing from the §7.1 list of misses that depend on the model.
* **W4. REPORT §9 and POSTRUN (ii), B3-12: "autocorrelated, seasonal residuals" (POSTRUN: "AR(1) waves and a seasonal
  cycle ... which inflate the size").** Partly wrong. With the same random draws (`scratch/season_check.py`, 2000
  `minus` samples, gate seeds): fixed rate 0.107 with the declared season, 0.188 with the season removed, and 0.017 with
  the season but no AR(1) waves. The AR(1) waves cause the excess. The deterministic season adds residual variance that
  the OLS standard error counts but the slope estimate does not carry, so it makes the test more conservative.
* **W5. REPORT §9 / POSTRUN (ii): B3-04's failed clean pass "comes from the skeleton" while B2-08 to B2-11 "do not".**
  Inconsistent classification of one mechanism, a threshold without a test whose null sampling sd is comparable to the
  threshold. For B3-04, §7.3 of the same report gives the claim's threshold as the cause. Defensible only as a matter of
  degree: in B3-04 a world with more kidney variation would shrink the SE, while at n = 40 no world removes the binomial
  floor (P(>= 24/40) = 0.13).
* **W6. REPORT §7.3, B2-08 to B2-11: "their detections stand".** Supported for B2-08, B2-10 and B2-11 (counterfactual
  27, 28 and 48 of 200). For B2-09 it is not supported by the declared streams (26 against 18, 23 against 20;
  counterfactual 10/200); only the noise stream separates the twins.
* **W7. POSTRUN (iii), B3-09: the venous content "was made Fick-consistent with the measured cardiac output".** The
  wording is inaccurate: `fixed.py` L13 uses the true output (L8), and the 10% measurement error is added afterwards
  (L15). The coupling comes from the shared measurement error, as it would with any physiologically consistent venous
  content, so calling it steering is debatable. The statement that `K2_HIGH_SIZE` (34/200) relies on it is correct.
* **W8. POSTRUN "needed" world for B2-04** (shared slow component between indicators and outcome). Doubtful under the
  fixed `minus` rule; see the table.

### What the report explains that I missed

* **World-author awareness and steering** (P/C/N readings; POSTRUN item (iii)). I did not assess them. The report reads
  B2-03 and B2-10 as C and flags B3-09 for steering. For the detection side of my attributions, B3-09's `minus` signal
  (34/200) is the kind of structure that steering would supply. The B3-09 detection stands on the control and the noise
  probe without it, so its `tool` attribution does not change.
* **Why B2-05's world has no strong shared persistence.** POSTRUN quotes world log C51: deterministic seasonal drivers
  were avoided to keep `minus` a clean null. I had no logs. This supports the case-world part of my mixed label, and
  shows the fixed `minus` rule itself makes this structure hard to build.
* **The guard expression** (REPORT §7.4): the precedence slip `-(n)//k` remains in six B-2 pairs (B2-02, B2-03, B2-08,
  B2-09, B2-11, B2-12). I saw it but did not record it. It binds only for an empty class and changes no count here.
* **Pre-run disclosure.** Every failed clean pass and several misses were predicted by the criterion authors in
  CASE.md §5 and §7 before the run (REPORT §7.3). I cited CASE.md for some of these, but did not state that all of them
  were predicted.
* **The seasonal cycle of B3-12.** I did not mention it in Part 1. Checked in Part 2 (W4): it is not a cause of the
  failure.

### Findings of this audit that the report does not contain

* B2-01: the fixed twin's AUC in `minus` is centred at 0.63, not 0.5, because row-level folds leak country identity;
  the 0.75 threshold absorbs it.
* B3-03: in `minus` systolic pressure on BSA explains R-squared 0.027 on average, so even a perfect proxy of BSA could
  not reach the claim's 0.05. The miss does not depend on the size of the ratio's distortion.
* B3-05: its declared `minus` induces r 0.115 between the indices, against Pearson's 0.4 to 0.5. The detection rests on
  the noise probe alone, and that probe responds to any correlation of two quotients with a shared denominator.
* B3-08: the fixed twin keeps a small coupling through the shared visit term (r 0.06 in `minus`); harmless at 0.3.
* Counterfactual sizes for the six non-attributable detections: the error alone would be flagged in B2-08, B2-10 and
  B2-11, and not in B2-09, B3-04 or B3-12.
* Post hoc class counts: no miss or failed clean pass in B-2 or B-3 is attributed to the gate. Without the
  case-attributed pairs, B-2 is 3/3 and 3/3 and B-3 is 6/6 and 6/6 (too few pairs for a verdict).
