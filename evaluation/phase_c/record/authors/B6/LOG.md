# LOG (B-6 criterion author, Phase C part 1)

Status: COMPLETE. BRIEFS.json, PRIVATE.json (12 briefs each) and this log are written. Term check (banned list) run on BRIEFS.json by a read-only python snippet: no hits; JSON valid; key sets as the instruction file requires.

## Sandbox files read (local)
AUTHOR_PHASE1_C.md, PREREG_PHASE_C.md, SOURCES_ADDENDUM.md, SOURCES.md, PREREG_PHASE_B.md (lines 20-100 plus a grep). Nothing outside the sandbox was read. The coordinator message after a usage-limit reset was acted on (log written early, then appended/finalised).

## Sources read and how
| Key | How read | Location |
|---|---|---|
| LAZ18 (addendum) | full text | PMC5902037 (sections: Animal experiments, Cell culture experiments, Slice preparations and histological samples, EU criteria incl. cages and drinking water, Analysis of hierarchical data, Box 1, Fig 1 literature review) |
| LAZ10 | full text (Europe PMC XML) | PMC2817684 (Background incl. rotarod example, intraclass correlation, Table 1, repeated measures, hierarchical data, summary-measure analysis, How to check reported values) |
| MAK19 | full text (Europe PMC XML) | PMC6785265 (section 'Interpreting comparisons between two effects without directly comparing them', Figure 1; 'Inflating the units of analysis' read but no brief rests on it) |
| NIE11 | abstract only (Europe PMC record; full text not open) | PMID 21878926; the documenting passage is in the abstract |
| HUR84 | full text of the PDF (text extracted in memory with pypdf, nothing saved) | Abstract; sections on simple, temporal and sacrificial pseudoreplication (pp. 200-205) |
| GEL06 | not read (supporting material only; no brief rests on it) | - |

Independent read sources for B-6: NIE11, HUR84, LAZ10, MAK19 (4), plus addendum LAZ18 (not counted as independent of LAZ10).

## URLs (every one fetched or searched)
1. https://pmc.ncbi.nlm.nih.gov/articles/PMC5902037/  LAZ18 full text, OK.
2. https://pmc.ncbi.nlm.nih.gov/articles/PMC2817655/  WRONG article (my guessed id; Toll-like receptors paper); content not used.
3. https://pmc.ncbi.nlm.nih.gov/articles/PMC6822592/  WRONG article (grant planning); not used.
4. https://europepmc.org/api/fulltextRepo?pprId=&type=FILE  HTTP 500, nothing read.
5. WebSearch (standard) for LAZ10 / MAK19 / NIE11 identifiers; it listed other URLs which I did not read except those below.
6. https://pmc.ncbi.nlm.nih.gov/articles/PMC2817684 , https://pmc.ncbi.nlm.nih.gov/articles/PMC6785265 , https://pubmed.ncbi.nlm.nih.gov/21878926/  returned bot-check pages (reCAPTCHA/cookies); not bypassed, nothing read.
7. https://fortinlab.bio.uci.edu/resources/Erroneous_analyses_of_interactions_in_neuroscience.pdf  HTTP 404.
8. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2817684/fullTextXML  LAZ10 full text, OK (read again by direct fetch inside a python snippet for the rotarod, IC and summary-measure passages).
9. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6785265/fullTextXML  MAK19 full text, OK.
10. https://elifesciences.org/articles/48175  client-challenge page; nothing read.
11. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:21878926%20AND%20SRC:MED&resultType=core&format=json  NIE11 abstract record, OK.
12. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5902037/fullTextXML  LAZ18 full text via Europe PMC (re-read for the cage, multi-day, Box 1 and hierarchical-data passages).
13. WebSearch (standard) for the HUR84 abstract.
14. https://www.zoology.ubc.ca/~bio501/R/readings/hurlbert%201984%20ecol%20monogr%20-%20pseudoreplication.pdf  HUR84 PDF; the indexer returned binary, so the text was extracted in memory with pypdf (25 pages, OK).
15. https://biomedical-sciences.ed.ac.uk/sites/default/files/2024-08/Hurlbert%20article%201984.pdf and https://agris.fao.org/search/fr/records/65deb72a90674e46e6533b00  fetched into the search index; binary/uninformative, not used.

