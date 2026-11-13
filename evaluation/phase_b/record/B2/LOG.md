# B-2 phase 1 log

## Sources read
- PREREG_PHASE_B.md and SOURCES.md: full.
- KAP23: arXiv 2207.07048, read through the ar5iv HTML version by targeted section search (Sec 2.4 taxonomy L1.1-L3.3, Table 1 header, Appendix B.4/B.5 on civil-war imputation and temporal cross-validation, Appendix C). Not read line by line; the cited cases (Oner 2020, Blagus and Lusa 2015, Kaufman 2019, Wang 2019) are known only as KAP23 describes them.
- AMB02: full text read (PMC124442) after the coordinator request: Backward Elimination with SVM, Forward Selection with Fisher's Rule, Cross-Validation, Correction for Bias Selection, Discussion.
- SIM03: now read via SIM03_openalex_abstract.txt (designer OpenAlex reconstruction, about 3,500 words). Earlier: the JNCI paper could NOT be opened (OUP 403; PubMed needs cookies; Europe PMC, Crossref and Semantic Scholar return no abstract; the BRB PDF fetched as raw binary and is related material, not cited). b2-01 and b2-02 passages are marked NOT VERIFIED; their classifier and sizes are author choices.
- Public docs (README, GATE, MANIFEST, SPEC) not read; nothing under truth_gate, kapi, tests, examples, evaluation (other than the two phase_b files) was read.

## Briefs written (12, all kept)
b2-01 SIM03 L1.1; b2-02 SIM03 L1.1; b2-03 AMB02 L1.3; b2-04 AMB02 L1.3; b2-05 KAP23 L1.2 (label-dependent imputation); b2-06 KAP23 L1.2 (synthetic oversampling); b2-07 KAP23 L1.4 (repeated rows in data); b2-08 KAP23 L1.4 (oversampling by copying); b2-09 KAP23 L3.1 (binary AUC); b2-10 KAP23 L3.1 (ridge R^2 weekly series); b2-11 KAP23 L3.2 (patients with patches); b2-12 KAP23 L3.2 (hospitals, ridge R^2).
Per source: KAP23 8, AMB02 2, SIM03 2. Banned-term and procedure-word check run with a script (also on split, select, held-out, cross-val): clean.

## Abandoned drafts
- L1.3 case from KAP23 neuroimaging (Whelan and Garavan): dropped, KAP23 already at its cap of 8 and AMB02 documents L1.3 directly.
- Target encoding of a high-cardinality categorical (L1.2): dropped, needs integer codes in a value array, forbidden by the encoding rules.
- Feature scaling/PCA on all data: out of scope (O-1), not B-2.
- A third SIM03 case (selection before leave-one-out): dropped as a near copy of b2-03/04.

## Notes and rule tensions (reported, not bent)
- b2-07 must say that some rows are repeated entries; otherwise the world cannot contain them. This describes the data, not the procedure, but it hints at the error type.
- Temporal and shared-unit briefs (b2-09..12) say "future" or "new hospitals/patients" because the claim itself is about them; no split is described.
- b2-05 uses a bool mask for missing values instead of NaN so the allowed finite-value guard does not fire.
- Feature caps: AMB02 and SIM03 data have thousands of genes; capped at 60, stated in private notes.
- The L1.1 regime relies on n<p resubstitution being optimistic for the chosen threshold; I did not simulate (phase 1, no code).

