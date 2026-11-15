# WORLD_LOG — batch04 (C46–C54)

Common conventions. In every skeleton `plus` and `minus` call one shared generator with the same order of random draws,
so under one seed `minus` differs from `plus` only in the quantity that is set to null. Where removing a dependence
would change a marginal distribution, the dependence is redirected to an independent draw of the same variable (drawn
in `plus` too, unused there), so the marginals stay the same. Effect sizes were set from population-scale or oracle
checks (true generative weights, true responsive set, very large N); no analysis was run on study-shaped draws as a
candidate criterion, and Truth_Gate was not run (the package was imported only to load the `Study` objects).

## C46
- `plus`: 8 ordinal items (0–3) from one severity factor (loadings 0.58–0.72) cut at item-specific thresholds. About
  31% of patients have a total of at least 12 on items 2–8; population AUC of item 1 for that group is about 0.76
  (threshold 0.65; with 300 patients the AUC's SE is about 0.03).
- `minus`: item 1 loads on an independent factor with the same loading and cuts (same item 1 distribution, population
  AUC 0.50); items 2–8 are unchanged.
- Control: item 1 column permuted across patients.
- Judgement call: the claim is so specific that the effect size could only be set by its own statistic; I computed it
  once on a 200 000-patient population to calibrate the loadings, not on study-sized draws.

## C47
- `plus`: 32 of 80 patients malignant; 6 of 20 features shift by 0.9 patch-noise SD in malignant tissue (patch-wise
  strength 0.6–1.4). Each patient has their own feature offsets (SD 0.8) and slide-level staining, each patch a
  staining factor; features have different scales and offsets. Oracle patch-level AUC about 0.87, so a classifier
  learned on other patients should reach about 0.80–0.85.
- `minus`: the malignancy shift is zero; patient-level and staining structure unchanged (patches of one patient still
  resemble each other, so splitting by patch instead of by patient still looks predictive).
- Control: malignancy labels permuted across patients (patches stay with their patient).

## C48
- `plus`: 20/20 samples; 50 randomly placed genes of 1000 differ by 0.8 gene SD between classes; gene baselines and
  SDs vary; 3 weak hidden factors (loading SD 0.1). Analytic expectation for a linear-kernel centroid rule trained on
  32 samples: about 0.85 accuracy (threshold 0.60; with 40 samples the estimate's SE is about 0.06–0.08). Chosen
  that large because n = 40 gives a noisy accuracy estimate and non-linear kernels do worse than the linear bound.
- `minus`: class shift zero for every gene; everything else unchanged.
- Control: class labels permuted across samples.
- Judgement call: effect size set analytically only; I did not run any classifier.

## C49
- `plus`: a latent liability drives 10 of 30 speech measures (loading 0.45, mixed signs; all measures share a general
  factor 0.40); diagnosis = liability + assessment noise above a cut (prevalence about 35%, so plain accuracy and
  balanced accuracy differ); severity rating is a noisy 0–10 reading of the same clinical picture (AUC for diagnosis
  about 0.95). Oracle balanced accuracy of the speech measures about 0.77 (threshold 0.70).
- `minus`: the speech measures load on an independent variable instead of the liability (same speech distribution, no
  information about diagnosis or severity); diagnosis, severity rating and their relation unchanged.
- Controls: (1) speech-measure rows permuted across children, diagnosis and severity kept paired, so an analysis that
  gets its accuracy from the severity rating still holds under it; (2) diagnosis permuted across children.
- Judgement call: in `minus` speech is unrelated to severity as well, because any speech–severity link would carry
  diagnostic information through severity.

## C50
- `plus`: usual SBP N(152, 14), visit-to-visit SD 11; patients with reading 1 >= 160 (about 82 of 250) are treated,
  response mean 12 mmHg (SD 6) on reading 3. Mean fall reading 2 -> 3 among the selected about 11.9 (SD across studies
  1.9); it is at least 8 in about 98% of studies. Regression to the mean makes reading 1 -> 2 fall about 7.7 mmHg
  in both worlds.
- `minus`: treatment response zero; selection on reading 1, usual pressures and visit noise unchanged (fall 2 -> 3
  about 0, fall 1 -> 2 still about 7.7).
- Control: readings 2 and 3 swapped at random within patient (pre/post labels exchangeable if treatment does nothing);
  at least one patient is always swapped.
- Judgement call: only patients at or above 160 at screening are treated; the others are followed untreated.

## C51
- `plus`: 5 weather anomaly series and 3 calendar flags, all stochastic and autocorrelated (AR(1), rho 0–0.8);
  demand = 1000 + drivers · beta + AR(1) noise (rho 0.5, SD 75). Drivers carry about 53% of demand variance
  (threshold 0.30; one driver has no effect).
- `minus`: demand follows an independent realisation of the same driver process, so demand keeps its distribution and
  autocorrelation and the observed drivers carry no information.
- Control: drivers shifted circularly against demand by 52–348 weeks (keeps the autocorrelation of both series).
- Judgement call: no deterministic seasonal driver, because a deterministic calendar term would be shared by any
  "independent" copy and `minus` could not be a clean null.

## C52
- `plus`: 15 healthy, 15 patients; true slopes -16 vs -8 ms/session, between-subject slope SD 5.5, session noise SD 18;
  patients start slower (610 vs 520 ms). Standardised difference of fitted slopes about 1.3; roughly 93% of studies significant
  in the claimed direction.
- `minus`: both groups' mean slope set to the pooled -12 ms/session; start-level difference, slope variability and
  noise unchanged.
- Control: group membership permuted across subjects.

## C53
- `plus`: creatinine falls with age (-9 mg/24 h per year, r about -0.40); log albumin = 0.7 · log creatinine +
  0.135 per SD of age + noise (SD 0.40). Population partial correlation about 0.28 on the raw scale and 0.29 on the log
  scale (threshold 0.15; SE about 0.035 at n = 800); the unadjusted albumin–age correlation is only about 0.14.
- `minus`: the age term of albumin uses an independent age draw: partial correlation 0, while the unadjusted
  albumin–age correlation is about -0.14 (through creatinine). The structural albumin–creatinine relation is
  unchanged; their marginal correlation moves from 0.25 to 0.35 because age no longer offsets it.
- Control: age permuted across participants.
- Judgement calls: albumin skew kept moderate (log SD 0.40) so the claim holds for the raw-scale partial correlation
  named in the claim; albumin depends on creatinine directly rather than through a hidden common cause, so that the
  null has a partial correlation of exactly zero (a common cause would leave a small collider correlation).

## C54
- `plus`: 50/50 trials; a focal patch of 12 of 64 electrodes (8 x 8 grid) responds, about 2.3–6.5 microvolts (mean 4.5), with
  trial-to-trial gain SD 0.3; background = common activity (SD 3) + 6 smooth spatial patterns + local noise (SD 4).
  R-squared over the truly responsive electrodes about 0.30 (threshold 0.10); it reaches 0.10 in about 98% of
  studies even on half of the trials.
- `minus`: response zero at every electrode, background unchanged. No electrode responds, so electrodes picked from
  the same trials that are then analysed show only selection effects.
- Control: stimulus condition permuted across trials.
- Judgement call: the brief does not give the responsive electrodes; the set is fixed in the generator and not
  included in the data, so it has to be found from the data.

No brief was impossible to model as written.
