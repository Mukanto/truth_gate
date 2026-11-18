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

## Criteria (criterion author, half B3A)

### What was written
For all 15 cases (folder ids D-006, D-008, D-015, D-017, D-020, D-031, D-036, D-037, D-038, D-040, D-050, D-053, D-062, D-067, D-071): `faulty_body.py`, `fixed_body.py`, `CASE.md` in `cases\<id>\`. Scratch scripts in `work\`: `gen.py` (writes the 30 body files as text; never imports them), `check_form.py` (AST form check, fixed bodies only), `run_fixed.py` (fixed bodies on self-generated arrays), `check_estimators.py` and `why_none.py` (fixed code only), `make_case_md.py` (CASE.md text), `run_fixed_output.txt`.

### Sources and URLs
Nothing fetched online (no WebSearch, no WebFetch, no curl). Read inside the sandbox: `CRITERION_AUTHOR_D.md`, `SOURCES.md`, `SOURCES_D.md`, `half\BRIEFS.json`, `half\PRIVATE.json`, `half\CASE_IDS.json`, `half\LOG.md`, `half\cases\D-006\brief.json`, a grep of `agent_docs\README_TOOL.md`, and `half\fetched\chi13.txt` (the Analyses/Blomqvist passage, to confirm the formulas of the CHI13 cases). `pkg\` was not read or imported. Truth_Gate was not run in any form. No context-mode tool, no agent, no git.

### Design
- Each body file has `import numpy as np`, small shared helpers (`_flat`, `_corr`, `_resid`, `_partial_corr`, `_r2`, `_std_coef`, `_change_stats`, same set in both files of a case) and `criterion(d)`. The two files of a case differ only in the error line(s) and the correction line(s); the `diff` of each pair was read (no other difference).
- Structure of every `criterion`: load; non-finite and minimum-size guards; the error or the correction lines; identical zero-variance guards on the quantities that enter the statistic; the statistic; comparison with the claim's threshold. No randomness is used (no `rng`), so the same data always give the same answer.
- Estimators: partial correlation = correlation of least-squares residuals on an intercept and the accounted variable; standardised coefficient = coefficient times SD(regressor)/SD(response); incremental R-squared = difference of two least-squares R-squared values; Blomqvist = `(b_crude + k)/(1 - k)` (CHI13), faulty passes `k = 0.0` (crude); random-effects correlation (D-006) in closed form for the balanced design (covariance of per-child least-squares coefficients minus sigma^2 (X'X)^-1).
- Faulty bodies: syntax check only (`py -c "import ast,sys; ast.parse(...)"`), all 15 OK. Never run or simulated.

### Runs of the fixed bodies (all on arrays generated here; no rates)
1. Form check of the 15 fixed bodies (`check_form.py`): OK.
2. Smoke (`run_fixed.py`, 3 independent random arrays per case with the brief's keys, shapes, dtypes): all return bool, or None for D-006, D-015 in some draws. Maximum time per call at most 1.1 ms (D-062), others below 0.4 ms. First version of D-037 also returned None on some arrays; see revisions.
3. Direction run (one clearly-claim-met and one clearly-claim-not-met self-built array per case): True and False for all 15.
4. Estimator checks on known truth (`check_estimators.py`, n = 200000): D-015 adjusted corr(level, change) -0.6287 vs true -0.6270 (crude -0.6542); D-037 adjusted slope -0.5048 vs true -0.5019 (crude -0.7521), k from a retest sample 0.5016 vs 0.4999; D-006 corrected correlation -0.6289 vs true -0.6270 (uncorrected -0.6857); partial correlation (D-040 helper) 0.5021 vs 0.5000; standardised coefficient (D-038 helper) 0.1766 vs 0.1778.
5. `why_none.py`: the None results of D-015 come from k > 1 (estimated ICC below 0, so the true-part variance is not positive); those of D-006 from an estimated variance component not positive (boundary of the random-effects fit), on independent random arrays with no trend.

### Revisions of the fixed bodies (after their first run)
- D-015: 1 (helper `_change_stats` now returns the slope and the correlation and each caller checks the one it uses; docstring extended; both files changed alike).
- D-037: 1 (same helper change: the first version returned None when the correlation was not finite although the claim uses only the slope).
- D-006: 1 (docstring only: the None condition of the fitted model was added).
- All other cases: 0. (Before the first run of any body I corrected the generator twice: the zero-variance test in `_change_stats` now uses `_flat`, and D-037's `k` line; not counted as revisions of a run body.)

### Deviations from the private notes
- Minimum sizes capped at the smallest size at which the statistic is defined: partial correlations (D-040, D-062 per species, D-031) 3 instead of 4; D-008 at least 1 patient with a defined slope instead of 2.
- D-006: the fitted random-effects model returns None when an estimated variance component is not positive (a boundary solution with undefined correlation). I read it as the zero-variance guard / non-finite result, but it can return None on arrays without a trend; flagged for review in `CASE.md`.
- D-015: the conversion of the adjusted slope to a correlation uses the true-part SDs derived from k (the source gives no formula for r_Blomqvist); non-positive true-change variance gives None as non-finite.
- D-017: the faulty rescaling uses the mean height of all subjects (the note leaves the rescaling height open).
- No repair request received; no rate or test result from any later check was seen.

### Rules found impossible to satisfy
None.
