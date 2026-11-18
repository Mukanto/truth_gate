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


## Criteria (criterion author, class B-2 half A, source KAP23)

Author of the criterion bodies. Same sandbox folder; nothing outside it was read, no URL was fetched (the documenting passages are the brief author's, taken from the private notes), no agent was started, no git, no context-mode tool, no Truth_Gate. `faulty_body.py` files were never run or simulated: the only operation on them was `ast.parse` (syntax check, all 15 passed), plus reading and `diff` of their text.

### Files written
- `work/build_cases.py`: assembles the 30 body files (shared helper functions + a shared criterion frame; the error block for the faulty, the correction block for the fixed). It writes text only and imports nothing it writes.
- `work/check_fixed.py`: form check (AST) and smoke run of the FIXED bodies only, on arrays generated there.
- `work/test_helpers.py`, `work/sanity_fixed.py`, `work/sanity_d066.py`: unit checks of helpers and sanity runs of the FIXED bodies on self-generated arrays.
- `work/build_case_md.py`: writes the 15 `CASE.md` files.
- Per case: `faulty_body.py`, `fixed_body.py`, `CASE.md` in `cases/<id>/` (D-004, D-005, D-010, D-014, D-022, D-027, D-029, D-039, D-041, D-042, D-044, D-054, D-055, D-060, D-066).

### Runs (fixed bodies and helpers only)
1. `check_fixed.py`, form check of all 15 fixed bodies: no error (only `import numpy as np` and function definitions at module level, `criterion(d)` with a docstring, no decorators, no global/nonlocal, literal defaults, no free names, no `np.random` function other than `default_rng`). Smoke run on 2 arrays per case (4 calls): all bool, deterministic, time per call between 0.000 s and 0.042 s (slowest D-042, 1200 x 20 with the linking step; D-014 0.034 s). Far inside the 30-minute budget.
2. `test_helpers.py`: ridge dual form equals the explicit primal solution and recovers a noiseless linear fit; AUC (with ties) equals brute-force pairwise; stratified folds; Welch-t selection finds planted columns; `link_components` forms one component for a planted chain of near copies and equals an independent union-find on a random array (298 components); `impute` leaves no NaN and keeps observed entries; polynomial features have 66 columns for 10 readings; the penalised logistic fit has gradient about 5e-15 after 25 Newton steps; forward-chaining block indices as intended (D-055 blocks start at index 167 with 162 fitting rows; D-039 starts 200, 240, 280, 320, 360 with fitting ends 200, 237, 277, 317, 357; D-004 cut 175).
3. `sanity_fixed.py`: one strong planted signal per case (fixed body returned True in 14 of 15; D-066 returned False for a 2-of-15-columns signal under one-nearest-neighbour) and guard checks (NaN in X, constant y, a single class, one positive, a fully missing column all returned None; constant X in D-039 returned False because the forecasts still differ between blocks). `sanity_d066.py`: clustered rare class True, noise False. These runs checked that the code works; no rate was estimated and nothing was tuned.

### Revisions of the fixed bodies
0 after the first run of any fixed body. (Before the first run the builder was edited once: the unused `pred` allocation of D-004's fixed body was moved into the faulty block.)

### Judgement calls and deviations (details in each CASE.md, section 7)
- B2A-R5 (D-039): the 3-month gap is applied from the second block on, as the note is written; the first block is fitted on months 1 to 200.
- B2A-06 (D-029): the guard minimum is 2 rows (1-NN cross-validation needs a held-out and a fitting row); the note's 1 counts held-out rows.
- B2A-R2 (D-041): penalised logistic regression defined as Newton from zero, unpenalised intercept, penalty (lambda/2)||w||^2 on standardised columns.
- B2A-05 (D-054): Welch form of the two-sample t statistic; ties broken by column index.
- B2A-03 (D-014): columns updated in ascending order within a sweep (Gauss-Seidel).
- B2A-R4 (D-066): rare class = True rows are copied; no copies when True is the majority.
- Only faulty bodies of D-055, D-004, D-044, D-039 use randomness (`default_rng(0)`); D-066 uses it in both, same seed.

### Repairs
None requested. I saw no count, rate or test result of any later check.
