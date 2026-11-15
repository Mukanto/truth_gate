# LOG, B-3 criterion author, Phase C part 1

Status: COMPLETE (BRIEFS.json, PRIVATE.json, LOG.md written).

## Files read (sandbox only)
AUTHOR_PHASE1_C.md, PREREG_PHASE_C.md (all), SOURCES.md, SOURCES_ADDENDUM.md, PREREG_PHASE_B.md (lines 15-84: B-3 row, decision rules, section 2 timing, encoding, guards). agent_docs/ and pkg/ listed, not needed in this part.

## Sources read and URLs tried (every URL)
| Source | URL | Result |
|---|---|---|
| CUR13 | https://pubmed.ncbi.nlm.nih.gov/24022766/ | blocked (cookie wall) |
| CUR13 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1152/advan.00053.2013&resultType=core&format=json | OK, abstract read (full text not open, as the addendum says) |
| ARC81 | https://pmc.ncbi.nlm.nih.gov/articles/PMC1345570/ | blocked (reCAPTCHA); this PMCID was a guess, not verified |
| ARC81 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22Mathematic%20coupling%20of%20data%22&resultType=core&format=json | OK, search hits |
| ARC81 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:7212790%20AND%20SRC:MED&resultType=core&format=json | OK, abstract read in full (PMID 7212790; full text subscription only) |
| KRO93 | https://www.jstor.org/stable/2983064 | blocked (client challenge) |
| KRO93 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22Spurious%20correlation%20and%20the%20fallacy%20of%20the%20ratio%20standard%22&resultType=core&format=json and ...query=DOI:%2210.2307/2983064%22... | no record of the paper itself (hit count 0 for DOI) |
| KRO93 | https://api.crossref.org/works/10.2307/2983064 | metadata only, no abstract |
| KRO93 | https://api.openalex.org/works/doi:10.2307/2983064 | metadata only, no abstract |
| KRO93 | https://api.semanticscholar.org/graph/v1/paper/DOI:10.2307/2983064?fields=title,abstract,tldr | abstract elided by publisher; tldr only: "ratios in regression analyses can lead to incorrect or misleading inferences ... avoid ratios in regression" |
| PEA97 | https://royalsocietypublishing.org/doi/10.1098/rspl.1896.0076 | 403 |
| PEA97 | https://api.openalex.org/works/doi:10.1098/rspl.1896.0076 | metadata, no full text |
| PEA97 | https://archive.org/advancedsearch.php?q=title%3A%28spurious+correlation+indices+organs%29... | found items paper-doi-10_1098_rspl_1896_0076 and philtrans00847732 |
| PEA97 | https://archive.org/metadata/paper-doi-10_1098_rspl_1896_0076 , https://archive.org/metadata/philtrans00847732 | metadata OK |
| PEA97 | https://archive.org/download/paper-doi-10_1098_rspl_1896_0076/paper-doi-10_1098_rspl_1896_0076.pdf | empty response via curl to stdout (to retry with another method) |

## Incident (disclosed)
Two `ctx_search` calls without a `source` filter returned snippets indexed by OTHER sessions of this machine's shared context-mode store (labels such as "batch:MAK19 eLife ten mistakes headings,ARC81 Europe PMC search,Bland Altman BMJ 1994" and "CUR13 Curran-Everett ratios search"). That is outside my sandbox. I did not seek it, did not use it beyond what I then re-fetched myself from Europe PMC (the ARC81 and CUR13 abstract texts are from my own fetches above), and from then on I use ctx_search only with a `source` filter on my own labels or avoid the shared store. The only content seen were public abstracts; the labels reveal that some earlier session looked at ARC81, CUR13, MAK19 and a Bland-Altman paper. Reported in the final message.

## What the sources say (as read)
* CUR13 abstract: ratio meaningful "only if the relationship between numerator and denominator is a straight line through the origin"; regression incl. analysis of covariance "can accommodate an analysis of the relationship between numerator and denominator when a ratio is useless".
* ARC81 abstract: four coupling types. Type 1 directional changes; Type 2 functional relationship between two calculated variables with common component variables; Type 3 direct algebraic coupling, one variable derived from another; Type 4 indirect/physiologic coupling. "one variable either directly or indirectly contains the whole or components of the second variable."
* KRO93: only title and the Semantic Scholar tldr read (ratios in regression give misleading inferences; recommends avoiding them; correction = regression with the denominator as covariate). Documenting passage will be located as title/abstract level only.
* PEA97: title only so far (spurious correlation of indices: ratios sharing a denominator).

