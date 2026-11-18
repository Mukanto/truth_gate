# Checklist log (dependence between units, per data key)

For each brief and each data key, how the units in a real dataset of this kind can depend on each other: order in
time; groups, sites or repeated measurements of the same unit; components shared between variables; many variables
relative to the number of units. Each dependence gets a size and the place the size comes from. All sizes come from
general knowledge of typical values in the field. No reference was looked up in this session, because the sandbox
rules forbid reading anything else. Every dependence listed as modelled is present in both `plus` and `minus`. Only
the claimed effect differs between them.

---

## D-052 (young vs old training gain; `pre`, `post`, `young`, 40 participants)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| `pre`, `post` | **Repeated measurement of the same person.** Both scores share the person's stable true ability. | Yes. Ability SD 11 (young) and 13 (old); measurement error SD 5 per score, so test-retest reliability is about 0.83 to 0.87 | Typical test-retest reliability of standardised performance and cognitive scores is 0.8 to 0.9 |
| `pre`, `post` | **Shared measurement component in the improvement.** Improvement = post - pre contains -(error of pre), so it is negatively correlated with `pre`. This follows from the data structure itself. | Yes (comes from the measurement error SD 5) | Same reliability figure |
| `post` | **Between-person variability of the true gain.** | Yes. SD 4 points within an age group | Training studies show individual differences in gain of roughly 0.3 to 0.5 of the score SD |
| `post` | **The true gain depends weakly on baseline within a group** (compensation: weaker people gain a little more). | Yes. -0.1 points of gain per point of ability, correlation about -0.15 | Reported baseline-gain correlations in training studies are usually small, between -0.3 and +0.2 |
| `young` vs `pre` | **Group difference at baseline.** Older adults score lower and vary more. | Yes. Means 104 vs 96 (about 0.6 SD); SD 11 vs 13 | Age differences in performance scores are often 0.5 to 1 SD, and older samples are more heterogeneous |
| all | Order in time | Not modelled. All participants do the same programme; the order of participants carries no information, so the row order is random | Single cohort, one pre and one post session |
| all | Sites or cohorts | Not modelled. One programme with 40 people, and the brief has no site axis | — |
| all | Many variables relative to units | Not applicable (3 keys, 40 units) | — |

## D-055 (daily predictors X and outcome y, 1000 days in order, 6 features)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| `X` | **Order in time: autocorrelation.** Each predictor has its own AR(1) component. | Yes. phi from 0.55 to 0.85 per predictor | Daily environmental or behavioural series usually have lag-1 autocorrelation of 0.5 to 0.9 |
| `X` | **Common factor shared by the predictors** (e.g. one weather system drives temperature, humidity and pressure). | Yes. One shared AR(1) factor (phi 0.9), loadings between 0.4 and 0.7 in absolute value, so pairwise predictor correlations reach about 0.5 in absolute value | Typical correlations among daily meteorological and pollution variables are 0.2 to 0.6 |
| `y` | **Order in time: short-memory autocorrelation of the outcome's own noise.** | Yes. AR(1) phi 0.6, 75% of the noise variance | Typical for daily counts or loads after removing covariates |
| `y` | **Slow drift of the outcome level** (population, reporting or demand changes). | Yes. AR(1) phi 0.99, 10% of the noise variance | Slow level changes over months are common in multi-year daily series |
| `y` | **Day-of-week pattern** (lower on weekends). | Yes. Fixed weekly profile, 15% of the noise variance; the weekday of day 0 is random | Weekday effects in health-service and demand data are commonly 10 to 20% of the variance |
| `X`, `y` | Shared components between X and y other than the claimed relationship (e.g. a shared seasonal calendar) | Not modelled. A shared deterministic cycle would itself be predictive information about future y, so it is excluded from both worlds. y keeps its own weekly cycle, which X does not have | — |
| all | Groups or sites | Not applicable. One series | — |
| all | Many variables relative to units | No (6 predictors, 1000 days), but the effective number of independent days is about a third of 1000 because of the autocorrelation | Implied by the AR parameters above |