No fetch from github.com/Mukanto/truth_gate or any published evaluation material. No Truth_Gate run, no criterion code, nothing written outside this sandbox folder.

## Briefs written (12, none abandoned)
| id | source | mechanism | family | setting | sizes |
|---|---|---|---|---|---|
| B6-01 | LAZ18 | units-not-independent | mean | prenatal exposure, pups of dams | 20 dams x 8 pups |
| B6-02 | LAZ18 | units-not-independent | proportion | cell culture, responding cells in wells | 12 wells x 150 cells |
| B6-03 | LAZ18 | units-not-independent | regression-slope | histology, dose per animal, neurons in sections | 12 x 4 x 25 |
| B6-04 | LAZ18 | units-not-independent | mean | cage-level drinking-water treatment, 2 animals per cage | 40 cages x 2 |
| B6-05 | NIE11 | significant-here-not-there | mean | pre/post change in two groups | 40 subjects |
| B6-06 | NIE11 | significant-here-not-there | regression-slope | per-subject learning slopes, two groups | 30 x 8 |
| B6-07 | NIE11 | significant-here-not-there | mean | task effect in region A vs region B, within subject | 24 subjects |
| B6-08 | HUR84 | units-not-independent | mean | samples within tanks (sacrificial) | 8 tanks x 10 |
| B6-09 | HUR84 | units-not-independent | other (Mann-Whitney) | successive dates within plots (temporal) | 12 plots x 12 dates |
| B6-10 | LAZ10 | units-not-independent | mean | rotarod, rats x 3 days | 10 rats x 3 days |
| B6-11 | LAZ10 | units-not-independent | correlation | subject means over repeated days | 16 subjects x 10 days |
| B6-12 | MAK19 | significant-here-not-there | correlation | difference of two correlations, groups of 20 | 40 participants |

Per source: LAZ18 4, NIE11 3, HUR84 2, LAZ10 2, MAK19 1 (max 4 respected). Addendum-source briefs: 4 (LAZ18).

## Abandoned briefs / considered and dropped before writing
* Multi-day cell-culture design (days x wells, treatment crossed with day, paired by day): dropped, because ignoring the day pairing makes the pooled well-level test conservative, not too liberal, so it would not show the documented error.
* Hurlbert simple pseudoreplication (one unit per treatment): dropped, because with 1 unit per group no fixed analysis exists.
* Hurlbert/Lazic single-rat-per-group hierarchical example (2 rats x 100 cells): dropped, because the fixed criterion cannot estimate any between-unit variance.
* A brief on MAK19 "Inflating the units of analysis" (pre/post in 10 participants, regression): dropped for overlap with B6-11 in statistic and structure; and cap on MAK19.

## Notes on rules
* Rules found impossible to satisfy: none. Two points of judgement are recorded in the private notes: B6-11 extends LAZ10's repeated-measures statement to a correlation; B6-09 uses a Mann-Whitney test (family `other`).
* The sizes field is a string that states every array dimension as a number and each array's value count.
* The brief claims name the quantity the fixed analysis estimates (for example the test of the difference between two effects, the per-subject slope, the subject means); the estimand lines in PRIVATE.json say why.


# Part 2 (B-6 criterion author, Phase C criterion bodies)

Status: COMPLETE for all 12 cases (B6-01 .. B6-12): `faulty.py`, `fixed.py` and `CASE.md` written in every case folder.

## Files read (local)
AUTHOR_PHASE2_C.md, PREREG_PHASE_C.md, PREREG_PHASE_B.md, SOURCES.md, SOURCES_ADDENDUM.md, this LOG.md (Part 1), PRIVATE.json, agent_docs/GATE.md (lines 100-175 and a grep for 'probe'), pkg/truth_gate/study.py (class names and Study fields only, to read attributes in the pre-check script), cases/*/ASSIGNMENT.json and cases/*/skeleton.py (all 12).
URLs fetched in Part 2: none. No ctx_* tool was used. Nothing outside the sandbox folder was read; nothing was written outside it.

