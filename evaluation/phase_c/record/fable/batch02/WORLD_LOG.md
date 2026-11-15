# WORLD_LOG — batch02 (C16–C30)

General conventions used in every skeleton:

* `plus` and `minus` are the same generator with one parameter changed; both consume the random stream identically,
  so everything the claim is not about has the same distribution (and, per seed, the same values) in both worlds.
* Effect sizes were chosen so that the analysis named in the claim, done at the level of the experimental unit, has a
  power of roughly 0.9 (calculated by hand from the generator's variances; no test or analysis was run). With the small
  unit counts of several briefs this needs a large standardised effect; that is what a study of that size can detect.
* Where removing the effect would also change a marginal distribution (C19, C24, C30), `minus` replaces the source of
  the effect with an independent variable of the same distribution, so variances and marginals are kept.
* Group masks have fixed group sizes at random positions. Every permutation control re-draws until the result differs
  from its input, so a control never returns the data unchanged.
* Checks I ran (plain Python, my own script in the scratchpad): docstring equals the brief, module-level node types,
  forbidden names, keys/shapes/dtypes, finiteness, time per call (all under 2 ms after import warm-up), controls change
  the data, and descriptive oracle summaries (group mean differences, known-coefficient residuals) showing the effect
  in `plus` and not in `minus`. No criterion-like analysis was written or run; Truth_Gate was not run.

## C16
`plus`: 24 treated / 24 untreated rats; heart = 240 + 2.2·body + 65 mg·treated + N(0, 65); the drug also makes treated
animals about 25 g lighter (both worlds). `minus`: the direct 65 mg effect is 0; the body-mass effect of the drug stays.
Control `permute_treated`: treatment labels permuted across animals.
Effect 65 mg (about 5.5% of heart weight, about 3.3 standard errors of the adjusted coefficient). Judgement call: the
drug's effect on body mass and the non-zero intercept are kept in `minus`, so unadjusted or ratio-based comparisons are
confounded there, as they would be in a real study.

## C17
`plus`: four dose groups (0, 5, 10, 20 mg/kg) of three animals; density = 11 + 0.16·dose + animal N(0, 1) + section
N(0, 0.5) + neuron N(0, 2). `minus`: slope 0, all three variance levels kept. Control: dose permuted across animals.
Slope 0.16 gives +3.2 spines/10 µm at the top dose, about 3.6 standard errors when the animal is the unit (12 animals).
Judgement call: the hierarchy (animal > section > neuron) is real in both worlds, so neurons are not independent.

## C18
`plus`: liking on a 0–100 slider, SD about 15, treatment +16 points (d about 1.05, needed for 20 per group);
willingness to pay is log-normal, correlated with liking through a participant trait (r about 0.3), and has its own
treatment effect of 0.25 log units. `minus`: liking effect 0; willingness to pay unchanged, including its treatment
effect. Control: participants (both ratings together) re-dealt at random to the two conditions.
Judgement call: the claim is only about liking, so by the fixed rule the willingness-to-pay effect stays in `minus`.

## C19
`plus`: 150 of 1000 voxels (random positions, not given in the data) form a region driven by the trait with population
correlation 0.75 in each session; every voxel also has a stable subject-specific component (30% of the non-signal
variance, same in both sessions), a whole-brain session effect (10%) and independent noise (60%). `minus`: the region
is driven by a subject variable independent of the trait (correlation with the trait 0), same variances and structure.
Control: trait scores permuted across participants.
Effect 0.75 because the claim needs a mean correlation of at least 0.5 with only 16 participants (oracle region mean
0.74, SD 0.07 across draws). Judgement calls: the region is not marked in the data (the brief gives no mask), so it has
to be found by whoever writes the criterion; the second session is an independent measurement of the same subjects;
no spatial smoothness was modelled.

## C20
`plus`: scores N(70, 10) with 4% low-effort participants around 45 in either condition, clipped to 0–100; treatment
+7.5 points (d about 0.67 on the contaminated distribution, about 3.4 standard errors with 50 per group). `minus`:
effect 0, same contamination. Control: participants re-dealt at random to the two conditions.
Judgement call: the low-effort tail is kept in both worlds because the claim says "on all participants".

## C21
`plus`: about 15% defective units (Bernoulli per unit); 50 features in five correlated sensor channels (within-channel
correlation 0.4), with fixed feature scales and offsets; defective units are shifted by 0.67 SD on six fixed features
(Mahalanobis distance 2, so a balanced linear rule reaches about 0.84 and a prior-weighted one about 0.76 on new
units). `minus`: shifts 0, the features carry no information. Control: defect labels permuted across units.
Judgement call: the informative features are fixed indices (the same sensor features in every dataset).

## C22
`plus`: 4 treated / 4 control tanks; tank level log-normal (SD 0.20 on the log scale) around 40 per litre, sample
patchiness log-normal SD 0.25, Poisson counts; treated tanks at 0.45 of the control density. `minus`: ratio 1.
Control: treatment labels permuted across tanks.
Effect: a 55% reduction, about 4.5 standard errors of the difference of tank means; with four tanks per group a smaller
effect would not be detectable. Judgement call: the ten samples of a tank share the tank level (intraclass correlation
about 0.3), in both worlds.

## C23
`plus`: 5 treated / 5 control rats; latency = 115 s + learning (0, 15, 28 s over days) + rat N(0, 22) + day noise
N(0, 12) + 55 s for treated rats, clipped at the 300 s cut-off (not reached in practice). `minus`: drug effect 0.
Control: treatment labels permuted across rats.
Effect 55 s (about 3.7 standard errors with the rat as the unit). Judgement call: the three days are repeated measures
of one rat (intraclass correlation about 0.77), in both worlds.

## C24
`plus`: C log-normal; A = 20 + 0.5·C + gamma noise; B = 30 + 0.6·C + 0.75·(A's own variation) + gamma noise, all in
linear units and linear in C. Expected R-squared gain about 0.10 (partial correlation about 0.48). `minus`: the 0.75
term comes from a variable independent of A with the same distribution, so the gain is 0 in expectation while B keeps
its marginal distribution and both genes keep their dependence on C. Control: gene A permuted across samples.
Judgement call: the conditional means are linear in C on the linear scale, so the null of the claim's own linear
model is exact in `minus`.

## C25
`plus`: population = 250 + 1.5·t thousand plus persistent AR(1) deviations (phi 0.9, SD 4); admissions = 8 per thousand
+ 20 per month per year of time + seasonal cosine (amplitude 80) + AR(1) "waves" (phi 0.6, SD 55) + N(0, 20), rounded.
`minus`: time trend 0; admissions still rise through population growth (about 12 per year). Controls: time permuted
across months; time reversed (the trend then has the opposite sign).
Effect 20 admissions/month/year (about 1% per year), roughly 3.5 standard errors when autocorrelation is allowed for.
Judgement call: month-to-month residuals are autocorrelated and seasonal in both worlds, as real admission series are.

## C26
`plus`: 20 + 20 samples; gene baselines N(8, 1.5), gene SDs 0.3–1.0, three sample-level factors unrelated to class;
50 random genes differ between classes by 0.8 within-class SD (half up, half down), giving an expected accuracy of
about 0.9 on new samples for a centroid classifier trained on 40 samples. `minus`: no gene differs.
Control: class labels permuted across samples.
Judgement calls: classes are exactly balanced, so 0.60 is not reachable by guessing the majority class; with 40 samples
an honest accuracy estimate is itself noisy (chance level 0.5, SD about 0.08), which the criterion writer has to handle.

## C27
`plus`: 10 exposed / 10 control dams, 8 pups each; activity = 100 + litter N(0, 15) + pup N(0, 18) + 25 for exposed
litters. `minus`: exposure effect 0. Control: exposure labels permuted across dams.
Effect 25 units (about 3.6 standard errors with the litter as the unit). Judgement call: pups of one dam share the
litter effect (intraclass correlation about 0.4), in both worlds.

## C28
`plus`: 250 neurons, mean rates log-normal around 5 spikes/s; each neuron has a true orientation index drawn from
N(0, 0.3) (clipped to ±0.9), so truly vertical-preferring neurons have a mean true index of about 0.24; spike counts
in a 1 s window are Poisson with trial-to-trial gain fluctuations (gamma, CV 0.5). `minus`: true index 0 for every
neuron; any observed preference is trial noise (observed index SD about 0.13). Control: within each neuron the 30
presentations are re-dealt at random to the two orientations.
Judgement calls: the null is "no neuron has an orientation preference" (not "mean index just below 0.1"); vertical and
horizontal presentations are separate trials, so trials are not paired across the two arrays.

## C29
`plus`: 50 signature probe sets (random positions), 25 sensitive / 35 resistant lines; signature probes are higher in
sensitive lines by 0.8 log2 on average (probe effects SD 0.3), share a co-regulation factor per line (SD 0.30), and all
probes share an array offset (SD 0.15) plus noise SD 0.6; 40 non-signature probes differ by sensitivity in either
direction. `minus`: signature difference 0, everything else kept. Controls: sensitivity labels permuted across cell
lines; the signature replaced by a random probe list of the same size.
Effect 0.8 log2 against the claimed threshold of 0.5 (standard error of the difference about 0.09).

## C30
`plus`: usual pressure N(155, 12); the two baseline readings share a visit-level deviation (SD 3) and each has reading
error SD 6; true fall = 10 + 0.45·(usual − 155) + N(0, 6); week 12 has its own visit and reading error. Expected
correlation between (first − week 12) and the second reading about 0.43. `minus`: the 0.45 term comes from a patient
variable independent of pressure, so mean and spread of the fall are kept and the expected correlation is about 0.06.
Control: the second baseline reading permuted across patients.
Judgement call: the two baseline readings are taken at the same visit, so I gave them a small shared visit-level
deviation; this leaves a small positive correlation (about 0.06) in `minus` that is not a real dependence of the fall
on starting pressure. I did not use "permute week-12 readings" as a control: it would break the pairing inside the
fall itself and produce a large correlation for reasons unrelated to the claim.

## Briefs that could not be modelled as written
None. Ambiguities noted above: C19 (region not given), C26 (the claim has no test, only a threshold on a noisy
estimate), C30 (shared error of the two baseline readings), C18 (second outcome's own effect kept in `minus`).
