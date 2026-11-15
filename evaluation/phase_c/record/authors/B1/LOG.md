# LOG (B-1 criterion author, Phase C part 1)

Status: COMPLETE. 12 briefs written to BRIEFS.json and PRIVATE.json (same local_ids B1-01 .. B1-12, same order). Nothing abandoned after drafting; design alternatives dropped during planning are listed below.

## Files read in the sandbox
AUTHOR_PHASE1_C.md, PREREG_PHASE_C.md, PREREG_PHASE_B.md (sections 0 to 2, 4, rule lines), SOURCES.md, SOURCES_ADDENDUM.md. `agent_docs/` and `pkg/` not read (not needed in this part). Nothing outside the sandbox folder was read and nothing was written outside it except scratch text files in the session scratchpad (derived plain text of the fetched sources). Truth_Gate not run, no criterion code written.

## Sources read and how, with every URL
Tools: HTTP fetches through the context-mode fetch tool and short Python urllib scripts (plain GET, User-Agent Mozilla/5.0). No CAPTCHA or bot check was bypassed (the PMC article pages returned a browser-check text in the first indexing call; the later direct GET returned the article HTML, which is how the full text was read).
* KRI10 (addendum): https://pmc.ncbi.nlm.nih.gov/articles/PMC2949251/ read in full (abstract, introduction, questions 1 to 13 with the five authors' answers). Also https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC2949251&retmode=xml (front matter and abstract only; publisher disallows full-text XML).
* MOR03 (addendum): https://pmc.ncbi.nlm.nih.gov/articles/PMC1125994/ read in full (what is RTM, diagnostic tests, summary points, figure legend, new treatments, placebo effect, public health, healthcare management, clinical audit, solutions). Also efetch XML (front matter only).
* KRI09: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=PMC2841687&retmode=xml (author manuscript, full text; abstract, introduction, examples 1 and 2 read; supplementary information not read).
* MAK19: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6785265/fullTextXML (full text, circular analysis section read). Correct PMC id found via https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.7554/eLife.48175&format=json&resultType=lite . An earlier fetch of https://pmc.ncbi.nlm.nih.gov/articles/PMC6773438/ and https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6773438/fullTextXML was a wrong id (a different paper, on tardigrade Dsup); its content was discarded and not used.
* VUL09: abstract only, via https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1111/j.1745-6924.2009.01125.x&format=json&resultType=core . Publisher page https://journals.sagepub.com/doi/10.1111/j.1745-6924.2009.01125.x returned HTTP 403; guessed author-site PDF URLs on edvul.com returned 404 (http://www.edvul.com/pdf/VulHarrisWinkielmanPashler-PPS-2009.pdf, https://www.edvul.com/pdf/Vul-etal-2009inpress.pdf, https://www.edvul.com/voodoocorr.php).
* BAR05: abstract only, via https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1093/ije/dyh299&format=json&resultType=core . https://academic.oup.com/ije/article/34/1/215/655072 returned HTTP 403.
* Failed fetches (HTTP 500, twice): https://www.ebi.ac.uk/europepmc/webservices/rest/PMC2949251/fullTextXML, .../PMC1125994/fullTextXML, .../PMC2841687/fullTextXML.
Independent read sources used: MOR03 (full), KRI09 (full), MAK19 (full), VUL09 (abstract), BAR05 (abstract): at least 3 independent. KRI10 is not counted as independent of KRI09/VUL09 (addendum note).

## Briefs (all 12 kept)
| id | source | mechanism_tag | family | structure / size | addendum |
|---|---|---|---|---|---|
| B1-01 | MOR03 | extreme-group-change | mean | hormone-therapy trial, 2 arms, 300 women | yes |
| B1-02 | MOR03 | split-by-baseline-compare-change | mean | bone density, two 12-month scans, 600 women | yes |
| B1-03 | MOR03 | extreme-group-change | mean | blood pressure, 250 patients x 3 readings | yes |
| B1-04 | KRI10 | select-then-test-same-data | mean | subject-specific ROI, 12 x 8 runs x 300 voxels | yes |
| B1-05 | KRI10 | select-then-test-same-data | mean | group-level voxel set, 40 x 1000 | yes |
| B1-06 | KRI10 | select-then-test-same-data | regression-slope | one participant, 240 trials x 500 voxels | yes |
| B1-07 | KRI09 | select-then-test-same-data | mean | neurons, 250 x 15 trials | no |
| B1-08 | KRI09 | select-then-test-same-data | R-squared | EEG, 100 trials x 64 electrodes | no |
| B1-09 | VUL09 | select-then-test-same-data | correlation | 16 subjects x 1000 voxels, 2 sessions | no |
| B1-10 | MAK19 | split-by-baseline-compare-change | mean | neurons, tertiles, 240 | no |
| B1-11 | MAK19 | select-then-test-same-data | mean | patients vs controls, 60 x 200 time samples | no |
| B1-12 | BAR05 | extreme-group-change | proportion | 500 patients, three visits | no |

