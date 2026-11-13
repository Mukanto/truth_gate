# Instructions for criterion authors, Phase C, part 1 (briefs)

You are a **criterion author** in a pre-registered evaluation of Truth_Gate, a tool that checks whether the acceptance
criteria of computational studies can fail. You work only in your **sandbox folder** (given in your task), which holds
copies of the files you may read: `PREREG_PHASE_C.md` (read all of it; §1, §2 and §4 matter most), `PREREG_PHASE_B.md`
(for the rules it cites), `SOURCES.md` (keys and references), `SOURCES_ADDENDUM.md` (additional sources with their
documenting passages), the folder `agent_docs/` (the tool's documentation) and `pkg/` (the tool's code, for later use; you
do not need it in this part). Your class is given in your task.

## What you must not do

* Do not read anything outside your sandbox folder on this machine (in particular no other author's folder). Do not fetch
  anything from the project's code repository or from any published material of its earlier evaluations. Read the sources
  themselves (DOIs in `SOURCES.md` and `SOURCES_ADDENDUM.md`; most have open full texts or abstracts on PubMed Central,
  Europe PMC or arXiv) and log every URL you read.
* Do not run Truth_Gate and do not write any criterion code in this part.
* Write only inside your sandbox folder.

## What you write, per planned case

Plan **12 cases** for an in-scope class (2 per out-of-scope class: the O author writes 2 per O-1, O-2, O-3). Base each case
on a setting the source actually describes. Within your class every case differs from every other in at least one of:
the statistic, the data structure, the pipeline step where the error occurs, the sample-size regime. At most 4 cases per
source (KAP23 up to 8 in B-2); for B-2 at least 1 case of L1.1, 1 of L1.3, 2 of L1.4, 2 of L3.1, 2 of L3.2 (VAR06 cases
count as L1.3). **At least 4 of your 12 cases rest on sources of `SOURCES_ADDENDUM.md`** (in-scope classes).

1. **A neutral brief** (public: it goes to a world author who is not told the error, the class or the source):
   * `claim`: the scientific claim with its statistic and decision threshold, as a researcher would state it. **The claim
     is about the quantity that the corrected (fixed) analysis estimates**; do not say how the error enters and do not say
     what "claim false" means.
   * `data_keys`: every array of the data dict: key, shape with named axes, dtype (`float` or `bool`), meaning. Group,
     subject, trial and time structure in array axes, never integer codes; binary labels `bool`.
   * `sizes`: within the range the source describes; at most 1000 rows (or units) along any axis and at most 500 000
     values in any array. Use the source's sizes when they fit; otherwise the largest that fits the timing rule of PB §2
     (estimate it roughly; the exact check comes later) and say so in the private note. **State every array dimension as a
     number** in `sizes`.
   * The claim is positive (the criterion holds when the effect is present).
   * Banned terms (any inflection, case-insensitive): circular, double dip, leak, pseudorepl, coupl, spurious,
     non-independ, nonindepend, regression to the mean, selection bias, overfit, inflat, contaminat, optimis. Also avoid
     words that describe the faulty procedure itself (how items are chosen, how data are split).
   * **What a brief may state** (PREREG_PHASE_C §2, verbatim):
     > A brief may state (i) the sizes, (ii) the axes named in the shape of each key and what each key measured, and (iii)
     > what the claim itself states. It may not state any other fact about how rows, units, splits, repetitions or
     > variables are related, ordered, duplicated, shared or selected. An axis named in a shape (subjects, trials, time in
     > order) is setting; a statement about how the data on that axis are arranged beyond its name is not. Naming a
     > quantity in the claim is allowed only where the claim's estimand requires it (the estimand line of the private note
     > says which). No data key names a variable by its role in the error.
2. **A private note** (never shown to the world author): source key; the documenting passage (quote of at most two
   sentences, or its location); the error as it will appear in the faulty criterion, with the parameters the source
   documents; the correction in the fixed criterion; **the estimand of the faulty and of the fixed statistic**; the
   `mechanism_tag` and `statistic_family` from the closed lists below; for B-2 the KAP23 subtype; the **minimum selection
   size** an allowed guard will use (no more than the smallest size at which the statistic is defined); a sizes note (the
   source's sizes, or the largest size within the timing estimate or why a smaller size is realistic when the source
   states none; what the source reports about how the error's size depends on the sample size or number of features, or
   "not stated").

**Closed lists, with definitions** (the same text as `PHASE_B_TABLE.json` `vocabulary`; an ambiguous case is decided by
the definitions and, where two tags fit, by the order in which they are listed: the first that fits is used).

`mechanism_tag`:
* B-1, in this order:
  * `extreme-group-change`: units are chosen for an extreme value (one tail: top or bottom fraction, or beyond a cut) of a
    noisy baseline measurement, and the claim is about the change of those units from that baseline.
  * `split-by-baseline-compare-change`: units are divided into two or more groups by a noisy baseline measurement (for
    example a median split or tertiles), and the change from baseline is compared between the groups.
  * `select-then-test-same-data`: units, features or a subset (voxels, genes, neurons, cells, trials) are selected by a
    test, ranking or threshold on the same data on which the reported statistic is then computed.
* B-2: the KAP23 subtype (`L1.1`, `L1.2`, `L1.3`, `L1.4`, `L3.1`, `L3.2`) as PB §1 defines it; VAR06 pairs are `L1.3`.
* B-3, in this order:
  * `ratio-shared-denominator`: two ratios with the same denominator are related to each other.
  * `ratio-vs-denominator-proxy`: a ratio is related to a variable that is not part of the ratio but varies with its
    denominator.
  * `change-vs-baseline`: a change (a later minus an earlier measurement of the same variable) is related to the earlier
    measurement or to a quantity computed from it.
  * `shared-measured-component`: two quantities whose formulas both contain the same measured term as a factor or
    divisor (products, ratios, or changes in them), or such a quantity related to one of its own factors or divisors.
  * `target-from-labels`: the outcome is a category label or an additive score defined by a rule (a threshold, a sum or
    count of items) that contains a variable it is then related to.
