# Instructions for brief authors, Phase D

You are a **brief author** in a pre-registered evaluation of Truth_Gate. Truth_Gate is a tool that checks whether the
acceptance criteria of computational studies can fail. Each case is built from an analysis error documented in the
published literature. Your task names:
- your class (B-2, B-3, or decoys);
- your half;
- the number of cases and reserves you write;
- the subtypes or mechanism tags you must cover;
- the sources you may use.

You write briefs and private notes only. Other agents write the criteria and the worlds later.

`TASK.json` also lists the (mechanism_tag, statistic_family) combinations that two earlier evaluations used for your
sources. Prefer another statistic family where the source allows, and say in the private note when you could not.

## Which class a setting belongs to

PB §1's decision rules, verbatim:

| Class | Decision rule |
|---|---|
| B-1 circular analysis | items (voxels, cells, features, subjects, trials) are selected or grouped using the data, and an effect statistic of the selected items is then tested or reported on the same data, including "improvement" of units selected for extreme values of the same noisy measurement; the statistic is **not** a prediction score |
| B-2 procedure-level leakage | the statistic is a prediction score claimed to estimate performance on new data (from a held-out set, from cross-validation, or, for L1.1, from the training data itself), and the evaluation lets test information into training |
| B-3 coupling by construction | the statistic is coupled to its target by construction or by shared measurement error: ratios with a shared denominator (in a correlation or a regression), variables that share measured components, a change score against its own baseline, a target computed from the labels it is compared with |
| B-6 inflated-size decision rules | an inferential rule whose false-positive rate exceeds its nominal level in a world without the effect that keeps the study's dependence structure: a difference claimed from "significant here, not there"; non-independent units counted as independent |

When a brief meets two rules (for example feature selection followed by a cross-validated score), the more specific
one wins, in this order: B-2, B-6, B-1, B-3.

## What you may read

Your **sandbox folder** holds copies of the only files you may read:
- this file;
- `SOURCES.md` (keys and references);
- `SOURCES_D.md` (the documenting passages of the sources allotted to you);
- your task file `TASK.json`;
- `agent_docs/`, the tool's documentation (it describes the tool only).

You may read the sources themselves online. Most have open full texts or abstracts on PubMed Central, Europe PMC or
arXiv.

## What you must not do

- Do not read anything outside your sandbox folder on this machine.
- Do not fetch anything from the project's code repository, or from any published material of its evaluations.
- Log every URL you read.
- Do not start any other agent or any tool that runs a model.
- Do not use any context-mode tool (`ctx_*`), and no scratch folder outside your sandbox.
- Do not write or run any analysis code. The one exception is your structure statistic, which you may run on arrays
  you generate yourself with the brief's shapes, to check that it returns a finite float. Log those runs.

## What you write, per case

Base each case on a setting the source actually describes. Within your class, every case differs from every other in at
least one of:
- the statistic;
- the data structure;
- the pipeline step where the error occurs;
- the sample-size regime.

The other half of your class writes its own cases from other sources. The designer checks the difference rule across
both halves.

### 1. A neutral brief

It is public: it goes to a world author who is not told the error, the class or the source.

- **`claim`.** The scientific claim with its statistic and decision threshold, as a researcher would state it. The claim
  is about the quantity that the corrected (fixed) analysis estimates. Do not say how the error enters, and do not say
  what "claim false" means. The claim is positive: the criterion holds when the effect is present.
- **`data_keys`.** Every array of the data dict: key, shape with named axes, dtype (`float` or `bool`), meaning.
  - Group, subject, trial and time structure goes in array axes, never in integer codes.
  - Binary labels are `bool`.
- **`sizes`.** Within the range the source describes, with at most 2000 units along any axis and at most 2 000 000
  values in any array.
  - Use the source's sizes where they fit. Otherwise use the largest that keeps a check of the corrected analysis within
    about 30 minutes (a rough estimate; the exact check comes later), and say so in the private note.
  - State every array dimension as a number.
- **Banned terms**, in any inflection, case-insensitive: circular, double dip, leak, pseudorepl, coupl, spurious,
  non-independ, nonindepend, regression to the mean, selection bias, overfit, inflat, contaminat, optimis. Also avoid
  words that describe the faulty procedure itself (how items are chosen, how data are split).
- **What a brief may state** (verbatim):
  > A brief may state (i) the sizes, (ii) the axes named in the shape of each key and what each key measured, and (iii)
  > what the claim itself states. It may not state any other fact about how rows, units, splits, repetitions or
  > variables are related, ordered, duplicated, shared or selected. An axis named in a shape (subjects, trials, time in
  > order) is setting; a statement about how the data on that axis are arranged beyond its name is not. Naming a
  > quantity in the claim is allowed only where the claim's estimand requires it (the estimand line of the private note
  > says which). No data key names a variable by its role in the error.

