# CASE B1-02 (world C43)

## 1. Identification
Case id B1-02; world id C43; class B-1; subtype None.
Mechanism tag: split-by-baseline-compare-change. Statistic family: mean.
Allowed-guard minimum (private note): 2 women per group for the two-sample (Welch) t statistic.
Size ratio (brief size to source size): source states none (see the sizes note of the private note: Source gives no sample size for the figure (cites a trial of women on alendronate or raloxifene)).

## 2. Source and documenting passage
Source key: MOR03.
Passage (from the private note of the brief author): Figure 1 legend: "Women are grouped according to the percentage change at 12 months, and values for 24 months are percentage change from value at 12 months." Text: "most patients (> 80%) who lost bone in the first year of treatment went on to gain bone in the second year despite no change in treatment." (PMC1125994, full text)
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: In women treated for osteoporosis, first-year responders keep gaining more bone than first-year non-responders: women whose bone mineral density rose over the first year (from the start of treatment to the first 12-month scan) gain at least 0.5 percentage points more over the second year (percentage change from the second 12-month scan to the 24-month scan) than women whose density fell over the first year, and a one-sided Welch t test of that difference between the two groups of women is significant at the 0.05 level.

Data keys:
  * `bmd_start`, float, (women,): bone mineral density of each woman at the start of treatment (g/cm2)
  * `bmd_m12_scan1`, float, (women,): bone mineral density at the 12-month visit, first of two scans taken at that visit (g/cm2)
  * `bmd_m12_scan2`, float, (women,): bone mineral density at the 12-month visit, second of two scans taken at that visit (g/cm2)
  * `bmd_m24`, float, (women,): bone mineral density at the 24-month visit (g/cm2)

Sizes: {"women": 600}

## 4. Mapping
Faulty: groups the women by the sign of the first-year change (bmd_m12_scan1 vs bmd_start) and measures the second-year percentage change from the same 12-month reading, 100*(bmd_m24 - bmd_m12_scan1)/bmd_m12_scan1; difference of group means (rose minus fell) >= 0.5 and one-sided Welch t test at 0.05. Fixed: the same grouping, second-year change measured from the second 12-month scan, 100*(bmd_m24 - bmd_m12_scan2)/bmd_m12_scan2; same threshold and test (MOR03, Figure 1 legend and text). Women with a first-year change of exactly 0 are in neither group.

Estimand line. Claim names the two 12-month scans because the estimand (second-year change by first-year response, with independent 12-month readings) requires them. Faulty: difference in mean second-year change between first-year gainers and losers where one 12-month reading defines the group and starts the second-year change. Fixed: the same difference with the second-year change started from the second scan.
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
Faulty: difference in mean second-year change between first-year gainers and losers where one 12-month reading defines the group and starts the second-year change. Fixed: the same difference with the second-year change started from the second scan.

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
  * plus: holds 200, fails 0, None 0, exceptions 0 (n = 200)
  * minus: holds 3, fails 197, None 0, exceptions 0 (n = 200)
  * control:reassign_second_year_records: holds 6, fails 194, None 0, exceptions 0 (n = 200)
  * probe:noise: holds 5, fails 195, None 0, exceptions 0 (n = 200)
  * probe:zeros: holds 0, fails 0, None 5, exceptions 0 (n = 5)
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = 0.000097 s (mean of 30 calls on plus samples), g = 0.000069 s (mean plus generation, 30 samples), S = 5 (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = 0.4 s (limit 900 s).

## 7. Deviations, problems, skeleton requests
Direction of the documented error against the claim: the shared reading makes first-year losers show a gain in the second year (the source's own observation), that is a bias of the group difference that is opposite in sign to the direction the claim asserts. The faulty criterion is therefore expected to hold less often than the fixed one in plus and may not hold in minus either; I did not run or simulate it, this is a statement about the documented mechanism only. The note's mechanism was kept unchanged; the designer should read a miss on this pair with this in mind.
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no (addendum source).
- Mechanism tag / statistic family (private note): split-by-baseline-compare-change / mean.
- Allowed-guard minimum (private note): 2 women per group for the two-sample (Welch) t statistic
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