## Revision after coordinator request (AMB02/SIM03 parameters, quotes)
- b2-03 changed: faulty now Fisher LDA (ridge in numpy) with forward selection by leave-one-out error on all 62 tissues, 3 genes, internal leave-one-out error reported; fixed = external 10-fold. Reason: these are the source's reported procedure and numbers; earlier nearest-centroid/top-5/10-fold-internal were my choices. Brief text unchanged; sizes now 62 tissues, 40/22, as in the source.
- b2-04 changed: faulty now RFE-style backward elimination to 8 genes (source's eight-gene example) with a ridge linear classifier standing in for the SVM, leave-one-out scores; fixed = external 10-fold with RFE inside folds. Sizes in brief changed from 40 patients to 72 (47/25), as the source's leukaemia data. Reason: source values instead of mine.
- Adaptations that remain author choices (stated in PRIVATE.json): pre-filter 20 of 60 genes (source 400 of 2000), ridge for LDA/SVM, 60-gene cap.
- b2-01, b2-02 (SIM03): passages marked NOT VERIFIED; no source-reported parameters exist to adopt.
- KAP23 passages for every subtype used are now verbatim quotes from the full text (L1.2, L1.4, L3.1, L3.2). The L1.3 subtype is documented through AMB02, not KAP23.
- Banned-term/procedure-word check rerun on the revised briefs: clean.

## Revision 2: SIM03 verified against the OpenAlex reconstruction
- b2-01: passage now a quote (resubstitution: 98.2% of null datasets with zero misclassifications). Sizes in the brief changed from 40 samples to 20 samples (10 per class), as in SIM03 simulation (20 profiles, 6000 genes; genes still capped at 60). Faulty = resubstitution error of a predictor built on all 20; fixed = leave-one-out with gene selection, weights and rule redone inside (source: median 11 of 20 misclassified under no difference). Not reported in the text: classifier and gene-selection threshold; mine: nearest centroid, top 5 genes by t, threshold 0.80.
- b2-02: passage now a quote (definition of resubstitution; need for unbiased error). Brief unchanged. Faulty = resubstitution AUC; fixed = 5-fold refit. Source reports only the setting (small n, prognostic 5-year outcome, studies under 50 specimens); logistic model, n=30, 20 markers, 5 folds, AUC remain my choices.
- Not used: SIM03 van t Veer example (27% partial vs 41% full leave-one-out error, 44 disease-free patients) is gene selection outside the loop, i.e. L1.3, and SIM03 would then supply a third source for L1.3; not added to keep to the 12 planned.
- Defect found and fixed in my own briefs: the sizes field of several briefs named the source (for example the data set of a source). Sizes in BRIEFS.json are now source-free; the source remarks moved to the private notes. A script now checks the briefs for source names: clean. Banned-term check: clean.

# Phase 2 (criterion bodies), written by the successor criterion author

Read in this phase: AUTHOR_PHASE2.md, PREREG_PHASE_B.md, SOURCES.md, docs\GATE.md (grep for probes, budget, relational), docs\SPEC.md lines on probes (grep: noise = floats N(0,1), booleans Bernoulli(0.5), zeros = zeros/False), docs\MANIFEST.md (grep only), this class folder (PRIVATE.json, LOG.md, quotes.tsv, new34.txt, SIM03_openalex_abstract.txt via grep, the 12 cases). Nothing else.
Tools in `work\`: make_cases.py (builds faulty.py and fixed.py from skeleton.py: replaces only the line `    raise NotImplementedError`), precheck_fixed.py (fixed only), explore_param.py (fixed copies only, one constant varied), write_case_md.py. Faulty files: never imported or run; only ast.parse and a static symtable name check (no execution). Truth_Gate never run.
Checks after building: outside the criterion body faulty = fixed = skeleton in all 12 cases; no module-level name except `np` is used in any body; no `np.random.<fn>` call; one `default_rng(<int>)` per criterion that needs randomness, same seed in both twins.
Common choices (all cases): stratified random folds from a seeded generator; ridge logistic/ridge regression penalty 1.0 (library-default size) except b2-04; thresholds from the briefs; guards only for non-finite values, class counts too small for the folds, zero variance.

Per case (plus/minus = proportion of True in 200 samples of the fixed criterion, rng seed 2; full output in work\precheck_final.txt):
- b2-01 L1.1: plus 0.895, minus 0.055; noise 0.05 (n=1000 check: 0.046); revisions 0.
- b2-02 L1.1: plus 0.90, minus 0.035; noise 0.03; penalty sweep 1/5/20 -> plus 0.87/0.915/0.90, kept 1.0; revisions 0.
- b2-03 L1.3: plus 0.39, minus 0.00; low plus rate recorded in CASE.md, not changed (3 genes is the documented parameter); revisions 0.
- b2-04 L1.3: first version (penalty 1.0) plus 0.34 (100 samples, seed 1) and 0.22 (200, seed 77); sweep 1/10/30/65/150 -> plus 0.22/0.415/0.53/0.59/0.66, minus <=0.005; REVISION 1: penalty 70.0 (p close to n argument), final plus 0.675, minus 0.005. Faulty mirrored.
- b2-05 L1.2: plus 0.68, minus 0.00; revisions 0.
- b2-06 L1.2: first pre-check crashed on the noise probe (more positives than negatives -> negative number of synthetic rows). REVISION 1 (both files): number of synthetic rows = max(n_neg - n_pos, 0). Final plus 1.00, minus 0.00.
- b2-07 L1.4: plus 0.94, minus 0.00; revisions 0.
- b2-08 L1.4: REVISION 1 (both files): the same max(n_neg - n_pos, 0) fix applied preemptively after the b2-06 crash (same code pattern; its own noise probe had not been run yet). Final plus 0.95, minus 0.00; noise 0.11 (n=100) but 0.049 on 1000 probes.
- b2-09 L3.1: plus 0.425, None 0.075 (a class missing in the chronological train or test part), minus 0.03; revisions 0.
- b2-10 L3.1: plus 0.43, minus 0.00; penalty sweep 1/10/100 -> 0.415/0.445/0.445, kept 1.0; revisions 0.
- b2-11 L3.2: plus 0.62, minus 0.005; revisions 0.
- b2-12 L3.2: plus 0.595, minus 0.00; penalty sweep 1/20/100 -> 0.565/0.57/0.45, kept 1.0; revisions 0.
Correctness check of the batched leave-one-out (b2-03): equals naive leave-one-out on two random feature sets (23 = 23, 22 = 22).
Timing (fixed, 30 calls): all estimates between 1 and 63 seconds (limit 900); the slowest are b2-03 (63 s) and b2-04 (53 s).
Skeleton requests: none. Problems: none beyond the low plus rates of the fixed criteria in b2-03, b2-04, b2-09, b2-10 (0.39 to 0.675), recorded in the CASE.md files and not bent.
