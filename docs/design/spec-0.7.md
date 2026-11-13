# Truth_Gate 0.5: specification (spec 0.7) — v3

Status: **v3, 2026-11-13, for freeze.** Designer: Claude, under the author's delegation. v1 and v2 were reviewed blind
(`spec-0.7-REVIEW1.md`, `spec-0.7-REVIEW2.md`); the changes and reasons are in `spec-0.7-REVISIONS.md`. This is a delta to
the behaviour of Truth_Gate 0.4.1 (spec 0.6, with `docs/SPEC.md` 0.5 for the engine); everything not named here is
unchanged. Spec 0.7 is implemented by package 0.5.0 (spec numbers run ahead of package numbers: spec 0.6 is package
0.4.x). After the SHA-256 freeze nothing below changes; decisions taken during implementation go to
`spec-0.7-REVISIONS-post-freeze.md`.

## 0. Why, and what is decided

Phase B (`evaluation/phase_b/REPORT.md`, section 5.1) found that K1 made five flagged faulty criteria and five fixed
criteria UNDEFINED. Their analyses return `None` when a selection is empty, which happens mostly where the claimed effect
is absent (in `minus`, 16% to 87% of the samples), and K1 makes a component UNDEFINED as soon as one outcome on `plus`,
`minus` or `null` is UNDEFINED.

**The author's decisions (2026-11-13).** No human-written cases; the external evaluation uses a world author from a
different model (section 6). For K1 the author first proposed a threshold on the UNDEFINED rate with the UNDEFINED
samples left out of the counts, UNDEFINED above it; the first blind review showed that at the proposed default this
would change 1 of the 10 motivating files (6 at the largest allowed value) and that leaving samples out biases the rest
towards "an effect was found". The author then chose **abstention counting** (section 2): a deliberate `None` means "no
claim". The author's rule "above the threshold, UNDEFINED as today" is kept for `plus` (2.1).

**Not in 0.5** (moved to 0.6, decision under delegation): command worlds and transforms, the mutations `copy`, `stale`,
`relabel`, `files = glob` worlds, YAML and Parquet input. 0.5 changes one rule and evaluates it.

## 1. Terms

* **Soft UNDEFINED (abstention):** a criterion component's outcome is UNDEFINED because the criterion returned it:
  `None` from a Python criterion (also as the whole return of a criterion with components, or as the value of a declared
  component in a returned dict); a pattern that is UNDEFINED by its own rules (empty selection, non-finite value, zero
  denominator, types that do not fit; spec 0.6 section 4); the outcome `"UNDEFINED"` answered by a command criterion.
* **Hard UNDEFINED (failure):** every other UNDEFINED outcome, i.e. a failure the criterion did not handle: an exception
  raised by the criterion (including a pattern's missing key and the leak guard's `PermissionError`); a failed or
  invalid world generation (the sample has no data); a wrong return type, including `float('nan')`, numbers, strings and
  arrays (`BAD_RETURN`), and a command outcome string other than `HOLDS`, `FAILS`, `UNDEFINED`; a declared component
  missing from a returned dict; every command-criterion failure (`ExternalError` from an `{"error": ...}` answer,
  `ExternalTimeout`, `ExternalProtocolError`, `ExternalEncodingError`, `ExternalDied` and every later request).
* A criterion that catches its own exceptions and returns `None` turns a failure into an abstention; this cannot be
  detected and changes no statistic (2.2), but the user guidance says not to do it. The command protocol text states
  that an uncaught exception must be answered with `error` (the reference wrappers already do).
* For a component and a stream `s`: `n_s` counted evaluations, `h_s` HOLDS, `u_s` UNDEFINED, of which `a_s` soft and
  `e_s` hard (`u_s = a_s + e_s`). The **K1 streams** are `world:plus`, `world:minus` and, if declared, `world:null`.

## 2. K1 as a failure rule; abstention counted as no claim

### 2.1 The rules

For each component, after both evaluations (the K6 comparison is unchanged):