## D-056 (ANCOVA, 3 groups x 25 rats, `oxygen_uptake`, `body_mass`)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| `body_mass`, `oxygen_uptake` | **Shared size component (allometry).** VO2 scales with mass^b. | Yes. b = 0.67 on log scale; VO2 about 5 mL/min at 315 g | Intraspecific mass exponents of resting metabolism in rodents are about 0.6 to 0.75; resting VO2 of rats is about 15 to 20 mL/kg/min |
| `body_mass` | **Groups differ in body mass** (strain, diet or age groups). | Yes. Group means 295, 315, 335 g, about ±6%; within-group CV 10% (lognormal) | Body mass CV within a cohort of rats is usually 8 to 12%; group mass differences of 5 to 10% are common when groups are strains or diets |
| `oxygen_uptake` | **Shared measurement session.** Animals are measured over 5 days with 5 animals per group per day, and the respirometer calibration drifts from day to day. | Yes. Day effect SD 3% on log scale, shared by the animals with the same index in all three groups (balanced across groups) | Usual day-to-day drift of open-flow respirometry after calibration is a few percent |
| `oxygen_uptake` | **Individual variation after mass, and measurement error.** | Yes. Biological SD 9% plus measurement error 4% (log scale) | Mass-corrected resting metabolic rate typically has a between-individual CV of 8 to 15% |
| all | Cage clustering | Not modelled. Rats in metabolic studies are usually housed individually before respirometry, and the brief has no cage axis | Standard practice for respirometry |
| all | Order in time | Only through the measurement day above | — |
| all | Many variables relative to units | Not applicable | — |

## D-062 (12 species x 30 individuals, `femur`, `humerus`, `body_length`)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| all three | **Groups: species differ strongly in size.** Species means of body length run from 80 to 400 mm, and the bone/body ratios differ between species. Pooled across species, all three are correlated at r > 0.95 regardless of the within-species claim. | Yes. Log-uniform species means; species femur ratio SD 12%, humerus/femur ratio SD 8% | Range of a typical comparative sample of small to medium mammals |
| all three | **Common size factor within a species.** Both bones scale with body length. | Yes. Within-species slopes on log scale 0.95 ± 0.08 (femur) and 0.90 ± 0.08 (humerus); within-species correlation with body length about 0.75 to 0.85 | Long-bone vs body-length correlations within mammal species are typically 0.6 to 0.9 |
| `body_length` | **Subgroups within a species (sex).** Males are 4% longer. | Yes, through body length only | Moderate size dimorphism is common in small mammals |
| all three | **Species-specific variances.** Within-species body-length SD 5 to 9% and residual SDs 4 to 6% differ between species. | Yes | Typical within-species CVs of linear measurements |
| `femur`, `humerus` | **Shared residual component beyond body length** (integration of fore- and hindlimb, shared preparation or shrinkage, locality effects on limb proportions). Any such shared component *is* the claimed partial association. | It carries the claim: species-specific values in `plus`, zero in `minus` | — |
| all | Measurement error | Folded into the residuals. The null in `minus` is defined with respect to the recorded body length, so a latent size factor beyond recorded body length is not added (it would itself be a positive partial association) | Caliper error of 0.1 mm is small next to the biological residual |
| all | Order in time; many variables relative to units | Not applicable (3 measures, 30 per species) | — |

## D-064 (80 patients, 1500 genes, 8 clinical covariates, response)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| `expression` | **Many variables relative to units:** 1500 genes and 8 covariates for 80 patients. Any model can fit the 80 responses perfectly, so only a performance estimate on held-out patients means anything. | Yes (sizes from the brief) | Brief |
| `expression` | **Common factors shared between genes (co-expression modules).** 8 modules of 125 genes (proliferation, immune, stromal, ...); the remaining 500 genes carry no module. | Yes. Module loadings 0.35 to 0.8 of each gene's SD; 80% positive and 20% negative loadings | Tumour expression data typically show a handful of strong modules, each explaining 20 to 60% of its member genes' variance |
| `expression` | **Batch (sites or processing runs).** 4 batches of 20 patients, unrelated to response. | Yes. Batch shift SD 0.2 log2 units per gene | Usual size of residual batch effects after normalisation, 0.1 to 0.3 log2 |
| `expression` | **Shared per-sample component** (normalisation offset or RNA quality). | Yes. SD 0.1 log2, the same for all genes of a patient | Typical residual library or scale effects |
| `expression`, `clinical` | **Shared components between expression and clinical covariates:** the proliferation module and grade, stage, nodal status and tumour size all follow a latent tumour aggressiveness. | Yes. Loadings 0.45 to 0.6 on the latent factor, so correlations of about 0.2 to 0.35 | Grade-proliferation correlations of 0.3 to 0.5 are common in tumour cohorts |
| `clinical` | **Correlation among covariates** (age with performance status, performance status with albumin). | Yes. 0.3 and -0.3 | Typical clinical-cohort correlations |
| `clinical` | **Common denominator:** the covariates are standardised with the sample mean and SD, so each column has exactly mean 0 and SD 1 in every dataset | Yes (as the brief says "standardised") | Brief |
| `response` | **Bounded scale:** shrinkage is at most 100%, with some ties at 100 (complete response). | Yes. Clipped to [-50, 100] | RECIST percentage change |
| all | Order in time | Not modelled (patients are exchangeable; recruitment-order drift would be small) | — |

