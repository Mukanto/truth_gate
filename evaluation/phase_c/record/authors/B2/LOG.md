# LOG, B-2 criterion author, Phase C part 1

Status: COMPLETE (12 briefs written; BRIEFS.json, PRIVATE.json, LOG.md in the sandbox).
Sandbox: E:\Claude Projects\Kapi\phase_c_private\authors\B2\

## Sandbox files read
AUTHOR_PHASE1_C.md, PREREG_PHASE_C.md, PREREG_PHASE_B.md (all), SOURCES.md, SOURCES_ADDENDUM.md, agent_docs/README_TOOL.md.
Not read: pkg/ (not needed in this part), the other agent_docs files. No criterion code written, Truth_Gate not run.

## Sources read and how (every URL tried)
| Source | URL | How | Result |
|---|---|---|---|
| VAR06 | https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ | full text (via the fetch tool's summary) | read: simulated 40 samples (20/class) x 6000 features, shrunken centroids (delta 0.01-1, 10-fold CV), Gaussian-kernel SVM (C, gamma, LOOCV, top-3 t-statistic features), nested CV; null: CV error 37.8% vs true 50.0%; SVM null 41.7%; nested 54.2% (centroid), 35.3% vs 32.0% (SVM, non-null). Bias vs n or p: not analysed. |
| KAP23 | https://arxiv.org/pdf/2207.07048 | binary PDF, unreadable by the fetch tool | not read. NOTE: the fetch tool auto-saved the binary under C:\Users\user\.claude\projects\...\tool-results\ (outside the sandbox). I did NOT open that file. |
| KAP23 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856/ | reCAPTCHA page | not read |
| KAP23 | https://ar5iv.labs.arxiv.org/html/2207.07048 (offset 0, then offset 100000) | HTML full text, through the fetch tool's summary | read: taxonomy Section 2.4 (L1.1-L3.3), civil war case study (Section 4, Appendix B: test sets 896/1778/6363/6610/15744 rows, reported vs corrected AUC), Appendix C. No sizes for L1.4/L3.1/L3.2 examples; no neuroimaging/medicine/genomics examples beyond titles. |
| AMB02 | https://www.pnas.org/doi/10.1073/pnas.102102699 | HTTP 403 | not read |
| AMB02 | https://pmc.ncbi.nlm.nih.gov/articles/PMC124442/ (and the www.ncbi.nlm.nih.gov/pmc/articles/PMC124442/ redirect) | reCAPTCHA | not read |
| AMB02 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1073/pnas.102102699&format=json&resultType=core | Europe PMC record | abstract read (paraphrase by fetch tool) |
| AMB02 | https://europepmc.org/article/PMC/PMC124442 , https://europepmc.org/abstract/MED/11983038 , https://members.cbio.mines-paristech.fr/~jvert/svn/bibli/local/Ambroise2002Selection.pdf , https://data.zhenzhi.com/details/1/899426840 | 403 / certificate error | not read |
| AMB02 | web search "Ambroise McLachlan 2002 Selection bias in gene extraction ..." | search snippets | secondary: 3-gene error about 15% colon, 5% leukemia vs 10.7% and 0% reported before; 10-fold recommended; selection inside each CV stage |
| SIM03 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1093/jnci/95.1.14&format=json&resultType=core | Europe PMC record | no abstract, not open access |
| SIM03 | https://pubmed.ncbi.nlm.nih.gov/12511682/ (wrong PMID, cookie wall), https://academic.oup.com/jnci/article/95/1/14/2520180 (returned a different article), https://paperity.org/p/46568070/... (403), https://www.bohrium.com/paper-details/... (unreadable), web search for the abstract | only a third-party snippet about cross-validation and independent data | SIM03 NOT read (documenting passage not read); no brief rests on it |
| (other) | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:12511682%20AND%20SRC:MED (returned an unrelated Radiology article) | | discarded |
| (other) | https://europepmc.org/api/fulltextRepo?pprId=PPR&type=FILE&fileName=x | HTTP 500 | invalid probe, nothing read |

Also seen: the web-search result lists of two WebSearch calls (URLs only listed in results; not opened except as above).

## Briefs drafted (12; none abandoned)
| id | source | subtype | statistic | structure | size |
|---|---|---|---|---|---|
| B2-01 | KAP23 | L1.1 | AUC | country-years x 30 indicators | 896 x 30 |
| B2-02 | KAP23 | L1.4 (oversampling by copying) | sensitivity | patients x 12 measurements | 400 x 12 |
| B2-03 | KAP23 | L1.4 (oversampling by copying) | balanced accuracy | units x 50 sensor features | 1000 x 50 |
| B2-04 | KAP23 | L3.1 | accuracy | days (ordered) x 10 | 500 x 10 |
| B2-05 | KAP23 | L3.1 | R-squared | weeks (ordered) x 8 | 400 x 8 |
| B2-06 | KAP23 | L3.2 | AUC | patients x patches x 20 | 80 x 10 x 20 |
| B2-07 | KAP23 | L3.2 | Pearson correlation | participants x sessions x 10 | 40 x 4 x 10 |
| B2-08 | VAR06 | L1.3 (tuned shrinkage) | accuracy | samples x genes | 40 x 6000 |
| B2-09 | VAR06 | L1.3 (tuned shrinkage) | AUC | patients x genes | 40 x 4000 |
| B2-10 | VAR06 | L1.3 (tuned kernel parameters) | accuracy | samples x genes | 40 x 6000 |
| B2-11 | VAR06 | L1.3 (tuned number of genes) | balanced accuracy | subjects x genes | 40 x 1000 |
| B2-12 | AMB02 | L1.3 (gene panel chosen on all samples) | accuracy | tissues x genes | 62 x 2000 |

Counts: KAP23 7, VAR06 4, AMB02 1, SIM03 0. Subtypes: L1.1 1, L1.3 5 (4 VAR06 + 1 AMB02), L1.4 2, L3.1 2, L3.2 2. Addendum-source briefs: 4 (VAR06).

## Abandoned briefs
None written and abandoned. Ideas rejected before drafting:
* An L1.4 brief whose duplicates would have to be present in the world data: a brief may not state duplication, so the error would depend on the world author's choice; both L1.4 briefs use oversampling by copying, which the criteria bodies add (PB §1 tie rule).
* A VAR06 brief with a ridge regression and R-squared: the source describes classifiers only; not a setting the source describes.
* An SVM solver with the full (C, gamma) grid under the timing rule: infeasible; B2-10 notes that the part-2 author uses a closed-form kernel classifier with a smaller grid.
* SIM03 briefs: documenting passage not read.

## Checks done (own sandbox, plain Python, scratchpad script)
JSON parses; 12 briefs, 12 private notes with identical ids; no banned term in any brief (any inflection substring check); every array dimension stated as a number in `sizes`; at most 1000 along every row/unit axis (feature axes, such as genes, are not rows; the 6000-gene arrays are 240 000 values, under 500 000); every dtype float or bool; key sets exactly as the instruction file lists.

## Rule difficulties
* SIM03's documenting passage could not be read (paywall, no open abstract reachable), so no brief rests on it. The class still has three independent read sources (KAP23, AMB02 by abstract, VAR06).
* AMB02 was read only as an abstract and snippets; its dataset sizes (62 x 2000) are from memory of the standard colon dataset, marked unverified in the note.
* B2-04 and B2-05 name "later days/weeks" in the claim because the fixed estimand is performance on later periods; B2-06/07 name "new patients/participants" for the same reason. I judged these to be (iii) what the claim states. B2-12 states "uses three genes" as claim content. The designer may judge these differently.
* Claim thresholds were set so the documented faulty procedure plausibly holds in the minus world (VAR06 null accuracy about 0.58-0.62 for tuned parameters); this uses the source's reported null numbers only.

## Designer return (section 4 item 2): size cap on every axis
The designer rejected B2-08, B2-09, B2-10 and B2-12 because PREREG_PHASE_C section 2 caps every axis at 1000 (the 500 000 values cap is an additional per-array cap). My earlier check wrongly exempted feature axes (see "Checks done" above: that sentence was wrong). Changes, only in these four ids, in BRIEFS.json and PRIVATE.json:
| id | old sizes | new sizes | change |
|---|---|---|---|
| B2-08 | samples 40, genes 6000 | samples 40, genes 1000 | claim text "6000" -> "1000"; sizes; sizes_note |
| B2-09 | patients 40, genes 4000 | patients 40, genes 1000 | claim text "4000" -> "1000"; sizes; sizes_note; notes (gene count no longer differs from B2-08, so the two differ only in the statistic) |
| B2-10 | samples 40, genes 6000 | samples 40, genes 1000 | claim text "6000" -> "1000"; sizes; sizes_note (timing re-estimated, about 240 s) |
| B2-12 | tissues 62, genes 2000 | tissues 62, genes 1000 | sizes; sizes_note (colon dataset's 2000 genes reduced to the cap) |
Unchanged: claims otherwise, keys, estimands, sources, subtypes, tags, families, guard minima. Thresholds were kept (0.60, 0.65, 0.60, 0.70). The source (VAR06) reports no dependence of the bias on the number of features (fixed 40 x 6000), AMB02: not stated in the parts read; so the reduction to 1000 is not documented to change the bias, but I could not verify it does not. Timing estimates for the four fell (about 55, 55, 240, negligible seconds).
Re-check after the edit: JSON parses; 12 briefs; every axis of every array at most 1000 and every array at most 500 000 values; no banned term; no remaining "6000/4000/2000" in BRIEFS.json. Counts unchanged: KAP23 7, VAR06 4, AMB02 1; L1.1 1, L1.3 5, L1.4 2, L3.1 2, L3.2 2; 4 on the addendum source.
The designer also answered my three open questions (later days/weeks, new patients/participants, uses three genes: allowed; no SIM03 brief needed); nothing to change for them.

# Part 2 (criterion bodies), Sonnet line author
Started 2026-11-15. Read in the sandbox: AUTHOR_PHASE2_C.md, PREREG_PHASE_C.md, PREREG_PHASE_B.md, SOURCES.md, SOURCES_ADDENDUM.md, BRIEFS.json, PRIVATE.json, LOG.md (part 1), agent_docs/GATE.md (first part), agent_docs/SPEC.md (grep of the probe section), pkg/truth_gate/ (grep for the probes only; Truth_Gate not run), all 12 cases' ASSIGNMENT.json and skeleton.py.
Online: https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ (VAR06) through ctx_fetch_and_index, label b2-part2-var06: returned a reCAPTCHA page, nothing read (no workaround attempted). The VAR06 parameters therefore come from the part-1 note only.
Plan: scratch builder script work\build_cases.py writes the bodies (shared head/helpers, version-specific guard and tail) into faulty.py and fixed.py; faulty gets only the syntax check; fixed gets pre-checks via work\precheck_*.py.

## Part 2: work record
Files written (inside the class folder only): cases/B2-01..B2-12/faulty.py, fixed.py, CASE.md; work/build_cases.py (writes the criterion bodies from text; never imports a criterion), work/precheck.py (imports fixed.py only), work/precheck_final.txt (final pre-check output), work/null_stat_check.py (modified copy of the fixed source for B2-08 and B2-11, returns the statistic), work/structure_check.py (text/AST checks), work/write_case_md.py.
Faulty files: syntax check only (`py -c "import ast,sys; ast.parse(...)" faulty.py`), all 12 ok. Never run, simulated or pre-checked. Truth_Gate never run; pkg/ put first on sys.path only so that the case files import (the fixed files were imported through importlib from precheck.py).
Static check (work/structure_check.py): faulty and fixed equal the frozen skeleton outside the criterion body (prefix and suffix identical), no module-level name of the skeleton other than np is read by any body, the only randomness is rng = np.random.default_rng(<integer>) in both files.

### Pre-checks of the fixed criteria (counts of holds / n; seeds 777000+ then 888000+)
B2-01 n100: plus 88, minus 3, ctrl 0/1, noise 0 | n200: plus 179, minus 7, ctrl 0/3, noise 0.
B2-02 draft 5-NN n100: plus 49, minus 1, noise 10 -> rev1 logistic n100: plus 100, minus 0, ctrl 1, noise 23 -> rev2 (oversample the smaller class) n100: plus 100, minus 0, ctrl 1, noise 0 | n200: plus 199, minus 0, ctrl 0, noise 1.
B2-03 draft 5-NN n60: plus 2, minus 0 (repeat n100 plus 6) -> rev1 logistic n100: plus 100, minus 0, noise 0 -> rev2 n100 same | n200: plus 200, minus 0, noise 0.
B2-04 n100: plus 81, minus 1, ctrl 0, noise 0 | n200: plus 157, minus 0, ctrl 0, noise 0.
B2-05 n100: plus 99, minus 0 | n200: plus 195, minus 0, ctrl 0, noise 0.
B2-06 n100: plus 100, minus 0 | n200: plus 197, minus 0, ctrl 0, noise 0.
B2-07 n100: plus 98, minus 4, ctrl 0 | n200: plus 200, minus 2, ctrl 2, noise 0.
B2-08 n100: plus 100, minus 17, ctrl 28, noise 26 | n200: plus 200, minus 47, ctrl 39, noise 69; statistic on 300 minus samples: mean 0.496, sd 0.114, P(>=0.6) 0.237.
B2-09 n100: plus 100, minus 8, ctrl 11, noise 9 | n200: plus 200, minus 17, ctrl 15, noise 26.
B2-10 n20: plus 18, minus 5, ctrl 4, noise 4 | n40: plus 33, minus 12, ctrl 4, noise 8.
B2-11 n100: plus 100, minus 23, ctrl 28, noise 9 | n200: plus 200, minus 45, ctrl 42, noise 39; statistic on 300 minus samples: mean 0.506, sd 0.106, P(>=0.6) 0.207.
B2-12 n100: plus 100, minus 2, ctrl 1, noise 1 | n200: plus 200, minus 0, ctrl 8, noise 2.
All zeros probes: None on every sample (all-False labels), as intended by the guard.

### Revisions of fixed criteria (each mirrored in the faulty one)
B2-02 rev1: 5-NN -> ridge-penalised logistic regression (plus 0.49, noise 0.10 with 5-NN; a low-capacity-in-noise classifier is needed for the claim's sensitivity threshold). B2-02 rev2: oversampling copies the smaller class, whichever it is (noise 0.23 when the random labels made the positive class the majority and no copying took place). B2-03 rev1: 5-NN -> logistic (plus 0.033 with 5-NN on 50 noisy features). B2-03 rev2: the same oversampling function as B2-02 (parity; no visible change). No other case was revised.

### Fixed criteria that are weak in the skeleton (recorded in CASE.md, not repaired)
B2-08, B2-10, B2-11 hold in minus at about 0.17-0.30 (threshold 0.60 on 40 samples, nested CV variance); B2-09 at 0.08. B2-04 holds in plus at 0.785-0.81.

### Timing (final fixed criteria; estimate 2 x 200 x (S+1) x (t+g), limit 900 s)
B2-01 14 s, B2-02 4, B2-03 24, B2-04 5, B2-05 3, B2-06 6, B2-07 1, B2-08 91, B2-09 101, B2-10 563 (t 0.234 s, 40 calls), B2-11 56, B2-12 9. No size request.

### Deviations from the part-1 notes (details in CASE.md)
B2-02/03: logistic regression instead of 1-NN/5-NN; B2-10: kernel ridge for the SVM, 5x5 grid, outer 10-fold (as the note anticipated); gene counts as in the skeleton (1000). Guards are stated per structure (smallest size at which each fit is defined). No skeleton request.

## Repair round (after the blind fidelity audit, item (c): B2-01, B2-06, B2-10)
All three requests accepted (the auditor's arithmetic is right: `-(n) // k` is `(-n) // k`, so my guard_cv helper computed n + ceil(n/k)). Changes, bodies only:
* B2-01 fixed.py guard -> n - ceil(n/5) >= 2 per class; faulty guard unchanged (no folds).
* B2-06 fixed.py and faulty.py guard -> the same patient-level n - ceil(n/5) >= 2 per class in both.
* B2-10 fixed.py guard -> n - ceil(n/10) >= 3 per class; faulty guard unchanged (min >= 3).
Helper `guard_cv_ok` added to work/build_cases.py; only B2-01, B2-06, B2-10 were rebuilt (the other nine files were not touched). Faulty files: syntax check only, ok; structure_check ok.
Pre-checks of the fixed criteria (work/precheck_repair.txt, seed 999000): B2-01 n200: plus 179, minus 8, ctrl 0/4, noise 0, zeros None 200. B2-06 n200: plus 198, minus 0, ctrl 0, noise 0, zeros None 200. B2-10 n40: plus 32, minus 7, ctrl 7, noise 7, zeros None 40. Timing estimates 14 s, 6 s, 567 s. Revisions of the fixed criteria: B2-01 1, B2-06 1, B2-10 1 (all guard-only; B2-02 and B2-03 keep their 2 earlier revisions).
Not changed, as instructed: the same helper (guard_cv, with the same precedence slip) wrote the fixed guards of B2-02, B2-03, B2-08, B2-09, B2-11 and B2-12 (depth 1 or 2). There the fixed guard tests n + ceil(n/k) (or the nested form) instead of n - ceil(n/k), so it returns None only for an empty class, not below the stated minimum. It never fires on the worlds, controls or probes pre-checked (zeros probe returns None through the empty class). Left for the coordinator's decision.
The faulty criteria were never run, simulated or pre-checked; Truth_Gate was never run.