## Briefs drafted (all 12 kept; text in BRIEFS.json, notes in PRIVATE.json)
| id | source | tag | family | setting, size |
|---|---|---|---|---|
| B3-01 | CUR13 | ratio-vs-denominator-proxy | regression-slope | heart weight, treated (bool), body mass; 48 animals |
| B3-02 | CUR13 | ratio-vs-denominator-proxy | correlation | albumin and creatinine excretion, age; 800 participants |
| B3-03 | CUR13 | ratio-vs-denominator-proxy | R-squared | LV mass, body surface area, systolic BP; 300 patients |
| B3-04 | CUR13 | ratio-shared-denominator | regression-slope | liver, kidney weight, body mass; 150 mice |
| B3-05 | PEA97 | ratio-shared-denominator | correlation | femur, tibia, humerus lengths; 1000 skeletons |
| B3-06 | PEA97 | ratio-shared-denominator | correlation | 3 observers' estimates vs true value; 200 trials x 3 |
| B3-07 | PEA97 | ratio-shared-denominator | regression-slope | organ lengths over body length, per species; 15 x 40 |
| B3-08 | ARC81 | change-vs-baseline | correlation | fall in SBP vs second baseline reading; 120 patients |
| B3-09 | ARC81 | shared-measured-component | correlation | O2 delivery vs expired-gas uptake (cardiac output shared by the Fick-calculated version); 60 patients |
| B3-10 | ARC81 | target-from-labels | classification | AUC of item 1 for a label from the item total; 300 x 8 |
| B3-11 | KRO93 | ratio-shared-denominator | R-squared | qPCR genes A, B, C; 96 samples |
| B3-12 | KRO93 | ratio-vs-denominator-proxy | regression-slope | monthly admissions vs time and population; 120 months |

Per source: CUR13 4, PEA97 3, ARC81 3, KRO93 2. On the addendum source (CUR13): 4 of 12. Banned-term scan (my own script over BRIEFS.json, the listed terms plus ratio, divid, normali, select, independent, shared, common): no hit except the substring in 'individuals' (B3-07).

## Abandoned briefs (considered, not drafted into the files)
* Mean of a ratio as an estimate of a slope ('mean(y/x) >= threshold', CUR13): no B-3 tag fits (a ratio related to nothing).
* Ratio against its own denominator (y/x vs x) with a positive claim (CUR13/KRO93): the artefact is negative in sign when the numerator is unrelated to the denominator; a positive claim cannot be false-passed that way, and the sub-proportional-scaling estimand was not clean (measurement error biases the fixed slope too). Dropped.
* Relative vessel dilation (percent change from baseline) vs baseline diameter: the quotient really does fall in the world where the absolute change is constant, so the claim's estimand did not separate the faulty from the fixed statistic cleanly. Dropped.
* Ecological regression of district counts on district counts with population as denominator (KRO93 line): counts scale with the denominator, so no artefact arises by construction without a further assumption; dropped.
* Nutrient densities per energy (same reason: numerators scale with the denominator).

## Rules found hard to satisfy
* ARC81 and KRO93 settings: the full texts are not open; the settings of B3-08 to B3-12 are my illustrations of the abstract-level definitions, not examples read in the sources (flagged in the private notes). The same for CUR13 (abstract only, as the addendum says).
* B3-01 family: the claim's threshold is on a regression coefficient of a bool predictor, so regression-slope precedes mean by the precedence rule.

