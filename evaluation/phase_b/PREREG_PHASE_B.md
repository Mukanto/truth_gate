# Phase B: external evidence — pre-registration

Status: **v3, 2026-11-12, FROZEN (`FREEZE_PREREG.json`).** Designer: Claude, under the author's delegation. v2 answered blind
review 1 and v3 the targeted review 2 (`REVIEW1.md`, `REVIEW2.md`); the changes and reasons are in `REVISIONS.md`. Frozen spec: `docs/design/spec-0.6.md` (§14, Phase B
principles); post-freeze decisions `docs/design/spec-0.6-REVISIONS-post-freeze.md` R-35 (adds B-6) and R-36 (declares the
deviations from §14). After review and a SHA-256 freeze, nothing below changes. No case exists when this text is written.

## 0. Question and headline

Does Truth_Gate 0.4.0, **together with worlds and controls declared by someone who does not know the error**, flag
acceptance criteria that contain errors documented in the published literature, and does it pass the corrected
criteria, when the analysis is written inside the criterion?

The classes were chosen because the gate's mechanism should reach them; that choice is the claimed scope, not evidence
of breadth. Out-of-scope classes stay in the set to check the claimed scope. Every detection is labelled by what found
it (§6): the gate's own noise probe, or the declared streams.

## 1. Classes and decision rules

**In scope (each with a threshold):**

| Class | Decision rule (applied by the designer to each brief, before the audit) | Independent sources (`SOURCES.md`) |
|---|---|---|
| B-1 circular analysis | items (voxels, cells, features, subjects, trials) are selected or grouped using the data, and an effect statistic of the selected items is then tested or reported on the same data, including "improvement" of units selected for extreme values of the same noisy measurement; the statistic is **not** a prediction score | KRI09, VUL09, MAK19, BAR05 |
| B-2 procedure-level leakage | the statistic is a prediction score claimed to estimate performance on new data (from a held-out set, from cross-validation, or, for L1.1, from the training data itself), and the evaluation lets test information into training. Subtypes (KAP23): L1.1 no test set; L1.2 pre-processing that uses the outcome labels (target encoding, label-dependent imputation, oversampling of classes) before the split; L1.3 feature selection on all data; L1.4 duplicates across the split; L3.1 temporal leakage; L3.2 train and test share units (subjects, patients, sites) | KAP23, AMB02, SIM03 |
| B-3 coupling by construction | the statistic is coupled to its target by construction or by shared measurement error: ratios with a shared denominator (in a correlation or a regression), variables that share measured components, a change score against its own baseline, a target computed from the labels it is compared with | PEA97, ARC81, KRO93 |
| B-6 inflated-size decision rules | an inferential rule whose false-positive rate exceeds its nominal level in a world without the effect that keeps the study's dependence structure: a difference claimed from "significant here, not there"; non-independent units counted as independent | NIE11 (with GEL06 as supporting material), HUR84, LAZ10, MAK19 |

When a brief meets two rules (for example feature selection followed by a cross-validated score), the more specific
one wins in this order: B-2, B-6, B-1, B-3. B-2 subtype ties: oversampling by copying rows is L1.4, by synthesising
rows L1.2; feature selection before cross-validation is L1.3. The designer assigns class and subtype before the audit;
they never change after the run.

**Not built:** B-4 (inert or mirror-blind tests) and B-5 (unit or scale errors in thresholds). No documented instance in
published research outside this project was found (`SOURCES.md`). The report carries one line for each: "no
documented cases; no evidence either way".

**Out of scope (no threshold; misses expected):**

| Class | Error | Sources |
|---|---|---|
| O-1 data-level leakage | KAP23 L2 (illegitimate features), L1.2 pre-processing that does not use the labels (scaling, unsupervised imputation, PCA on all data), L3.3 (biased test sample) | KAP23 |
| O-2 flexibility outside the criterion | which analysis is reported is chosen after seeing several | SIM11 |
| O-3 errors in the real data or the model | row or label offsets in the real data; spreadsheet and exclusion errors; an error model inconsistent with its estimator | BAG09, HER14, GHZ26 |

