# Removals from the agent document set (PREREG_PHASE_C section 4 item 0(a))

Source: docs/GATE.md, docs/MANIFEST.md, docs/SPEC.md and the tool parts of README.md at tag v0.5.0 (README_TOOL.md keeps the sections: title, Who it is for, Getting started, Run the gate, Quick start without Python code, The command line, In CI, A study in Python, Limits). Each block below was removed by the designer before the two-reader triage, because it states an evaluation, its results, its cases or its process.

## README_TOOL.md, lines 1-1 (line `<!-- Agent document set`)

```
<!-- Agent document set marker -->
```

## GATE.md, lines 365-365 (bullet `* Tiny denominators:`)

```
* Tiny denominators: several evaluation criteria rest on a handful of cases and are reported as they are.
```

## SPEC.md, lines 6-20 (until:> The released package `> **This is an edited copy for publication.**`)

```
> **This is an edited copy for publication.** It contains three frozen documents in order: the v0 specification
> (spec 0.3), the v0.2 delta (spec 0.4) and the v0.3 delta (spec 0.5). Private project names, local paths, the
> Turkish decision quotes and the details of the private pilot were removed or replaced by neutral wording; the
> technical content (rules, flags, verdict mapping, evaluation criteria) was not changed. Section numbers inside a
> delta refer to the v0 document.
>
> SHA-256 (first 16 hex digits) of the frozen originals, which are not published:
>
> | Original | Spec version | SHA-256 (first 16 hex) |
> |---|---|---|
> | v0 specification | 0.3 | `88074F1D26CA24B7` |
> | v0.2 delta | 0.4 | `FD9BCC3DC377F441` |
> | v0.3 delta | 0.5 | `17E1B57F90914BD9` |
>
> The released package (`kapi`, version 0.3.0) implements spec 0.5.
```

## SPEC.md, lines 27-27 (line `- **Freeze rule:**`)

```
- **Freeze rule:** This file is frozen (SHA-256 recorded in a freeze record) after the D4 pre-freeze smoke test (§11) and **before any evaluation case (§12) is executed**. After the freeze, changes go to a new spec version with a deviation note; results are reported against the frozen version.
```

## SPEC.md, lines 28-28 (line `- **Roles:**`)

```
- **Roles:** The author owns product decisions. An AI assistant (the drafting session) wrote this spec and reviewed all code. Implementation was delegated to a coding subagent. An independent reviewer session (Tenkit) authored evaluation set E2.
```

## SPEC.md, lines 279-291 (section `## 11. D4 pre-freeze smoke test`)

```
## 11. D4 pre-freeze smoke test (for this spec and the evaluation harness)
Run after implementation and before the freeze. Print only "defined / reachable / covered". Never print evaluation results, and never run evaluation cases.
1. **Defined:** every check computes on toy studies in stochastic and deterministic modes; the certificate validates against §7; the CLI exit codes work.
2. **Reachable:**
   - for each of the four verdicts, at least one toy study produces it;
   - for each flag in §5, at least one toy study raises it and one does not;
   - for each evaluation criterion P1–P4 (§12.4), both outcomes are reachable when computed on **synthetic mock result tables** (not real gate outputs on evaluation cases).
3. **Covered:**
   - every check K1–K7 has tests;
   - every flag is documented in the README;
   - every evaluation case in §12 has a declared expected check and a fixed twin.
4. If anything fails, fix the spec or code before freezing and record the fix and its reason here (§14).

```

## SPEC.md, lines 292-348 (section `## 12. Evaluation`)