1. `K1_UNDEFINED` (C; verdict UNDEFINED, unchanged cascade) if `e_s > 0` for some K1 stream (any hard UNDEFINED, exactly
   as 0.4 treats every UNDEFINED), **or** `2 * a_plus > n_plus` (the criterion abstains on most samples of the world in
   which the claim is true: it is not a test of the claim there; this is the author's "above the threshold, UNDEFINED",
   with the point-rate threshold of the K3–K5 inconclusive rules, written in integers).
2. Otherwise, for every K1 stream with `a_s > 0`, the information flag `K1_ABSTAINED:<s>` (C), for example
   `K1_ABSTAINED:world:minus`. (The author's working name was `K1_UNDEFINED_RATE`; the new name says what is reported and
   cannot be mistaken for `K1_UNDEFINED`.)
3. Otherwise, also for `s` in {`world:minus`, `world:null`} with `2 * a_s > n_s`, the **capping** flag
   `K1_ABSTAINED_MAJORITY:<s>`
   (C; caps the verdict at WEAK, like `K5_INCONCLUSIVE`): a criterion that abstains on most samples where the claim is
   false has not shown that it fails there, and a broken `minus` or `null` world (NaN data, wrong dtypes, an always-empty
   selection) would otherwise read as a clean pass.

Information flags never enter a verdict rule, a suppression rule or an expected-flag list of an evaluation.
`K1_ABSTAINED_MAJORITY` is capping only; it is never suppressed. `K1_UNDEFINED` records which rule fired: the certificate
shows it through `counts` (`hard_undefined > 0` on a K1 stream, otherwise the `plus` majority), and `truth-gate explain
K1_UNDEFINED` explains both causes.

### 2.2 Statistics

Every HOLDS-based statistic keeps the 0.4 counting, in which an UNDEFINED outcome counts as not-HOLDS out of `n` (SPEC
4.1): K2 (including `K2_FAILS_UNREACHABLE`, "`h_minus == n_minus`" in the code), every SL, `K2_LOW_POWER`, `K2_HIGH_SIZE`,
the `HIGH_RATE` rule, K3–K5 (and their inconclusive rules, which count soft and hard UNDEFINED alike), the premise map,
`pattern_stats`, the identical-`minus` analysis (whose extra recording calls are not counted samples) and the suppression
rules. In 0.4 these flags were already computed and recorded for a component that K1 made UNDEFINED, and no suppression
or cascade step reads `K1_UNDEFINED` other than the verdict; 0.5 only stops K1 from overriding them when the UNDEFINED
outcomes are abstentions.

**K8 keeps its own rule**, unchanged from 0.4: a before/after pair with an UNDEFINED side is left out of the change
count and counted as undefined; `K8_INCONCLUSIVE` (capping) applies above 50%. This is a stated limitation: because a
component may now abstain on `plus` or `minus` samples and still reach a verdict, abstentions on the "before" side of a
pair can hide changes on up to half of the pairs of a world (`known_limitations`, 2.4). In deterministic mode an
abstention on a K1 stream makes every pair of that world undefined, hence `K8_INCONCLUSIVE` whenever an invariance is
declared. Unifying K8 with abstention counting is left to a later version.

**Why abstention cannot hide a false positive in the HOLDS-based checks.** An abstention on `minus` or `null` counts as
not-HOLDS, the same as `False`: a criterion that returns `None` where it would otherwise hold does not make the claim
there, and the same `None` on the real data makes no claim either. On `plus` an abstention lowers the HOLDS rate, so it
can only weaken power and separation; `K2_HOLDS_UNREACHABLE` (zero HOLDS in `plus`) is mandatory and never suppressed.
Nothing is left out of a HOLDS count, so there is no selection effect. The probes keep their rule: more than 50%
UNDEFINED gives `K5_INCONCLUSIVE:<probe>`.

### 2.3 Deterministic and quick modes

