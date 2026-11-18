# LOG, author B3B (B-3, half B)

## Sources read
All seven sources were read through their abstracts only (none has an open full text). The abstracts are saved in `fetched\`.

| Key | How | Where |
|---|---|---|
| ATC76 | abstract, rebuilt from the OpenAlex inverted index (text decoding only) | `fetched\atc76_oa.json` |
| CUR13 | abstract (Europe PMC; PMID 24022766; not open access) | `fetched\cur13_epmc.json` |
| TU07 | abstract (Europe PMC; not open access) | `fetched\tu07_epmc.json` |
| BLO77 | abstract, rebuilt from the OpenAlex inverted index | `fetched\blo77_oa.json` |
| TU04 | abstract (Europe PMC; not open access) | `fetched\tu04_epmc.json` |
| STR87 | abstract (Europe PMC; not open access) | `fetched\str87_epmc.json` |
| MOR86 | abstract (Europe PMC; not open access) | `fetched\mor86_epmc.json` |

## URLs
- https://pubmed.ncbi.nlm.nih.gov/?term=Curran-Everett+Explorations+in+statistics+analysis+of+ratios+and+normalized+data (WebFetch; returned only a cookie notice, nothing read)
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1152/advan.00053.2013&resultType=core&format=json (WebFetch, then curl)
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1002/sim.2538&resultType=core&format=json (curl)
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1016/j.jdent.2003.10.001&resultType=core&format=json (curl)
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1152/jappl.1987.62.5.2083&resultType=core&format=json (curl)
- https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1152/jappl.1986.60.1.335&resultType=core&format=json (curl)
- https://api.openalex.org/works/doi:10.2307/2412740 (curl)
- https://api.openalex.org/works/doi:10.1080/01621459.1977.10479950 (curl)
- WebSearch (standard): query "Moreno Stratton Newell Feustel 1986 Mathematical coupling of data: correction of a common error for linear calculations example". It returned no page for MOR86. Of its results I read none beyond the snippets; the PMC1345065 link in it was not opened and was not used.
- No GitHub page and no material of the tool or of its evaluations was fetched.

## Code run (allowed exceptions only)
1. Two small decoding commands (`py -c ...`) to decode the OpenAlex abstracts, and one `python -c` print of the CUR13 abstract field from its JSON; these are text extraction, not analysis. The other abstracts were read with `grep`.
2. The structure statistics check, `scratch\check_stats.py`: for each brief, arrays of the brief's shapes were generated (normal(10, 2); bool with p = 0.5) and the structure statistic was run on them. All 15 returned a finite Python float (values between 0.006 and 1.43; the values carry no meaning, the arrays are random).

## Briefs drafted
15 written (10 cases, 5 reserves); none abandoned. IDs B3B-01..10 are the cases, B3B-11..15 the reserves.

| ID | Source | Tag | Family | Case or reserve |
|---|---|---|---|---|
| B3B-01 | ATC76 | ratio-shared-denominator | correlation (partial) | case |
| B3B-02 | ATC76 | ratio-shared-denominator | regression-slope (mean of per-population slopes) | case |
| B3B-03 | CUR13 | ratio-vs-denominator-proxy | mean (two groups, ANCOVA) | case |
| B3B-04 | CUR13 | ratio-vs-denominator-proxy | mean (three groups, F test) | case |
| B3B-05 | TU07 | change-vs-baseline | correlation (Oldham) | case |
| B3B-06 | BLO77 | change-vs-baseline | regression-slope (latent, individuals x occasions) | case |
| B3B-07 | TU04 | change-vs-baseline | R-squared | case |
| B3B-08 | STR87 | shared-measured-component | correlation | case |
| B3B-09 | STR87 | shared-measured-component | regression-slope (mean of per-animal slopes) | case |
| B3B-10 | MOR86 | shared-measured-component | correlation (linear calculation) | case |
| B3B-11 | ATC76 | ratio-shared-denominator | other (first-eigenvalue share) | reserve |
| B3B-12 | CUR13 | ratio-vs-denominator-proxy | mean (paired) | reserve |
| B3B-13 | BLO77 | change-vs-baseline | correlation (latent, 3 occasions) | reserve |
| B3B-14 | STR87 | shared-measured-component | R-squared (consumption on cardiac output) | reserve |
| B3B-15 | TU04 | change-vs-baseline | regression-slope (mean of per-trial slopes) | reserve |

Decisions taken, for the designer:
- CUR13 uses the family `mean` in all three briefs, because earlier evaluations used R-squared, correlation and regression-slope for ratio-vs-denominator-proxy on this source. The three differ by data structure (two groups; three groups on an axis; paired sessions).
- All five change-vs-baseline briefs and the shared-measured-component ones carry a second independent reading key (`..._retest`, `..._2`). It is there so that the structure statistic can be computed from parts of the data that the claim-false version leaves unchanged. The fixed analyses of B3B-05, B3B-07, B3B-15 do not use it. For STR87 the fixed analysis uses it as the independent measurement of the cardiac output (documented correction). Contents have no repeat key, so their error is taken as negligible in the correction (stated in the private notes).
- B3B-08, -09, -14 name "the standard Fick definitions" in the claim, without formulas, because the estimand needs the two derived quantities.
- B3B-10 (MOR86): the abstract gives no physiology example. The setting (difference of two measured contents against one of them) is an assumption of mine for a linear calculation from two measured variables; it is flagged in the private note.
- ATC76 settings 2 and 3 of the abstract (Y = X1/X2 against Z = X1, and against Z = X2) were not used as separate briefs; all three ATC76 briefs use the shared-denominator setting (Y = X1/X2 against Z = X3/X2), as allotted, and differ by statistic and structure.

## Rules found impossible or tight (reported, not bent)
- ATC76 states simulation samples of at least 25,000. The cap is 2000 per axis, so B3B-01 uses 2000.
- No source gives a number for any structure statistic's `note_value`; every value is "source states none" with a reason.
- Only abstracts were available. Settings described in the briefs are those the abstracts name; sample sizes are mine unless stated (TU04: 12 trials taken from the abstract).

## Repairs
None requested.

## Criteria (criterion author, half B3B; 15 cases written, 10 cases and 5 reserves)

Done for all 15 case folders: `faulty_body.py`, `fixed_body.py`, `CASE.md`. Scripts in `work\`: `make_bodies.py` (generates the two
bodies of every case from one template, so they differ only in the error and its correction), `make_case_md.py` (writes
the CASE.md files), `check_fixed.py` (form check and runs of the fixed bodies on random arrays), `verify_fixed.py`
(cross-check of the fixed bodies against independent re-implementations).

### Reading
- Read inside the sandbox: `CRITERION_AUTHOR_D.md`, `SOURCES.md`, `SOURCES_D.md`, `half\BRIEFS.json`, `half\PRIVATE.json`,
  `half\CASE_IDS.json`, `half\LOG.md`, `half\cases\D-023\brief.json` (first lines only), the seven abstracts in `half\fetched\`
  (to confirm the passages, text only), and the file list of `agent_docs\` and `pkg\` (not opened). `agent_docs\` and `pkg\`
  were not read or used.
- URLs: none fetched. Nothing from the project's code repository or its evaluations. No context-mode tool, no other agent, no git.

### Decisions common to all cases
- p-values (B3B-03, -04, -12): only `import numpy as np` is allowed, so the t and F tail probabilities are computed with a
  numpy-only regularised incomplete beta (Lentz continued fraction, Lanczos log-gamma). Checked in scratch against scipy.stats:
  worst relative error 1.1e-13 over a grid of statistics and degrees of freedom.
- Where a statistic is a regression coefficient with a test (B3B-03, B3B-12), faulty and fixed use the same OLS helper, so
  the Student/paired t test on the ratio and the analysis of covariance share their structure.
- Corrected variances: the private notes of B3B-09, -10, -13, -14 say "None when a corrected variance is not positive"; the
  same line was used for B3B-06 and B3B-08 (the statistic is undefined there). The same line in the faulty body is the
  plain zero-variance guard. This is a reading of the guard list (zero variance -> variance not positive after correction),
  reported in the CASE.md files of B3B-06, -08, -09, -10, -13, -14 for confirmation.
- Content errors are taken as negligible in B3B-08, -09, -14 (documented simplification of the notes: only the cardiac output has a
  repeat key). First-order Taylor terms are exact for these products when the contents are error-free. k = 10 converts
  L/min x mL/dL to mL/min.
- The error variance of a repeated measure is var(first - second, ddof 1) / 2.
- Blomqvist (B3B-06, -13): times 0..m-1; initial value = level at the first visit (intercept of the individual line); pooled
  s2 = SSR / (n (m - 2)); subtractions s2 (1/m + tbar^2/Sxx), s2/Sxx, and -s2 tbar/Sxx for the covariance.
- No randomness is used anywhere (no generator is created).

### Runs of the fixed bodies (own arrays only)
| Run | What | Result |
|---|---|---|
| 1 | `check_fixed.py`: form check of all 15 fixed bodies; one run each on random arrays (normal(10, 2), bool p = 0.5) of the brief's shapes, plus a repeat on copies | no form errors; all returned bool or None (None for B3B-06 and B3B-10, pure-noise arrays with no positive corrected variance); repeats equal; 0.1 to 1.0 ms each |
| 2 | `verify_fixed.py`: 15 datasets generated for the check (latent-variable data, brief shapes); each fixed body was run twice with its last threshold literal replaced in memory by the independently computed reference value -/+ eps | all 15 flipped exactly at the reference: "ALL FLIPS OK" |
| 3 | `verify_fixed.py`: t and F tail-probability helpers vs scipy.stats | worst relative error 1.1e-13 |

Revisions of the fixed bodies after their first version: 0 for every case. No rate was computed, nothing was tuned.

### Checks of the faulty bodies
Only the permitted syntax check (`py -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" faulty_body.py`)
was run on each of the 15 faulty bodies: all parse. The faulty bodies were never imported, run, simulated or pre-checked,
and Truth_Gate was never run. `diff` of faulty against fixed (text comparison) confirmed that they differ only in the error and
its correction.

### Deviations from the private notes
- B3B-03: the faulty test is the Student (pooled) test, which the note allows.
- Guard readings as above (B3B-06, -08, -09, -10, -13, -14).
- Others: none.

### Repairs
None requested; no rate or test result was seen.
