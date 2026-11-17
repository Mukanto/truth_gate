# Validity audit of the B-2 and B-3 cases, Phase B

Auditor: independent agent, task `bc_validity_phase_b`. Part 1 was written before anything in `after_part1/` was opened.

## Part 1: own audit

### Method

* Read: `INSTRUCTIONS.md`, `PREREG_PHASE_B.md`, `EXPECTED_FLAGS.json`, `SOURCES.md`, `WORLD_INSTRUCTIONS.md`,
  `RESULTS.json`, `docs/GATE.md`, the 24 case folders (`CASE.md`, `ASSIGNMENT.json`, `faulty.py`, `fixed.py`, and the
  twin diff), the 48 certificates, and the flag rules in `truth_gate/checks.py`. No other file.
* Certificate counts are written "faulty vs fixed", as samples on which the criterion held, out of 200
  (`scratch/certtable.py` prints them for every stream).
* My own computations ran on copies in `scratch/` (interpreter `.venv-qiskit`, Python 3.14.2, numpy 2.5.4):
  * `scratch/stats.py`: the statistic of every faulty and fixed criterion (the `return bool(stat >= thr)` line
    patched to return `stat`) on 200 `minus`, 200 `plus` and 200 noise-probe samples. Sample i of `minus` uses
    `np.random.default_rng(i)`, of `plus` `default_rng(10000 + i)`; noise samples replace every float array by
    N(0, 1) and every bool array by Bernoulli(0.5) (`default_rng(20000 + i)`). The same samples go to both twins.
    Output `scratch/stats_out.json`. These hold counts reproduce the certificate counts within sampling error.
  * `scratch/w2.py`: one structural statistic per case on the same 200 samples (`scratch/w2_out.json`).
  * `scratch/extra.py`: B2-12 in-sample OLS R² on `minus`; B2-03 faulty criterion on a minus-like world with 60, 600
    and 2000 genes (100 samples each, `default_rng(i)`).
  * `scratch/b206_variant.py`: B2-06 faulty criterion with nearest-neighbour SMOTE in place of random-pair
    interpolation (200 + 200 samples, seeds as above). A sensitivity check, not a case file.
* "Mean statistic on minus" below always means my run (200 samples); counts with "cert" are from the certificates.

### Common observations

* Every one of the 48 components carries `K5_INCONCLUSIVE:zeros`: the guards return `None` on all 200 all-zero samples.
  That caps every verdict at WEAK, so no fixed twin could be FALSIFIABLE; WEAK counts as a clean pass (PREREG §6).
* `K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_NOISE` and `K5_HOLDS_ON_DEGENERATE` mean "not significantly lower than
  `plus`" (`truth_gate/checks.py` 256-285). A criterion that almost never holds in `plus` gets them without holding on
  those streams (B3-11 and B3-12 fixed: noise 0/200, zeros 0/200, yet both flags).
* B-2 misses share one pattern: the faulty statistic is inflated above the fixed one on `minus`, but its mean stays
  below the brief's threshold (B2-03 0.744 vs 0.80; B2-06 0.620 vs 0.75; B2-09 0.573 vs 0.75; B2-10 0.055 vs 0.30;
  B2-12 0.079 vs 0.40). Truth_Gate judges outcomes, so a sub-threshold inflation cannot raise a flag.