The same rules apply, on the counted indices (index 0 in deterministic mode). In deterministic mode each K1 stream has
one sample: an abstention on `minus` or `null` is a rate of 1 and gives `K1_ABSTAINED` and `K1_ABSTAINED_MAJORITY`
(verdict at most WEAK; in 0.4 it gave `K1_UNDEFINED`; deterministic SL already counts it as not holding, SPEC 4.3); an
abstention on `plus` gives `K1_UNDEFINED` as before. Quick mode uses the same rules on its 20 samples (UNDEFINED from 11
abstentions on `plus`); its certificates stay non-certifiable.

### 2.4 Recording and certificate

* `collect` records, with every UNDEFINED outcome, its kind (`soft` or `hard`) per stream, component and index. For every
  stream, `counts` gains `hard_undefined` (`e_s`, over the counted indices); `undefined` keeps `u_s`; certificate
  validation checks `holds + undefined <= n` and `hard_undefined <= undefined`.
* `errors[stream][component]` gains the names `BAD_RETURN` and `MISSING_COMPONENT` (counts, no message) next to the
  exception names, so that the error counts of a stream add up to its `hard_undefined`.
* `known_limitations` gains two sentences: "A criterion's own UNDEFINED outcomes (None, a pattern's UNDEFINED, a
  command's UNDEFINED) on plus, minus and null count as no claim; K1 makes the verdict UNDEFINED only for failures
  (exceptions, failed generation, wrong return types, missing components, command errors) or when the criterion
  abstains on more than half of the plus samples." and "K8 leaves pairs with an UNDEFINED side out of its change count;
  abstentions can therefore hide changes on up to half of the pairs."
* `spec_version` `"0.7"`, `tool_version` `"0.5.0"`; certificate schema 2 with these additions; the body-hash rule is
  unchanged. The CLI table and the CI summary already print every component flag; no change is needed there (tested).

### 2.5 Documentation, explain, user-visible changes

* `docs/GATE.md` (K1 text, flag table with `K1_ABSTAINED` as information and `K1_ABSTAINED_MAJORITY` as capping, the
  `EXTERNAL_DIED` note, which stays true because command failures are hard), `docs/MANIFEST.md` and the command-protocol
  text describe the soft/hard distinction.
* `INFORMATIONAL_FLAGS` gains a prefix registry for `K1_ABSTAINED:`, `CAPPING_PREFIXES` gains `K1_ABSTAINED_MAJORITY:`,
  and `explain` handles the two-colon keys.
* User guidance: return `None` when the analysis has nothing to claim (for example an empty selection); let a genuine
  error raise.
* CHANGELOG and GATE.md say plainly: a component that was UNDEFINED in 0.4 only because its criterion returned `None`
  is now judged by its other flags; a CI job that failed on such an UNDEFINED may now pass (or fail on a mandatory flag
  that 0.4 already computed).

## 3. Names (cleanup deferred from 0.4.1)

Independent of section 2:

* `StudyError("STUDY is not a kapi.Study")` → `"STUDY is not a truth_gate.Study"`. The text of a `StudyError` is recorded
  in the certificate's `load_error`, so it changes certificates of studies that fail this way.
* The leak-guard message `kapi leak guard blocked <event>` → `truth_gate leak guard blocked <event>` (only the exception
  type is recorded in certificates; the message is seen in tracebacks).
* The default certificate name stays `STUDY.kapi.json` until 1.0, with the `kapi` alias.

## 4. Compatibility (exact)

Let a **result** be, per component: the verdict, the sorted flag list, and `holds`, `undefined`, `n` and `bounds` per
stream; the comparison ignores `tool_version`, `spec_version`, `known_limitations`, the new `hard_undefined` fields and
`errors` keys, and the renamed texts of section 3. Between 0.4.1 and 0.5.0 on the same study file:

1. a component with no UNDEFINED outcome on a K1 stream has the same result;
2. a component with a hard UNDEFINED on a K1 stream, or with `2 * a_plus > n_plus`, has the same result;
3. every other component with `u_s > 0` on a K1 stream (soft only, at most half of `plus`) has the 0.4.1 flags without
   `K1_UNDEFINED`, with `K1_ABSTAINED:<s>` for each K1 stream with `a_s > 0` and `K1_ABSTAINED_MAJORITY:<s>` for `minus`
   or `null` with `2 * a_s > n_s`, the same counts and bounds, and the verdict that the 0.4.1 cascade gives for those
   flags;