```
## 12. Evaluation (pre-registered; frozen with this file)

### 12.1 Sets
- **E1, retrospective (self-authored).** Ten fault/fixed pairs reconstructed from documented incidents. The faulty version must be flagged with the expected check; the fixed twin must not be NOT_FALSIFIABLE or UNDEFINED.

| Case | Origin | Faulty version | Expected check(s) | Fixed twin |
|---|---|---|---|---|
| E1-01 | earlier study (tolerance below float resolution) | HOLDS iff \|mean(x) − μ₀\| < 1e-40, with scale 0.735 | K2_UNRESOLVABLE (and K2_HOLDS_UNREACHABLE) | tolerance 1e-3 |
| E1-02 | earlier study (uncovered regime) | regimes early and late, criterion only for early | K7_REGIME_UNCOVERED | criterion added for late |
| E1-03 | earlier study (component mismatch) | components time and position declared, only time returned | K7_COMPONENT_MISMATCH | both returned |
| E1-04 | earlier study (interpolating fit) | "flexible model fits with loss < ε" (interpolating fit) | K4_CONTROL_ALSO_HOLDS (and K2_NO_SEPARATION) | fixed-form theory model with no free parameters |
| E1-05 | earlier review (results-file leak) | criterion reads a results file to decide | K6_LEAK_ATTEMPT | no file access |
| E1-06 | earlier review (precision note) | tested premise mutation of magnitude 1e-25 at scale 1 | K2_UNRESOLVABLE or K3_PREMISE_NOT_TESTED | magnitude 1e-6, verdict flips |
| E1-07 | earlier study (dominant tolerance) | angle criterion whose tolerance dominates; geometry premise (tested) does not flip | K3_PREMISE_NOT_TESTED | tolerance at which geometry break flips |
| E1-08 | earlier study (self-labelled targets) | targets defined by the same labels the criterion checks | K5_HOLDS_ON_NOISE or K5_HOLDS_ON_DEGENERATE | targets computed from data |
| E1-09 | earlier study (direction invariance) | direction criterion invariant under path swap (mirror-symmetric field) | K3_PREMISE_NOT_TESTED | chiral statistic |
| E1-10 | earlier study (run-completed label) | HOLDS when execution completes regardless of residual | K2_FAILS_UNREACHABLE or K2_NO_SEPARATION | requires true residual ≤ tolerance |

- **E2, independent.** At least 12 fault/fixed pairs covering at least 6 fault types. Each case states its expected check(s). The set is authored from §3, §5 and §12 of this spec only; the reviewer session does not see the implementation. The set is hashed and the hash recorded before Kapı is run on it. If the reviewer session is not used (author's decision), E2 is reported as "not run" and P1b/P2b are not evaluated.
- **E3, external.** Two pairs reconstructed from published cases:
  - **E3-01 (Wu 2026, arXiv 2610.22445).** The constant reduction passes a closure criterion. Faulty version: the criterion is "closure error < ε" for a candidate reduction of a slow–fast system. Expected check: K5_HOLDS_ON_DEGENERATE or K5_HOLDS_ON_NOISE. Fixed twin: closure AND observable preservation.
  - **E3-02 (same paper, linear CKA).** Faulty version: correspondence validity judged by linear CKA > τ, which is invariant to a random rotation of the proposed map. Expected check: K3_PREMISE_NOT_TESTED, with the premise "the correspondence is correct" mutated by a random rotation. Fixed twin: held-out prediction R² under the proposed map.

### 12.2 Procedure
1. Kapı is implemented and unit-tested on toy studies only.
2. The drafting session reviews the code; D4 (§11) is run.
3. The code is hashed and frozen together with this spec.
4. The E1 and E3 case files are then written from the table above without modifying Kapı. They are hashed before the first run.
5. E2 is received from the reviewer session and its hash recorded.
6. Each case is run once in full mode. Primary results come from the frozen Kapı version only.
7. A bug found during evaluation is fixed in a new version; results with that version are labelled secondary.

### 12.3 Detection rule
A faulty case is **detected** if the study verdict is NOT_FALSIFIABLE or UNDEFINED **and** at least one of its expected checks appears among the raised flags. A fixed twin is **cleared** if its verdict is FALSIFIABLE or WEAK.

### 12.4 Primary criteria
- **P1a:** detected faulty cases / all faulty cases (E1 ∪ E2 ∪ E3) ≥ 0.90.
- **P1b:** the same rate restricted to E2 ≥ 0.80.
- **P1c:** no fault type (E2 types; E1 and E3 count by expected check) has zero detections.
- **P2a:** cleared fixed twins / all fixed twins ≥ 0.90. **P2b:** the same rate restricted to E2 ≥ 0.80.
- **P3:** every case whose expected check is K6_LEAK_ATTEMPT is detected (rate = 1.0).
- **P4:** every case run twice with `verify` gives an identical `body_sha256` (rate = 1.0).

Each criterion is reported as Held (`Tuttu`) or Failed (`Tutmadı`) with counts. Small denominators are reported as they are; no pooling hides a failed subset.

### 12.5 Reference baselines (sanity, not criteria)
- An "always NOT_FALSIFIABLE" gate meets P1 and fails P2.
- An "always FALSIFIABLE" gate meets P2 and fails P1.

Both are computed on the mock tables in D4 to show that the evaluation can distinguish them.

### 12.6 Exploratory (labelled as such)
- Confusion table of expected versus raised checks.
- Frequency of WEAK.
- Run time per case.
- Any additional flags raised on fixed twins.

```

