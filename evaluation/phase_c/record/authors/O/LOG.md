# LOG (O author, Phase C part 1)

Status: in progress. Resumable: append below; do not rewrite.

## Files read in sandbox
AUTHOR_PHASE1_C.md (all), PREREG_PHASE_C.md (all), PREREG_PHASE_B.md (all), SOURCES.md (all), SOURCES_ADDENDUM.md (all).
agent_docs/ and pkg/ not read (not needed in part 1).

## Plan
Targets: 2 briefs each for O-1 (KAP23), O-2 (SIM11), O-3 (BAG09, HER14). GHZ26 is named in PB section 1 for O-3 but has
no reference in SOURCES.md or SOURCES_ADDENDUM.md; it cannot be identified or read, so it is not used (rule not satisfiable;
reported).
Draft plan (not yet final):
- O-1a KAP23 L1.2 pre-processing without labels (scaling/PCA/imputation on all data before split)
- O-1b KAP23 L3.3 biased test sample (or L2)
- O-2a SIM11 two dependent variables, report whichever is significant
- O-2b SIM11 optional stopping
- O-3a BAG09 row/label offset
- O-3b HER14 spreadsheet row-range exclusion

## Sources read (URLs)
(append)

## Sources read (how, URLs)
- KAP23: abstract https://arxiv.org/abs/2207.07048 ; full text (ar5iv HTML) https://ar5iv.labs.arxiv.org/html/2207.07048 -- section 2.4 taxonomy read: L1.2, L2, L3.3 entries (read in the indexed text and via a tool summary; quotes in PRIVATE.json are short or located by section). Also fetched https://arxiv.org/pdf/2207.07048 (raw PDF, unreadable, not used).
- SIM11: Europe PMC record lookup https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1177/0956797611417632&format=json&resultType=lite (metadata only), https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=Simmons%20False-positive%20psychology%20AND%20OPEN_ACCESS:y&format=json (metadata only); abstract page https://stafforini.com/works/simmons-2011-falsepositive-psychology-undisclosed/ ; FULL TEXT PDF (text extracted) https://pdf.stafforini.com/simmons-2011-falsepositive-psychology-undisclosed.pdf -- read: Table 1 and its note (Situations A-D), the Figure 1 text (optional stopping). Web search result pages (WebSearch) used to locate it.
- BAG09: full text (ar5iv) https://ar5iv.labs.arxiv.org/html/1010.1092 -- read via tool extraction: Sections 2.2, 2.4-2.6, 3.2, 3.5-3.9, 6.1 passages on off-by-one gene lists, reversed labels, duplicates. A first guess https://arxiv.org/pdf/0910.1843 and https://ar5iv.labs.arxiv.org/html/0910.1843 was the wrong paper (a quasar paper); nothing used from it.
- HER14: PERI working paper WP322 (same authors/title, April 2013 version of the CJE paper) https://peri.umass.edu/publication/does-high-public-debt-consistently-stifle-economic-growth-a-critique-of-reinhart-and-rogoff/ and full text http://peri.umass.edu/wp-content/uploads/joomla/images/WP322.pdf (text extracted; spreadsheet error, exclusions, weighting, counts). The journal version (CJE 38(2)) itself was not opened; passages quoted are from the working paper, so wording may differ slightly from the journal text.
- Other URLs that failed or were not used: https://pmc.ncbi.nlm.nih.gov/articles/PMC3153277/ (guessed ID, bot-check page, nothing read), https://papers.ssrn.com/abstract=1850704 (listed by search, not opened).
- GHZ26: named in PB section 1 for O-3, but no reference exists in SOURCES.md or SOURCES_ADDENDUM.md, so it cannot be located or read. NOT used. This does not block the quota (2 O-3 briefs rest on BAG09 and HER14).
- Tool-result files saved by the harness for two PDF fetches sit outside the sandbox (harness tool-results folder); they were not opened by me.

## Briefs drafted (all kept; none abandoned)
O1-A KAP23 L1.2: PCA+standardisation on all rows before 5-fold CV; R-squared; 300 x 80.
O1-B KAP23 L3.3: borderline (middle band of rating) children left out of evaluation; balanced accuracy; 400 x 30 + rating.
O2-A SIM11 Situation A: 2 measures, 3 t tests (each + average), report if any significant; 20 per cell.
O2-B SIM11 Figure 1: repeated looks n=10..50 per condition; 50 per cell.
O3-A BAG09: one-row offset of the signature membership mask against the expression table; 1000 probe sets x 60 cell lines.
O3-B HER14: spreadsheet range stops five country rows short (lines 30-44 vs 30-49); 20 countries x 64 years.