4. the study verdict follows from the component verdicts and the study flags as before.

Consequence: 0.5.0 changes only components that 0.4.1 made UNDEFINED. A 0.4.1 detection (NOT_FALSIFIABLE) or clean pass
(FALSIFIABLE, WEAK) of a component cannot change. `verify` on a 0.4.x certificate exits 7 (R-2).

## 5. Tests required of the implementation

Written before the code where marked (G).

* One test per row of the classification of section 1, in stochastic and deterministic mode: `None`; whole-`None`
  return with components; `None` dict value (soft); missing component (hard); `float('nan')`, `1`, a string, an array
  (hard, BAD_RETURN); exception in `fn`; failed `generate` on `plus`, `minus`, `null`; pattern on an empty selection,
  a non-finite value, wrong types (soft) and a missing key (hard); command criterion answering `UNDEFINED` (soft),
  `{"error": ...}`, an invalid outcome string, a timeout and a death (hard); a command criterion with components, one
  `UNDEFINED` (soft) and one missing (hard).
* K1 boundaries in integers: `2 * a_plus = n_plus` (no K1), one more (K1), in full mode (100 vs 101) and quick mode (10 vs
  11); one hard UNDEFINED on `minus` (K1); `K1_ABSTAINED_MAJORITY` at `2 * a_minus = n` (absent) and one more (present).
* (G) **Metamorphic None = False:** for each fixture of the test suite with abstentions, replacing every `None` by `False`
  in the criterion leaves every flag except `K1_*`, `K3/K4/K5_INCONCLUSIVE`, `K8_*` and the verdict implied by them
  identical, in stochastic and deterministic mode.
* (G) **Gaming:** a faulty criterion that holds on 15% of `minus` samples overall and returns `None` on another 15% must
  get `K2_HIGH_SIZE`; a criterion that returns `None` on every noise-probe sample gets `K5_INCONCLUSIVE:noise`; a criterion
  with 40% abstention and 60% FAILS on `plus` is NOT_FALSIFIABLE with `K2_HOLDS_UNREACHABLE`; 60% abstention on `plus` is
  UNDEFINED; a `minus` world whose data are all NaN, with a criterion that returns `None` on non-finite input, is at most
  WEAK (`K1_ABSTAINED_MAJORITY:world:minus`).
* K8 with 40% abstention on the before side and changes on the rest: the recorded result is asserted (the limitation of
  2.2); deterministic `minus` abstention with an invariance declared: `K8_INCONCLUSIVE`.
* Identical-`minus` study with abstentions: UNTESTED, not UNDEFINED.
* The compatibility statement of section 4 on hand-built studies (no UNDEFINED; hard only; soft only; soft on `plus`
  above one half; soft majority on `minus`).
* Certificate fields and validation of 2.4; `explain K1_ABSTAINED`, `K1_ABSTAINED_MAJORITY`, `K1_UNDEFINED`; GATE.md
  tables (docs tests).

## 6. Pre-registered evaluation of 0.5

Frozen with this spec; run on the released 0.5.0 with default settings, full mode.

* **R0 (baseline, before any code change).** The regression set is recorded with tag `v0.4.1` in full mode: the 159
  studies of Phase A criterion A1 (as listed by `evaluation/compare_a1.py`) and the 108 Phase B files. The certificates,
  a list with their SHA-256 and the recording script are frozen (`evaluation/baseline_v041/`,
  `FREEZE_BASELINE_V041.json`) before the implementation starts.
