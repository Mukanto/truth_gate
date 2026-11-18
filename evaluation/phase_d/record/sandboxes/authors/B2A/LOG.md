# LOG, author B2A (class B-2, half A, source KAP23)

## Files read (all inside the sandbox)
BRIEF_AUTHOR_D.md, TASK.json, SOURCES.md, SOURCES_D.md, agent_docs/README_TOOL.md, MANIFEST.md, GATE.md, SPEC.md.
(`agent_docs/SCAN_REVIEW.json` was listed by the file search but not opened.) Nothing outside the sandbox was read.

## Sources read online, and how
KAP23 (Kapoor and Narayanan 2023, Patterns 4(9):100804):
- arXiv PDF: fetched, but the tool returned the raw PDF structure and no readable text. Nothing taken from it.
- PubMed Central full text (PMC10499856): read through WebFetch three times (3 prompts, each answered over characters 0 to 100000 of 126515; the last 26515 characters, mostly references, were not read). Used: the taxonomy entries L1.1 to L1.4, L3.1, L3.2, the histopathology and protein-family examples, the civil-war case study (12 papers, 4 with errors; "only 11" onset instances in a test set). Quotes in the private notes are as returned by the fetch tool, which cut some sentences; they are not verified character for character.
- Not stated in the source (so "source states none" is written throughout): sample sizes, feature counts, duplicate shares, missing rates, autocorrelation, how the error's size depends on sample size or number of features.

## URLs
1. https://arxiv.org/pdf/2207.07048 (PDF, unreadable output)
2. https://europepmc.org/api/fulltextRepo?pprId=PPR&type=FILE&fileName=x (a placeholder URL I tried by mistake; HTTP 500, no content; nothing used)
3. WebSearch query "Kapoor Narayanan Leakage and the reproducibility crisis in machine-learning-based science Patterns PMC full text" (results listed PMC10499856, par.nsf.gov/servlets/purl/10513990, arxiv.org/abs/2207.07048v1, ar5iv; only the PMC page was then fetched)
4. https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856 (fetched 3 times)
No GitHub repository of the tool and no published material of its evaluations was fetched.

## Analysis code run (the only exception)
`scratch/check_stats.py` was run once (`py check_stats.py`) on arrays generated with numpy from the briefs' shapes, to check that each structure statistic returns a finite float:
ratio p/n 1.5; polynomial terms/n 0.2167; missing fraction 0.2506; occupied categories/n 0.125; near-duplicate share 0.0 (no copies), 0.6 (180 exact copies in 600), 0.0 (random 2000 x 20); autocorrelation of a series 0.994 (random walk) and -0.006 (white noise); panel autocorrelation 0.002; intraclass correlation 0.495 (shared subject part) and 0.001 (independent); minority share 0.089. All finite Python floats. A second run parsed both JSON files, confirmed the 15 ids match, executed every `structure_statistic.code` definition (no call), and scanned the briefs for the banned terms and for procedure words (train, test, split, select, duplicate, fold, impute, encode, oversample): no hit.
No other analysis code was written or run. No agent was started, no git, no context-mode tool.

## Briefs written (10 pairs + 5 reserves = 15)
| local_id | subtype | family | setting (private) | differs from the others in |
|---|---|---|---|---|
| B2A-01 | L1.1 | R-squared | in-sample R-squared, ridge, 100 x 150 | reference |
| B2A-02 | L1.1 | correlation | in-sample correlation, quadratic OLS, 300 x 10 | statistic, model, regime |
| B2A-03 | L1.2 | R-squared | imputation using the outcome, continuous y, NaN in X, 250 x 20 | step, data structure |
| B2A-04 | L1.2 | correlation | target encoding of 150 districts (bool membership), 1200 | statistic, step, structure |
| B2A-05 | L1.3 | classification | top-20 feature choice on all rows, AUC, 80 x 1000 | |
| B2A-06 | L1.4 | other (MAE skill) | exact repeated records, 1-NN, 600 x 8 | |
| B2A-07 | L1.4 | correlation | near-identical records, 1-NN, 1200 x 20 | statistic, duplicate kind, size |
| B2A-08 | L3.1 | correlation | single daily series, random folds, 1000 days | |
| B2A-09 | L3.1 | other (MSE skill vs persistence) | station x day panel, 40 x 250 | statistic, structure |
| B2A-10 | L3.2 | other (MAE skill) | subject x trial x feature, 60 x 30 x 25 | |
| B2A-R1 | L1.1 reserve | other (MAE skill) | OLS 60 x 25 | statistic, model, regime |
| B2A-R2 | L1.2 reserve | classification | civil-war style class-conditional imputation, 1400 x 25 | outcome type, statistic |
| B2A-R3 | L1.3 reserve | R-squared | top-20 by correlation, continuous y, 100 x 500 | statistic, regime |
| B2A-R4 | L1.4 reserve | classification | oversampling by copying a rare class, 1-NN, 1000 x 15 | step, statistic |
| B2A-R5 | L3.1 reserve | regression-slope | monthly series, forward chaining, 400 x 3 | statistic, length |

## Abandoned drafts (not written to BRIEFS.json)
1. B2A-06 as R-squared with a 1-nearest-neighbour model: under no effect it needs about 60% repeated rows to hold (R-squared about 2f - 1), an unrealistic share; switched to MAE skill (about 36%).
2. L1.1 reserve as in-sample k-nearest-neighbour (k = 3) regression: the structure (a record counted among its own neighbours) is not a data property that a statistic on the data keys can measure; replaced by B2A-R1 (OLS, p/n set by the brief).
3. Draft claims for B2A-05 and B2A-R3 that named the 20 features "most strongly associated with" the outcome: removed, it states how items are chosen; now "uses 20 of the N features".
Briefs abandoned after writing: 0.

## Judgement calls to report
- Reserves are named B2A-R1 to B2A-R5 (prefix B2A- kept). One reserve per subtype of the TASK.json list (L1.1, L1.2, L1.3, L1.4, L3.1).
- `guard_minimum` is a single integer (rows evaluated); the notes say what it applies to (2 for R-squared, correlation, slope; 1 of each class for AUC; 1 for skill scores, which also return None when the baseline error is zero).
- `set_by_brief` is true where the structure is the brief's own size ratio (B2A-01, 02, 05, R1, R3); the statistic then reports features / samples (or the polynomial terms / samples in B2A-02) rather than the bare feature count.
- B2A-04 (target encoding): KAP23's quoted sentence names imputation and over/under sampling; target encoding comes from the subtype definition in the task. Stated in the note.
- Classification appears only in B2A-05 (no earlier L1.3 combination) and in reserves B2A-R2 and B2A-R4, where the source's setting is categorical; the earlier (L1.2, classification) and (L1.4, classification) combinations could not be avoided in those two reserves.
- Axes named `days_in_order` and `months_in_order` carry the time ordering in the axis name, as the brief rule's own example ("time in order") allows.

## Repairs
None requested. No count, rate or test result of any later check was seen.
