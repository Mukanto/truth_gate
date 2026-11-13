# B-1 phase 1 log

## Sources read
Read in full: PREREG_PHASE_B.md and SOURCES.md. Did not open the public docs (README, GATE, MANIFEST, SPEC).
The four source papers (KRI09, VUL09, MAK19, BAR05) were NOT re-fetched in this session. The error patterns come from the
"content checked" entries in SOURCES.md plus my prior knowledge of the papers. The passage fields in PRIVATE.json
therefore give section or topic locations, not verbatim quotes. A criterion author should verify the quotes
before the case freeze.

## Briefs written (12, none abandoned)
KRI09: B1-01 (voxels x runs, mean difference + t), B1-02 (neurons x orientations x trials, selectivity index),
B1-03 (subjects x halves x timebins, paired t on a chosen window).
VUL09: B1-04 (subjects x voxels, correlation), B1-05 (subjects x sessions x voxels, regression slope),
B1-06 (subjects x voxels with bool group, Welch t).
MAK19: B1-07 (samples x genes, mean absolute log fold change), B1-08 (cells x trials, proportion),
B1-09 (compounds x replicates, one-sample t).
BAR05: B1-10 (patients x visits + bool drug, change versus placebo), B1-11 (patients x 3 visits, proportion),
B1-12 (students x 3 tests, mean gain).

Abandoned: none. Considered and not drafted: a "responders" subgroup analysis (too close to BAR05 cases); a
channels x subjects correlation (duplicates VUL09 cases).

## Notes and deviations
* Voxel, gene and time-bin counts are capped at 60 or fewer features, so they are smaller than in the sources (reported in `sizes`).
* Several claims must name the population ("voxels that respond more...", "patients with high entry pressure"). The claim
  has to say what the effect is about. I did not describe the procedure that finds those items. Judge for yourself whether
  that is too suggestive for the world author (I-4).
* B1-12 and B1-11 share the same correction (a second pre-measure) and differ in statistic, selection direction, n.
* B1-02 uses a derived index with a constructed definition inside the claim, because the claim needs one statistic.
* Statistic: B1-10 and B1-12 contain a prose claim of effect size; the criterion author must read the sign conventions.
* Banned-term script run on the briefs: clean. The word "selected" does not appear in any claim.
* `build.py` in this folder generates both JSON files.

# Revision after coordinator request (source verification)

## Sources read (this pass)
* KRI09: PMC HTML page https://pmc.ncbi.nlm.nih.gov/articles/PMC2841687/ read as stripped text (Europe PMC REST returned HTTP 500). Searched the Introduction, Example 1, Example 2, Fig. 4 text.
* VUL09: PDF (ucsd.edu) converted with pdftotext; read sections 'The Nonindependence Error', survey results, Fig. 4 caption, reliability discussion, discussion of gradations of nonindependence.
* MAK19: Europe PMC fullTextXML (PMC6785265); read section 'Circular analysis' in full.
* BAR05: full text NOT accessible (OUP page blocked by a bot check; PDF links returned HTML). Only the abstract was obtained (Europe PMC search record). Everything in the BAR05 passages beyond the abstract is marked NOT VERIFIED in PRIVATE.json (B1-10, B1-11, B1-12): the blood-pressure, depression-score and test-score settings, the placebo-arm remedy and the second-baseline remedy.
* Earlier statement 'passages are topic locations' is superseded: PRIVATE.json now carries quotes or section locations.

## Revisions
* B1-03 replaced. Old draft: EEG window of the largest target/non-target difference. KRI09 mentions only 'a subset of sensors or sources' for EEG/MEG, not time windows, so the setting was not in the source. New: participants divided into subgroups by task performance (KRI09 Introduction states this exact selection form) with a two-group comparison of improvement. Data: score (participants, blocks), 60 x 4.
* B1-09 replaced. Old draft: compound screen (hit calling); no source describes it. New: neurons binned by baseline activity, MAK19's own worked example in 'Circular analysis'. Data: base (neurons, epochs=2), post (neurons,), 200 neurons.
* Passages for all 12 cases rewritten with quotes or locations.
* Nothing else was changed: the checks of setting and sizes below found no contradiction.