## D-066 (1000 patients, 15 clinical measurements, rare outcome)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| `X` | **Common factors shared between measurements (organ systems):** 3 blocks of 5 (inflammation, haemodynamics, renal or metabolic). | Yes. Loading 0.55 in each block, so within-block correlations are about 0.3 | Typical correlations among related laboratory and vital-sign measurements are 0.2 to 0.6 |
| `X` | **Sites:** 4 hospitals with different laboratory calibration and case mix. | Yes. Site offset SD 0.2 SD per measurement; prevalence of the outcome is the same at every site | Typical inter-laboratory bias of a few tenths of an SD |
| `X` | **Skewed laboratory values** (CRP, lactate, bilirubin are lognormal). | Yes. Log-scale SD 0.45 | Lab values are often right-skewed |
| `X` | **A minority subgroup with abnormal values** (8% of patients with shifted values in 9 measurements). | Yes, in both worlds: in `plus` this subgroup is the outcome group; in `minus` it is an equally sized subgroup unrelated to the outcome | — |
| `y` | Prevalence | 8% (Bernoulli per patient, so the count varies around 80) | "Rare outcome" in clinical cohorts: often 3 to 10% |
| all | Order in time | Not modelled (patients exchangeable; secular drift small over one cohort) | — |
| all | Many variables relative to units | No (15 features, 1000 patients), but only about 80 positives, so the minority class is small relative to 15 dimensions | Implied by prevalence |

## D-067 (60 rats, kidney weight, heart weight, body mass)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| all three | **Common size factor (allometry on body mass).** | Yes. Exponent 0.90 for heart, 0.85 for kidney; each organ's correlation with body mass is about 0.70 | Organ-to-body-mass correlations within a rat cohort are typically 0.5 to 0.8 |
| all three | **Groups (litters).** The 60 rats come from 20 litters of 3; litter shares genes and maternal environment. Litter identity is not recorded and the rows are in random order. | Yes. ICC 0.15 for body mass and for each organ's residual. In `plus` the kidney-heart residual correlation is the same at the litter and at the individual level; in `minus` it is zero at both | Litter ICCs of 0.1 to 0.3 are typical for rodent body and organ weights |
| `kidney_weight`, `heart_weight` | **Shared component beyond body mass** (lean mass, hydration or blotting state of the same animal). This shared part *is* the claimed relation. | It carries the claim: residual correlation 0.45 in `plus`, 0 in `minus` | — |
| all three | Measurement error | Folded into residuals (balances to 1 mg are negligible; blotting variability 2 to 3%) | — |
| all | Sex | Not modelled. One sex (male), standard for such cohorts | — |
| all | Order in time; many variables relative to units | Not applicable | — |

## D-068 (25 populations x 40 beetles, head width, wing length, body length)

| Key | Dependence | Modelled? Size | Where the size comes from |
|---|---|---|---|
| all three | **Groups: populations differ in mean size** (geographic size variation). | Yes. Population SD of mean body length 0.8 mm (CV about 7%) | Typical between-population size CVs in beetles are 3 to 10% |
| `head_width`, `wing_length` | **Between-population relationship of head and wing beyond body length** (e.g. habitat-related flight morphology). This lies outside the within-population claim. | Yes, the same in both worlds. Correlation 0.4 between population-level head and wing deviations | — |
| all three | **Common size factor within a population.** | Yes. Within-population correlations with body length about 0.74 (head) and 0.8 (wing) | Typical for linear body measurements in insects |
| `body_length` | **Subgroups within a population (sex):** females are 0.5 mm longer. | Yes, through body length only | Female-biased size dimorphism is common in beetles |
| `wing_length` | **Population-specific coefficient.** The within-population head coefficient varies between populations. | Yes. SD 0.12 mm/mm around the mean in `plus`; the same component in `minus` comes from an independent head-residual copy, so every population's coefficient is 0 | Moderate heterogeneity of allometric coefficients among conspecific populations |
| all | Measurement error | Folded into the recorded values. The null in `minus` is defined with respect to the recorded body length; a hidden latent size would create a spurious head coefficient and is not added | Micrometer error of 0.02 to 0.05 mm is small next to the within-population SDs |
| all | Order in time; many variables relative to units | Not applicable | — |