## Method
* `work/make_cases.py` (text only) builds faulty.py and fixed.py from skeleton.py by replacing the single line `    raise NotImplementedError`; it never imports or executes a case file. `work/verify_twins.py` (text and AST) checks that the twins equal the skeleton outside the criterion body, that the body reads no module-level name except `np`, has no import, no `np.random`, no `default_rng`. Result: all 12 ok.
* No criterion uses randomness, so no `rng` is created. The p value of Student's t is computed inside the body with a numpy-only incomplete-beta helper (Lanczos log-gamma, Lentz continued fraction) because scipy and `math` may not be imported. Helper text tested against scipy.stats.t.sf (`work/helper_test.py`, log `work/helper_test_log.txt`): 2238 points, largest relative error 3.9e-11. The z tests (B6-09, B6-12 fixed) use the constant 1.959963984540054 (two-sided 5% normal critical value).
* Twin structure: in B6-01, 02, 03, 04, 08, 09, 10, 11 the twins differ in exactly the two lines that build the analysed arrays (`.ravel()` or a repeated dose versus `.mean(axis=1)`). In B6-05, 06, 07, 12 the faulty criterion is the "significant here, not there" rule (two one-sample or group-wise tests and a pattern decision) and the fixed criterion the direct test of the difference (change-score t test, slope t test, paired t test on the difference of effects, Fisher z).

## Pre-checks of the FIXED criteria (never of the faulty ones)
* Pre-check 1 (`work/precheck_fixed.py 400`, log `work/precheck_fixed_log_run1.txt`): 400 samples per stream per case (plus, minus, declared control on plus samples, hand-built noise probe, all-zero probe 20 samples, declared shuffle probe), plus agreement with an independent scipy implementation on 800 samples and timing. plus 0.895-0.932, minus 0.013-0.037, control 0.000-0.045, noise 0.010-0.028; scipy disagreements 0 in all 12 cases.
* Pre-check 2 (final structure, `work/precheck_fixed.py 1000`, log `work/precheck_fixed_log_run2_final.txt`): 1000 samples per stream. plus 0.900-0.935, minus 0.020-0.033, control 0.006-0.050 (B6-12: 0.050), noise 0.018-0.031, shuffle 0.024-0.033; scipy disagreements 0 of 2000 in all 12 cases. All-zero probe: None (zero variance or empty group) in every case.
* Revisions of any fixed criterion: 0 in all cases. One revision of a FAULTY criterion text (before any run, by design of the text only): B6-02 faulty was changed from the note's two-proportion z test to the same Welch t function as the fixed criterion applied to the cell-level 0/1 responses, so that the twins differ only in the unit (reason: audit items (c) and (g); reported as a deviation in CASE.md). The fixed B6-02 criterion was not touched by that change.
* The faulty criteria were never run, simulated or pre-checked. The only operation on them: the syntax check `py -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" faulty.py` (12 of 12 ok), and the text/AST check above.

## Timing (final fixed criterion, mean of 100 calls on plus samples)
t about 0.03-0.06 ms, g about 0.01-0.07 ms; S = 5 (B6-04 and B6-11: 6); estimates 2 x 200 x (S + 1) x (t + g) between 0.14 s and 0.28 s (limit 900 s). No timing remedy, no SIZE REQUEST.

## Deviations from the private notes (details in each CASE.md)
* B6-02: faulty uses Welch t on the cell-level 0/1 outcomes instead of a two-proportion z test (see above).
* B6-09: guard minimum 1 plot per group instead of the note's 2 (the rank-sum statistic exists from 1; PREREG_PHASE_C section 2 caps the minimum at the smallest defined size). Normal approximation with tie and continuity corrections in both twins.
* B6-12: faulty uses the same 4-per-group guard as the fixed (note: same guards in both twins).
* B6-05, 06, 07: the faulty rule constrains only the direction of the first effect; the second effect only has p >= 0.05 (as NIE11 describes the pattern).
* Skeleton requests: none. SIZE REQUESTs: none.
* Observation, recorded not acted on: B6-12 fixed holds in 0.050 of control samples (above the 0.025 one-sided null rate).