* B-6, in this order:
  * `significant-here-not-there`: a difference between two effects is decided by one test being significant and another
    not, instead of by a test of the difference.
  * `units-not-independent`: the test treats as independent replicates observations that are nested in, or share, the
    unit to which the condition was applied (cells in animals, animals in tanks or litters, repeated measures in subjects).
* O: the O subtype (`O-1`, `O-2`, `O-3`) as PB §1 defines it.

`statistic_family` (the family of the statistic on which the claim's threshold is placed; a significance test of that
statistic does not change the family), in this order:
* `classification`: the performance of a classifier or of a predictor of a categorical outcome (accuracy, balanced
  accuracy, error rate, AUC, F1, sensitivity, specificity).
* `R-squared`: the explained variance of a regression, in-sample or cross-validated.
* `regression-slope`: a regression slope or standardised slope, or a summary (mean, test) of per-unit slopes.
* `correlation`: a Pearson, Spearman or partial correlation coefficient.
* `proportion`: the share of units that meet a condition (for example responders), other than a classifier's performance.
* `mean`: a mean, a mean difference or a mean change (one-sample, paired, two-sample or Welch t tests; F tests on means).
* `other`: none of the above (the note names the statistic).

## Examples of "what a brief may state" (illustrations, not cases)

The examples illustrate the rule; their settings are not taken from the listed sources. Do not copy an example as a
brief.

| Class | Passes | Fails, and why |
|---|---|---|
| B-1 | keys `scores (students, items)`: score of each student on each test item; `hours (students,)`: weekly study hours | adding "the analysed items are those whose scores track study hours" (states a selection) |
| B-2 | key `measurements (rows, measurements)`, rows: registry entries; claim about accuracy on new patients | "about a quarter of the rows repeat an earlier entry" (states repetition), or a key named `repeat_flag` (names a role in the error) |
| B-3 | claim "across plants, total leaf nitrogen and total photosynthetic capacity are associated after accounting for leaf area: their correlation adjusted for leaf area is at least 0.4"; keys `nitrogen (plants,)`, `capacity (plants,)`, `leaf_area (plants,)` (the estimand requires naming the third quantity) | "both per-area values share the leaf area, which varies widely between plants" (states a shared quantity and how it varies) |
| B-6 | keys `score (classrooms, pupils)`, `new_method (classrooms,)` (bool) | "pupils in the same classroom share a teacher" (states a dependency between units) |

**Naming the estimand in B-3** (the claim names only what the estimand requires; the other mechanisms follow the same
pattern): `ratio-shared-denominator` and `ratio-vs-denominator-proxy`, as in the example (the relation after accounting
for the quantity the source's correction adjusts for); `change-vs-baseline`, the relation between the level of a quantity
and its change, with keys for the measurement at each time; `shared-measured-component`, the relation between the two
derived quantities as the source's correction estimates it, with keys for the measured terms (and for the independent
measurement where the documented correction uses one); `target-from-labels`, the relation between the predictor and an
outcome defined without it, with keys for the measured items. A mechanism for which no brief meets §2 is not used.

## Output files (in your sandbox folder)

* `BRIEFS.json`: list of `{"local_id", "claim", "data_keys": [{"key", "shape", "dtype", "meaning"}], "sizes"}`; nothing
  else.
* `PRIVATE.json`: list of `{"local_id", "source", "passage", "faulty", "fixed", "estimand", "mechanism_tag",
  "statistic_family", "guard_minimum", "subtype", "sizes_note", "notes"}`.
* `LOG.md`: every brief drafted, including abandoned ones with the reason; every source read and how (full text, abstract,
  section); every URL.

## Final message

Report the number of briefs per source (and per subtype for B-2), how many rest on addendum sources, the number
abandoned, which sources you read and how, and any rule you found impossible to satisfy (report it; do not bend it).

## Differences from Phase B's `AUTHOR_PHASE1.md`

| Phase B | Phase C |
|---|---|
| read `PREREG_PHASE_B.md`, `SOURCES.md` and the repository's README, GATE, MANIFEST, SPEC | read only the sandbox copies (`PREREG_PHASE_C.md`, PB, stripped `SOURCES.md`, `SOURCES_ADDENDUM.md`, `agent_docs/` with evaluation results removed) |
| do not read other authors' folders or forbidden repository folders | do not read anything outside the sandbox; no fetching from the repository or earlier evaluations; every URL logged |
| numbers given in the task; at most 4 per source | 12 per in-scope class (2 per O class); at most 4 per source; ≥ 4 on addendum sources; VAR06 counts as L1.3 |
| sizes ≤ 300 rows, ≤ 60 features | ≤ 1000 per axis, ≤ 500 000 values per array; source sizes where they fit; every dimension stated as a number; sizes note |
| no estimand rule | the claim is about the fixed analysis's quantity; estimands in the note |
| banned terms; avoid describing the faulty procedure | the same, plus the verbatim "what a brief may state" text, four examples (not to be copied) and how the estimand is named in B-3 |
| private note: source, passage, faulty, fixed, subtype, notes | plus estimand, mechanism_tag, statistic_family (closed lists with definitions and precedence), guard_minimum, sizes_note |
| "Nothing else in these objects (no source, no class, no error)" | "nothing else" (output files) |
| everything else | the same (positive claims, encoding rules, logging, final message) |