## SPEC.md, lines 355-355 (line `- E1 is self-authored`)

```
- E1 is self-authored, which is why E2 and E3 exist.
```

## SPEC.md, lines 358-389 (section `## 14. Change log`)

```
## 14. Change log
- 0.1-draft (2026-11-05): first draft by the drafting session. Not frozen.
- 0.2-draft (2026-11-05, the drafting session's self-review before delegation):
  - targets use significance at level `a`, so random fluctuation does not raise WEAK;
  - new capping rule `HIGH_RATE:<stream>`;
  - `allow_paths` restricted to static files; studies are single files in v0;
  - probe-evasion weakness added to §13.
- 0.3-draft (2026-11-05, after implementation review; D4 finding, before freeze):
  - **§4.3 changed.** Deterministic mode had used one noise draw and had included Kapı's own random probes in the determinism check, which could raise NONDETERMINISTIC for a deterministic study. Kapı's random probes now use three draws (HOLDS if any draw holds) and are excluded from the determinism check.
  - **Implementation interpretations adopted** (the conservative reading in every case):
    1. Directory listings by the import machinery of `sys.path` entries are not leaks; any other listing outside the allow-list is a leak.
    2. Study files are loaded with `compile` + `exec` from the bytes read before arming, not through the import system.
    3. Relative `allow_paths` resolve against the study's directory; a missing file is a `StudyError`.
    4. A load failure records `load_error` (type only; message only for `StudyError`). A leak during import gives UNDEFINED plus `K6_LEAK_ATTEMPT`.
    5. `BAD_RETURN` is informational. Its UNDEFINED outcomes already trigger K1 in `plus`/`minus` and the inconclusive caps elsewhere. [Since 0.5 (spec 0.7), only a hard UNDEFINED outcome (a failure) or abstention on more than half of the `plus` samples gives `K1_UNDEFINED`; see [`GATE.md`](GATE.md).]
    6. `K7_COMPONENT_MISMATCH` is study-level; extra keys count as a mismatch; a missing component is UNDEFINED.
    7. A non-empty `control_waiver` raises `K4_WAIVED` even when controls are listed.
    8. `K3_INCONCLUSIVE` also applies to assumed premises. A tested premise with an unresolvable magnitude always gets `K3_PREMISE_NOT_TESTED`.
    9. K4/K5 inconclusive flags are added alongside the SL-based flags; only K3 replaces its decision.
    10. `HIGH_RATE` applies to tested premises, controls, probes, null and shuffle, not to assumed premises.
    11. `m` is computed from the declaration only.
    12. Extra construction checks: empty criteria, non-positive budget, out-of-range targets, empty components, unknown roles.
    13. Extra body fields: `errors`, `unresolvable`, `known_limitations`, `study_flag_details`, `probe_unchanged_keys`, `load_error`; bounds rounded to 12 decimals.
    14. Harness: an expected check matches an equal flag or the prefix of a parametrised flag; P1c counts E2 by `fault_type` and E1/E3 by expected check; the P4 denominator is two runs-pairs per case.
  - E1-06 expected checks written as alternatives.
- **D4 run (2026-11-05, on 0.3-draft code; 275 unit tests OK):**
  - Defined: all checks in both modes, certificate, CLI.
  - Reachable: all 25 flag families raised and not raised; all four verdicts; P1a–P4 both outcomes, computed on synthetic mock tables; P1b/P2b "not evaluated" without E2; both baselines fail as intended.
  - Covered: every flag in the README; E1 has 10 complete rows; E3 has 2 cases; no evaluation case files exist.
  - Two first-pass "no" results came from the smoke script itself, not from Kapı: a text search for "Tuttu" missed tests that use constants, and escaped pipes broke the table parse. Both were replaced by direct computation. No spec or code change was needed.
- **0.3 (2026-11-05): frozen.** Only the version labels changed ("0.3-draft" → "0.3" in this header, `kapi/certificate.py`, `kapi/__init__.py` and two tests). The full suite was rerun before hashing.

```

