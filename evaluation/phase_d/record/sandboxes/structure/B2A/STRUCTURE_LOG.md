# STRUCTURE_LOG, sandbox B2A (Phase D structure author)

15 reference worlds written, one per case in `cases\`. Measured with seeds 1000..1199 on 200 samples per world, using the
note's `stat` code (values: mean (sd), plus / minus; both worlds identical because the structure is generated before and
independently of the `minus` change). Every file passes my own checks: keys, shapes and dtypes equal the brief's, finite
values (NaN only where the brief declares it, D-014 and D-041), control returns changed data, every call at most 10 ms.
No online source was needed or fetched. No criterion was written or run; no analysis of any kind was run on samples
except the structure statistic, per-world variance of y, and for the time series the lag-1 autocorrelation of y
(descriptive checks of the generator, to confirm that `minus` leaves the outcome's variance and dynamics unchanged).

## Common design of `minus`

The claimed relationship is severed by moving the signal part of y to other units: a permutation of samples (or of
subjects, of compounds, of entries), or, for time series, a circular shift of the signal by 25-75% of the series length
(and a permutation of stations in D-004). Labels (bool y) are permuted. So X, the noise, the variance and distribution
of y, its own autocorrelation and every dependence listed below are identical in both worlds; only X-to-y information is
null. Where the brief allows, no key is added: all dependencies are carried by the arrays' axes. The faulty analyses
need no key beyond X and y (and category in D-010); nothing was planted for them. Controls: permute y across the
units (subject blocks in D-044, circular shift of y by a random large lag in the time series, station order also in
D-004). Control id equals the case id.

Effect sizes were set by reasoning from the generator parameters (rule 8), not estimated; the stated "expected" values are
back-of-envelope, not measured.

## D-004 (daily forecasts versus persistence, 40 stations x 250 days x 5 predictors)
- Structure: value 0.8 = approved (proposed typical lag-1 autocorrelation, source gives none). Measured 0.8265 (0.0211) / 0.8265 (0.0211), tolerance 0.16.
- Other dependencies: predictors = station offset (variance share 0.05) + a component common to all stations, AR(1) 0.93 (0.75) + local AR(1) 0.5 (0.20); 0.3 correlation between predictors in the common part. y noise (variance 0.8) = common-in-time AR(1) 0.95 (0.30) + station-day AR(1) 0.20 (0.50). Outcome lag-1 autocorrelation about 0.5 (measured 0.52 plus, 0.50 minus, pooled-centred), i.e. persistence is a competitive baseline in both worlds.
- `minus` nulls: the predictors' contribution to y (station order permuted and series shifted by 62-188 days).
- Keys the error needs: X and y only. Slowly varying shared components in X and in the outcome noise are what make a spurious in-period fit transferable to interleaved days.
- Effect parameters (plus): y = sqrt(0.20) z + noise, z = unit-variance linear combination of the 5 predictors with weights (1, -0.9, 0.7, -0.6, 0.5); total variance 1, noise variance 0.8. Expected skill versus persistence (future days) about 0.1 in plus, about -0.1 in minus.

## D-005 (ridge R-squared, 100 samples x 150 biomarkers)
- Structure: 1.5 = shape (150/100), set by the brief. Measured 1.5 (0) / 1.5 (0).
- Other dependencies: 5 latent factors, communality 0.6 per biomarker (fixed loadings), unique variance 0.4.
- `minus` nulls: the factor-driven part of y (permuted across samples).
- Keys the error needs: X and y only.
- Effect: y = sqrt(0.55) z + sqrt(0.45) e, z = unit-variance combination of the 5 factors (weights 1, 0.8, 0.6, 0.5, 0.3). Expected out-of-sample R-squared of the penalty-1 ridge fitted on 80 samples about 0.2 to 0.3 (the noise-fitting share of the min-norm-like fit costs about 0.2).

## D-010 (district + covariates, 1200 patients x 150 districts)
- Structure: 0.125 = occupied districts / patients, approved (proposed, from the brief's size). Measured 0.125 (0) / 0.125 (0); every district gets at least one patient.
- Other dependencies: district sizes 1 + multinomial with gamma(2) weights (mean 8, uneven, some 1-2); three correlated covariates (age 0.10 to BMI, 0.35 to pressure, 0.30 BMI-pressure) with a district-level share 0.09 of their variance; natural units (age 52 sd 14, BMI 27 sd 4.5, pressure 130 sd 16).
- `minus` nulls: covariate effect and district random effect (signal permuted across patients).
- Keys the error needs: category, covariates, y (all in the brief).
- Effect: y = covariate effects (0.24, 0.18, 0.10 per sd; variance about 0.13) + district effect (variance 0.06, ICC 0.06) + noise (variance 0.81). Expected out-of-sample correlation about 0.35.

## D-014 (laboratory values, 250 x 20, NaN 25%)
- Structure: 0.25 = approved (proposed typical missing rate). Measured 0.2498 (0.0102) / 0.2498 (0.0102), tolerance 0.05.
- Other dependencies: 3 latent factors, communality 0.5; missingness by column (rates 0.10 to 0.40, mean 0.25) times a patient-level propensity (gamma, mean 1), independent of y and of the values.
- `minus` nulls: the laboratory-value part of y (permuted across patients).
- Keys the error needs: X (with NaN) and y.
- Effect: y = sqrt(0.40) z + sqrt(0.60) e, z = unit-variance combination of the complete values (12 non-zero weights between -0.8 and 1.0). Expected out-of-sample R-squared of the ridge after mean-type imputation about 0.2.
- Note: under `minus` X carries no information on y, so the size of any label-using imputation's leak is whatever the faulty procedure builds from chance association and cannot be tuned by me without planting.

## D-022 (second-order polynomial, 300 x 10)
- Structure: 0.2167 = shape (65 terms / 300), set by the brief. Measured 0.2167 (0) / 0.2167 (0).
- Other dependencies: readings share a process state (correlation 0.3).
- `minus` nulls: the response surface (permuted across runs).
- Keys the error needs: X and y only.
- Effect: signal variance about 0.61 (linear weights 0.345, 0.2875, 0.23, 0.1725, 0.115; squares of readings 1 and 2 with 0.1725, 0.138; products 3x4 and 5x6 with 0.1725, 0.138), noise variance 1; signal share about 0.38. Expected out-of-sample correlation about 0.45-0.5.

## D-027 (OLS MAE skill, 60 x 25)
- Structure: 0.4167 = shape (25/60), set by the brief. Measured 0.4167 (0) / 0.4167 (0).
- Other dependencies: measurements correlated 0.25; 8 informative measurements with equal weights scaled to signal variance 2.33, noise variance 1 (signal share 0.70).
- `minus` nulls: the linear signal (permuted across samples).
- Keys the error needs: X and y only.
- Effect: expected out-of-sample MAE skill about 0.2-0.3 (MSE inflation of OLS with 25 of 48-60 samples is about 1.7-2.1 times the noise).

## D-029 (1-NN MAE skill, 600 rows x 8, repeated records)
- Structure: 0.3 approved; measured 0.3378 (0.0104) / 0.3378 (0.0104), tolerance 0.06. I chose the upper part of the tolerance because the note says the MAE criterion needs about 0.36 to separate the worlds.
- Other dependencies: about 70 groups of 2-4 records (probabilities 0.3, 0.5, 0.2) of the same entry, covering about 34% of rows, copies differ by 0.03 sd in X and 0.03 in the latent target; rows shuffled. Properties follow 3 latent factors (communality 0.6). Target = exp(1.5 x latent), right-skewed (a skewed target makes the 1-NN MAE ratio on unrelated entries smaller than the Gaussian 1.41).
- `minus` nulls: the properties' contribution to the target, permuted at entry level (copies keep the same target).
- Keys the error needs: X and y; repeated records are carried by the rows themselves.
- Effect: latent = sqrt(0.85) z + sqrt(0.15) e. Expected 1-NN MAE skill on distinct entries about 0.2; on minus, with copy share in the fitting rows of about 0.3, the apparent skill is near the 0.10 threshold (borderline, see questions).

## D-039 (monthly calibration slope, 400 months x 3)
- Structure: 0.9 = approved (proposed lag-1 autocorrelation). Measured 0.8915 (0.0140) / 0.8915 (0.0140), tolerance 0.18.
- Other dependencies: predictors AR(1) 0.95, 0.90, 0.85 with 0.2 shared innovations; y noise AR(1) 0.8.
- `minus` nulls: the predictors' contribution to y (signal shifted by 100-300 months).
- Keys the error needs: X and y only (slow predictors and a slow outcome produce spurious in-period fits).
- Effect: y = sqrt(0.5) z + sqrt(0.5) noise, z = unit-variance combination (1, -0.8, 0.6). Measured lag-1 of y 0.85 (plus), 0.84 (minus). Expected future-months slope about 1.

## D-041 (civil-war onset AUC, 1400 x 25, NaN 30%)
- Structure: 0.3 = approved (proposed missing rate). Measured 0.2959 (0.0048) / 0.2959 (0.0048), tolerance 0.06.
- Other dependencies: 56 onsets (4%, exact count); 3 latent factors (communality 0.25); missingness by column (0.05 to 0.55, mean 0.30) times a country-year propensity (gamma 3, mean 1), independent of the onset.
- `minus` nulls: the onset labels (permuted; the class shift stays in X, tied to the original labels, so X is unchanged).
- Keys the error needs: X (with NaN) and y.
- Effect: class mean difference 0.5 sd, alternating in sign over the 25 indicators (Mahalanobis D squared about 6 before missingness, about 4 after). Expected out-of-sample AUC about 0.8-0.85. As in D-014 the label-using imputation's leak under `minus` is a chance effect of about 56 onsets.

## D-042 (1-NN correlation, 1200 records x 20, near-identical records)
- Structure: 0.3 approved; measured 0.3452 (0.0071) / 0.3452 (0.0071), tolerance 0.06 (upper part chosen, since the correlation under no effect is about the share of records with a copy in the fitting set).
- Other dependencies: about 140 groups of 2-4 records (same size mix as D-029), differing by 0.04 sd in X and 0.05 in y; descriptors follow 5 latent factors (communality 0.75).
- `minus` nulls: descriptors' contribution to the response, permuted at compound level (copies keep the same response).
- Keys the error needs: X and y only.
- Effect: y = sqrt(0.65) z + sqrt(0.35) e. Expected 1-NN correlation on distinct compounds about 0.45-0.5.

## D-044 (subject-level repeated trials, 60 x 30 x 25)
- Structure: ICC 0.5 = approved (proposed moderate ICC). Measured 0.4951 (0.0124) / 0.4951 (0.0124), tolerance 0.10.
- Other dependencies: features correlated 0.16 in both the subject and the trial part; y = feature effect + subject effect (variance 0.25, independent of the subject's features) + trial noise (0.30).
- `minus` nulls: the feature-driven part of y (permuted across whole subjects).
- Keys the error needs: none beyond X and y; the subject axis carries the repeated-measures structure. Subject-specific feature offsets (25 dimensions against 60 subjects) are what lets a fit on trials of the same subjects reproduce subject-level outcome variance.
- Effect: feature-driven variance 0.45 (10 features with alternating signs, equal size), total variance 1. Expected new-subject MAE skill about 0.15.

## D-054 (expression, 80 x 1000, 20-feature selection)
- Structure: 12.5 = shape (1000/80), set by the brief. Measured 12.5 (0) / 12.5 (0).
- Other dependencies: 50 co-expression modules of 20 genes (correlation 0.36 within modules); balanced 40 cases / 40 controls; two modules (40 genes) shifted by 0.65 sd between cases and controls (plus).
- `minus` nulls: the diagnosis labels (permuted; the shifted genes stay tied to the original labels, so X is unchanged).
- Keys the error needs: X and y only.
- Effect: gene-level standardised difference about 0.6 in 40 of 1000 genes. Expected out-of-sample AUC of the whole pipeline about 0.7-0.8.

## D-060 (imaging features, 100 x 500, 20-feature selection)
- Structure: 5.0 = shape (500/100), set by the brief. Measured 5.0 (0) / 5.0 (0).
- Other dependencies: 20 regions of 25 features (loading 0.7, correlation 0.49 within a region).
- `minus` nulls: the region-driven part of y (permuted across samples).
- Keys the error needs: X and y only.
- Effect: y = sqrt(0.30) F0 + sqrt(0.04) F1 + noise (variance 0.66), F0 and F1 the latent factors of regions 0 and 1. Expected out-of-sample R-squared of the pipeline about 0.2.

## D-066 (rare outcome, 1-NN balanced accuracy, 1000 x 15)
- Structure: minority share 0.08 = approved (proposed). Measured 0.08 (0) / 0.08 (0) (exactly 80 outcomes).
- Other dependencies: 2 latent factors (communality 0.3); a minority subgroup shifted by 1.3 sd in 8 of 15 measurements (plus).
- `minus` nulls: the outcome labels (permuted; the subgroup shift stays tied to the original labels, so X is unchanged).
- Keys the error needs: X and y only. The data carry no copies; the copying is a step of the faulty analysis.
- Effect: Mahalanobis separation about 3 (shift vector length squared 13.5). Expected 1-NN balanced accuracy for new patients about 0.7; I could not check it (rule 8), the 0.65 threshold is within a few points of it.

## D-055 (daily correlation, 1000 x 6)
- Structure: 0.8 = approved. Measured 0.8126 (0.0082) / 0.8126 (0.0082), tolerance 0.16.
- Other dependencies: predictors AR(1) 0.92, 0.88, 0.84, 0.80, 0.76, 0.70 (mean 0.82) with 0.2 shared innovations; y noise AR(1) 0.92.
- `minus` nulls: the predictors' contribution to y (signal shifted by 250-750 days).
- Keys the error needs: X and y only.
- Effect: y = sqrt(0.28) z + sqrt(0.72) noise, z = unit-variance combination (1, -0.8, 0.6, -0.5, 0.4, -0.3). Measured lag-1 of y 0.90 in both worlds. Expected future-days correlation about 0.5.

## Final-message points (also in my reply)
- Time-series claims (D-004, D-039, D-055): my generators make the outcome persistent and the predictors slow, which is the only mechanism by which a linear ridge can profit from interleaved days. How large the leak is depends on the faulty analysis; I cannot measure it (rule 8).
- D-039: the claim's slope statistic on a short test window has a sampling sd near 1 under no relation even for the correct analysis (about sqrt((1-q)/(p q)) for test share q, p = 3 predictors), so a clean correction is hard at this size whatever the world.
- D-014, D-041: a label-using imputation leaks only through chance association when X and y are unrelated; with realistic missingness the leak under `minus` is small and not tunable without planting.
- D-029, D-042: group-size mix and share are set near the top of the note's tolerance so that the duplicate leak can reach the thresholds; the criteria are borderline.

## Repairs
None requested.

## Return of D-014 and D-041 (rule 9, non-finite values): nothing changed
The check script rejected both files with "X has non-finite values". I changed neither file. Reason: no file can meet
both the brief and rule 9.
- The brief declares X with NaN where a value was not measured (D-014: "a value that was not measured for a patient is
  NaN"; D-041: "an indicator that was not recorded for a country-year is NaN"), and rule 1 requires the brief's meanings.
- The approved structure statistic of both cases is `np.mean(np.isnan(X))` (0.25 and 0.3, rule 2). A world without NaN
  gives 0.0, which fails rule 2 by the full value; a world with inf instead of NaN is also non-finite and gives 0.0 on
  the statistic; a finite sentinel (for example 0 or a large number) gives 0.0 as well and would contradict the brief's
  meaning of X.
- So the only worlds that meet the brief and the approved value contain NaN, which rule 9 rejects. The missingness is the
  exploited structure itself, so it cannot be moved out of X without a new key or a changed brief, and rule 5 forbids both.
The current files stay as they are (measured NaN share 0.2498 and 0.2959 on 200 samples per world, see above). I saw no
count, rate or result of any later check.