Abandoned ideas (not written as briefs): O-1 L2 illegitimate features (Filho et al. hypertension, antihypertensive drug use as feature): no brief can name the illegitimate feature without naming its role or can fix it without telling which key is illegitimate. O-3 BAG09 label reversal and duplicated samples (duplicates would be B-2 L1.4 by PB tie rules; reversal is covered by the offset pair). GHZ26 (see above).

## Rule checks and risks noted
- Banned-term check done by eye on all claims, keys and meanings (no circular, double dip, leak, pseudorepl, coupl, spurious, non-independ, regression to the mean, selection bias, overfit, inflat, contaminat, optimis; also avoided selected, split, excluded, dropped, shifted in the briefs). A scripted check is the designer's.
- "5-fold cross-validation" appears in the O-1 claims: it defines the statistic (out-of-sample R-squared / balanced accuracy for new subjects), it is not the error.
- O1-A claim names "first 10 principal components": the estimand (predictive R-squared of that pipeline) requires it.
- O1-B key severity_rating, O3-A key on_signature: named by what they hold; possible reading as role-naming noted for the designer.
- All sizes <= 1000 per axis and <= 500 000 values (max array 60 000). Timing: all criteria are far below 900 s by rough estimate (largest per-call cost is a 5-fold SVD or logistic fit on <= 400 x 80).
- Every dimension is stated as a number in sizes.
- New-source minimum does not apply (out-of-scope classes). Overlap with Phase B: not assessable by me (the table is the designer's); no Phase B material was read.

## Status
Complete: BRIEFS.json (6), PRIVATE.json (6), LOG.md written.

## Part 2 (criterion bodies; Sonnet author, 2026-11-15)

Files read: AUTHOR_PHASE2_C.md, PREREG_PHASE_C.md, PREREG_PHASE_B.md, PRIVATE.json, LOG.md (part 1), agent_docs/GATE.md, and for each case ASSIGNMENT.json and skeleton.py. No URL was fetched in part 2 (the passages come from PRIVATE.json). BRIEFS.json, SOURCES*.md, pkg/ sources, agent_docs other than GATE.md were not read. Truth_Gate was never run; `pkg/` was put first on sys.path only so that fixed.py files load (the skeletons import truth_gate); only world functions and the fixed criterion were called.

Scratch scripts (work\): precheck_fixed.py (imports fixed.py only), validate_p_helper.py, validate_welch_helper.py, precheck_o3b_shuffle.py. None imports or executes faulty.py. The only operation on any faulty.py was the AST syntax check (all six passed), plus a text comparison of faulty and fixed against the skeleton (identical outside the body) and a text diff of faulty against fixed.

Case by case (fixed-criterion revisions in brackets):
- O1-A [0]: pipeline fitted inside folds (fixed) vs PCA/standardisation on all rows (faulty). plus 196/200, minus 0/200, control 0/200, noise 0/200. t=0.0298 s, S=5, estimate 72.5 s.
- O1-B [0]: all children (fixed) vs middle 30 percent of severity_rating dropped (faulty). plus 170/200, minus 0/200, controls 0/200 each, noise 0/200. plus rate 0.85 recorded, not bent. t=0.0054 s, S=6, estimate 15.6 s.
- O2-A [0]: one t test on liking (fixed) vs any of three tests (liking, wtp, raw average) (faulty). plus 372/400, minus 10/400, control 7/400, noise 7/400. Helper validated against scipy (max |dp| 2.8e-11; 0/2000 decision disagreements). estimate 0.1 s.
- O2-B [0]: one test at n=50 (fixed) vs a test at every n=10..50 (faulty). plus 376/400, minus 12/400, control 11/400, noise 8/400. estimate 0.1 s.
- O3-A [0]: signature mask as given (fixed) vs np.roll(mask, 1) (faulty). plus 299/300, minus 0/300, controls 0/300, noise 0/300. Welch p helper validated against scipy (max |dp| 2.5e-13). t=0.000094 s, g=0.0011 s, S=6, estimate 3.3 s.
- O3-B [0]: all 20 countries (fixed) vs first 15 country rows (faulty). plus 400/400, minus 0/400, control 0/400, shuffle probe 2/400, noise all None (empty-selection guard). estimate 0.8 s.

Interpretation recorded for O3-B: the note's "first 15 of 20" and "drop the first five rows" were read as keeping rows 0..14 (range stops five rows short); the skeleton's country rows are exchangeable so the other reading is statistically identical.
No skeleton request, no size request, all six cases have CASE.md.
