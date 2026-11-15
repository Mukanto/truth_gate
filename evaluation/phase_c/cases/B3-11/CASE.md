# CASE B3-11

## 1. Identity
Case id B3-11; world id C24; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key KRO93. Passage (as recorded in the part-1 private note): Abstract (EconPapers/RePEc record of doi:10.2307/2983064): 'Spurious correlation refers to the correlation between indices that have a common component ... The consequences of using a single ratio as either the dependent or one of the independent variables in a multiple-regression analysis are described.'
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: Across tumour samples, the expression of gene A and the expression of gene B are positively related after accounting for the expression of gene C: the gain in R-squared when gene A expression is added to a linear regression of gene B expression on gene C expression is at least 0.05.
Data keys:
  * `gene_a_expression` (samples,) float: Quantitative PCR expression signal of gene A in each tumour sample, in arbitrary linear units.
  * `gene_b_expression` (samples,) float: Quantitative PCR expression signal of gene B in each tumour sample, in arbitrary linear units.
  * `gene_c_expression` (samples,) float: Quantitative PCR expression signal of gene C in each tumour sample, in arbitrary linear units.
Sizes: samples = 96; gene_a_expression, gene_b_expression and gene_c_expression each have shape (96,).

## 4. Mapping
Documented error (note): R-squared of the simple regression of gene_b_expression/gene_c_expression on gene_a_expression/gene_c_expression; claim holds when R-squared >= 0.05. Documented parameter: both quotients share the gene C signal, which varies from sample to sample.
Documented correction (note): Gain in R-squared when gene_a_expression is added to the regression of gene_b_expression on gene_c_expression; claim holds when gain >= 0.05.
As implemented. Faulty: R-squared of the regression of gene_b_expression / gene_c_expression on gene_a_expression / gene_c_expression, holds when >= 0.05. Fixed: gain in R-squared when gene_a_expression is added to the regression of gene_b_expression on gene_c_expression, holds when the gain >= 0.05.
Guards as coded: Faulty n >= 3, fixed n >= 4; zero variance of a variable entering the statistic -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: extra variance of gene B explained by gene A beyond gene C. Faulty: variance of one gene-C-standardised signal explained by the other, which includes the common gene C term.
Mechanism tag ratio-shared-denominator, statistic family R-squared (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 280/300, fails 20/300, None 0/300 (rate 0.933)
* minus: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* control permute_gene_a_across_samples: holds 0/300, fails 300/300, None 0/300 (rate 0.000)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 9/300, fails 291/300, None 0/300 (rate 0.030)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.061 ms, g = 0.022 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.2 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
none
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): ratio-shared-denominator / R-squared.
- Allowed-guard minimum (private note): 4 samples (2 predictors plus intercept, 1 residual degree of freedom); zero variance -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
