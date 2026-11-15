# CASE B1-01 (world C33)

## 1. Identification
Case id B1-01; world id C33; class B-1; subtype None.
Mechanism tag: extreme-group-change. Statistic family: mean.
Allowed-guard minimum (private note): 2 women per arm after the cut for the Welch t statistic (faulty: 2 active-arm women for the paired t statistic).
Size ratio (brief size to source size): source states none (see the sizes note of the private note: Source states no sizes (a short commentary)).

## 2. Source and documenting passage
Source key: MOR03.
Passage (from the private note of the brief author): Placebo effect section: "Women recruited to trials of hormone replacement therapy typically score highly on a symptom index. Because the trialists are identifying women with relatively extreme menopausal symptoms, once treatment starts, improvement will occur in both the placebo and active treatment groups because of regression to the mean." (PMC1125994, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: Among women whose menopausal symptom index at the start of the trial was at least 20 points, active hormone therapy lowers the index more than placebo does: the mean fall in the index (start minus week 12) is at least 3 points greater on active therapy than on placebo, and a one-sided Welch t test of that difference between the two arms is significant at the 0.05 level.

Data keys:
  * `index_start`, float, (women,): menopausal symptom index of each woman at the start of the trial (higher is worse)
  * `index_week12`, float, (women,): symptom index of each woman at week 12
  * `active`, bool, (women,): True if the woman was randomised to active hormone therapy, False if to placebo

Sizes: {"women": 300}

## 4. Mapping
Faulty: keeps women with index_start >= 20, takes only the active-arm women and tests the within-arm fall (index_start minus index_week12): mean fall >= 3 and one-sided paired t test (df n-1) at 0.05; the fall of selected extreme starters includes the regression of their start values, and no arm contrast absorbs it (MOR03, placebo effect section). Fixed: the same selection in both arms; difference of mean falls (active minus placebo) >= 3 and one-sided Welch t test at 0.05 (the placebo arm, selected the same way, absorbs the regression). The cut 20 is the claim's own.

Estimand line. Claim names the cut on the start-of-trial index because the estimand is defined for that subgroup. Faulty: mean fall from start to week 12 among active-arm women with start >= 20 (includes the regression of the extreme start values). Fixed: difference between arms in mean fall among women with start >= 20 (randomised comparison, regression cancels).
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: mean fall (start to week 12) among active-arm women with start >= 20. Fixed: difference between arms in mean fall among women with start >= 20.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 198, fails 2, None 0, exceptions 0 (n = 200)
  * minus: holds 0, fails 200, None 0, exceptions 0 (n = 200)
  * control:permute_active: holds 1, fails 199, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 0, fails 0, None 200, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000080 s (mean of 30 calls on plus samples), g = 0.000032 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.3 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
The statistic differs by design (paired within-arm t versus two-arm Welch), as the private note says; the threshold 3 and the one-sided 0.05 level are the same.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): extreme-group-change / mean.
- Allowed-guard minimum (private note): 2 women per arm after the cut for the Welch t statistic (faulty: 2 active-arm women for the paired t statistic)
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
