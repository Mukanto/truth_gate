# World log (Phase D, batch eb6876)

General conventions, applied to every skeleton:

* `plus` and `minus` share one generator `_simulate(rng, effect)`. `minus` calls it with the claimed coefficient,
  shift or correlation set to 0; every noise term, size, structure and distribution the claim is not about keeps its
  `plus` value. Because the noise terms are kept (rule 3, "same noise levels"), an outcome whose variance partly came
  from the effect has a somewhat smaller marginal variance in `minus`. I chose this literal reading over keeping the
  outcome's marginal distribution.
* Controls are `transform`s that return the full dict and break the claimed relationship inside the study's own
  structure. Relational pairs were declared only where a first-axis shuffle certainly breaks the claim (none for
  D-012 and D-047; reasons below).
* Checks I ran (scratch files `_scratch_*.py` in this folder): module form and forbidden names, keys, shapes, dtypes,
  finiteness, shapes the same across draws and worlds, controls change the data and return the full dict,
  reproducibility for a fixed seed, timing (largest call 10 ms, D-011). Effect checks were model-level or pooled over
  many draws (population means, Monte Carlo constants). I did not fit models, run tests or compute any per-dataset
  decision statistic, and I did not run the gate. Statements below about what an analysis would give (expected
  held-out r, R^2 or gain, in-sample values under minus, the Fick coupling) are analytic approximations, not
  measured.

## D-007 (expression -> survival, out-of-sample R^2 >= 0.10)
* plus: 2000 log2 genes in 8 co-expressed programmes (40-200 genes; gene-specific means and SDs). Programme 0
  (proliferation, 120 genes) drives log survival: corr 0.72, log-survival SD 0.6, median 26 months, lognormal, no
  censoring (the brief says survival is observed for every patient). minus: proliferation coefficient = 0; residual
  survival noise and all expression structure unchanged. Control: survival permuted across patients. Relational
  (expression, survival_months).
* Effect: oracle R^2 0.52 on the log scale and 0.47 on the raw month scale (the claim is about survival_months). It
  is chosen strong because with 50 patients and 2000 genes an honest out-of-sample estimate recovers only part of it
  (my expectation is about 0.2-0.3 for a sensible in-fold pipeline). Under minus, an in-sample fit of 2000 genes
  would still reach R^2 near 1.

## D-008 (mean within-patient slope of VO2 on DO2 >= 0.1)
* plus: 40 patients x 6 occasions. True CO and CaO2 vary between patients and between occasions (within-patient
  log-SD 0.13 and 0.05), DO2 = 10 x CO x CaO2. True VO2 = patient baseline (extraction 0.27 x baseline DO2, so VO2 and
  DO2 are associated between patients) + patient slope x (DO2 - baseline DO2) + metabolic noise (5%). Slopes ~
  N(0.20, 0.05). CvO2 follows from the Fick equation with the true values. Measured: CO with thermodilution error
  (7%), CaO2 (2%), CvO2 (+-0.3 mL/dL), expired-gas VO2 = (true VO2 + pulmonary VO2 ~8 mL/min) x 5% error.
* minus: mean slope 0 (supply independence), with the between-patient slope SD 0.05, the between-patient association,
  the noise and all measurement errors unchanged. Control: expired-gas VO2 permuted across occasions within each
  patient. Relational (cardiac_output, vo2_expired_gas), which mismatches patients.
* Effect and judgement: a true slope of 0.20 because CO error attenuates the observed within-patient slope
  (reliability about 0.78). The population check gives an observed within-patient slope of 0.157 in plus and 0.000 in
  minus. The worlds keep two realistic traps: VO2 recomputed by the Fick equation from CO, CaO2 and CvO2 shares CO and
  CaO2 error with DO2 (mathematical coupling, a spurious slope of about 0.07 in minus), and a pooled between-patient
  slope is about 0.27 in minus. The control also exposes a criterion that ignores vo2_expired_gas.

## D-010 (district + 3 covariates predict y, out-of-sample r >= 0.25)
* plus: 150 districts with unequal sizes (lognormal weights; median 6 patients, a few districts can be empty).
  Covariates are age, BMI (lognormal) and SBP, correlated with each other; district deprivation shifts BMI and SBP.
  y = 50 + 10 x (covariate signal [10% of variance] + district effect [7%, partly deprivation] + noise [83%]).
  minus: covariate coefficients and district effects = 0; noise, district sizes and covariate distributions
  unchanged. Control: y permuted across patients. Relational (covariates, y).
