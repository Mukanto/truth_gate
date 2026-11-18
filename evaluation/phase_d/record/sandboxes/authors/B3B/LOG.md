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