## SPEC.md, lines 396-399 (bullet `- **Why v0.2:**`)

```
- **Why v0.2:** The v0 evaluation gave P1a–P3 Held and P4 Failed. It produced three findings:
  1. Inflated false-positive rates (the p-hacking / multiplicity class) received only WEAK.
  2. When `plus` never holds, misleading downstream flags cascade.
  3. P4 was ill-defined for studies whose fault is non-reproducibility.
```

## SPEC.md, lines 439-479 (section `## Δ4 — Evaluation of v0.2`)

```
## Δ4 — Evaluation of v0.2 (pre-registered; frozen with this file)

### Δ4.1 Sets
- **R (regression).** The v0 sets E1E3 (`CASES_SHA256.json` D012088E5128DDD5) and E2 (E6EAD83AD9FC934B), unchanged. Their v0 outcomes are known, so R is a regression check only. It is not evidence of detection power.
- **E4 (new, independent).**
  - **Size:** at least 16 fault/fixed pairs in at least 6 fault types.
  - **False-positive inflation:** at least 4 pairs belong to this class (`fault_class: "fp_inflation"`). Examples: multiple comparisons without correction, optional stopping, threshold or outcome chosen after looking, subgroup fishing. Their expected checks include `K2_HIGH_SIZE` or a `HIGH_RATE:*` family.
  - **Weak twins:** at least 4 pairs whose fixed twin is designed to be legitimately **WEAK** (`expect_fixed: "WEAK"`; for example a valid but underpowered design).
  - **Adversarial:** at least 2 pairs.
  - **Authoring:** E4 is written from the public spec texts only (0.3 §1–§5 and §12, this delta, README). The author has no access to the implementation. The set is hashed before its first run.

### Δ4.2 Detection and clearance
Unchanged from 0.3 §12.3:
- A faulty case is detected if its verdict is NOT_FALSIFIABLE or UNDEFINED and at least one expected check is raised.
- A fixed twin is cleared if its verdict is FALSIFIABLE or WEAK.
- An expected check written as a family (`HIGH_RATE`) matches any `HIGH_RATE:<stream>`.

### Δ4.3 Primary criteria (E4 unless stated)
- **P1a:** detected / faulty ≥ 0.90.
- **P1b:** detection within `fp_inflation` ≥ 0.80.
- **P1c:** no E4 fault type has zero detections.
- **P2:** cleared / fixed ≥ 0.90.
- **P3:** every E4 case whose expected checks include `K6_LEAK_ATTEMPT` is detected (1.0). If there is none: "not evaluated".
- **P4′ (replaces P4):** each file in R ∪ E4 is run twice.
  - If the first run's flags contain `K6_NONREPRODUCIBLE` or `NONDETERMINISTIC`, the file passes iff both runs contain that flag and have the same verdict.
  - Otherwise it passes iff both runs have the same `body_sha256`.
  - Pass rate = 1.0.
- **P5 (WEAK path):** among pairs with `expect_fixed: "WEAK"`, the fixed twin's verdict is exactly WEAK in ≥ 0.80 of them. With fewer than 4 such pairs: "not evaluated".
- **R1:** every R faulty case is detected (1.0).
- **R2:** every R fixed twin is cleared (1.0).

Each criterion is reported as Held (`Tuttu`) or Failed (`Tutmadı`) with counts. Small denominators are reported as they are. Exploratory analyses are labelled as such.

### Δ4.4 Procedure (drafting-session default; same discipline as 0.3 §12.2)
1. Implement v0.2 with toy studies only.
2. The drafting session reviews the code.
3. Run D4: defined / reachable / covered. Include reachability of Δ1 (`K2_HIGH_SIZE` → NOT_FALSIFIABLE) and of Δ2 (suppression raised and not raised), and both outcomes of P1b, P4′, P5, R1 and R2 on mock tables.
4. Freeze this file and the code (freeze record).
5. Hash E4.
6. Run R and E4 once, in full mode, with a new runner (`evaluation/run_eval_v02.py`). The v0 runner stays untouched.

```