* Effect: oracle r about 0.41. My expectation for an honest out-of-sample r is about 0.35 (most of the district part
  is lost to shrinkage with about 8 patients per district). Under minus, an in-sample fit of 153 parameters to 1200
  rows gives r of about 0.36, so the high-cardinality factor matters.

## D-011 (expression distinguishes AML/ALL, AUC >= 0.90)
* plus: 72 samples, 25 AML and 47 ALL (as in the classic leukaemia set) in random order. A lineage score = 3.0 x
  (type indicator) + N(0, 1) loads on a myeloid programme (60 genes, up) and a lymphoid programme (60 genes, down),
  with gene loadings 0.35-0.9 (per-gene d about 0.9-1.9; about 75 genes have |d| > 1.5), plus 6 unrelated background
  programmes. minus: lineage shift = 0. The lineage programmes stay as covariation unrelated to the label, and the
  class counts and noise are unchanged. Control: labels permuted. Relational (expression, myeloid).
* Effect: population AUC of the lineage score about 0.98. AML vs ALL is a difference of lineage, so a large
  separation is what a careful study expects. The large margin over 0.90 still leaves room for honest held-out
  estimation with 72 samples.

## D-012 (fenced vs open occupancy, difference >= 0.10 and one-sided test p < 0.05)
* plus: 10 plots, 5 fenced at random. Quadrat occupancy is Bernoulli(expit(-0.85 + 1.5 x fenced + plot effect
  [SD 0.5] + within-plot microhabitat [SD 0.7, AR(1) 0.6 along the 30 quadrats])). Pooled means are 0.64 fenced and
  0.32 open; the SD of plot occupancy within a group is 0.13. minus: fence effect = 0, so fenced plots have the
  open-plot distribution, with all other variation unchanged (pooled 0.32 vs 0.32).
* Control: exclosure labels reversed. Judgement: I did not use a permutation of the 5-of-10 labels, because with
  partial label overlap a correct plot-level test would hold at roughly its nominal 5% rate, which is too close to the
  HIGH_RATE bound. No relational pair, for the same reason.
* Effect: a difference of 0.32 is the size a 5-vs-5 plot design needs for good plot-level power. The between-plot
  and spatial variation make quadrats non-independent, so quadrat-level (pseudoreplicated) tests are anticonservative
  in minus.

## D-022 (quadratic OLS, 66 terms, out-of-sample r >= 0.30)
* plus: 300 runs, 10 readings with AR(0.4) correlation in their own units. The true quality function has 3 linear
  terms, 2 concave squares (optima) and 2 interactions. It explains 37% of the variance (Monte Carlo SD constant
  0.8178). minus: the process function = 0; noise and reading distribution unchanged. Control: y permuted across
  runs. Relational (X, y).
* Effect: OLS with 66 parameters on about 240-300 runs adds estimation variance of about p/(n-p-1) = 0.38 of the
  noise. I expect a held-out r of about 0.45, a clear margin. Under minus the in-sample r is about 0.47, so in-sample
  evaluation fails there.

## D-023 (beetles, partial correlation head-wing | body >= 0.30)
* plus: body length is a mixture of two sexes (14.4 and 15.6 mm, SD 1.0). Head and wing are linear in the recorded
  body length (slopes 0.175 and 0.71). The residuals (SD 0.185 and 0.53 mm, measurement error included) have
  correlation 0.37, the partial correlation. Marginal r(head, body) 0.74, r(wing, body) 0.85, r(head, wing) 0.76.
  minus: residual correlation = 0, with slopes, SDs and body-length distribution unchanged.
* Control: wing length permuted within blocks of 10 specimens of similar body length. This keeps the wing-body
  relation and destroys the residual association, so it exposes a criterion that uses the simple correlation.
  Relational (head_width, wing_length).
* Judgement: head and wing are generated given the recorded body length, so the minus partial correlation is exactly
  0. Measurement error in body length with head and wing depending on the true length would leave about 0.03 in
  minus. Effect 0.37 with n = 2000 (SE about 0.02).