## Size and setting checks
* KRI09 Example 2 simulates 30x30x20 voxels, 200 time points; the source gives no subject counts for 'typical' studies, so 20 subjects, 150 neurons, 60 participants are within a plausible range but not stated by the source. Voxel/neuron counts are my caps.
* VUL09: Fig. 4 simulates 10 subjects and 10,000 voxels; the source gives no typical n for surveyed studies in the text I read, only that correlations well below .5 would often not have been significant 'with these sample sizes'. The earlier claim '8-30 subjects' in my notes is NOT VERIFIED; n=16/24/28 is consistent with the source's remark but not quoted from it. Sessions (B1-05) are my construction (the source only discusses test-retest across sessions).
* B1-06: VUL09 'Study 26' supports group-split plus voxel selection; the Welch t statistic is my variant.
* B1-07, B1-08: MAK19 and KRI09 name genes and neurons as examples of selected features; the specific tumour/normal panel and the tone-responsive cells are my instances.
* Dropped the earlier statement in the first LOG (B1-09 'MAK19 and BAR05 extreme-value logic' for compounds).


## Designer edit, 2026-11-12T21:23:37 (step 1, before shuffling)

Source remarks removed from the `sizes` field of the public briefs (moved to the private notes); claims and data keys untouched.
- B1-01: removed from sizes: (voxel count capped; fMRI regions in the source are larger)
- B1-02: removed from sizes: (single recording session; source discusses typical single-unit samples of this size)
- B1-04: removed from sizes: (VUL09 reports about 8-30 subjects and thousands of voxels; voxel count capped)
- B1-05: removed from sizes: (VUL09: typical n around 16)
- B1-07: removed from sizes: (source studies use thousands of genes; capped)


# Phase 2 (criterion bodies), written by the continuing B-1 author