## Checkpoint 2 (after the usage-limit reset)
* PEA97 FULL TEXT read: https://archive.org/download/philtrans00847732/00847732_djvu.txt (OCR of Proc. R. Soc. 60:489-498, sections 1-5: indices with the same denominator, bones example r about 0.4-0.5, shrimp/prawn/crab organs over total length, personal-equation data of three observers, formula for r of two indices, r = 0.5 for equal coefficients of variation). The PDF at archive.org/download/paper-doi-10_1098_rspl_1896_0076/...pdf returned 200 and 606541 bytes by curl -o /dev/null but empty via stdout; not needed.
* KRO93 ABSTRACT read in full: https://econpapers.repec.org/RePEc:bla:jorssa:v:156:y:1993:i:3:p:379-392 ("consequences of using a single ratio as either the dependent or one of the independent variables in a multiple-regression analysis ... incorrect or misleading inferences ... use of ratios in regression analyses be avoided"). Also found via https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22Kronmal%22%20AND%20%22ratio%22%20AND%20%22spurious%22 a 2026 open-access paper PMC13633979 (fulltextXML at https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13633979/fullTextXML) that cites KRO93 for regression with the denominator as a covariate instead of a ratio (secondary).
* ARC81: abstract only (Europe PMC, PMID 7212790). Citing-paper lookups (secondary, reference lists only, no Archie settings): fullTextXML of PMC2578938, PMC2588884, PMC464119, PMC1746239, PMC1478791 via europepmc REST. Also https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:18563386... (2008 paper on coupling, no abstract).
* CUR13: abstract only.
* WebSearch used once for the KRO93 abstract (query text: title and 'abstract').

## Resume point
Plan fixed (12 briefs): CUR13 x4 (B3-01..04), PEA97 x3 (B3-05..07), ARC81 x3 (B3-08..10), KRO93 x2 (B3-11,12). Done: BRIEFS.json, PRIVATE.json and this log written and validated.

# Part 2 (criterion bodies), B-3 criterion author

## Files read (sandbox only)
AUTHOR_PHASE2_C.md, PREREG_PHASE_C.md, PREREG_PHASE_B.md, SOURCES_ADDENDUM.md, LOG.md and PRIVATE.json (part 1), agent_docs/GATE.md (grep of the probe passages), pkg/truth_gate/probes.py and the Control/Study dataclasses in pkg/truth_gate/study.py (probe definitions and attribute names), all 12 `cases/B3-xx/ASSIGNMENT.json` and `skeleton.py`. No URL was fetched in part 2 (no `ctx_*` tool called); the documenting passages are those recorded in part 1. Truth_Gate was never run; the package was imported only so that the fixed case files load (pkg/ first on sys.path).

## Work
* Wrote the 12 faulty and 12 fixed criterion bodies with `work/build_bodies.py` (replaces only the line `    raise NotImplementedError` in the copies of the skeletons; verified for all 24 files that the text before and after that line equals the skeleton). Helpers are defined inside the body; only `d` and `np` are used; no module-level skeleton name is read; no randomness.
* Syntax check of every faulty file with `ast.parse`: all 12 ok. The faulty criteria were never imported, run, simulated or pre-checked.
* Student-t tail (needed in B3-01 and B3-12 because only numpy is allowed): numerical integral after the substitution x = sqrt(df) tan(theta); checked against scipy in `work/check_tsf.py` (helper only): max absolute error 2.2e-6 over df 1..797 and t -3..8.
* Pre-check of the fixed criterion, run 1 (`work/precheck_fixed.py`, output `work/precheck_fixed_run1.txt`): 300 samples each of plus, minus, every declared control (transform applied to a plus sample) and the noise probe, one zeros sample, per case. Plus hold rates: 01 0.94, 02 1.00, 03 0.99, 04 1.00, 05 1.00, 06 1.00, 07 1.00, 08 0.92, 09 1.00, 10 1.00, 11 0.93, 12 0.95. Minus hold rates: 01 0.08, 02 0, 03 0, 04 0.16, 05 0, 06 0, 07 0, 08 0, 09 0.02, 10 0, 11 0, 12 0.12. Controls and noise: all at or below 0.05 except B3-04's control (0.19) and B3-12's permute-time control (0.05). Zeros: None everywhere. B3-10 noise: None in 300/300 (one label class empty).
* Revisions of the fixed criteria: 0 for all 12.
* Timing: estimates between 0.1 s and 1.0 s (limit 900 s); no speed change.
* Weak fixed criteria recorded in CASE.md, not repaired: B3-04 (minus 0.16), B3-12 (minus 0.12), B3-01 (minus 0.08).
* Deviations from the private notes (in the CASE.md of each): B3-01 faulty uses the pooled two-sample t test (OLS on the treatment dummy) instead of Welch, so both versions share one routine; B3-07 returns None when any species has an undefined coefficient instead of skipping it; guard minima are the smallest size at which each version's own statistic is defined (faulty simple models one observation smaller than the fixed models, as in the notes).
* CASE.md written last for all 12 cases (`work/build_case_md.py`).
* Skeleton requests: none. Size requests: none.