## SPEC.md, lines 484-495 (section `## Δ6 — Change log`)

```
## Δ6 — Change log
- 0.4-draft (2026-11-05): first draft by the drafting session, after the author's decisions. Not frozen.
- **Implementation review (2026-11-05):** The Δ1 and Δ2 code matches this delta. A coded assertion forbids suppression from changing a verdict.
  - Interpretations adopted: the kept unresolvable-magnitude `K3_PREMISE_NOT_TESTED` is not listed in `suppressed`; suppression also triggers when `plus` is entirely UNDEFINED (zero HOLDS); `suppressed_by`/`suppressed` appear only if something was suppressed; P4′ input lists are named `faulty_runs`/`fixed_runs`; regression rows use `set` = R-E1/R-E2/R-E3.
  - Three files written with CRLF line endings were normalised to LF.
- **D4 run (2026-11-05):** 30/30 defined / reachable / covered.
  - 328 unit tests and 18 runner tests OK.
  - Reachable: Δ1 (`K2_HIGH_SIZE` and `HIGH_RATE` → NOT_FALSIFIABLE, `K2_LOW_POWER` → WEAK); Δ2 (suppression raised and not raised, stochastic and deterministic; unresolvable K3 kept); P1a–R2 both outcomes on synthetic mock tables, with P3/P5 "not evaluated" cases.
  - Covered: regression sets intact; no E4 yet.
  - The v0 runner test in the main tree now fails by design, because the main tree is no longer the v0 freeze. The frozen v0 tree passes its own runner and unit tests.
- **0.4 (2026-11-05): frozen.** Only the version labels changed ("0.4-draft" → "0.4" in this header, `kapi/certificate.py`, `kapi/__init__.py`, the README, the v0.2 harness and runner docstrings, and five tests). Both test suites were rerun before hashing.

```

## SPEC.md, lines 628-677 (section `## Δ6 — Change log`)