## What was read
AUTHOR_PHASE2.md, PREREG_PHASE_B.md, this folder (LOG.md, PRIVATE.json, cases/*/ASSIGNMENT.json and skeleton.py), and `grep` lines of docs/GATE.md about the probes (noise = i.i.d. N(0,1), zeros, shuffle). Sources were not re-read; one attempt to fetch the VUL09 PDF failed (404/HTML) and was dropped. Truth_Gate was never run; the faulty criteria were never run, simulated or pre-checked (syntax check only, `ast.parse`, done in `work/make.py` and again per file).

## Method
`work/bodies.py` (criterion bodies and the single differing line per case), `work/helpers.py` (t, F and incomplete-beta helpers written with numpy only, since scipy may not be imported), `work/make.py` (writes faulty.py and fixed.py from the frozen skeleton, replacing only the `raise NotImplementedError` line), `work/check_identity.py` (confirms each file differs from its skeleton only at that line and that faulty and fixed differ only in the error line(s)), `work/test_helpers.py` (helpers against scipy in scratch only: max abs error 2.4e-13), `work/precheck.py` (fixed criterion only; plus/minus/control 200 samples each, noise 100, zeros 10, timing over 30 calls). Results: `work/precheck_round1.txt`.
Faulty and fixed differ only in how the selection data relate to the evaluation data: the faulty uses the same data for both, the fixed uses separate data (runs, trial halves, subject halves, a second baseline, a control arm). B1-10 differs also in the test (paired t vs Welch t) because the correction adds an arm.

## Per case
(rates of the fixed criterion: holds/200; "None" = guard returned undefined)
* B1-01: plus 0.87, minus 0.00, control 0.01, noise 0.03. 0 revisions. Note adapted (per-subject z-map selection, two directions).
* B1-02: first version plus 1.00, minus 0.02, noise 0.37 (index ratio exploding on N(0,1) data). Revision 1: index clipped to [-1, 1]; second version plus 1.00, minus 0.02, control 0.01, noise 0.20. Residual noise rate left as is (see CASE.md).
* B1-03: plus 0.715, minus 0.03, control 0.00, noise 0.00. 0 revisions. Fix changed from note (split on block 1, outcome block 3 - block 0), decided analytically from the skeleton's learning curve before pre-checks.
* B1-04: plus 0.845, minus 0.015 (None 39/200), control 0.00, noise 0.03. 0 revisions.
* B1-05: plus 0.98, minus 0.06 (None 100/200), control 0.11 (None 111/200), noise 0.02. 0 revisions. p < 0.05 instead of the note's p < 0.01. The skeleton's stable subject-by-voxel component carries session-0 selection into session 1; reported, not changed.
* B1-06: plus 0.505, minus 0.01, control 0.01, noise 0.02. 0 revisions. Low plus rate comes from the skeleton's effect size (0.75 at sd 1 with 14 per group). Not changed.
* B1-07: plus 0.905, minus 0.00, control 0.005, noise 0.04. 0 revisions.
* B1-08: plus 1.00, minus 0.105 (None 70/200), control 0.115, noise 0.07 (None 31/100). 0 revisions. The 70% proportion over the guard minimum of 5 responders is a loose statistic; kept the note's guard.
* B1-09: plus 0.905, minus 0.005, control 0.00, noise 0.00. 0 revisions.
* B1-10: plus 0.925, minus 0.03, control 0.045, noise 0.00 (all None). 0 revisions.
* B1-11: plus 0.955, minus 0.03, control 0.08, noise 0.02. 0 revisions.
* B1-12: plus 0.89, minus 0.00, control 0.00, noise 0.00. 0 revisions.
Timing: the largest estimate is B1-02 (about 5.8 s); all are far below 900 s. No skeleton request in any case.

## Concerns recorded for the report
* Fixed criteria that may be flagged by the gate for reasons of the statistic or skeleton rather than the error: B1-02 (holds on noise about 20%), B1-05 (holds on minus/control 6-11%), B1-06 (holds in plus only about 50%), B1-08 (holds on minus/control about 10%), B1-11 control 8%.
* In B1-04, B1-05, B1-06 and B1-08 the faulty criterion returns None whenever its selection is empty, as allowed by the guard; how often that happens in minus was deliberately not examined (faulty not run).
* All p < 0.05 selection levels are conventional values, not quoted from the sources, except where the claim states them.


## Phase 2 repair (fidelity audit, item (a), B1-04 and B1-05)
Request from the coordinator: the auditor answered (a) "no" for B1-04 and B1-05 because the selection used r > 0 and two-sided p < 0.05, while VUL09 Fig. 4 caption (src/vul.txt, lines about 375-376) documents "a positive correlation with p < .01" and the private note says r > 0, p < 0.01. My earlier reason for p < 0.05 in B1-05 (empty selection in noise samples) is not accepted by item (a).
Change: in both twins of both pairs, `_tq(0.025, ...)` became `_tq(0.005, ...)` (r > 0 and two-sided p < 0.01); comments updated. Sidedness is not stated by the source or the note; I kept the original two-sided reading and changed only the level. Nothing else changed. Faulty files: syntax check only (ast.parse), never run. `work/check_identity.py` re-run: all 12 cases still differ from their skeleton only at the criterion line and faulty/fixed differ only in the error line. `work/bodies.py` edited the same way.
Fixed pre-check after the repair (200 samples per world/control, 100 noise; this is revision 1 of both fixed criteria; earlier rates in `work/precheck_round1.txt`, new in `work/precheck_repair.txt`):
* B1-04: plus 0.84 (was 0.845), minus 0.01 (None 128/200; was 0.015, None 39), control 0.00 (None 128), noise 0.00 (None 49/100). Timing est. 3.3 s.
* B1-05: plus 0.925 (was 0.98, None 5/200), minus 0.03 (None 169/200; was 0.06, None 100), control 0.05 (None 170; was 0.11), noise 0.00 (None 75/100). Timing est. 1.9 s.
Consequence recorded, not changed: with p < 0.01 an empty selection (None, allowed guard) is now the usual outcome in minus and noise samples for both faulty and fixed, so detection through the minus/noise streams will be rarer; this follows from the documented threshold.