## D-027 (OLS on 25 measurements, n = 60, out-of-sample MAE gain >= 0.10)
* plus: 25 measurements in 5 correlated blocks (r = 0.5), 8 non-zero coefficients, population R^2 0.72. minus: all
  coefficients 0; noise SD and measurement distribution unchanged. Control: y permuted. Relational (X, y).
* Effect and judgement: R^2 0.72 is a strong effect, but it is about the minimum for which the claim is reliably true
  with this design. With 26 parameters and 48-59 training samples, held-out OLS error variance is inflated about
  1.8-2.1 times, so R^2 0.72 gives an expected MAE gain of about 0.2-0.3. Under minus, in-sample OLS still shows a
  large gain.

## D-035 (classifier, balanced accuracy >= 0.65)
* plus: 1500 records, prevalence 12% (Bernoulli, so the count varies). Latent Gaussian variables with a 3-factor
  correlation structure. Positives are shifted on 7 variables, Mahalanobis distance 1.2 (optimal balanced accuracy
  about 0.73). Columns 0-6 are log-normal laboratory values; the others are vital and metabolic values in their units.
  minus: class shift = 0; prevalence, correlations and transforms unchanged. Control: labels permuted. Relational
  (features, positive).
* Judgement: the class imbalance is realistic and intended. Plain accuracy, or a 0.5-probability threshold, behaves
  very differently from balanced accuracy here.

## D-040 (skulls, partial correlation breadth-height | length >= 0.2)
* plus: length is a mixture of two sexes (181 and 189 mm, SD 6). Breadth and height are linear in length (0.13 and
  0.30 mm/mm), with residual SDs 5.8 and 5.5 mm and residual correlation 0.36. Marginal r(B,H) 0.29, r(B,L) 0.11,
  r(H,L) 0.35, typical cranial values. minus: residual correlation = 0, with everything else unchanged.
* Control: height permuted within blocks of 10 skulls of similar length. Relational (breadth, height).
* Effect: 0.36 with n = 300 (SE about 0.05), large enough to clear 0.2 with a margin. Generated given the recorded
  length, as in D-023.

## D-042 (1-NN regression, new compounds, r >= 0.30)
* Judgement call (main one in this batch): the brief distinguishes compound records from new compounds. I modelled
  1200 records of 600 distinct compounds: each compound has 1 + multinomial extra records (1-6), and repeat records
  have identical descriptor rows and independent assay noise (SD 0.4).
* plus: compounds come from 50 congeneric series in a 4-dimensional latent chemical space. There are 20 descriptors
  (4 right-skewed), each a linear map of the latent plus compound-level noise, in its own units. Activity = 6 + a
  smooth nonlinear function of the latent (SD 0.67) + a compound-specific deviation (SD 0.5, activity cliffs).
* minus: the descriptor-determined activity = 0. Compound deviations, assay noise, the repeat-record structure and
  the descriptors are unchanged. A record-level evaluation that finds the identical-descriptor duplicate therefore
  still shows a correlation of about 0.6 in minus. A compound-level evaluation shows none.
* Control: compound mean activities permuted across compounds (compounds identified by identical descriptor rows),
  keeping the within-compound deviations. Relational (X, y) shuffles records.
* Effect: I expect a held-out (new-compound) r of about 0.4-0.45.

## D-047 (hot flushes, proportion with week12 <= entry - 10 among screening >= 60 is >= 0.5)
* plus: stable true severity N(52, 13). Screening, entry and week 12 each add independent visit fluctuation (SD 9).
  True improvement from entry to week 12 is N(15, 9). Scores are clipped to 0-100. About 184 patients have screening
  >= 60. Expected proportion with a drop of 10 or more is about 0.63; the pooled mean entry - week12 among them is
  14.9.
* minus: mean true improvement = 0, with the SD of change, the severity distribution and the visit fluctuation
  unchanged. Regression to the mean after screening selection is preserved: among the selected, screening - entry
  averages 5.9 points in both worlds, so a criterion that measures change from screening is biased upward.
* Control: entry and week 12 swapped (time reversed). No relational pair: shuffling week12 across patients would
  pair high entry scores with random week-12 scores and make a correct criterion hold.
* Effect: a mean improvement of 15 points on a 0-100 scale, a moderate treatment-plus-placebo response.
