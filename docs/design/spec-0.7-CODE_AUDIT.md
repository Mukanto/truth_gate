# Code audit of Truth_Gate 0.5.0 against spec 0.7 (blind)

Auditor: blind code auditor (did not write the code). Scope: the uncommitted working tree against `HEAD` (v0.4.1) and
`docs/design/spec-0.7.md` sections 1-5. Reproduction scripts: `C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\e99bcaed-1f5d-4c84-948a-5ba1699cb0eb\scratchpad\code_audit\`
(`r1_det_probe.py`, `r1b_det_probe_reverse.py`, `r2_diff_run.py` + `r2_compare.py`, `r3_pattern_fuzz.py`, `r4_validate.py`).
The full test suite passes (963 tests, 4 skipped, about 52 s). The frozen files (`test_spec07_gaming.py`,
`toy_studies_spec07/`, `spec-0.7*.md`) match the hashes in `FREEZE_TESTS_G_0.7.json` and `FREEZE_SPEC_0.7.json`.

Result: no blocking finding. One major finding, six minor findings.

## Findings

### 1. (major) In deterministic mode the `errors` counts of a random probe do not add up to `hard_undefined`

`truth_gate/checks.py:534` (collect: `errors` counts a hard outcome only for `i < n_counted`, so for index 0) against
`truth_gate/checks.py:570-576` (`stream_stats`: for a random probe in deterministic mode the combined outcome decides
`hard_undefined` from all three draws). Spec 2.4: "`errors[stream][component]` gains the names `BAD_RETURN` and
`MISSING_COMPONENT` ... so that the error counts of a stream add up to its `hard_undefined`." CHANGELOG 0.5.0 repeats it
as fact. It is false in both directions on `probe:noise`, `probe:zeros`, `probe:shuffle:*`:

* Reproduction `r1_det_probe.py` (deterministic study, the criterion is soft on draws 0 and 1 and raises on draw 2):
  `draws ['UNDEFINED','UNDEFINED','UNDEFINED'] counts {'holds': 0, 'undefined': 1, 'hard_undefined': 1, 'n': 1} errors {}`.
  The certificate says one hard failure and records no error.
* Reproduction `r1b_det_probe_reverse.py` (the criterion raises on draw 0 only, draws 1 and 2 FAIL):
  `counts {'holds': 0, 'undefined': 0, 'hard_undefined': 0, 'n': 1}  errors {'ValueError': 1}  draws ['UNDEFINED','FAILS','FAILS']`.
  An error is recorded for a stream that has `hard_undefined` 0 and `undefined` 0. (The second direction was already
  present in 0.4.1, where `errors` counted index 0 only; spec 0.7 turned it into a stated invariant.)

No verdict changes (these streams are not K1 streams; K5 reads `undefined`, which is the 0.4.1 value), so the effect is
on certificate content only. The existing tests check the invariant on K1 streams only
(`test_the_error_counts_of_a_k1_stream_add_up_to_hard_undefined`, `tests/test_spec07.py:294`), and the deterministic
probe tests pin only the toy where both draws raise (`tests/test_deterministic_probes.py:104-110`), where it holds by
luck. Fix: in `stream_stats`/`collect`, for a random probe in deterministic mode derive `errors` from the same
combined rule as `hard_undefined` (one entry, the cause of the first hard UNDEFINED draw, only when the combined
outcome is UNDEFINED and hard; none otherwise), and add a test that sums `errors` against `hard_undefined` over every
stream of every certificate in `tests/toy_studies*` in both modes. Alternatively restate 2.4 and the CHANGELOG as
"for the K1 streams and in stochastic mode" (needs a post-freeze entry, see finding 2).

### 2. (minor) The implementer's decision on the deterministic probe rule is not in the post-freeze log

`spec-0.7.md` header: "decisions taken during implementation go to `spec-0.7-REVISIONS-post-freeze.md`." The log holds
only R-1 and R-2. The docstring of `stream_stats` (`checks.py:566-568`) says "spec 0.7, 2.4 does not say" and chooses
"hard if any UNDEFINED draw is hard". Judgement of the rule itself (task item 3): it is consistent with the spec text
(it keeps `hard_undefined <= undefined`, and it keeps K5 unchanged). The readings "all UNDEFINED draws hard", "draw 0
decides" and "always soft" give the same verdicts in every case, because no probe stream is a K1 stream and no
statistic reads `hard_undefined` of a probe; they differ only in `hard_undefined` and `errors`. Fix: add an R-3 entry
with the rule, the alternatives and the finding-1 consequence.

### 3. (minor) Stale version and spec pointers in the documentation

* `docs/GATE.md:3`: "Version 0.4 follows spec 0.6; the design record is in `design/`" (it is 0.5 and spec 0.7; the
  sentence also sends the reader for "the formal rules and statistics" to `SPEC.md` (0.3), whose K1 text,
  `docs/SPEC.md:146-148`, `:222`, `:372`, still says any UNDEFINED outcome gives `K1_UNDEFINED`).
* `README.md:341` "design/ (spec 0.6 and its revisions)" and `README.md:325-328` ("Phase B ... points at two things for a
  later version ... how K1 treats UNDEFINED outcomes that come from a criterion's own guard") read as open items although
  0.5.0 implements exactly this. `docs/EVALUATION.md:219-221` (the B-1 explanation) likewise says nothing about 0.5.
* `docs/MANIFEST.md:299` ("references a missing key or does not fit the data raises an error, which the engine turns into
  UNDEFINED", mutations): not stated that this is a hard UNDEFINED. A mutation that raises `NotApplicable` in a derived
  `minus` world is a failed generation, hence hard and `K1_UNDEFINED` (the spec lists only patterns as soft; the code
  does exactly that, no `NotApplicable` is caught in `manifest.py` or `mutations.py`). A user who reads "UNDEFINED
  means abstention" will not expect it. Fix: one sentence each.

### 4. (minor) Certificate validation lets a malformed `counts` through

`truth_gate/certificate.py:156-159` (`_counts_problems`): `counts` that is `None`, `[]` or `{}`, or a certificate whose
`counts` lacks a stream, validates clean (`r4_validate.py`: `counts=None -> []`, `counts=[] -> []`, `counts={} -> []`,
`no minus stream -> []`). The `key in comp` check upstream passes because the key exists. For a 0.7 certificate the
validator should require a dict that names at least `world:plus` and `world:minus` (the engine always writes them).
Also, an explicit `hard_undefined: null` reports "is missing", which is acceptable. `errors` is not cross-checked
against `hard_undefined` (spec 2.4 does not ask for it; fine, but see finding 1).

### 5. (minor) Public documents that the Phase C authors read still carry evaluation results

The spec and `tests/test_spec07.py:1046` forbid evaluation results only in `GATE.md`, `MANIFEST.md`, `SPEC.md`, and
those three are clean. `README.md:245-255, 325` (Phase A and Phase B results, the Phase B report path) and
`CHANGELOG.md:37` (the case name `evaluation/cases/E2/E2-07_faulty.py` and why it moves) are also "public documentation"
in the sense of spec 6 R3 ("criterion authors read the 0.5.0 public documentation"). Spec 6 also says they read "neither
the Phase B cases nor the Phase B record". The PREREG for Phase C should name the exact files the agents are given; if
the whole repository is given, the README paragraph about Phase B and the CHANGELOG case name are a leak path. No code
change.

### 6. (minor) One weakened existing assertion

`tests/test_stage_a.py:155` changed `limits[3:]` to `limits[3:5]`. This is harmless (the two new sentences are checked
verbatim in `tests/test_spec07.py:844` and the count of 7 in `tests/test_v03.py:798`), but the cleaner edit is
`limits[3:5]` plus an assertion `len(limits) == 7` in the same test.

### 7. (minor) `explain` accepts any suffix after the family colon

`truth-gate explain K1_ABSTAINED:anything` prints the family entry (same behaviour as `HIGH_RATE:` and
`K5_INCONCLUSIVE:` before). Not a regression; noted for completeness.

## What was checked and found correct

1. Classification (task 1). Soft: `None` whole return or dict value (`checks.py:316-345`), a command's `"UNDEFINED"`
   (`external.py:53, 135` then `_classify`), pattern `NotApplicable` (`patterns.py:722`, `Pattern.fn`). Hard: exceptions
   (`evaluate_detailed`, including `KeyError` from `Pattern.evaluate` and the guard's `PermissionError`), failed or
   invalid generation (`Sample(None, name)`), non-bool returns, NaN, numbers, strings, arrays, non-dict with components,
   missing component, every `External*` exception and `InvalidOutcome`. Verified with the 40+ per-row tests (both modes)
   and independently by `r3_pattern_fuzz.py`: 19 pattern specs against 15 hostile data shapes (empty, NaN, inf, str,
   bool, 2-D, length mismatch, 0-d, zero denominator ...) raise nothing but the missing-key `KeyError`, so no
   data-dependent condition of a pattern leaks into a hard UNDEFINED.
   `hard_undefined == sum(errors)` holds on every stream of the 213 components of `r2_compare.py`, except the
   deterministic random-probe case of finding 1.
2. K1 rule (task 2): `check_k1` (`checks.py:185-205`) is exactly 2.1: hard on any K1 stream or `2*a_plus > n_plus` gives
   only `K1_UNDEFINED` (no information flags, as section 4 item 2 needs); otherwise `K1_ABSTAINED:<s>` and, for minus and
   null with `2*a_s > n_s`, the capping `K1_ABSTAINED_MAJORITY:<s>`. `CAPPING_PREFIXES`/`INFORMATIONAL_PREFIXES` are
   registered; the two prefixes do not shadow each other (`K1_ABSTAINED:` is not a prefix of `K1_ABSTAINED_MAJORITY:`).
   The cascade and the suppression set are untouched; the diff of `checks.py` changes no statistic (K2-K7, Wilson
   bounds, HIGH_RATE) and `k8.py` is not modified (it still calls the 4-tuple `evaluate_criterion`, which returns
   `Evaluation[:4]`).
3. Compatibility (task 7), by experiment: I ran 0.4.1 (`git archive HEAD` copy) and 0.5.0 over 292 study files minus
   the slow `evaluation/cases` (213 components: toys, spec07 fixtures, 108 Phase B files, examples). Classified from the
   0.4.1 result as in R1: 167 components item 1, 6 item 2, 20 item 3, 1 `BAD_RETURN`; every item 1 and item 2 component
   has an identical verdict, flags, counts and bounds (the single difference, `toy_nonreproducible`, is the
   unseeded-randomness study of R-1), every item 3 component has the 0.4.1 flags minus `K1_UNDEFINED` plus
   `K1_ABSTAINED*`, with the same counts. The ten Phase B components move as `spec-0.7-R2-prediction.json` says (five
   faulty to NOT_FALSIFIABLE, five fixed to WEAK, B1-05/B1-06/B2-09 also with `K1_ABSTAINED:world:plus`).
4. Certificate (task 4): `counts[s].hard_undefined`, `errors` names `BAD_RETURN` and `MISSING_COMPONENT`,
   `spec_version "0.7"`, `tool_version "0.5.0"`, the two `known_limitations` sentences are verbatim (checked against
   spec 2.4 character by character), the validator enforces `holds + undefined <= n`, `hard_undefined <= undefined`,
   integer types, and requires `hard_undefined` from 0.7 on while a 0.6 certificate without it validates.
5. Other consumers (task 5): `badge.py` (verdict only), `ci.py` and `cli.py` (print flags verbatim, no prefix parsing),
   `suggest.py`, `passes.py` (`add_component_flags` recomputes the verdict with the new `component_verdict`),
   `freeze.py`, `mutations.py` do not need a change. `explain` resolves `K1_ABSTAINED:world:minus`,
   `K1_ABSTAINED_MAJORITY:world:null`, bare and lower-case names (run by hand), `kind_of` labels them information and
   capping.
6. Renamed texts (task 6): only the two StudyError and guard texts changed; `grep` finds no frozen example, evaluation
   file or certificate that carries the old texts.
7. Docs and changelog (task 8) agree with the code on the classification, the flag table, the `K1_UNDEFINED` two causes,
   the CI effect and the K8 limitation; GATE.md, MANIFEST.md and SPEC.md contain no Phase B/C or case names; version pins
   are 0.5.0 everywhere (`pyproject.toml`, README, action template, pre-commit hook).
8. Tests (task 9): `tests/test_spec07.py` has a test for every bullet of spec section 5 (classification rows in both
   modes including command criteria, K1 integer boundaries 100/101 and 10/11, majority boundary, K8, identical-minus,
   the section 4 statement on hand-built studies, certificate, explain, docs) and the two (G) tests are in the frozen
   gaming file. The changed existing tests are version bumps and the added `hard_undefined` key; the one changed K1 test
   keeps the old three assertions with `hard=` and adds the new rule in a separate test.
