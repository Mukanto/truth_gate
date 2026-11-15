# CASE B3-01

## 1. Identity
Case id B3-01; world id C16; class B-3; subtype none (n/a).

## 2. Source and documenting passage
Source key CUR13. Passage (as recorded in the part-1 private note): Abstract: 'only if the relationship between numerator and denominator is a straight line through the origin will the ratio be meaningful. If not, the ratio will misrepresent the true relationship between numerator and denominator.' Correction named in the abstract: regression techniques 'including analysis of covariance'. (Europe PMC record of PMID 24022766; abstract only, full text not open.)
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: In adult rats, animals given the drug have a larger heart weight than untreated animals after accounting for body mass: in a linear regression of heart weight on treatment status and body mass, the coefficient of treatment status is positive and significant at the one-sided 5% level (t test).
Data keys:
  * `heart_weight` (animals,) float: Wet heart weight of each animal, in mg.
  * `body_mass` (animals,) float: Body mass of each animal, in g.
  * `treated` (animals,) bool: True for animals given the drug, False for untreated animals.
Sizes: animals = 48; heart_weight, body_mass and treated each have shape (48,).

## 4. Mapping
Documented error (note): Heart weight divided by body mass for each animal; one-sided two-sample (Welch) t test of that quotient between treated and untreated animals, claim holds when p < 0.05 with the treated mean larger. Documented parameter: the numerator-denominator relation is a straight line NOT through the origin (positive intercept for heart weight versus body mass), and the groups differ in body mass.
Documented correction (note): Analysis of covariance: OLS regression of heart weight on treatment status (bool) and body mass; one-sided t test on the treatment coefficient (positive, p < 0.05).
As implemented. Faulty: ordinary least squares of the quotient heart_weight / body_mass on treatment status, one-sided t test of the treatment coefficient (positive and p < 0.05). Fixed: ordinary least squares of heart_weight on treatment status and body_mass, same one-sided t test of the treatment coefficient. Both use one OLS-t routine and one Student-t tail routine (numerical integration, no scipy).
Guards as coded: Faulty guard: residual df >= 1 (n >= 3); fixed guard: residual df >= 1 (n >= 4, as the note says); no animal in one group or zero residual variance -> None; non-finite -> None.
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): Fixed: difference in heart weight between treated and untreated animals at equal body mass (adjusted treatment effect). Faulty: difference between the groups in the mean of heart weight divided by body mass, which also moves with the groups' body-mass difference whenever the intercept is not zero.
Mechanism tag ratio-vs-denominator-proxy, statistic family regression-slope (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
* plus: holds 282/300, fails 18/300, None 0/300 (rate 0.940)
* minus: holds 24/300, fails 276/300, None 0/300 (rate 0.080)
* control permute_treated: holds 15/300, fails 285/300, None 0/300 (rate 0.050)
* noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes): holds 14/300, fails 286/300, None 0/300 (rate 0.047)
* zeros probe: 1 sample, None (zero variance guard)
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = 0.181 ms, g = 0.017 ms, S = 5 (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.5 s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
The note names a Welch test for the faulty version. I implemented the faulty comparison as the pooled-variance two-sample t test (OLS of the quotient on treatment status) so that both versions share one OLS-t routine and the same one-sided 5% rule (audit items (b), (g)); with 24 + 24 animals the two tests differ negligibly. The note's guard on zero variance of body_mass is replaced by the guard on the treatment coefficient (constant body mass does not make that coefficient undefined). The p value comes from a numerical integral (max abs. error against scipy 2e-6 over df 1 to 797, scratch check work/check_tsf.py), because only numpy may be used.
Skeleton requests: none. Size requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): ratio-vs-denominator-proxy / regression-slope.
- Allowed-guard minimum (private note): 4 animals with at least 1 animal in each group (smallest size at which the treatment coefficient and its t statistic exist: 3 parameters, 1 residual degree of freedom); zero variance of body_mass -> None; non-finite -> None.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
