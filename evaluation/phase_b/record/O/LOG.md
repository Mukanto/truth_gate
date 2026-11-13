# LOG (phase 1, O-1..O-3)

## Briefs written (6): O1a, O1b, O2a, O2b, O3a, O3b
Per source: KAP23 2, SIM11 2, BAG09 1, HER14 1. Per class: O-1 2, O-2 2, O-3 2.

## Abandoned drafts
- O1c (KAP23 L3.3, test sample biased toward easy cases): abandoned, only 2 O-1 cases requested; would need a test-membership array that reveals the structure.
- O2c (SIM11 covariate/interaction flexibility, OLS treatment coefficient with sex covariate): abandoned, quota of 2 O-2.
- O3c (GHZ26, model inconsistent with its estimator): abandoned. Read AUDIT_blind.md and REPORT.md in full. The case lives in a hardware-counts model (P and C readout terms) and the claim depends on device-specific model components; it cannot be put in a neutral brief with at most 300 rows and plain arrays without reproducing the model, and quota is 2 O-3.

## Sources read
- KAP23: arXiv abstract page only (abstract; the taxonomy details L2/L1.2/L3.3 were not retrievable from that page, so passages in PRIVATE.json rely on the taxonomy as listed in SOURCES.md and my recall).
- SIM11: PubMed fetch failed (cookie wall); not read this session. Parameters (n=20 per cell, adding 10 observations, several correlated DVs) come from recall and SOURCES.md.
- BAG09: arXiv abstract (row or column offsets confirmed).
- HER14: Oxford page fetch returned only navigation, no abstract; not verified this session, recall of the critique used.
- GHZ26: AUDIT_blind.md and REPORT.md read in full.
- PREREG_PHASE_B.md, SOURCES.md, docs/MANIFEST.md read. README, GATE.md, SPEC.md were not read.

## Rule problems to report
- Faithful BAG09 offset case (O3a): the faulty criterion fails on plus because the offset removes the real relation; mismatch with the published direction of the error.
- Several passages are from recall because fetches failed; the designer should verify them.
- The claim in O2a names measure 1 as primary, and O2b says "once the planned sample is complete"; both state the planned analysis, which is what the fixed twin does. They do not say what the faulty one does.
- Brief checker: no banned terms found by my own regex.

## Revision after coordinator message (sources re-read)
Sources now read as follows (replaces the earlier "Sources read" list):
- KAP23: ar5iv full text, section 2.4 (L2, L1.2, L3.3 quoted verbatim in PRIVATE.json for L2 and L1.2). L3.3 text also read (spatial bias, selection bias) but not used in a case.
- SIM11: full text PDF (UBC course copy), Table 1 and the text of the first two rows. Verified n=20 per cell, r=.50, three tests, 15,000 simulations, 10 additional observations.
- BAG09: arXiv full text PDF (via pdftotext): abstract, Fig. 2 caption, sections 2 and 3.
- HER14: PERI WP322 PDF (via pdftotext): "Spreadsheet coding error", exclusions, weighting sections; 20 advanced economies, 1946-2009. The OUP/CJE page was not needed.
- GHZ26: AUDIT_blind.md and REPORT.md in full (unchanged). PREREG, SOURCES, MANIFEST read; README/GATE/SPEC not read.

Changes:
- O2b: look schedule corrected from 20/25/30 to 20 and 30 (SIM11: one extra look after 10 more per cell). PRIVATE faulty text and note updated; brief unchanged.
- O2a: parameters verified, no change except quote.
- O3a: error placement corrected. BAG09's offset is along the gene list (replace one probeset id with the next row), not a sample-to-label shift. Brief now has expr (cell_lines, 20) with the signature in columns 5-9 (1-based); faulty uses columns 6-10; sizes "60 cell lines; 20 genes".
- O3b: spreadsheet error omits the FIRST five (alphabetical) countries, not the last five; faulty criterion also drops early years of one further country (analogue of New Zealand) and uses equal country weights. Sizes note: source is 64 years; 15 used because of the 300-row cap. Source uses four debt bins; brief uses the 90% split.
- O1a, O1b: passages replaced by KAP23 quotes; no parameter change.
- All passages now are quotes or section locations; none left "not verified".
- Brief regex check re-run: no banned terms.


# Phase 2 (criterion bodies), O-1..O-3

Method: bodies written by work/patch.py (replaces only the `raise NotImplementedError` line); text check work/check_text.py
confirms faulty.py and fixed.py equal skeleton.py outside the body and that imports are unchanged; syntax check
(`ast.parse`) run on every faulty.py. The faulty criteria were never run, simulated or pre-checked; Truth_Gate was never run.
Pre-check of the fixed criteria: work/precheck_fixed.py (seed 777, 300 plus/minus/control samples, 100 per probe; probes
are my own approximation, float arrays N(0,1) or zeros, bool arrays fair coin or False). Output: work/precheck_fixed_run1.txt.
Shared helper (O2a, O2b): one-sided Welch p via a numpy-only regularised incomplete beta; checked against tabulated 5%
critical values (work/helper_test.py).

| Case | Fixed holds plus | minus | control | noise | zeros | t | g | estimate | revisions |
|---|---|---|---|---|---|---|---|---|---|
| O1a | 280/300 | 23/300 | 16/300 | 0/100 | 0/100 (UNDEFINED) | 0.052 ms | 0.042 ms | 0.2 s | 0 |
| O1b | 261/300 | 2/300 | 1/300 | 0/100 | 0/100 (UNDEFINED) | 1.164 ms | 0.088 ms | 3.0 s | 0 |
| O2a | 256/300 | 20/300 | 10/300 | 5/100 | 0/100 (UNDEFINED) | 0.063 ms | 0.014 ms | 0.2 s | 0 |
| O2b | 273/300 | 19/300 | 20/300 | 3/100 | 0/100 (UNDEFINED) | 0.045 ms | 0.007 ms | 0.1 s | 0 |
| O3a | 284/300 | 0/300 | 0/300 | 0/100 | 0/100 (UNDEFINED) | 0.041 ms | 0.023 ms | 0.2 s | 0 |
| O3b | 300/300 | 46/300 | 12/300 | 0/100 (UNDEFINED) | 0/100 (UNDEFINED) | 0.015 ms | 0.109 ms | 0.3 s | 0 |

Problems and notes:
- O1a, O1b: split sizes (150/100, 72/48) and the least-squares classifier / 5 components were fixed before any pre-check.
- O3a: the note's expectation that the faulty criterion usually fails in plus may not hold, because the offset window
  (columns 6-10) shares four of the five signature columns of the skeleton generator (reading the generator only). The
  faulty criterion was written as documented; not changed.
- O3b: fixed criterion holds in 46/300 minus samples (skeleton keeps the country growth-debt correlation and reverse
  causation in minus); not changed. Faulty statistic differs from fixed in exclusions and equal weighting, both documented in HER14.
- No skeleton requests.
