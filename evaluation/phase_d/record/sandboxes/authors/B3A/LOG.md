# LOG, author B3A (B-3, half A)

## Sources read, and how
- **CHI13** (Chiolero et al. 2013): full text, via the Europe PMC full-text XML. Read in full: abstract, Problem, methods table, Simulations (scenarios, analyses), Results, Discussion, Glossary, Appendix.
- **PEA97** (Pearson 1897): abstract only, OCR text from OpenAlex (`abstract_inverted_index`, read from the saved JSON). The abstract is the whole readable text.
- **KRO93** (Kronmal 1993): abstract only, through the RePEc/IDEAS page (WebFetch excerpt and summary). OpenAlex returned only the citation line. The passage in SOURCES_D (single ratio, deflator as covariate) was also used.
- **ARC81** (Archie 1981): abstract only, PubMed efetch text. Full text (PMC1345065) not retrievable (HTTP 500). The abstract documents the coupling, not a correction; the correction used in the notes is the generic remedy (an independent measurement of the shared term) and the notes say it is not verified in the source text.

## URLs
- https://pmc.ncbi.nlm.nih.gov/articles/PMC3854983/ (WebFetch; blocked by a browser-verification page, nothing read)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3854983/fullTextXML (curl, saved to `fetched/chi13.xml` and `fetched/chi13.txt`; read in full)
- https://api.openalex.org/works/doi:10.1098/rspl.1896.0076 (curl, `fetched/pea97.json`; abstract read)
- https://api.openalex.org/works/doi:10.2307/2983064 (curl, `fetched/kro93.json`; citation line only)
- https://api.openalex.org/works/doi:10.1097/00000658-198103000-00008 (curl, `fetched/arc81.json`; saved, not used)
- https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=7212790&retmode=text&rettype=abstract (curl, `fetched/arc81_pubmed.txt`; abstract read)
- https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1345065/fullTextXML (curl; HTTP 500, nothing)
- https://ideas.repec.org/a/bla/jorssa/v156y1993i3p379-392.html (WebFetch; KRO93 abstract excerpt)
- WebSearch 1 (query on the KRO93 title and abstract). Result URLs listed, only the IDEAS/RePEc page was fetched: https://econpapers.repec.org/RePEc:bla:jorssa:v:156:y:1993:i:3:p:379-392, https://ideas.repec.org/a/bla/jorssa/v156y1993i3p379-392.html, https://bibbase.org/network/publication/kronmal-spuriouscorrelationandthefallacyoftheratiostandardrevisited-1993, https://scilit.com/publications/744bfa104a404ed3000d83b26571acba, https://www.law.nyu.edu/sites/default/files/The%20Ratio%20Problem.pdf, and others (snippets only, not fetched)
- WebSearch 2 (query on Archie 1981, type 2 coupling, oxygen delivery and consumption). Only search snippets were seen, none fetched: https://deepblue.lib.umich.edu/bitstream/2027.42/27778/1/0000172.pdf (snippet: oxygen delivery and consumption both contain cardiac output), https://pmc.ncbi.nlm.nih.gov/articles/PMC464119, https://www.jci.org/articles/view/108541/version/1/pdf/render.pdf and others. Used only as support that the setting (delivery vs Fick consumption sharing cardiac output) is the textbook physiological case; not a documenting passage.
- No GitHub repository and no published evaluation material was fetched.

## Analysis code run (the one allowed exception)
- `scratch/check_stats.py`, run as `py -I scratch/check_stats.py`: builds arrays with each brief's shapes and sizes (random positive log-normal values; random booleans for `smoker`), runs each `structure_statistic.code` and prints type and finiteness. Result: all 15 statistics return a Python `float`, finite. No other analysis code was written or run. The JSON files were also loaded by that script, which confirmed they parse.

## Briefs drafted (15 written, 0 abandoned)
IDs are neutral (B3A-01 to B3A-15); the source map is in `PRIVATE.json`.