* **R1 (regression, necessary).** A comparison script frozen with R0 classifies each component from the **0.4.1
  certificate only**: with `E` = the sum of the `errors` counts on the K1 streams and `u_plus` = the `plus` UNDEFINED
  count, a component without a `BAD_RETURN` flag or a `K7_COMPONENT_MISMATCH` falls under section 4 item 1 if no K1 stream
  has an UNDEFINED outcome, item 2 if `E > 0` or `2 * u_plus > n_plus`, item 3 otherwise; for these components 0.5.0 must
  give exactly the result section 4 prescribes and `hard_undefined == E`. Components with `BAD_RETURN` or a mismatch form
  a separate reported group (0.5.0's `hard_undefined >= E`); none is expected in the regression set, which is why section
  5 carries the per-cause tests. Deterministic studies are reported as a separate line. R1 holds if every component of
  the first group matches.
* **R2 (Phase B rerun, development only).** The prediction computed from the 0.4.0 certificates before the freeze is
  frozen with this spec (`spec-0.7-R2-prediction.json`: component, expected verdict, expected flags). All ten UNDEFINED
  components are soft only with `a_plus / n_plus <= 0.085`; the five faulty ones become NOT_FALSIFIABLE with expected
  flags, the five fixed ones WEAK; no `K1_ABSTAINED_MAJORITY` changes a verdict. 0.4.0 and 0.4.1 agree on these files
  (no change to verdicts, flags or counts; R0 records it). R2 is labelled **development data, not evidence**: the rule
  was chosen after these cases were seen; R2 checks that the implementation does what the prediction says.
* **R3 (Phase C: errors documented in the literature, worlds by a different Claude model line).** A new
  pre-registration, `evaluation/phase_c/PREREG_PHASE_C.md`, reviewed and frozen before any Phase C case exists, with Phase
  B's design (classes B-1, B-2, B-3, B-6 and out-of-scope cases; at least 10 pairs per in-scope class; roles; fidelity and
  post-run audits; the same thresholds; expected flags without information flags) and these fixed differences:
  * **new briefs only.** Fresh criterion-author agents (Sonnet, one per class) write the briefs and, after the
    skeleton freeze, the criterion bodies; they read neither the Phase B cases nor the Phase B record. The Phase B source
    list may be used and sources may be added; a case whose error and setting overlap a Phase B brief is flagged in the
    table.
  * **The world author is Fable** (Claude Code agent model `fable`), a different model line from the Opus and Sonnet
    models that write the briefs, the criteria, the audits and the gate, **from the same vendor and family (Anthropic
    Claude)**. Its model id and run dates, and the 0.5.0 build (commit) are recorded.
  * The criterion authors read the 0.5.0 public documentation (the tool under test, as a user would) and receive Phase
    B's guard rules (allowed guards return `None`) in their instructions, fixed before any skeleton exists.
  * **Primary comparison:** 0.5.0 against 0.4.1 on the same frozen Phase C files, per class: components UNDEFINED under
    0.4.1; detections and clean passes gained; faulty twins that move from UNDEFINED to FALSIFIABLE or WEAK (misses that
    0.4.1 hid) and fixed twins that move from UNDEFINED to NOT_FALSIFIABLE (false alarms that 0.4.1 hid), both reported
    by name; by section 4 no 0.4.1 detection or clean pass can be lost, and any such loss counts against 0.5. A "no
    change" outcome is reported as such.
  * Claims allowed in the report: what the gate did on errors documented in the literature, with worlds declared by a
    different Claude model line that did not know the error; not "independent of the gate's authors", not "errors
    nobody anticipated".

## 7. Decisions under delegation (open to the author's objection)

1. Soft/hard distinction as in section 1; hard UNDEFINED keeps 0.4's K1 (review 1, finding 2).
2. `plus` abstention above one half stays UNDEFINED (the author's rule), threshold fixed in integers, not a declared
   target (no knob for the evaluated author).
3. `minus`/`null` abstention above one half caps at WEAK (`K1_ABSTAINED_MAJORITY`) rather than being accepted silently
   (review 2, finding 2; no effect on the development data).
4. K8 keeps its rule, with the limitation stated (review 2, finding 1).
5. Flag name `K1_ABSTAINED` instead of the working name `K1_UNDEFINED_RATE`.
6. Scope: one rule and two renamed texts; the other planned 0.5 features move to 0.6.
7. Phase C uses new briefs (review 1, finding 8).