Per source: MOR03 3, KRI10 3, KRI09 2, MAK19 2, VUL09 1, BAR05 1 (cap 4 per source respected). Addendum-source briefs: 6 of 12 (minimum 4).

## Abandoned or dropped during planning (not written as briefs)
* Road-crash junction counts with a speed-enforcement programme (MOR03): no clean fixed estimand without a control key; dropped.
* Hospital league table with extra resources (MOR03): same structure as B1-01 with a control; dropped for lack of difference.
* Dispersion (SD or coefficient of variation) of responses in selected voxels (KRI10 Q8): the bias is toward smaller dispersion, so a positive claim of the form "dispersion at least x" fails more often under the error instead of holding; no positive direction worked; dropped.
* Selection by A+B and test of A-B (KRI10 Q8, orthogonal contrasts): independent under balanced noise, not an error; dropped.
* Behavioural subgroups by task performance (KRI09): same mechanism as B1-02 and B1-10; dropped in favour of the EEG case B1-08.
* MAK19 correlation of post-manipulation response with the change score: belongs to B-3 (change against its own value), excluded by the precedence rule.
* MAK19 removal of outliers before a correlation: the source documents no criterion or threshold; replaced by the time-window case B1-11, which uses the source's "defining a region of interest" along time.
* Cross-subject classifier accuracy after feature selection (KRI09 Example 1): a prediction score, excluded from B-1 by PB section 1 (belongs to B-2).

## Checks done on the briefs
Banned terms from AUTHOR_PHASE1_C (any inflection, case-insensitive) searched with a script over BRIEFS.json: no hit. Words about how items are chosen or data are split (select, split, bin, exclude, outlier, baseline) also absent, except that the claims of B1-04 to B1-12 name the group, region or window the claim's quantity refers to (the estimand lines say why). dtypes are float or bool only; group/subject/trial/time structure is carried by array axes; sizes give every dimension as a number; at most 1000 per axis and at most 500 000 values per array (largest: 86 400). All claims are positive.

## Rules found impossible to satisfy
None. Judgement calls for the designer: (1) the claim of nearly every brief names the group, region or window the estimand refers to (allowed where the estimand requires it, noted in each estimand line) while also avoiding words for the procedure; (2) B1-02, B1-09, B1-10 carry extra keys (second scan, second session, resting recording) that give the fixed criterion an independent measurement, described in the key meanings only as what each measured; (3) the cut values and thresholds for the faulty and fixed criteria that the sources do not state (t > 2.0, p < 0.05, p < 0.005, p < 0.01, window of 10) are marked as typical values in the private notes; (4) VUL09 and BAR05 were read in abstract only.

# Part 2 (criterion bodies, B-1)

Status: COMPLETE for all 12 cases (B1-01 .. B1-12). Faulty and fixed bodies written into `cases\<id>\faulty.py` and `fixed.py` (only the line `    raise NotImplementedError` replaced; both files start and end byte-identically with the frozen skeleton, verified by a prefix/suffix comparison). `CASE.md` written for every case (last).