## 2. What a case is

* A **pair** of Python study files, `faulty.py` and `fixed.py`, in `evaluation/phase_b/cases/<case-id>/`, with a
  `CASE.md` (§3). Each file is a single 0.3-style study: `from kapi import Study, Criterion, World, Premise, Control`
  and `numpy`; no other import, no file access, no helper modules.
* **The twins are byte-identical except inside the body of the criterion function(s).** Everything else is the
  committed skeleton (§4).
* **The analysis is inside the criterion:** selection, fitting, cross-validation or testing happen in the criterion
  function, on the data it receives.
* `plus`: realistic data in which the claim is true, in the setting of the brief. `minus`: the same data structure
  (n, features, grouping, time order, dependence) in which the claim is false. Optional `null`. At least one control
  that breaks the theory of the claim. The same in both twins.
* **Encoding rules:** group, subject, trial and time structure is carried by array axes (for example shape
  `(subjects, trials)` or rows in time order), never by integer codes stored in a value array; binary labels are `bool`
  arrays; claims are positive (the criterion holds when the effect is present and the evidence supports it).
* The world author may declare `relational` pairs (for example features and labels) and a `null` world.
* `Budget()` and `Targets()` keep their defaults (200 samples, power 0.8, declared size 0.05). `deterministic = True`
  only if the analysis is deterministic.
* **Allowed guards** in criteria: checks that values are finite, that a selection is non-empty or large enough, that a
  variance is positive; such a guard returns `None` (UNDEFINED). Nothing else may inspect the input's distribution;
  in particular no test of whether data look like noise or zeros.
* **Timing:** before the freeze, the criterion author measures in plain Python the mean time `t` of one call of the
  **fixed** criterion on a `plus` sample, and `g` of one world generation. Each stream evaluates the criterion once per
  sample, the identical-minus analysis adds about one stream, and the gate evaluates everything twice; so the estimate is
  `2 × 200 × (S + 1) × (t + g)`, with S = the number of worlds, controls, premises and relational pairs declared, plus 2
  for the probes. It must be at most 15 minutes. The faulty criterion must have the same computational structure apart
  from the error (audit item (g)). After the
  freeze, a check that runs beyond 60 minutes counts as a miss (faulty) or a failed clean pass (fixed). Run times are
  reported.
* Data stay small: at most 300 rows (or units) and at most 60 features per sample.

## 3. `CASE.md`

* The source key(s) and the passage that documents the error (quoted in at most two sentences, or located by section).
* The neutral brief exactly as given to the world author (§4).
* One paragraph mapping the faulty criterion to the documented error and the fixed criterion to the correction.
* The class (and B-2 subtype) assigned by the designer.
* The criterion author's plain-Python pre-checks of the fixed criterion and the timing estimate.

## 4. Roles and order of work

