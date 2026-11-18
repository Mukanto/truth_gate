# Checklist log (dependencies between units, per brief)

For each brief: how the units of a real dataset of this kind depend on each other, the size chosen and where the size
comes from. Every dependence listed as "modelled" is present identically in `plus` and `minus`; only the claimed effect
differs. Sizes come from typical published values for this kind of data (my domain knowledge; no source was read).

## D-007 (expression 50 x 2000, survival_months 50)
- **Order in time:** patients are diagnosed over several years and tumour samples are processed in batches in roughly
  diagnosis order. Modelled: 4 contiguous processing batches (12-13 patients each), gene-wise batch shift SD 0.3 x gene
  SD (~9% of a gene's variance; batch effects in array / RNA-seq studies typically explain 5-15%). A calendar-era trend
  in survival is not modelled (one cohort over a few years; small next to the residual SD of log survival, 0.62).
- **Groups / repeated measurements:** one sample per patient; batches as above. No site is given; not modelled.
- **Shared components:** co-expression modules: 8 latent factors, 60% of genes belong to one module, which explains
  20-60% of that gene's variance (typical within-module gene-gene correlations 0.2-0.6 in tumour data); 20% of member
  genes load negatively. A sample-level normalisation / RNA-quality shift common to all genes, SD 0.15 log2. Survival
  depends on two module scores (proliferation, immune), i.e. on a shared component, not on single genes.
- **Many variables relative to units:** 2000 genes vs 50 patients (p/n = 40). With no signal, the largest of 2000
  gene-survival correlations at n = 50 is typically about 0.5.

## D-008 (cardiac_output, arterial_o2_content, venous_o2_content, vo2_expired_gas; 40 x 6)
- **Order in time:** 6 sequential occasions per patient; within-patient fluctuations follow AR(1) across occasions:
  cardiac output rho 0.4 (within-patient CV 15%, as in studies that change DO2 with fluids / inotropes), haemoglobin
  rho 0.6 (SD 0.5 g/dL), SaO2 rho 0.3 (SD 0.012), metabolic rate rho 0.5 (SD 15 mL/min); persistence over hours in ICU
  haemodynamics.
- **Repeated measurements of the same unit:** 40 patients x 6 occasions with patient-level levels: body surface area
  (SD 0.2 m^2), cardiac index (SD 0.6 L/min/m^2), Hb (SD 1.3 g/dL), SaO2 (SD 0.015), VO2 index (SD 18 mL/min/m^2) and a
  patient-specific slope (SD 0.08 around the mean). Between-patient variance dominates (ICC of cardiac output ~0.7).
- **Shared components:** (a) DO2 = 10 x CO x CaO2 and Fick VO2 = 10 x CO x (CaO2 - CvO2) share the measured CO and the
  measured CaO2 (mathematical coupling); thermodilution CO error CV 6% (average of three injections; single-injection
  reproducibility ~10%). (b) CaO2 and CvO2 share one Hb measurement (CV 2%, co-oximetry); saturation errors SD 0.008
  (arterial) and 0.015 (venous). (c) Between patients, body size scales both CO and VO2 (common factor), giving a
  between-patient VO2-DO2 association that is not the within-patient claim. (d) Expired-gas VO2 has its own,
  independent error, CV 6% (metabolic monitors are accurate to about 5-10%).
- **Many variables relative to units:** no (4 variables, 240 observations), but each within-patient slope rests on 6
  points, and DO2 measurement error (~55 mL/min vs a within-patient true SD ~130 mL/min) attenuates slopes by ~15%.

## D-010 (category 1200 x 150, covariates 1200 x 3, y 1200)
- **Order in time:** none given; recruitment order carries no information. Not modelled.
- **Groups:** patients clustered in 150 postal districts with uneven sizes (log-normal weights, SD 0.8 on the log
  scale: 0 to ~30 patients per district, mean 8, several districts with 0-2 patients). District effect on y: ICC about
  0.06 (area-level ICCs for health outcomes are typically 0.02-0.10). Each district has a deprivation index that also
  raises BMI (+1.2 kg/m^2 per SD) and SBP (+2 mmHg per SD), so covariates cluster by district too.
- **Shared components:** age -> SBP (0.45 mmHg per year) and BMI -> SBP (0.7 mmHg per kg/m^2), giving corr(age, SBP)
  about 0.40 and corr(BMI, SBP) about 0.24 (typical population values); deprivation is shared by BMI, SBP and y.
- **Many variables relative to units:** 150 district indicators + 3 covariates vs 1200 patients; about 8 patients per
  district, so a district mean of y has reliability only about 0.34 at ICC 0.06.

## D-011 (expression 72 x 2000, myeloid 72)
- **Order in time / batches:** samples come from two collection series processed separately (38 + 34, as in the
  classic training / independent-set split of this kind of study); gene-wise batch shift SD 0.3 x gene SD, independent
  of leukaemia type.
- **Groups / repeated measurements:** one sample per patient; batches as above.
- **Shared components:** 8 co-expression modules unrelated to lineage (as in D-007); a lineage programme of 40
  co-regulated marker genes driven by one programme score that also varies within each type (marker genes correlate
  about 0.3-0.7 with each other within a type); 40 further genes with small independent differences; sample-level
  normalisation shift SD 0.15 log2.
- **Many variables relative to units:** 2000 genes vs 72 samples (25 AML, 47 ALL).

## D-012 (occupied 10 x 30, exclosure 10)
- **Order in space / time:** quadrats lie along a transect inside each plot and seaweed is patchy: a latent AR(1) along
  the quadrat index with rho 0.5 (patches spanning a few quadrats), giving a lag-1 correlation of about 0.33 between
  neighbouring presence scores.
- **Groups:** 30 quadrats nested in each plot, and the treatment is applied to plots: plot random effect SD 0.3 on the
  probit scale (between-plot SD of occupancy ~0.11; substrate and tidal-height differences); a shore/year shift SD 0.2
  shared by all 10 plots of one survey.
- **Shared components:** all quadrats of a plot share the plot's fence status and plot effect.
- **Many variables relative to units:** no, but 300 quadrats rest on only 10 independent units (5 fenced, 5 open).

## D-022 (X 300 x 10, y 300)
- **Order in time:** runs are in production order. A common process state drifts (AR(1) rho 0.8 between consecutive
  runs) and loads on 7 readings; each reading also has its own AR(1) drift (rho 0.5); the part of the quality score not
  explained by the readings contains an AR(1) drift (rho 0.6, 20% of that part). Consecutive runs in continuous
  manufacturing are typically this strongly autocorrelated.
- **Groups:** raw-material lots of 10 consecutive runs: a lot effect on the 3 feedstock readings (loadings 0.5-0.6)
  and an independent lot effect in quality (15% of its unexplained part).
- **Shared components:** the process state shared by 7 readings gives inter-reading correlations of about 0.2-0.36;
  sensor noise SD 0.2 of each reading's SD (reliability ~0.96).
- **Many variables relative to units:** 66 polynomial terms vs 300 runs (p/n = 0.22); squares and products of
  correlated readings are strongly collinear.

## D-023 (head_width, wing_length, body_length; 2000)
- **Order in time:** none (museum series).
- **Groups:** specimens from 12 collecting localities of uneven size; locality mean log size SD 0.04 vs individual SD
  0.08 (about 20% of size variance, typical of geographic size variation within an insect species); locality offsets
  in relative head width and relative wing length SD 0.012 each, independent of each other (~10% of residual variance).
- **Shared components:** general body size drives all three traits (allometric slopes 0.9 head, 1.1 wing; correlation
  of each trait with body length ~0.85-0.9); body length measured with 1% error, so size is not completely removed by
  conditioning on it; 1% measurement error on head and wing.
- **Many variables relative to units:** no.

## D-027 (X 60 x 25, y 60)
- **Order in time / batches:** the 60 samples are measured in two assay runs of 30; run offsets SD 0.3 (in units of a
  measurement's SD) per measurement.
- **Groups:** none beyond the runs.
- **Shared components:** the 25 measurements are driven by 3 latent factors (communalities 0.2-0.55) plus measurement
  error SD 0.3 (reliability ~0.85 with the run offsets), so they are collinear.
- **Many variables relative to units:** 26 parameters (with intercept) vs 60 samples (p/n = 0.43).

## D-035 (features 1500 x 20, positive 1500)
- **Order in time:** unknown record order; not modelled.
- **Groups:** records from 4 sites (40/30/20/10%) with site calibration offsets SD 0.2 per variable; prevalence the
  same at every site (no site-label confounding).
- **Shared components:** 3 latent physiological factors (loadings 0.45-0.65) shared by 18 variables; 8 variables are
  skewed (log-normal lab values).
- **Many variables relative to units:** 20 variables vs 1500 records, but only ~225 positives (prevalence 15%).

## D-040 (breadth, height, length; 300)
- **Order in time:** three burial phases of one skeletal series (50/30/20%), with phase offsets in breadth and in
  height, SD 1 mm each, independent of each other (secular change; ~3% of variance).
- **Groups:** sex, about 50/50; males larger by 1.5 SD of general size (about 6 mm in length, 3.8 mm in breadth and
  height: typical 3-5% cranial dimorphism).
- **Shared components:** a general cranial size factor drives all three dimensions; length is an imperfect size proxy
  (own shape variation SD 4 mm + measurement error 1 mm), so residual size is shared by breadth and height;
  measurement error 1 mm per dimension (inter-observer caliper error 0.5-1.5 mm).
- **Many variables relative to units:** no.

## D-042 (X 1200 x 20, y 1200)
- **Order in time:** none (records pooled from several sources), record order shuffled.
- **Repeated measurements of the same unit:** 1200 records of 900 unique compounds (300 replicate records, some
  compounds 3-4 times; ~25% replicate records is typical of pooled bioactivity data); replicates have identical
  descriptors; replicate measurement SD 0.45 log units (typical inter-lab pIC50 variability 0.4-0.7).
- **Groups:** 8 assay sources with offsets SD 0.3 log units; 80% of compounds in 60 congeneric series (scaffolds) that
  form clusters in descriptor space and share a series-level activity.
- **Shared components:** descriptors correlated through 4 latent physico-chemical dimensions (size, lipophilicity,
  polarity, aromaticity).
- **Many variables relative to units:** 20 descriptors vs 900 compounds: not many, but distances in 20 dimensions.

## D-047 (screening, entry, week12; 600)
- **Order in time:** screening (week -2), entry (week 0), week 12. Symptom fluctuation (day-to-day and seasonal) as an
  Ornstein-Uhlenbeck process with time constant 4 weeks and SD 8 points: corr(screening, entry fluctuation) = 0.61,
  corr(entry, week 12) = 0.05; rating error SD 5 points per visit. Selection on screening >= 60 therefore selects
  partly transient highs that persist into entry and fade by week 12 (regression to the mean).
- **Groups:** 20 sites x 30 patients; site rater offset SD 3 points, constant across visits.
- **Shared components:** each patient's stable severity (SD 11) is common to all three scores; individual change
  varies between patients (SD 8).
- **Many variables relative to units:** no.