* B-3 ratio cases (B3-05 to B3-12) share one design feature: the brief states the claim through the ratio statistic
  itself (for example B3-09: "the standardised regression slope ... of infections per admission on the number of
  beds"), so the faulty criterion computes exactly the brief's statistic and the fixed criterion computes a different
  statistic with the brief's threshold. The faulty twin is then wrong only if `minus` puts denominator error or a
  size-dependent path into the data, and the fixed twin can hold in `plus` only if `plus` carries the claim by a path
  that survives the adjustment.

### Summary table

| id | subtype, source | detected | clean pass | W2 | R1 | R2 | C1 | C2 | attribution |
|---|---|---|---|---|---|---|---|---|---|
| B2-01 | L1.1, SIM03 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-02 | L1.1, SIM03 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-03 | L1.3, AMB02 | no | yes | weak | yes | n/a | yes | clean (low power) | case-size |
| B2-04 | L1.3, AMB02 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-05 | L1.2, KAP23 | yes | yes | weak | yes | yes | yes | clean | tool |
| B2-06 | L1.2, KAP23 | no | yes | yes | yes | n/a | yes | clean | tool |
| B2-07 | L1.4, KAP23 | yes | yes | yes | yes | yes (fragile) | yes | clean | tool |
| B2-08 | L1.4, KAP23 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-09 | L3.1, KAP23 | no | no | weak | yes | n/a | yes | not clean | mixed |
| B2-10 | L3.1, KAP23 | no | yes | weak | yes | n/a | yes | clean (low power) | case-world |
| B2-11 | L3.2, KAP23 | yes | yes | yes | yes | yes | yes | clean | tool |
| B2-12 | L3.2, KAP23 | no | yes | weak | yes | n/a | yes | clean | case-world |
| B3-01 | ARC81 | yes | yes | weak | yes | yes | yes | clean | tool |
| B3-02 | ARC81 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-03 | ARC81 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-04 | ARC81 | yes | yes | yes | yes | yes | yes | clean | tool |
| B3-05 | PEA97 | yes | no | yes | yes | yes (noise flag only) | partly | not clean | case-fixed |
| B3-06 | PEA97 | no | yes | no | yes | n/a | yes | clean | case-world |
| B3-07 | PEA97 | yes | no | weak | yes | yes | yes | not clean | case-fixed |
| B3-08 | PEA97 | yes | yes | yes | yes | yes | yes | clean (low power) | tool |
| B3-09 | KRO93 | no | yes | no | yes | n/a | yes | not clean (scored clean) | case-world |
| B3-10 | KRO93 | no | yes | no | yes | n/a | yes | clean | case-world |
| B3-11 | KRO93 | yes | no | yes | yes | yes | partly | not clean | case-fixed |
| B3-12 | KRO93 | no | no | no | yes | n/a | partly | not clean | mixed |

### Pairs

#### B2-01 (W38, L1.1, SIM03): detected yes (NOT_FALSIFIABLE), clean pass yes (WEAK)

* **W1.** With 60 candidate genes on 20 samples, a selection-plus-centroid rule built and scored on the same samples
  fits noise (resubstitution).
* **W2: yes.** `minus` has 60 genes with no class difference on 20 samples (`faulty.py` 5, 15 with eff 0): p/n = 3.
  Faulty resubstitution accuracy on `minus`: mean 0.894 (192/200 ≥ 0.80); fixed leave-one-out: mean 0.468.
* **W3.** 20 samples × 60 genes. Source: "20 specimens, 10 per class" and "the 60-gene cap (6000 in the source)"
  (`CASE.md` §4). Rows match; genes are 1% of the source, and the bias is already saturated at 60.
* **R1: yes.** The only difference is `faulty.py` 57 (`pred = fit(x, y)(x)`) against a leave-one-out loop around the
  same `fit` (`fixed.py` 57-61).
* **R2: yes.** minus 186 vs 8; control `permute_tumour` 191 vs 13; noise 195 vs 13.
* **C1: yes.** Selection, weights and rule are refitted without the left-out sample, as `CASE.md` §4 says SIM03 requires.
* **C2.** minus 8, control 13, noise 13, plus 177: **clean**.
* **Attribution: tool.** Adequate case; the error drives every expected flag.

#### B2-02 (W35, L1.1, SIM03): detected yes, clean pass yes

* **W1.** 20 markers on 30 patients: a logistic model's AUC on its own training data fits noise.
* **W2: yes.** 20 uninformative markers on 30 patients in `minus` (`faulty.py` 5, 11). Faulty in-sample AUC on `minus`:
  mean 0.980 (200/200 ≥ 0.75); fixed 5-fold CV AUC: mean 0.506.
* **W3.** 30 × 20. Source states none ("the source documents the setting only qualitatively", `CASE.md` §4).
* **R1: yes.** Only `faulty.py` 76 (AUC of the fit on all patients) against stratified 5-fold CV with refit.
* **R2: yes.** minus 200 vs 6; control 200 vs 7; noise 200 vs 7.
* **C1: yes.** **C2.** minus 6, control 7, noise 7, plus 165: **clean**.
* **Attribution: tool.**

#### B2-03 (W36, L1.3, AMB02): detected no (WEAK), clean pass yes (WEAK)

* **W1.** Many candidate genes without class information: selection on all tissues picks chance-correlated genes, and the
  leave-one-out error computed inside the selection is optimistic.
* **W2: weak.** The structure is there but small: 60 null genes, which also sit in 6 co-expression blocks (mean
  within-block correlation 0.248 on `minus`), so the effective pool is smaller still. Faulty internal LOO accuracy on
  `minus`: mean 0.744 (16/200 ≥ 0.80); fixed external CV: mean 0.583; majority-class rate 0.645. Same faulty criterion on
  a minus-like world of the same form with more genes (`extra.py`): 5/100 hold at 60 genes, 61/100 at 600, 97/100 at
  2000.
* **W3.** 62 tissues × 60 genes. Source: 62 tissues and 2000 genes, "pre-reduction to the 20 genes with the largest
  |t| (source: 400 of 2000)" (`CASE.md` §4). Rows match; genes are 3% of the source, under the PREREG cap of 60
  features (§2).
* **R1: yes.** Same `select()`; faulty runs it on all data and reports its internal LOO error (CV1IE), fixed repeats it in
  each of 10 training folds (CV10E). The LOO-versus-10-fold difference is part of AMB02's own comparison.
* **R2: n/a.**
* **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 85 (`K2_LOW_POWER`): **clean**, low power (42.5%).
* **Attribution: case-size.** The selection bias is present (+0.16 accuracy over the external estimate) but with 3% of
  the source's genes it rarely reaches 0.80; with 2000 genes it would hold in almost every null sample.

#### B2-04 (W27, L1.3, AMB02): detected yes, clean pass yes

* **W1.** As B2-03, with recursive feature elimination down to 8 genes on all 72 patients.
* **W2: yes (small but sufficient).** 60 null genes in blocks (within-block correlation 0.159). Faulty LOO AUC on
  `minus`: mean 0.770 (63/200 ≥ 0.80); fixed external CV: 0.506.
* **W3.** 72 × 60. Source: "gene cap 60 (source 7129)" (`CASE.md` §4); the quoted passage reports CV1IE "about 10%
  for only eight genes" on label-independent data.
* **R1: yes.** `faulty.py` 80-85 (RFE on all rows, then LOO) against RFE inside each of 10 folds.
* **R2: yes.** minus 67 vs 1; control 55 vs 0; noise 60 vs 0.
* **C1: yes.** **C2.** minus 1, control 0, noise 0, plus 133: **clean**.
* **Attribution: tool.**

#### B2-05 (W16, L1.2, KAP23): detected yes (generic: noise probe only), clean pass yes

* **W1.** Unobserved entries filled with outcome-class means computed on all rows carry label information into
  the features, in proportion to the gap between the classes' observed means.
* **W2: weak.** On `minus` the class gap of observed values is chance only: mean |onset − non-onset| gap 0.176 sd on the
  six indicators that are informative in `plus`, against 0.687 sd in `plus`. Missingness (26.9% onset rows, 19.0%
  others) is the same in both worlds but a mean fill does not encode it. Faulty CV AUC on `minus`: mean 0.597 (4/200 ≥
  0.75); fixed: 0.499.
* **W3.** 250 × 12, about 20% missing. Source passage states none.
* **R1: yes.** `faulty.py` 89-96 (class-conditional mean on all rows, before CV) against a fold-wise unconditional mean
  (`fixed.py` 95-99). The class mean is a stand-in for the source's outcome-using random-forest imputation (`CASE.md` §4).
* **R2: yes.** Only noise carries an expected flag: 22 vs 0. The noise probe has 50% missing entries and balanced classes,
  which enlarges the injected gap; minus 3 vs 0, control 2 vs 0.
* **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 140: **clean**.
* **Attribution: tool.** The detection is real and from the error, but generic; the declared `minus` could not show it.

#### B2-06 (W18, L1.2, KAP23): detected no, clean pass yes

* **W1.** Synthetic positives interpolated from real positives before the split fall in training and test folds, so a
  synthetic test row has its parent or siblings in training.
* **W2: yes.** 20% positives give on average 60.4 synthetic rows from about 20 positives. On `minus` the leak operates:
  the faulty rule calls 0.996 of synthetic test rows and 0.976 of real positives positive, but only 0.249 of real
  negatives negative, because the synthetic rows lie near the positive centroid and become the nearest neighbours of
  everything in 30 dimensions. Balanced accuracy: faulty mean 0.620 (0/200 ≥ 0.75), fixed 0.497.
* **W3.** 100 × 30. Source states none.
* **R1: yes.** SMOTE on all rows then CV over real and synthetic rows, against SMOTE inside training folds and scoring
  on real rows. Random-pair interpolation (the earlier author's simplification) does not decide the result: with
  nearest-neighbour SMOTE the faulty mean is 0.647 and 6/200 hold (`b206_variant.py`).
* **R2: n/a.** **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 200: **clean**.
* **Attribution: tool.** This is a limit of judging decisions, not a case defect: the case is adequate and the error
  expresses itself (+0.12 balanced accuracy), but on null data the faulty criterion makes no false claim at 0.75, so no
  check of outcomes can see it.

#### B2-07 (W04, L1.4, KAP23): detected yes (declared: control only), clean pass yes

* **W1.** Exact repeated rows split across folds, so a 1-NN test row finds its own copy in training.
* **W2: yes.** 50 of 200 rows repeat an earlier row with its diagnosis (`faulty.py` 5, 13-26); 40.1% of rows have an
  exact copy on `minus`. Faulty CV accuracy on `minus`: mean 0.709 (24/200 ≥ 0.75); fixed after de-duplication: 0.529.
* **W3.** 200 × 15, a quarter repeated (brief). Source states none.
* **R1: yes.** The fixed twin only adds the collapse of identical rows (`fixed.py` 69-72).
* **R2: yes, fragile.** control `permute_diagnosis_by_patient` 20 vs 0 (flagged); minus 12 vs 0 (not flagged). Both
  streams are null worlds with the same duplicates and the same expected rate (my run: 24/200 on `minus`); the flag
  rests on one stream passing the Wilson bound.
* **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 190: **clean**.
* **Attribution: tool** (detection near the boundary; the error's mean accuracy 0.71 lies just under 0.75).

#### B2-08 (W30, L1.4, KAP23): detected yes, clean pass yes

* **W1.** Copies of fraud rows made before the split are exact duplicates across folds; 1-NN finds them.
* **W2: yes.** About 12% fraud gives about 114 copies (43% of the augmented rows; `faulty.py` 53-58). Faulty F1 on
  `minus`: mean 0.933; fixed 0.112.
* **W3.** 150 × 10. Source states none.
* **R1: yes.** **R2: yes.** minus 200 vs 0; control 200 vs 0; noise 41 vs 15.
* **C1: yes.** **C2.** minus 0, control 0, noise 15 (7.5%, not flagged), plus 194: **clean**.
* **Attribution: tool.**

#### B2-09 (W14, L3.1, KAP23): detected no, clean pass no (fixed UNDEFINED)

* **W1.** Outcome and features that both move slowly in time, so shuffled folds let the model learn period-specific
  patterns from temporal neighbours.
* **W2: weak.** Indicators are autocorrelated (lag-1 0.79 on `minus`), but onsets hardly (lag-1 0.088), and in `minus`
  the indicators are independent of the hazard (`faulty.py` 19-25). Mean |corr(indicator, onset)| is 0.080 against
  0.058 after permuting onsets across rows. Faulty shuffled-CV AUC on `minus`: mean 0.573 (4/200 ≥ 0.75); fixed 0.519.
* **W3.** 200 rows × 8. Source states none.
* **R1: yes.** Shuffled stratified 5-fold CV against a chronological 70/30 split; the fixed adds a guard that returns
  `None` if a class has fewer than 2 rows in either part (`fixed.py` 101-102), part of the single split.
* **R2: n/a.** **C1: yes.** `CASE.md` §4: "The source's own corrected split (earlier years train, later years test) is
  of the same kind."
* **C2.** minus 11 (6 UNDEFINED), control 3, noise 1, plus 73 (17 UNDEFINED); `K1_UNDEFINED`, verdict UNDEFINED:
  **not clean**.
* **C3.** The 60-row test window holds fewer than 2 onsets in 17/200 `plus` and 6/200 `minus` samples; the allowed guard
  returns `None`, and Truth_Gate 0.4.0 makes any UNDEFINED outcome on `plus` or `minus` a K1_UNDEFINED verdict. The
  criterion author recorded the 7.5% abstention before the freeze (`CASE.md` §7). The test itself is sound for size
  (minus 5.5%, noise 0.5%) but weak (plus 36.5%). Under the 0.5 rule (abstention on at most half of `plus` is no claim,
  `docs/GATE.md` "What changed in 0.5") the verdict would be WEAK.
* **Attribution: mixed.** Miss: case-world (the time structure a linear model could exploit is weak in `minus`). Failed
  clean pass: the fixed design (one short test window in a world with rare onsets) together with the 0.4.0 abstention
  rule.

#### B2-10 (W37, L3.1, KAP23): detected no, clean pass yes

* **W1.** Autocorrelated target and indicators: shuffled folds let the model fit a within-sample association that
  temporal neighbours share.
* **W2: weak.** Target lag-1 0.73 and indicators 0.68 on `minus`, but the target follows a driver independent of every
  indicator (`faulty.py` 19-27). In-sample OLS R² of admissions on the six indicators: mean 0.146 (0.037 after
  permuting weeks), so even an in-sample fit stays below 0.30. Faulty shuffled-CV R²: mean 0.055 (2/200 ≥ 0.30); fixed
  chronological R²: −0.81.
* **W3.** 150 weeks × 6. Source states none ("the source documents only the mechanism", `CASE.md` §4).
* **R1: yes.** **R2: n/a.** **C1: yes.**
* **C2.** minus 0, control 0, noise 0, plus 73: **clean**, low power (36.5%).
* **Attribution: case-world.** The only exploitable structure in `minus` is a chance association of independent
  autocorrelated series, too weak to approach the threshold.

#### B2-11 (W06, L3.2, KAP23): detected yes (declared), clean pass yes

* **W1.** Patches of one patient share a patient effect, so patch-level random folds put a patient on both sides.
* **W2: yes.** ICC of patch features within patient on `minus`: 0.491. Faulty patch-level AUC on `minus`: mean 0.708
  (49/200 ≥ 0.75); fixed patient-level folds: 0.494.
* **W3.** 40 patients × 6 patches × 20 features. Source states none.
* **R1: yes.** One line: `faulty.py` 78 folds over patch rows, `fixed.py` 78 over patients.
* **R2: yes.** minus 39 vs 0; control 58 vs 0.
* **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 115: **clean**.
* **Attribution: tool.**

#### B2-12 (W49, L3.2, KAP23): detected no, clean pass yes

* **W1.** Length of stay clustered by hospital, with characteristics that let a model recognise the hospital, so random
  patient-level folds leak hospital effects.
* **W2: weak.** Stay is strongly clustered (ICC 0.519 on `minus`), but one patient's 15 characteristics identify the
  hospital only weakly (ICC 0.310), and the model is linear. In-sample OLS R² of stay on the characteristics (all 240
  rows): mean 0.208, 1/200 ≥ 0.40, an upper bound for what the random split can exploit. Faulty R² on `minus`: mean
  0.079 (0/200 ≥ 0.40); fixed hospital folds: −0.332.
* **W3.** 12 hospitals × 20 patients × 15. Source states none.
* **R1: yes.** **R2: n/a.** **C1: yes** (block cross-validation, the remedy named in the passage).
* **C2.** minus 0, control 0, noise 0, plus 121: **clean**.
* **Attribution: case-world.** The leak raises R² by about 0.4 over the fixed twin, but from a negative base; the
  hospital information reachable by a linear model on these characteristics is below the threshold.

#### B3-01 (W29, ARC81): detected yes (generic), clean pass yes

* **W1.** Fick consumption and delivery share measured CO, Hb and SaO2, so their measurement errors correlate them.
* **W2: weak.** In `minus` true consumption is independent of delivery and the venous saturation is Fick-consistent
  (`faulty.py` 15-18), so only measurement errors are shared (thermodilution 15%, `faulty.py` 19). Correlation induced
  on `minus`: mean 0.258 (6/200 ≥ 0.5; cert 8/200).
* **W3.** 40 patients. Source states none (abstract only).
* **R1: yes.** The only difference is consumption from the Fick lines (`faulty.py` 46, 49) against `vo2_expired`.
* **R2: yes.** control `permute_vo2_expired` 200 vs 1; noise 169 vs 0. The control flag holds by construction (the
  faulty never reads the permuted key, a direct consequence of computing consumption from the shared components);
  the noise flag is the coupling itself (on N(0, 1) components the shared product dominates, mean r 0.706).
* **C1: yes.** **C2.** minus 0, control 1, noise 0, plus 190: **clean**.
* **Attribution: tool.** The detection comes from the error, through the noise probe and the control, not from `minus`.

#### B3-02 (W26, ARC81): detected yes (declared), clean pass yes

* **W1.** Thermodilution output is the denominator of SVR and also the other variable, so its error makes them
  negatively related.
* **W2: yes.** Thermodilution error 18% (`faulty.py` 15). Induced Spearman on `minus`: mean −0.298 (29/200 ≤ −0.4;
  cert 25/200).
* **W3.** 100 patients. Source states none.
* **R1: yes.** One line (`faulty.py` 45). **R2: yes.** minus 25 vs 0.
* **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 197: **clean**.
* **Attribution: tool.**

#### B3-03 (W53, ARC81): detected yes (declared), clean pass yes

* **W1.** EDV computed as SVI / RVEF shares the RVEF error with the regressor.
* **W2: yes.** Thermistor error 0.04 on a mean of 0.32 (`faulty.py` 15). Induced standardised slope on `minus`: mean
  −0.216 (32/200 ≤ −0.4; cert 24/200).
* **W3.** 30 patients. Source states none.
* **R1: yes.** **R2: yes.** minus 24 vs 2; control 196 vs 3 (the faulty does not read the permuted radionuclide
  volume).
* **C1: yes.** **C2.** minus 2, control 3, noise 3, plus 172: **clean**.
* **Attribution: tool.**

#### B3-04 (W45, ARC81): detected yes (generic), clean pass yes

* **W1.** Changes in Fick consumption and in delivery share the changes in measured CO, Hb and SaO2.
* **W2: yes.** Shared thermodilution error 8% at each time point (`faulty.py` 27). Induced R² on `minus`: mean 0.102
  (23/200 ≥ 0.25; cert 27/200).
* **W3.** 24 patients × 2 time points. Source states none.
* **R1: yes.** **R2: yes.** minus 27 vs 1; control 198 vs 1; noise 172 vs 3.
* **C1: yes.** **C2.** minus 1, control 1, noise 3, plus 176: **clean**.
* **Attribution: tool.**

#### B3-05 (W01, PEA97): detected yes (generic), clean pass no

* **W1.** Femur/column and tibia/column share the column length, whose own variation correlates the two indices.
* **W2: yes.** The column term (log sd 0.03) is shared by both indices (`faulty.py` 18). Index correlation on `minus`:
  mean 0.372 (77/200 ≥ 0.4; cert 75/200); the source reports "about 0.4 to 0.5" for bones sorted at random.
* **W3.** 120 skeletons. Source states no data size.
* **R1: yes.** Index correlation against the partial correlation of the absolute lengths given column length.
* **R2: yes, through the noise flag only.** noise 56 vs 0 is attributable. `K2_HIGH_SIZE` is not: minus 75 vs 34, and the
  fixed twin carries the same flag.
* **C1: partly.** Partial correlation is the standard correction (`CASE.md` §4), not stated in the quoted passage. It
  removes the shared-denominator term but keeps the shared body size.
* **C2.** minus 34, control 0, noise 0, plus 198; `K2_HIGH_SIZE`, NOT_FALSIFIABLE: **not clean**.
* **C3.** In `minus` body size g (log sd 0.06) scales all three bones (`faulty.py` 9, 16-18), and column length measures it
  with noise (reliability about 0.8), so partialling out the column leaves part of g in both femur and tibia. Fixed
  statistic on `minus`: mean 0.321 (41/200 ≥ 0.4), matching `CASE.md` §7 (0.317). The analytic value is about 0.31.
* **Attribution: case-fixed.** The detection is fine. The failure is a correction that is not valid in a world where
  the denominator is a noisy proxy of a common size factor.

#### B3-06 (W17, PEA97): detected no, clean pass yes

* **W1.** Two indices with a shared denominator correlate when the denominator varies independently of the
  numerators or carries error.
* **W2: no.** Totals are built as per-capita value × population and population has no error (`faulty.py` 15-16), so
  dividing recovers the true per-capita values exactly. On `minus`, corr(log population, log per-capita CO2) is −0.005;
  the faulty per-capita Spearman has mean 0.003 (0/200 ≥ 0.5).
* **W3.** 150 countries. Source states none.
* **R1: yes in form** (two indices with a shared denominator). The brief's claim is about per-capita values, so the
  faulty statistic is the claim's own statistic.
* **R2: n/a.** **C1: yes.** **C2.** minus 0, control 0, noise 0, plus 200: **clean**.
* **Attribution: case-world.** `minus` lacks any shared-denominator artefact. Because the claim is stated per capita, a
  world could add one only through population error, which is small in practice.

#### B3-07 (W43, PEA97): detected yes (generic), clean pass no

* **W1.** Yield/area and fertilizer/area share the recorded area and its 15% error.
* **W2: weak.** The area error is shared (`faulty.py` 16), but it is small against the per-hectare spreads: induced
  slope on `minus` mean 0.109 (9/200 ≥ 0.3; cert 8/200).
* **W3.** 90 farms. Source states none.
* **R1: yes.** **R2: yes.** Only noise carries an expected flag: 56 vs 0, from ratios of N(0, 1) values with a shared
  denominator. On `minus` the faulty holds less often than the fixed (8 vs 23).
* **C1: yes.** Ratio-free regression with the denominator as covariate.
* **C2.** minus 23, control 11, noise 0, plus 151; `K2_HIGH_SIZE`: **not clean**.
* **C3.** On the raw scale, with log-normal farm sizes (log sd 1.0), a few large farms dominate the OLS fit, and the
  recorded area is a noisy covariate, so fertilizer_total (proportional to true area) gets positive weight in `minus`.
  Fixed statistic on `minus`: mean 0.081 but spread wide (cert 23/200 ≥ 0.3). The same model on logs gives `minus` mean
  0.080, sd 0.072, 1/200 ≥ 0.3, and `plus` 192/200, so a clean correction existed on these worlds.
* **Attribution: case-fixed.**

#### B3-08 (W24, PEA97): detected yes (generic), clean pass yes

* **W1.** Both per-kg ratios fall with body mass, so dividing by mass correlates them.
* **W2: yes.** Elasticities −0.3 and −0.25 on log mass (`faulty.py` 14-15). Induced R² on `minus`: mean 0.106 (19/200
  ≥ 0.25; cert 22/200).
* **W3.** 30 athletes. Source states none.
* **R1: yes.** **R2: yes.** minus 22 vs 1; noise 90 vs 2.
* **C1: yes.** **C2.** minus 1, control 0, noise 2, plus 110 (`K2_LOW_POWER`): **clean**, low power (55%).
* **Attribution: tool.**

#### B3-09 (W23, KRO93): detected no, clean pass yes (but see C2)

* **W1.** A ratio outcome regressed on a predictor that tracks the denominator is spurious when the numerator is not
  proportional to the denominator.
* **W2: no.** Infections are Poisson counts proportional to admissions (`faulty.py` 12-14): elasticity of infections on
  admissions on `minus` 0.999. Beds track admissions (r 0.964), but corr(beds, rate) is −0.002; faulty slope mean −0.002
  (0/200 ≤ −0.3).
* **W3.** 100 hospitals. Source states none.
* **R1: yes in form.** The claim is stated for the rate itself, so the faulty statistic is the claim's own statistic.
* **R2: n/a.** **C1: yes.**
* **C2.** minus 17, control 0, noise 0, plus 108: scored clean (WEAK), but **not clean** in substance: 17/200 is 8.5%,
  and my independent run gives 33/200 on `minus` (the criterion author's pre-check also gave 33/200). That rate would
  raise `K2_HIGH_SIZE`.
* **C3.** Beds and admissions are almost collinear (r 0.964), so the coefficient of beds is very variable (sd 0.316 on
  `minus`, `CASE.md` §7). The clean pass rests on a favourable draw.
* **Attribution: case-world** (miss; the structure is absent). The clean pass is not robust.

#### B3-10 (W51, KRO93): detected no, clean pass yes

* **W1.** A ratio predictor whose denominator drives the outcome carries the denominator's effect when the ratio
  correlates with the denominator.
* **W2: no.** Heart weight is exactly ratio × body weight (`faulty.py` 13-14), so the ratio is uncorrelated with body
  weight (r 0.001 on `minus`) although pressure rises with body weight. Faulty slope: mean −0.001 (0/200 ≥ 0.3).
* **W3.** 60 rats. Source states none.
* **R1: yes.** **R2: n/a.** **C1: yes.** **C2.** minus 3, control 4, noise 3, plus 200: **clean**.
* **Attribution: case-world.** A world with heart weight scaling faster than body weight would carry the structure.
  The usual allometry (exponent below 1) would push the artefact in the opposite direction.

#### B3-11 (W02, KRO93): detected yes (declared), clean pass no

* **W1.** Energy per m² falls with area, and occupants track area, so the ratio outcome correlates with occupants
  through the denominator.
* **W2: yes.** On `minus`: Spearman(EUI, area) −0.247 and Spearman(occupants, area) 0.905. Faulty Spearman: mean −0.227
  (30/200 ≤ −0.3; cert 41/200).
* **W3.** 150 buildings. Source states none.
* **R1: yes.** **R2: yes.** minus 41 vs 0.
* **C1: partly.** Partial Spearman given area is the standard adjustment, but it tests the conditional association
  while the brief's threshold (−0.3) was set for the marginal one.
* **C2.** minus 0, control 0, noise 0, plus 4; `K2_NO_SEPARATION` and the "not lower than plus" flags: **not clean**
  (it does not hold where the claim is true).
* **C3.** `plus` puts only a small direct occupant effect into the data (−0.12 log units per sd, `faulty.py` 16). The
  fixed statistic on `plus` has mean −0.126 (3/200 ≤ −0.3), as `CASE.md` §7 records (−0.125). Most of the claimed
  association in `plus` runs through area, which the world author also kept in `minus`.
* **Attribution: case-fixed.** The detection is attributable; the correction cannot hold in `plus`.

#### B3-12 (W11, KRO93): detected no, clean pass no

* **W1.** As B3-09: rate = leavers / headcount regressed on payroll, which tracks headcount.
* **W2: no.** Leavers are Poisson counts proportional to headcount (elasticity 1.015 on `minus`). Payroll tracks
  headcount (r 0.948), but corr(payroll, rate) is −0.001; faulty R² mean 0.003 (0/200 ≥ 0.1).
* **W3.** 250 firms. Source states none.
* **R1: yes in form.** The claim is stated for the rate itself.
* **R2: n/a.** **C1: partly** (as B3-11).
* **C2.** minus 15, control 0, noise 0, plus 1; `K2_NO_SEPARATION`, NOT_FALSIFIABLE: **not clean**.
* **C3.** In `plus` the rate depends on headcount only, and payroll is headcount × an independent wage (`faulty.py`
  9-15), so payroll carries nothing about leavers beyond headcount. Fixed partial R² on `plus`: mean 0.0105 (1/200 ≥
  0.1), as `CASE.md` §7 says ("No correction in Kronmal's ratio-free form can hold in plus").
* **Attribution: mixed.** Miss: case-world. Failed clean pass: case-fixed (the adjustment removes the only path by
  which `plus` makes the claim true).

### Class summary (post hoc; it does not change the pre-registered result)

**B-2** (12 pairs; pre-registered: 7 detections, 11 clean passes)

| | tool | case-world | case-size | case-error | case-fixed | mixed | unclear |
|---|---|---|---|---|---|---|---|
| misses (5) | 1 (B2-06) | 3 (B2-09, B2-10, B2-12) | 1 (B2-03) | 0 | 0 | 0 | 0 |
| failed clean passes (1) | 0 | 0 | 0 | 0 | 0 | 1 (B2-09: fixed design with the 0.4.0 abstention rule) | 0 |
| detections not attributable to the error (0) | | | | | | | |

All 7 detections are attributable to the error. B2-07 is fragile, and B2-05 is generic only.

Leaving out every pair with a case-attributed component (B2-03, B2-09, B2-10, B2-12; B2-09 counted as case because both
of its components involve the case): **detections 7 of 8, clean passes 8 of 8** (one-sided 95% Wilson lower bounds
0.589 and 0.747). Leaving out components instead of pairs: detections 7 of 8, clean passes 11 of 11 (0.589, 0.803).
B2-06 stays in as a tool miss: it is a limit of outcome-level checking (the error inflates the estimate, but not past
the threshold on null data).

**B-3** (12 pairs; pre-registered: 8 detections, 8 clean passes)

| | tool | case-world | case-size | case-error | case-fixed | mixed | unclear |
|---|---|---|---|---|---|---|---|
| misses (4) | 0 | 4 (B3-06, B3-09, B3-10, B3-12) | 0 | 0 | 0 | 0 | 0 |
| failed clean passes (4) | 0 | 0 | 0 | 0 | 4 (B3-05, B3-07, B3-11, B3-12) | 0 | 0 |
| detections not attributable to the error (0) | | | | | | | |

All 8 detections are attributable. In B3-05 only the noise flag is; its `K2_HIGH_SIZE` is shared with the fixed twin.
B3-01 rests on the noise probe and on a control the faulty twin ignores by construction.

Leaving out every pair with a case-attributed component (B3-05, B3-06, B3-07, B3-09, B3-10, B3-11, B3-12): **detections
5 of 5, clean passes 5 of 5** (lower bounds 0.649 each). Leaving out components instead of pairs: detections 8 of 8,
clean passes 8 of 8 (0.747 each). B3-09's scored clean pass is not robust (C2), and it is left out in both counts with
its miss.

**Reading.** On these cases the B-2 shortfall is mainly a case result. Three misses come from `minus` worlds in which
the leak has little to work with (B2-09, B2-10, B2-12). One comes from the 60-gene cap (B2-03). One is a genuine
outcome-level limit (B2-06). The one failed clean pass is a fixed-criterion design meeting the 0.4.0 abstention rule.
The B-3 shortfall is entirely a case result. The four misses are worlds with no shared-denominator artefact; three of
them have a brief that states the claim through the ratio itself. The four failed clean passes are corrections that do
not test the claim on the declared worlds.

## Part 2: comparison with the evaluation's report and post-run audit

`after_part1/` was opened only after Part 1 was written. The SHA-256 of both Part 1 files was saved before opening
(`scratch/part1_sha256.txt`, copies in `scratch/part1_frozen.*`), and Part 1 above is unchanged. Compared with
`after_part1/REPORT.md` (sections 5 to 7) and the B-2 and B-3 entries of `after_part1/POSTRUN_AUDIT.md`. Three new
checks, run after reading, are in `scratch/part2_checks.py`.

### Pairs where my attribution or explanation differs

| id | report / post-run audit | this audit | better supported | evidence |
|---|---|---|---|---|
| B2-06 | REPORT 5.2: "the declared world did not contain enough of what the error exploits". POSTRUN: "the synthetic rows do not leak a label in a null world with 30 independent markers. Needed: ... (low dimension, tight minority cluster)" | tool: the leak operates, but the threshold is not crossed | this audit, on the mechanism | On `minus` the faulty rule calls 0.996 of synthetic test rows and 0.976 of real positives positive, so the label does leak. The miss comes from specificity 0.249 (synthetic rows are the nearest neighbours of real negatives); balanced accuracy is 0.620. The prescribed fixes leave the case: the brief fixes 30 biomarkers, and a tight positive cluster would give a nearest-neighbour rule real information about status, which the `minus` rule forbids. Whether to label this "tool" or "case (the brief's setting)" is a judgement; "the world lacks the structure" is not supported. |
| B2-12 | POSTRUN: "seeing the hospital in training cannot help. Needed: a minus where the hospital shift in the characteristics is correlated with the hospital effect on stay" | case-world (weak), same attribution, different mechanism | this audit | Seeing the hospital does help: faulty R² on `minus` 0.079 against fixed −0.332 (+0.41), and in-sample OLS R² 0.208. With 12 hospitals and 15 characteristics, a linear map from the hospital shifts to any 12 hospital effects exists, so independence limits the leak through noise; it does not prevent it. The prescribed world would make the characteristics predict stay in new hospitals, the claim itself, so it would break the `minus` rule. Larger shifts that stay independent of the stay effect would strengthen the leak within the rule. |
| B3-07 | REPORT 5.3 and POSTRUN (ii yes): the skeleton defeats the fixed criterion, "Skeleton property; the correction is the documented one" | case-fixed | this audit | The same regression on logs gives `minus` mean 0.080, sd 0.072, 1/200 ≥ 0.3, and `plus` 192/200. The raw-scale fixed twin has the same mean (0.081) but sd 0.183, giving 20/200 in my run and 23/200 in the certificate. The errors-in-variables bias (about 0.08) is a skeleton property but would not by itself raise `K2_HIGH_SIZE`. The spread from raw units with log-normal farm sizes is the fixed criterion's choice ("in raw units as the faulty criterion", `CASE.md` §4). |
| B3-05, B3-11, B3-12 (failed clean passes) | skeleton (POSTRUN ii yes; REPORT 5.3 "fixed criteria that the skeleton defeats") | case-fixed | equal; the difference is a label | Both name the same mechanisms: in B3-05 a shared body size with a noisy common denominator; in B3-11 and B3-12 the correction changes the estimand while `plus` carries the claim on the raw ratio. Both place the cause in the case, not the tool. I named the fixed twin because the worlds follow the brief's claim as worded, and the brief states it through the ratio statistic; the evidence does not decide between the two labels. |
| B2-09 (failed clean pass) | criterion-side: "the guard in the fixed criterion meeting K1, not ... the skeleton" (REPORT 5.1, POSTRUN ii no) | mixed: the fixed design together with the 0.4.0 K1 rule | compatible | REPORT §6 calls it the guard meeting K1 "as released". `docs/GATE.md` "What changed in 0.5" shows the rule was later relaxed, and under 0.5 this fixed twin would be WEAK. Both readings are right; mine makes the tool half explicit. |
| B3-10 (miss) | POSTRUN: "Needed: a minus where heart weight and body weight carry a common error" | case-world; a structure-bearing world needs heart weight to scale faster than body weight | this audit | `part2_checks.py`, 200 `minus` samples each, faulty slope: exact world mean +0.018, 6/200; 5% body-weight error +0.010, 6/200; common 5% error +0.018, 6/200 (it cancels in the ratio); exponent 1.3 +0.270, 72/200; exponent 0.8 −0.159, 1/200. |
| B3-09 (miss) | POSTRUN: "Needed: a minus where infections and admissions share a size-driven component that the beds variable also tracks" | case-world; the brief states the claim for the rate itself | this audit | A size-driven component shared by infections and admissions makes the per-admission rate depend on size, which makes the brief's claim true, not false. A structure-bearing `minus` would need measurement error shared by the rate and the predictor, the kind the post-run audit proposes for B3-12. |

The other B-2 and B-3 attributions agree in substance: B2-03 (size: "small at the 60-feature cap"), B2-10, B3-06, B3-12
(miss), and the detected pairs (all detections follow from the error).

### Claims about these pairs that I find unsupported or wrong

1. POSTRUN B2-06, "the synthetic rows do not leak a label": wrong (sensitivity 0.996 on synthetic test rows in `minus`).
2. POSTRUN B2-12, "seeing the hospital in training cannot help": wrong (faulty 0.079 vs fixed −0.332; in-sample 0.208).
   Its prescribed world would break the `minus` rule.
3. POSTRUN B3-07, "area with a 15% error that enters both totals": wrong in detail. The totals use the true area and the
   error is only in `farm_area` (`faulty.py` 16-17). Its conclusion, "skeleton property", is not supported (row B3-07
   above).
4. POSTRUN B3-10 prescription (a common error in heart and body weight): wrong. A common multiplicative error cancels in
   the ratio (6/200, as in the exact world).
5. POSTRUN B3-09 prescription: doubtful, since it would make the brief's claim true in `minus`.
6. POSTRUN B2-09 and B2-10 prescriptions ("indicators and onsets / the target share a slow component"): incomplete. A
   shared slow component that persists across the chronological cut gives the indicators real forward-predictive value,
   which is the claim. Only a shared component that does not carry into the later period would keep `minus` false.
7. REPORT 5.1, B2-09's split "leaves one class empty in 17 plus samples": imprecise. The guard fires when a class has
   fewer than 2 rows in the training or the test part (`fixed.py` 101-102), not only when it is empty.
8. REPORT 5.2's closing sentence, "The miss shows that the declared world did not contain enough of what the error
   exploits", does not fit B2-06 (row above). B2-03 is a size limit, which the report's own item for it says.
9. REPORT §1 gives the B-3 Wilson lower bound as 0.432; `RESULTS.json` has 0.431492, which rounds to 0.431. Trivial.
10. REPORT §7 (i) and the post-run audit list caveats for B2-05, B2-07, B3-05 and B3-07, but not for B3-01. B3-01's
    detection rests on the noise probe and on a control flag that holds by construction: the faulty criterion never
    reads `vo2_expired`, so 200/200. `minus` (8/200) carries no flag. The control flags of B3-03 and B3-04 (196/200,
    198/200) hold by construction too, but those pairs also carry `K2_HIGH_SIZE`.

### What the report explains that I missed or understated

1. **B2-09, clustering of onsets.** The post-run audit says the abstentions come from onsets clustering in time. My W2
   reported a lag-1 autocorrelation of onsets of 0.088, and C3 spoke of "rare onsets"; that understated the clustering.
   Check: onsets in the 60-row test window of `plus` have variance 30.6 against 7.3 for a binomial with the same mean,
   and 6.0% of samples have fewer than 2, against 0.11% under independence (`minus`: 20.2 vs 7.7; 2.0% vs 0.07%). The
   abstentions come from window-scale clustering. My W2 answer for the faulty error is unchanged, because in `minus`
   the indicators are independent of the hazard.
2. **B2-07, steering by the brief.** The brief itself states that about a quarter of the rows repeat an earlier entry
   with its diagnosis (POSTRUN iii). I recorded this as the brief's size but did not flag that the structure the
   detection uses was dictated by the brief.
3. **B3-05.** The world author kept the index artefact near the threshold "on purpose" (world log, not in my folder).
4. **Awareness of the world author.** The report sorts pairs by what the world log says the world author anticipated
   (P, C, N), and notes that no C pair (B2-10, B3-09, B3-12) was detected. It also says the world author inferred the
   error for 45 of 54 briefs, so declared detections show the gate working with an anticipating declarer. I had no world
   log and did not assess this; my W2 findings for the C pairs (weak or no structure) agree with it.

### Effect on the class summary

None: Part 1 stands. If B2-06 were counted as a case attribution (the report's reading), the post-hoc B-2 count over the
remaining 7 pairs would be 7 of 7 detections and 7 of 7 clean passes. The B-3 counts do not change under any of the
differences above, which concern only labels and mechanisms inside case attributions.