1. **Criterion authors** (one fresh agent per class: B-1, B-2, B-3, B-6, and one for O-1 to O-3) read this document,
   `SOURCES.md` and the sources. For each planned case they write (a) a **neutral brief**: the claim, including its
   statistic and decision threshold, in words that do not say how the error enters (for example "within the brain
   region whose activity relates to the trait, activity correlates with the trait at r ≥ 0.5 across 16 subjects"),
   the data keys with shapes and meanings, and sample sizes within the range the source describes; and (b) a private
   error note. A brief may not contain these terms or their inflections: circular, double dip, leak, pseudorepl, coupl,
   spurious, non-independ, nonindepend, regression to the mean, selection bias, overfit, inflat, contaminat, optimis
   (checked by the designer's script). A brief does **not** say what "claim false" means; the world author applies the
   fixed rule below. Authors log every brief they write, including abandoned ones, with the reason.
2. The designer assigns each brief's class (§1 rules), gives every brief a random id, and shuffles them.
3. **The world author** (one fresh agent for all classes) receives only the shuffled briefs, the encoding rules and the
   public documentation. It does not know the classes, the errors or the sources. For each brief it writes the
   **skeleton**: worlds, controls, premises, budget, targets, and a stub `def criterion(d): raise NotImplementedError`
   whose docstring lists the data keys. **Fixed rule for `minus`:** the quantity the claim is about is set to its null
   (no relationship, no difference, no predictive information), and every other quantity keeps its `plus` value. For a
   claim that one effect exceeds another, the null is that the two effects are equal, each other quantity unchanged. The
   world author may run its own code in plain Python and simulate the documented probes.
4. The designer checks the skeletons mechanically and freezes them (`FREEZE_SKELETONS.json`).
5. The criterion authors write, for each of their skeletons, the faulty and the fixed criterion bodies. They may not
   change anything else. The faulty criterion uses the parameters the source documents (or the typical values it
   states). They may pre-check the **fixed** criterion in plain Python (for example, that it usually holds in `plus` and
   fails in `minus`), and they log each pre-check and the number of revisions of each fixed criterion. They may not run,
   simulate or pre-check the faulty criterion in any form, on the worlds or elsewhere. A request to change
   a skeleton goes through the designer, is logged, and is granted only for a defect that makes the fixed criterion
   impossible to write (for example a missing key); the changed skeleton is re-frozen.
6. Nobody runs Truth_Gate (any version) on a case before the case freeze. Authors do not read `truth_gate/`, `kapi/`,
   `tests/`, `examples/` or `evaluation/` outside `evaluation/phase_b/`.
7. The authors are models of the same family that wrote the gate and have read its documentation; this is stated in the
   report. No human domain reader was available for this phase.

**Size.** At least 10 pairs per in-scope class from at least 3 independent sources; at most 4 pairs per source per class,
except KAP23, which may supply up to 8 B-2 pairs. B-2 subtype minima: L1.1 ≥ 1, L1.3 ≥ 1, L1.4 ≥ 2, L3.1 ≥ 2, L3.2 ≥ 2.
Within a class every pair differs from every other in at least one of: the statistic, the data structure, the pipeline
step where the error occurs, the sample-size regime. At least 2 pairs per out-of-scope class.

## 5. Fidelity audit and case freeze (before any gate run)

1. **Mechanical check (designer's script):** the twins equal the frozen skeleton outside the criterion bodies; only
   `kapi` and `numpy` imported; no file, network or process access in the text; default `Budget` and `Targets`; any
   comparison of an input's mean, variance or distribution with a constant is listed for the auditor.
2. **Blind fidelity audit** (one fresh agent per class, not an author; it does not run the gate). Yes/no per pair:
   (a) the faulty criterion contains the error documented in the cited passage; (b) the fixed criterion applies the
   documented or a standard correction and nothing else; (c) the only difference between the twins is that error and
   its correction; (d) no gate-aware code beyond the allowed guards; (e) the brief passed the term check and states no
   negation of the claim; (f) the sizes in the brief are within the range the source describes; (g) the faulty and fixed
   criteria have the same computational structure apart from the error.
3. A "no" goes back to the criterion author once (criterion bodies only). A pair with a "no" after the repair, or one
   disputed between auditor and author, is dropped. Every repair and drop is reported with its reason. A class that ends
   with fewer than 10 pairs or fewer than 3 independent sources, or that misses a B-2 subtype minimum, is reported as
   "insufficient cases" and is not tested against its threshold.
4. **Freeze:** `py protocol/tools/freeze.py write evaluation/phase_b/cases -o evaluation/phase_b/FREEZE_CASES.json`,
   together with `EXPECTED_FLAGS.json`: for each case, the expected-flag list of its class with the `HIGH_RATE` streams
   enumerated from the case's own control ids and relational pairs.

## 6. Run, metrics, thresholds and reporting

* **Run:** Truth_Gate at tag `v0.4.0`, full mode, every file. Baselines on the same files: Truth_Gate 0.3.0 (tag
  `v0.3.0`; expected identical, a sanity check), "flag everything" (every faulty detected, no fixed passing),
  **noise-only** (detection counted only from `K5_HOLDS_ON_NOISE` and `HIGH_RATE:probe:noise`), and **declared-only**
  (detection counted only from the other expected flags).
* **Expected flags.** The four in-scope lists have the same content, because each error makes a criterion hold where
  the claimed effect is absent. For B-1, for B-2, for B-3 and for B-6: `K2_HIGH_SIZE`, `K2_FAILS_UNREACHABLE`,
  `K2_NO_SEPARATION`, `K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_NULL`, `K5_HOLDS_ON_SHUFFLE`,
  `HIGH_RATE:probe:noise`, `HIGH_RATE:world:null`, and, enumerated per case at the freeze, `HIGH_RATE:control:<id>` for
  each declared control and `HIGH_RATE:probe:shuffle:<a>,<b>` for each declared relational pair. Nothing else counts (in
  particular not `K1_UNDEFINED`, `K2_HOLDS_UNREACHABLE`, `K2_LOW_POWER`, `K3_*`, `K5_HOLDS_ON_DEGENERATE`,
  `HIGH_RATE:probe:zeros`, `HIGH_RATE:premise:*`, `K6_*`, `K7_*`, `K8_*`).
* **Detection** of a pair: the faulty file's study verdict is NOT_FALSIFIABLE **and** at least one component carries an
  expected flag. UNDEFINED, UNTESTED, WEAK, FALSIFIABLE, a load error or a run beyond 60 minutes is a miss. Each
  detection is labelled **generic** if `K5_HOLDS_ON_NOISE` or `HIGH_RATE:probe:noise` is among its flags, otherwise
  **declared**. A detection whose only expected flags are `K2_NO_SEPARATION` or `K2_FAILS_UNREACHABLE` is also labelled
  **K2-only** and reported separately, because a weak skeleton world can raise those flags for reasons unrelated to the
  error.
* **Clean pass** of a pair: the fixed file's verdict is FALSIFIABLE or WEAK. Anything else is a failure, reported with
  its flags.
* **Thresholds, per in-scope class:** every non-dropped pair counts (at least 10). The one-sided 95% Wilson lower bound
  of the detection rate is at least 0.6 **and** the one-sided 95% Wilson lower bound of the clean-pass rate is at least
  0.6. With 10 pairs this means at least 9 of 10 on both; a class whose true rates are near 0.85 would pass only about
  half the time. The intervals are the result; the HOLDS/FAILS verdict is a summary of them.
* **Report:** per class (and per B-2 subtype): pairs, detections (generic and declared), clean passes, Wilson bounds,
  verdict; the same for each baseline; every pair's verdicts and flags; every logged brief, drop, repair and skeleton
  change; run times; an explanation of every miss and every failed clean pass, written after the run and labelled as
  interpretation.

## 7. After the run

* The designer recomputes every number from the certificates with a separate script.
* A blind audit by a fresh agent (not an author or fidelity auditor) reads the frozen cases, the certificates and the
  report and answers per pair: (i) does each detection follow from the planted error (would the fixed criterion on the
  same worlds avoid that flag)? (ii) does a failed clean pass come from the skeleton rather than the fixed criterion?
  (iii) is there a sign that a brief steered the worlds?
* The thresholds and the expected flags never change after the run. A case found wrong after the run stays in the
  pre-registered table with the error reported next to it; a corrected table may be added, labelled post hoc.

## 8. Interpretations fixed now

* **I-1.** A detection says the gate (with the declared worlds) flagged the criterion for one of the expected reasons,
  not that it understood the error.
* **I-2.** A miss in an in-scope class is a limit of the gate or of the declared worlds; the report says which, as an
  interpretation, using the generic/declared split.
* **I-3.** A detection in an out-of-scope class is examined: it may come from a second, in-scope error in the case.
* **I-4.** Declared detections show what the gate does when the user declares a sensible `minus` world and control
  without knowing the error; they do not show that the gate would find the error without such declarations. The world
  author, a model of the same family, may often infer the error class from the form of the claim; the separation of roles
  reduces, but does not remove, this contamination.
* **I-5.** The structured B-2 subtypes (L1.4, L3.1, L3.2) rest mostly on one source (KAP23). MAK19 counts as a source in
  both B-1 and B-6; it is a review and cites KRI09 and NIE11.