```
## Δ6 — Change log
- 0.5-draft (2026-11-11): first draft by the drafting session, after the author's decisions. Not frozen.
- **Implementation (2026-11-11, coding subagent; drafting-session review the same day).**
  - **v0.2 archive:** the frozen v0.2 tree was archived read-only and matches its freeze record. Its suites pass (328 unit and 18 runner tests).
  - **New and changed code:**
    - new module `kapi/minus.py`;
    - changes in `kapi/checks.py`, `kapi/cli.py`, `kapi/certificate.py`, `kapi/__init__.py`, `pyproject.toml` and the README;
    - `kapi/study.py`, `sampling.py`, `guard.py`, `probes.py`, `stats.py` and `__main__.py` are byte-identical to v0.2, so the study API is unchanged.
  - **Drafting-session review:**
    - `minus.py` matches Δ1.2–Δ1.4.
    - In `checks.py`, the paired draw is stochastic only and is made after the counted samples. Δ1.5 is applied before the verdict, and the 0.4 Δ2 assertion still holds.
    - The harness detection rules match Δ4.2–Δ4.3.
  - **Plan conflict:** the existing toy `toy_no_separation` has a same-generator minus. It now raises `K2_MINUS_IDENTICAL`, and `K2_NO_SEPARATION` is suppressed (see Δ5), which broke two old tests. Its verdict stays NOT_FALSIFIABLE through other mandatory flags. Drafting-session decision: both tests point to a new toy, `toy_no_separation_distinct`, whose minus really differs. One explicit test documents the changed behaviour of the old toy. The old toy file is unchanged.
  - **The frozen v0.2 runner test** (`evaluation/test_run_eval_v02.py`) fails in the main tree by design, because it asserts the v0.2 version strings. The archived copy passes. The same thing happened to the v0 runner at v0.2.
  - **Interpretations adopted** (conservative in every case):
    1. If either compared sample cannot be generated, the samples are not identical, nothing is recorded and no flag is raised.
    2. `list` and `tuple` are never equal to each other.
    3. Object-dtype arrays use `numpy.array_equal`; an exception means not equal. "Plain bool" means `isinstance(r, bool)`.
    4. Dict methods not named in Δ1.3 (mutation, `repr`, `__ne__`, `__reversed__`, `|`) also count as "all keys read". A key is recorded before the access, even when the access raises `KeyError`.
    5. `read_keys` are converted to `str` and sorted.
    6. 0.4 Δ2 and Δ1.5 are computed independently from the same pre-suppression flag set, so a flag may appear in both `suppressed` and `suppressed_minus`. The verdict is taken after Δ1.5.
    7. The paired draw and the recording calls run after the counted samples, so stateful worlds are not disturbed. Deterministic mode reuses the stored `i = 0` minus sample.
    8. All components of a criterion share one `minus_check`.
    9. The value test inside `K2_MINUS_UNREAD` uses Δ1.2 equality.
    10. `pyproject.toml` version is 0.3.0.
    11. E5 manifest format:
        - one record per file, with `case_id`, `case_type`, `role` (faulty/fixed), `expected_verdict`, `expected_checks` and `file`;
        - exactly one faulty record per case, and at most one fixed record (T cases have none);
        - R sets keep the v0.2 format.
    12. Harness rules:
        - informational flags (`K2_MINUS_UNREAD`, `BAD_RETURN`) are dropped from expected checks before detection;
        - Q3 looks at the verdict only;
        - Q6 is "not evaluated" only with zero fixed twins;
        - the mode composition (at least 2 deterministic and 2 stochastic W pairs) is reported under `bookkeeping`, not as a criterion;
        - a T case without a fixed twin contributes one file to P4′.
    13. `run_eval_v03.py` reuses `verify_freeze`, `load_set`, `run_cases` and `_side` from `run_eval_v02.py` by import; that file is unchanged.
    14. Exit code 5 stays reserved for `verify`; code 6 is used only by `check`.
- **D4 run (2026-11-11, on 0.5-draft code; rerun by the drafting session):** 47/47 defined / reachable / covered.
  - Tests: 484 main-tree unit tests and 26 v0.3 runner tests OK. The archived v0.2 suites (328 + 18) also pass.
  - Reachable:
    - `K2_MINUS_IDENTICAL` raised and not raised in both modes, and not raised when one key changed;
    - UNTESTED in both modes, and exit code 6;
    - the verdict order (K1 > mandatory > UNTESTED > capping);
    - `K2_MINUS_UNREAD` raised and not raised, including "reads nothing", "all keys" and deterministic mode;
    - Δ1.5 suppression with and without `K2_HOLDS_UNREACHABLE`;
    - a T-type toy reaching NOT_FALSIFIABLE;
    - Q1–Q6, P4′, R1 and R2: both outcomes, plus "not evaluated", on synthetic mock tables.
  - Covered: README documents both flags, UNTESTED, `minus_check`, `suppressed_minus`, exit code 6 and the Δ5 weaknesses; the archived v0.2 tree matches its freeze record; no E5 set exists yet.
- **0.5 (2026-11-11): frozen** by the author's decision to freeze it as it stood. Only the version labels changed ("0.5-draft" → "0.5" in this header, `kapi/certificate.py`, the README and the tests that assert the label). The suites and D4 were rerun before hashing.

```