| id | source | tag | family | role | setting |
|---|---|---|---|---|---|
| B3A-01 | PEA97 | ratio-shared-denominator | correlation | pair | skulls, partial correlation given length, n=300 |
| B3A-05 | PEA97 | ratio-shared-denominator | proportion | pair | share of 12 species with partial correlation >= 0.2 |
| B3A-09 | PEA97 | ratio-shared-denominator | regression-slope | pair | rats, standardised slope, n=60 |
| B3A-11 | PEA97 | ratio-shared-denominator | R-squared | reserve | mice, incremental R-squared, n=1500 |
| B3A-02 | KRO93 | ratio-vs-denominator-proxy | mean | pair | FVC, smokers vs non-smokers, adjusted for height, n=600 |
| B3A-06 | KRO93 | ratio-vs-denominator-proxy | regression-slope | pair | deaths on sales with population, ratio as regressor, n=150 |
| B3A-10 | KRO93 | ratio-vs-denominator-proxy | R-squared | pair | liver mass, age beyond body mass, n=80 |
| B3A-12 | KRO93 | ratio-vs-denominator-proxy | correlation | reserve | cities, offences and median age given population, n=500 |
| B3A-03 | CHI13 | change-vs-baseline | correlation | pair | two waves plus a second baseline reading, n=500 |
| B3A-07 | CHI13 | change-vs-baseline | correlation | pair | six annual waves, random-effects correlation, 500 x 6 |
| B3A-13 | CHI13 | change-vs-baseline | regression-slope | reserve | Blomqvist, error variance from a retest sample |
| B3A-14 | CHI13 | change-vs-baseline | R-squared | reserve | Blomqvist-adjusted R-squared, second baseline reading |
| B3A-04 | ARC81 | shared-measured-component | correlation | pair | oxygen delivery vs consumption, n=120 |
| B3A-08 | ARC81 | shared-measured-component | regression-slope | pair | within-patient slope, 40 x 6 occasions |
| B3A-15 | ARC81 | shared-measured-component | R-squared | reserve | vascular resistance vs its own cardiac output |

Pairs: PEA97 3, KRO93 3, CHI13 2, ARC81 2 (10). Reserves: PEA97, KRO93, CHI13 x 2, ARC81 (5).

## Design decisions and rule notes
- Earlier tag-family combinations: avoided where the source allowed (PEA97 proportion in B3A-05; KRO93 mean in B3A-02; all CHI13 combinations were new). Not avoidable: PEA97 slope and R-squared, KRO93 slope, R-squared and correlation, ARC81 correlation, slope and R-squared. The natural statistics of a ratio-shared-denominator setting are correlation-type, and the proxy settings need a regression statistic. Each repeated combination differs in data structure, pipeline step or size; the private notes say so.
- Claims that depend on the sign of an induced association (B3A-02, -06, -12) are stated in absolute value, because the sign depends on how the world author relates the variables.
- The claim names the accounting variable only where the estimand needs it (length, height, population, body mass, delivery and consumption, cardiac output). No key is named by its role in the error; second readings (`bmi_baseline_retest`, `bmi_retest`, `co_fick`, `vo2_expired_gas`) are described by what they measured, as PC allows for the independent measurement a documented correction uses.
- Banned-term check on `BRIEFS.json` (grep, case-insensitive, all listed terms): no hit.
- ARC81 is read from its abstract only; its correction (independent measurement of the shared term) is not in the abstract.
- B3A-03, B3A-13 and B3A-14 give a five-year follow-up gap, which is the setting of the source's simulation (ages 5 to 10).
- No repair request was received; no rate or test result from any later check was seen.

## Rules found impossible to satisfy
None.

## Repair 1 (B3A-02, structure_statistic)
- Request: the "source states none" value 0.3 for the point-biserial correlation between `smoker` and `height` was rejected as implausibly large (about 0.6 SD height gap) with no stated mechanism.
- Changed only `structure_statistic.note_value` (0.3 to 0.1) and `structure_statistic.note_value_source` of B3A-02 in `PRIVATE.json`. The statistic code, the brief, the sizes and every other field are unchanged.
- New reason: mixed-sex sample, male-female height gap about 13 cm (within-sex SD about 7 cm, total SD about 9.5 cm), smoking somewhat more frequent in men (for example 30% against 15%), giving smokers about 2.8 cm taller (standardised difference about 0.3) and a point-biserial correlation of about 0.12 (about 0.08 at 25% against 15%); 0.1 sits between. These numbers are my own assumptions, since the source states none. The arithmetic was done by hand, no code was run.
- I confirm that I saw no count, rate or test result from any later check; the request quoted only the failing item.