## Files read
Sandbox only: `AUTHOR_PHASE2_C.md`, `PREREG_PHASE_C.md`, `PREREG_PHASE_B.md`, `agent_docs\GATE.md`, `SOURCES_ADDENDUM.md` (first part), `PRIVATE.json`, `LOG.md` (Part 1), every `cases\<id>\skeleton.py` and `ASSIGNMENT.json`, and in `pkg\truth_gate` only `study.py` (field names of World/Control/Study) and `probes.py` (dtype handling of the noise and zeros probes). No URL was fetched in Part 2 (the passages are the Part 1 quotations in the private notes); no `ctx_*` tool was called. Scratch scripts are in `work\`.

## Method
* One shared helper text (a Student-t upper tail by trapezoid quadrature of cos(x)^(df-1), numpy only, because the criterion may use only `d` and numpy). Checked against scipy in `work\test_sf.py` (absolute error at most 3e-5 for 1 to 600 df); scipy is not used inside any criterion.
* Bodies are generated by `work\build_bodies.py` from one template per case; the faulty and fixed bodies differ only in the lines that carry the error and its correction (B1-01 also in the test: paired within-arm versus two-arm Welch, as the note specifies).
* No randomness in any criterion (no `rng` created). Return values: True/False; None for non-finite input, an empty selection or one below the stated minimum, a zero variance. Nothing else inspects the distribution.
* Numbering convention: "even-numbered"/"odd-numbered" runs, trials and presentations are 1-based (B1-04, B1-06, B1-07, B1-08); "even-indexed participants" (B1-11) is 0-based. Stated in each `CASE.md`.

## Faulty criterion
Never run, simulated or pre-checked in any form; only `ast.parse` syntax checks were run on `faulty.py` (all 12 pass). The cross-check, pre-check and timing scripts load `fixed.py` only (the path is asserted in `work\precheck_fixed.py`).

## Pre-checks of the fixed criteria (all in `work\precheck_fixed.py`, N = 200 per stream, own seeds 70000+; results in `work\precheck_last.json`)
First (and only) run of the 12 fixed criteria; revisions of any fixed criterion: 0.
| case | plus holds | minus holds | notes |
|---|---|---|---|
| B1-01 | 198/200 | 0/200 | control 1/200; noise and zeros: None (empty selection) |
| B1-02 | 200/200 | 3/200 | control 6/200; noise 5/200 |
| B1-03 | 196/200 | 0/200 | control 0/200 |
| B1-04 | 200/200 | 0/200 | control 0/200; noise 0/200 |
| B1-05 | 200/200 | 2/200 (None 91) | controls 9 and 3/200 (None 20, 104); noise 5/200 (None 85) |
| B1-06 | 200/200 | 4/200 (None 9) | control 4, shuffle 4/200; noise 0 |
| B1-07 | 200/200 | 4/200 | control 8/200; **noise probe 99/200** (ratio index on near-zero sums; recorded in CASE.md, statistic not changed) |
| B1-08 | 179/200 | 3/200 (None 64) | control 3/200 (None 66); noise 9/200 |
| B1-09 | 199/200 | 11/200 (None 19) | control 8/200; noise 1/200 |
| B1-10 | 187/200 | 1/200 | control 4/200; noise 0 |
| B1-11 | 177/200 | 10/200 | control 9/200; noise 0 |
| B1-12 | 200/200 | 0/200 | control 0/200; noise None (empty selection) |
Zeros probe: None on all 12 (5 samples each). Cross-check of the fixed decisions against independent scipy re-implementations of the same rules (`work\crosscheck_fixed.py`, 60 plus + 60 minus samples per case): 0 disagreements in all 12 cases.

## Timing (fixed criterion; mean of 30 calls on plus samples; estimate 2 x 200 x (S+1) x (t+g), limit 900 s)
Largest: B1-05 about 93 s and B1-09 about 91 s; all others below 60 s. No size request.

## Problems recorded in CASE.md (no skeleton change requested for any)
* B1-02: the documented error biases the group difference opposite in sign to the claim's direction; a faulty miss on this pair may reflect that (qualitative statement, not simulated).
* B1-07: fixed holds on the noise probe about half the time (ratio index).
* B1-05 and B1-08: abstentions (empty selection) on 45.5% and 32% of minus samples in the pre-check; B1-09 abstains on 9.5% and its fixed criterion holds on 5.5% of minus samples.

# Repair round (B1-09, fidelity audit item (b))

Request (coordinator, from the blind audit): the fixed criterion of B1-09 must choose the voxels and estimate the correlation on different participants, not on two sessions of the same participants. Agreed; no dispute. Only the body of `cases\B1-09\fixed.py` was rewritten (`work\build_b09_repair.py`); `faulty.py` is byte-identical (SHA-256 recorded in `work\b09_faulty_sha_before.txt`, checked after: OK). No other case was touched. Syntax check by `ast.parse` on both B1-09 files: ok.
* Reason: the skeleton's stable subject-by-voxel component is shared by the two sessions, so session 2 is not independent of a choice made on session 1 (the first version held on 11/200 minus samples).
* New fixed rule: sessions averaged (as in the faulty twin); voxels chosen on participants 0-7 (same one-sided p < 0.005, 6 df); mean correlation of the chosen voxels on participants 8-15 >= 0.5. Guards: non-finite, empty selection, fewer than 3 participants per half, zero variance.
* Pre-check of the fixed criterion (plain Python, `work\precheck_fixed.py`, 200 samples per stream, `work\precheck_round2_b09.json`; first-round results kept in `work\precheck_round1.json`, `work\precheck_last.json` has the merged final values): plus 193/200 hold; minus 6/200 hold (None 15); control permute_trait 9/200 (None 9); noise 3/200; zeros None 5/5. Cross-check against a scipy re-implementation (`work\crosscheck_b09_repair.py`): 0 disagreements of 120. Fixed-criterion revisions for B1-09: 1.
* Timing: t = 0.0351 s, g = 0.0006 s, S = 5, estimate 85.6 s.
* `CASE.md` of B1-09: mapping and estimand lines, sections 5 and 6, section 7 and a "Repair" paragraph updated.
* The faulty criterion was never run, simulated or pre-checked; Truth_Gate was never run; nothing was read or written outside the class folder; no URL fetched, no `ctx_*` tool called.