**The estimand** (PC §2, verbatim): The claim of the brief is about the quantity that the **fixed** criterion
estimates; the faulty criterion estimates it in the documented wrong way. (For coupling by construction, for example,
the claim is about the relation between two quantities after accounting for a third, the data keys carry the measured
components, the faulty criterion accounts for the third by dividing by it and correlating the ratios, the fixed one by
a partial correlation or a regression with the third as a covariate.) The private note names the estimand of the
faulty and of the fixed statistic. A brief for which this cannot be done is not written.

**Naming the estimand in B-3** (PC, verbatim). The claim names only what the estimand requires; the other mechanisms
follow the same pattern:
- `ratio-shared-denominator` and `ratio-vs-denominator-proxy`: as in the example (the relation after accounting for the
  quantity the source's correction adjusts for);
- `change-vs-baseline`: the relation between the level of a quantity and its change, with keys for the measurement at
  each time;
- `shared-measured-component`: the relation between the two derived quantities as the source's correction estimates
  it, with keys for the measured terms (and for the independent measurement where the documented correction uses one);
- `target-from-labels`: the relation between the predictor and an outcome defined without it, with keys for the
  measured items.

A mechanism for which no brief meets "what a brief may state" is not used.

### 2. A private note

It is never shown to the world author. It holds:

- the source key, and the documenting passage (a quote of at most two sentences, or its location);
- **the error** as it will appear in the faulty criterion, with the parameters the source documents;
- **the correction** in the fixed criterion;
- **the estimand** of the faulty statistic and of the fixed statistic;
- the **model family** both twins use: the source's, where it names one; otherwise your choice and the reason. It will
  not change later;
- `mechanism_tag` and `statistic_family`, from the closed lists below; for B-2, the subtype;
- the **minimum selection size** that an allowed guard will use. It is no more than the smallest size at which the
  statistic is defined. The allowed guards, which return `None`, are an exhaustive list: non-finite values; an empty
  selection or one below that minimum; a zero variance;
- a **sizes note**: the source's sizes; or the largest size within the timing estimate; or, when the source states none,
  why a smaller size is realistic. Add what the source reports about how the error's size depends on the sample size or
  the number of features, or "not stated";
- **the exploited structure**, in one sentence: what in real data the error relies on (for example time order, repeated
  records of one unit, many features, a measurement shared between two quantities);
- **the structure statistic**:

  ```json
  {"code": "def stat(d):\n    ...\n    return float(value)",
   "direction": "greater" | "less", "null_value": <number>,
   "note_value": <number>, "note_value_source": "<quote with location, or 'source states none: <reason for the proposed value>'>",
   "set_by_brief": false}
  ```

  - `stat(d)` uses only the brief's data keys and numpy (`np`), and returns a finite float.
  - It measures how strongly a dataset carries the exploited structure.
  - It is computed from parts of the data that the "claim false" version of the data leaves unchanged, so that its
    expected value is the same whether the claim is true or false. Examples: the autocorrelation of a predictor (not
    of the outcome); the coefficient of variation of a denominator; the correlation between repeated records of one
    unit; the correlation between two measured terms that both derived quantities contain.
  - `null_value` is its value when the structure is absent. `note_value` is the value in the source's setting.
  - If the structure is fixed by the brief's sizes (for example a number of features), set `set_by_brief` to true; the
    statistic then reports that number.
  - **Decoys:** if no such statistic applies to the mechanism, set `structure_statistic` to null and say why.

**Closed lists.** These are PC's lists, with the same definitions and precedence: where two tags fit, the first that fits
in the order listed is used.

`mechanism_tag`:
- **B-2**, the subtype (KAP23; PB §1, verbatim):
  - `L1.1` no test set;
  - `L1.2` pre-processing that uses the outcome labels (target encoding, label-dependent imputation, oversampling of
    classes) before the split;
  - `L1.3` feature selection on all data;
  - `L1.4` duplicates across the split;
  - `L3.1` temporal leakage;
  - `L3.2` train and test share units (subjects, patients, sites).

  Ties are broken as in PB §1:
  - oversampling by copying rows is `L1.4`; by synthesising rows, `L1.2`;
  - feature selection before cross-validation is `L1.3`;
  - selecting a classifier's parameters on the test data counts as `L1.3`, as in PC.
- **B-3**, in this order:
  - `ratio-shared-denominator`: two ratios with the same denominator are related to each other.
  - `ratio-vs-denominator-proxy`: a ratio is related to a variable that is not part of the ratio but varies with its
    denominator.
  - `change-vs-baseline`: a change (a later minus an earlier measurement of the same variable) is related to the earlier
    measurement, or to a quantity computed from it.
  - `shared-measured-component`: two quantities whose formulas both contain the same measured term as a factor or
    divisor (products, ratios, or changes in them), or such a quantity related to one of its own factors or divisors.
- **Decoys, B-1:**
  - `extreme-group-change`: units are chosen for an extreme value (one tail: the top or bottom fraction, or beyond a
    cut) of a noisy baseline measurement, and the claim is about the change of those units from that baseline.
  - `split-by-baseline-compare-change`: units are divided into two or more groups by a noisy baseline measurement (for
    example a median split or tertiles), and the change from baseline is compared between the groups.
  - `select-then-test-same-data`: units, features or a subset (voxels, genes, neurons, cells, trials) are selected by a
    test, ranking or threshold on the same data on which the reported statistic is then computed.
- **Decoys, B-6:**
  - `significant-here-not-there`: a difference between two effects is decided by one test being significant and another
    not, instead of by a test of the difference.
  - `units-not-independent`: the test treats as independent replicates observations that are nested in, or share, the
    unit to which the condition was applied (cells in animals, animals in tanks or litters, repeated measures in
    subjects).

`statistic_family`, in this order. It is the family of the statistic on which the claim's threshold is placed; a
significance test of that statistic does not change the family.
- `classification`: the performance of a classifier or of a predictor of a categorical outcome (accuracy, balanced
  accuracy, error rate, AUC, F1, sensitivity, specificity);
- `R-squared`: the explained variance of a regression, in-sample or cross-validated;
- `regression-slope`: a regression slope or standardised slope, or a summary (mean, test) of per-unit slopes;
- `correlation`: a Pearson, Spearman or partial correlation coefficient;
- `proportion`: the share of units that meet a condition (for example responders), other than a classifier's
  performance;
- `mean`: a mean, a mean difference or a mean change (one-sample, paired, two-sample or Welch t tests; F tests on
  means);
- `other`: none of the above (the note names the statistic).

## Examples of "what a brief may state"

These illustrate the rule; they are not cases. Do not copy an example as a brief.

| Class | Passes | Fails, and why |
|---|---|---|
| B-2 | key `measurements (rows, measurements)`, rows: registry entries; claim about accuracy on new patients | "about a quarter of the rows repeat an earlier entry" (states repetition), or a key named `repeat_flag` (names a role in the error) |
| B-3 | claim "across plants, total leaf nitrogen and total photosynthetic capacity are associated after accounting for leaf area: their correlation adjusted for leaf area is at least 0.4"; keys `nitrogen (plants,)`, `capacity (plants,)`, `leaf_area (plants,)` (the estimand requires naming the third quantity) | "both per-area values share the leaf area, which varies widely between plants" (states a shared quantity and how it varies) |
| B-1 | keys `scores (students, items)`: score of each student on each test item; `hours (students,)`: weekly study hours | adding "the analysed items are those whose scores track study hours" (states a selection) |
| B-6 | keys `score (classrooms, pupils)`, `new_method (classrooms,)` (bool) | "pupils in the same classroom share a teacher" (states a dependency between units) |

## Repairs

A later check may send one of your notes back for repair: the structure statistic (it does not run, or it measures the
wrong thing), or a "source states none" value that an auditor rejected. The request names the case and quotes only the
failing item. It never contains a count, a rate or a test result from any later check. Change only that field, log the
change in `LOG.md`, and confirm that you saw no rate. You may be resumed for this, or a fresh agent of your role may do
it after reading your log.

## Output files (in your sandbox folder)

- `BRIEFS.json`: a list of `{"local_id", "claim", "data_keys": [{"key", "shape", "dtype", "meaning"}], "sizes"}`, and
  nothing else.
- `PRIVATE.json`: a list of `{"local_id", "source", "passage", "faulty", "fixed", "estimand", "model_family",
  "mechanism_tag", "statistic_family", "guard_minimum", "subtype", "sizes_note", "exploited_structure",
  "structure_statistic", "notes"}`.
- `LOG.md`:
  - every brief drafted, including abandoned ones with the reason;
  - every source read, and how (full text, abstract, section);
  - every URL.

## Final message

Report:
- the number of briefs per source, and per subtype or tag;
- the number abandoned;
- which sources you read, and how;
- any rule you found impossible to satisfy (report it; do not bend it).

## Differences from Phase C's `AUTHOR_PHASE1_C.md`

| Phase C | Phase D |
|---|---|
| criterion author, part 1; reads `PREREG_PHASE_C.md`, PB, `SOURCES.md`, `SOURCES_ADDENDUM.md` | brief author; reads this file, `SOURCES.md`, `SOURCES_D.md`, `TASK.json`, `agent_docs/`; no pre-registration text |
| one author per class, 12 briefs | two authors per class (halves, disjoint sources) or one for the decoys; the counts in `TASK.json` |
| sizes ≤ 1000 per axis, ≤ 500 000 values | ≤ 2000 per axis, ≤ 2 000 000 values; timing about 30 minutes |
| private note without model family | plus `model_family`, `exploited_structure`, `structure_statistic` |
| class rules and the estimand rules in PC and PB | PB §1's decision rules, PC §2's estimand paragraph and PC's "Naming the estimand in B-3", copied verbatim; examples for B-1, B-2, B-3 and B-6 |
| — | `TASK.json` lists earlier (tag, family) combinations; prefer another family |
| — | a repairs section |
| no context-mode rule | no context-mode tool, no scratch folder outside the sandbox, no other agent |
| everything else | the same (estimand rule, banned terms, verbatim "what a brief may state", closed lists, logging) |