## SPEC.md, lines 502-502 (bullet `- **Why v0.3:**`)

```
- **Why v0.3:** In a retrospective pilot on converted past studies, Kapı v0.2 cleared 7 of 75 clean criteria. A case review found that 35 of the 37 clean units flagged by K2 were flagged because of how the worlds were built, not because of the criteria. One pattern is mechanically detectable: a `minus` world whose data are identical to `plus`. In one pilot study all 22 data keys of the `minus` world were bit-identical to `plus` (measured outside Kapı). v0.2 reports such a case as NOT_FALSIFIABLE, which blames the criterion for a defect of the world.
```

## SPEC.md, lines 508-508 (line `  - E5 author:`)

```
  - E5 author: the independent reviewer session.
```

## SPEC.md, lines 578-620 (section `## Δ4 — Evaluation of v0.3`)

```
## Δ4 — Evaluation of v0.3 (pre-registered; frozen with this file)

### Δ4.1 Sets
- **R (regression).** E1E3 (`CASES_SHA256.json` D012088E5128DDD5), E2 (E6EAD83AD9FC934B) and E4 (C61A4856D7AF100E), unchanged. Their v0.2 outcomes are known, so R is a regression check only.
- **E5 (new, independent; author: the independent reviewer session).** Written from the public texts only: 0.3 §1–§5 and §12, 0.4, this delta and the README. No access to the implementation. Hashed before the first run. Each case states `case_type`, the expected verdict and the expected checks. Composition:
  - **W (identical minus), at least 5 pairs.** The faulty case has a `minus` that is identical to `plus` in the sense of Δ1.1–Δ1.2: expected **UNTESTED** with `K2_MINUS_IDENTICAL`. Its fixed twin has a working `minus`: expected FALSIFIABLE or WEAK. Both modes must appear, with at least 2 deterministic and 2 stochastic pairs.
  - **U (unread change), at least 4 pairs.** `minus` changes a quantity that the faulty criterion does not read (as in E1-10): expected **NOT_FALSIFIABLE** with `K2_FAILS_UNREACHABLE` or `K2_NO_SEPARATION`, and `K2_MINUS_UNREAD`. Fixed twin: the criterion reads the changed quantity; expected FALSIFIABLE or WEAK.
  - **T (traps), at least 3 cases.** An identical `minus` combined with a criterion that is vacuous for another reason (for example it holds on noise): expected **NOT_FALSIFIABLE** with the other mandatory flag, **not** UNTESTED.
  - **N (near-identical), at least 2 pairs.** `minus` differs from `plus` only slightly or only in one key that the criterion does not read: expected **not** UNTESTED (the faulty case is NOT_FALSIFIABLE with `K2_FAILS_UNREACHABLE` or `K2_NO_SEPARATION`).

### Δ4.2 Detection and clearance
- A **W** faulty case is **detected** iff its verdict is UNTESTED and `K2_MINUS_IDENTICAL` is raised.
- A **U, T or N** faulty case is **detected** iff its verdict is NOT_FALSIFIABLE or UNDEFINED and at least one expected check is raised (0.3 §12.3). An informational flag never counts as an expected check for detection.
- A fixed twin is **cleared** iff its verdict is FALSIFIABLE or WEAK.
- R cases use the 0.3 §12.3 rule unchanged. An R faulty case that becomes UNTESTED counts as **not** detected. Such cases are also listed separately in the report, with their `minus_check`. This listing is a reporting rule only; the count does not change.

### Δ4.3 Primary criteria
- **Q1 (identical minus):** detected W / all W faulty ≥ 0.90.
- **Q2 (no masking):** every U faulty case is detected, and none is UNTESTED (rate 1.0).
- **Q3 (traps):** every T case is NOT_FALSIFIABLE or UNDEFINED and not UNTESTED (rate 1.0).
- **Q4 (exactness):** every N faulty case is detected, and none is UNTESTED (rate 1.0).
- **Q5 (informational flag):** `K2_MINUS_UNREAD` is raised on ≥ 0.80 of U faulty cases.
- **Q6 (clearance):** cleared fixed twins / all E5 fixed twins ≥ 0.90.
- **P4′ (reproducibility):** as in 0.4 Δ4.3, over R ∪ E5 (rate 1.0).
- **R1:** every R faulty case is detected (1.0). **R2:** every R fixed twin is cleared (1.0).

Each criterion is reported as Held (`Tuttu`) or Failed (`Tutmadı`) with counts. Small denominators are reported as they are. Fewer cases than the minimum for a type → that criterion is "not evaluated".

### Δ4.4 Exploratory (labelled as such; not evidence)
Exploratory re-runs on converted past studies and a listing of regression cases whose verdict changed between v0.2 and v0.3 were planned. They motivated the design, so they are not evidence and are not reported here. The retrospective pilot is summarised in `docs/EVALUATION.md`.

### Δ4.5 Procedure (drafting-session default; same discipline as 0.4 Δ4.4)
1. Archive the frozen v0.2 tree read-only and verify it against its freeze record. This lets v0.2 certificates be reproduced.
2. Implement v0.3, testing on toy studies only.
3. The drafting session reviews the code.
4. Run D4: defined / reachable / covered.
   - Reachable: `K2_MINUS_IDENTICAL` raised and not raised (both modes); UNTESTED reached; exit code 6; `K2_MINUS_UNREAD` raised and not raised (including "reads nothing" and "all keys"); Δ1.5 suppression with and without `K2_HOLDS_UNREACHABLE`; a T-type toy reaching NOT_FALSIFIABLE.
   - Q1–Q6, R1, R2 and P4′: both outcomes on synthetic mock tables.
5. The author freezes this file and the code (freeze record).
6. Send the E5 task to the independent reviewer session.
7. Hash E5.
8. Run R and E5 once, in full mode, with a new runner (`evaluation/run_eval_v03.py`). The earlier runners and archives stay untouched.

```

## Two-reader triage (designer READER1.json, fresh agent READER2.json): sentences removed

* `SPEC.md` (designer (hit 54)): - Every check is individually unit-tested (§11). Tests use only toy studies written for the tests; they must not use or imitate evaluation cases (§12).
* `SPEC.md` (designer and reader 2 (hit 55)): Reason: otherwise a criterion that ignores the changed quantity (case E1-10) would be reported as a world defect.
* `SPEC.md` (designer (hit 56)): - **Drafting-session defaults** (open to objection before the freeze): exact equality (Δ1.2), the paired draw in stochastic mode (Δ1.1), the read-key recording rules (Δ1.3), the severity position of UNTESTED and exit code 6 (Δ2), the certificate field names (Δ3), the evaluation design (Δ4).
* `SPEC.md` (reader 2 (other sentence, SPEC.md:401)): It was found in the toy `toy_no_separation` during implementation.
* `SPEC.md` (designer (hit 60) and reader 2 (other sentence)): Any regression case built this way loses its R1 detection (Δ4.2).

