# Review 2 of spec 0.7 (Truth_Gate 0.5), DRAFT v2

Blind, targeted review. Read: `docs/design/spec-0.7.md` (v2), `spec-0.7-REVIEW1.md`, `spec-0.7-REVISIONS.md`,
`docs/SPEC.md` (sections 3, 4.1-4.3, 5, verdict cascade), `docs/design/spec-0.6.md` (patterns, command criteria),
`docs/GATE.md`, `evaluation/phase_b/REPORT.md` (5.1, 6), and `truth_gate/checks.py`, `minus.py`, `stats.py`, `k8.py`,
`passes.py`, `patterns.py`, `external.py`, `certificate.py`, `sampling.py`, `explain.py`/`cli.py`/`ci.py` (greps). I also
read the UNDEFINED counts, `errors` and flags of the ten motivating files in `evaluation/phase_b/run/certs/v040/`
(read-only). The gate was not run; no file other than this one was modified.

Counts: **0 blocking, 4 major, 8 minor** (12 findings).

---

## 1. Status of the findings of review 1

| # | Review 1 | Status in v2 |
|---|---|---|
| 1 (blocking) | Threshold rescues 1 of 10 files | Resolved by the author's decision (abstention counting). Checked: the ten 0.4.0 certificates have `errors = {}` on the K1 streams, no `BAD_RETURN` flag, one component each, `a_plus/n_plus <= 17/200 = 0.085`; so all ten are soft-only and none reaches rule 2. Their non-K1 flags (faulty: `K2_HIGH_SIZE`, `HIGH_RATE:*`; fixed: only `K4_INCONCLUSIVE`, `K5_INCONCLUSIVE:*`, `K2_LOW_POWER`) give the R2 prediction (5 NOT_FALSIFIABLE, 5 WEAK). The R2 sentence is true. |
| 2 (blocking) | Hard UNDEFINED tolerated | Resolved in the text (section 1). Whether the distinction can be computed is finding 3 below. |
| 3 (blocking) | Statistics unspecified when K1 fires | Moot and correctly so: `_component_record` computes every flag unconditionally before the verdict; nothing in `apply_cascade_suppression`, `SUPPRESSIBLE_FLAGS`, `minus.SUPPRESSIBLE_WHEN_IDENTICAL`, `add_flags_by_component` or the K8 merge reads `K1_UNDEFINED` except `component_verdict` (first test, exact string). A new flag named `K1_ABSTAINED:<s>` is not equal to `"K1_UNDEFINED"`, is not in `MANDATORY_*`/`CAPPING_*`, so the 0.4.1 cascade applies to the remaining flags as section 4 says. The assertion "cascade suppression changed a verdict" was previously masked by K1; I checked it cannot fire (K2_HOLDS_UNREACHABLE is raised whenever `plus.holds == 0` and is neither suppressible nor suppressed). |
| 4 (major) | Selective `None` hides false positives | Moot for every HOLDS-based statistic (None is exactly False in `_stats`, `sl`, `wilson_*`); not moot for K8 (finding 1) and for the 100%-abstention minus world (finding 2). |
| 5 (major) | Sensitivity analysis | Removed; correct. |
| 6 (major) | 0.05 default | Moot; the one new constant (0.5 on plus) is discussed in finding 5. |
| 7 (major) | Compatibility and R1 testable | Section 4 defines "result" and is true of the code (verified above). Remaining gaps: finding 4. |
| 8 (major) | R3 | Resolved except details in finding 9. |
| 9 (minor) | Asymmetry K1 streams / others | Resolved, but the justification is incomplete (finding 2). |
| 10, 11 | `max_undefined`, R2 label | Moot / resolved. |
| 12 (minor) | Implementation details | Partly open: informational-flag prefix registry (finding 8); the extra identical-minus call is still not stated as uncounted. |
| 13 | Names | Resolved (`_error_record` keeps the `StudyError` message only; the guard message is not recorded). |
| 14 | "Unchanged" statements | Open for K8 (finding 1). |
| 15 | Docs | Resolved; one inaccurate sentence (finding 8). |

---

## 2. Classification of every UNDEFINED path in the code

| Path | Class | Where it is observable today |
|---|---|---|
| `fn` returns `None` (single component) | soft | not recorded: outcome is the string `UNDEFINED`, `error` is None |
| `components` declared, whole return `None` | soft | same |
| `components`, dict value `None` | soft | same |
| `components`, declared key missing from the dict | hard | **not distinguishable** from a `None` value (`outcomes[cid] = UNDEFINED`, no error, not in `bad`) |
| `components`, non-dict return | hard (BAD_RETURN) | `bad_return` is a set of cids over all streams and indices; stream and index are lost |
| wrong value type (single or inside the dict; `float('nan')`, `1`, a string, an array) | hard (BAD_RETURN) | same |
| exception in `fn` (incl. leak-guard `PermissionError`) | hard | `errors[stream][cid][name]`, counted for `i < n_counted` |
| exception in or invalid output of `generate` (plus, minus, null) | hard | same (`Sample.error`); `plus` failure also makes derived streams hard, irrelevant to K1 |
| pattern: empty selection, non-finite value, zero denominator, **"the types do not fit"** | soft (returned as `None` by `Pattern.fn`) | as `None` |
| pattern: missing key (`KeyError`) or any non-`NotApplicable` exception | hard | `errors` |
| command: `"UNDEFINED"` outcome | soft | as `None` |
| command: `{"error"}` (`ExternalError`), `ExternalTimeout`, `ExternalProtocolError`, `ExternalDied` (including every later request), `ExternalEncodingError` | hard | `errors` |
| command: outcome string other than the three (`InvalidOutcome`) | hard (BAD_RETURN) | `bad_return` |

Every path has a class, but two are not computable from what `collect()` stores today (finding 3).

---

## Major

### 1. K8 leaves UNDEFINED pairs out of its counts, so "nothing is left out of any count" is false and abstention can hide a K8 failure (major)

Passage (2.2): "Nothing is left out of any count, so there is no selection effect"; "K8 ... unchanged"; review-1 finding 14 marked
"moot (no counting change)".

Reason. `k8._tally` puts a pair with an UNDEFINED side in `undefined`, and `_finish` computes `defined = pairs - undefined` and
`wilson_lower(changes, defined, level)`. A transformation that must not change the outcome but turns `HOLDS` into `None`
(or `None` into `HOLDS`) is a violation that is left out. In 0.4.1 the after-side exposure existed; the before-side did not,
because a `None` on a `plus`/`minus` sample (the before outcome is the K1 stream outcome at the same index, regenerated with the
same seeds) already made the component UNDEFINED. In 0.5 a component may abstain on up to half the plus samples and any number
of minus samples and still reach K8, where those pairs are excluded; only `K8_INCONCLUSIVE` (more than 50% of pairs, capping)
limits it. So up to half of the pairs of a world can hide a non-invariant criterion. Also in deterministic mode an abstention
on `minus` makes every pair of the `minus` world undefined: `K8_INCONCLUSIVE`, verdict WEAK whenever an invariance is declared;
section 2.3 says only `K1_ABSTAINED`.

Fix (choose one, state it):
* (a) Keep K8 as it is, correct the sentence ("K1-K5 and every flag that counts over `n` keep None as not-HOLDS; K8 excludes
  pairs with an UNDEFINED side as in 0.4, a new exposure for abstentions on the before side, bounded by `K8_INCONCLUSIVE`"), add
  the deterministic K8 consequence to 2.3, and add a test (abstains on 40% of pairs, changes on the rest: record what happens).
* (b) Count a pair with exactly one UNDEFINED side as a change when that side is a soft UNDEFINED on the **before** outcome (the
  new exposure only). This changes K8 flags only in components that 0.4.1 made UNDEFINED, so section 4 bullet 3 must list it.
  Option (a) is enough for a freeze if the limitation is stated.

### 2. No rate limit on abstention on `minus` and `null`: a broken world reads as a clean pass (major, needs the author's decision)

Passage (2.2, "Asymmetry with the probes, accepted"): "On the K1 streams an abstention is a legitimate outcome of the study's
own analysis."

Reason. For the probes the gate says "a criterion that abstains on noise has not shown that it fails there" and caps at WEAK
above 50%. The same sentence is true of `minus` and `null`, and for them nothing happens at any rate. K1 was the only detector of
a defective minus or null generator whose data make the criterion return `None`: a generator emitting NaN or Inf (zero
variance divided by zero), an array of the wrong dtype ("the types do not fit" is soft by `patterns.py`), a selection that is
always empty. With 100% abstention on `minus`: `minus.holds = 0`, `K2_FAILS_UNREACHABLE` not raised, `K2_NO_SEPARATION` not raised,
`K2_HIGH_SIZE` not raised, and the only trace is the information flag. The component can be FALSIFIABLE although the criterion was
never evaluated where the claim is false. B1-04 and B1-05 show that 85% abstention is also a real property of correct guards, so
the decision is about the threshold, not about the principle.

Fix. Add a capping flag for `2 * a_s > n_s` on `world:minus` and `world:null` (name e.g. `K1_ABSTAINED_MAJORITY:<s>`, same rule as
K3-K5; in deterministic mode an abstention on minus/null is a rate of 1, as `K5_INCONCLUSIVE` is for a deterministic probe).
Effect on the development data, checked from the 0.4.0 certificates: none. The faulty files with more than half abstention
(B1-04, B1-05) already have mandatory flags; the fixed ones (B1-04, B1-05) already have `K4_INCONCLUSIVE`, so the R2 prediction
does not move. Section 4 bullet 3 then reads "... and `K1_ABSTAINED_MAJORITY:<s>` for a stream with more than half abstentions".
If the author prefers to accept the hole, say so in 2.2 with this example, add a test that records the verdict of a 100%-abstaining
minus world, and add it to `known_limitations`.

### 3. The soft/hard split cannot be computed from what the engine records; the spec does not say what must change (major)

Passage (1, 2.4): "`counts` gains `hard_undefined`"; "a declared component missing from a returned dict" is hard.

Reason. See table 2. `collect()` keeps one string per (stream, component, index); the exception case is in `errors`
(counted for `i < n_counted`), but `BAD_RETURN` is a global per-component set (`bad_return |= bad`) and a missing component and a
`None` value give identical records. An implementer who counts hard outcomes from `errors` alone will classify BAD_RETURN and
missing components as soft, silently opening exactly the hole review 1 finding 2 described, for the case "criterion returns `np.nan`"
(the common way of writing "undefined"). In deterministic mode the counting must use index 0 only (the outcome list holds three
indices; `_stats` slices `[:n]`).

Fix. Add to section 2.4: "`collect` records a kind (`soft`, `hard`) with every UNDEFINED outcome per stream, component and index;
`hard_undefined` counts the first `n_counted` indices, so `holds + undefined <= n` and `hard_undefined <= undefined` for every
stream (certificate validation checks it)". Say that `errors` gains the keys `BAD_RETURN` and `MISSING_COMPONENT` (names recorded,
no message), so that the exception counts, BAD_RETURN and missing components add up to `hard_undefined`. Tests: one per row of
table 2, run in stochastic and deterministic mode.

### 4. R1 as written is circular and under-specified (major)

Passage (6, R1): "every component of 0.5.0 satisfies section 4 against 0.4.1".

Reason. Section 4 splits components by `hard_undefined`, which only 0.5.0 produces, so R1 classifies with the code it tests. The
0.4.1 recording cannot give the split exactly (missing components are not recorded; BAD_RETURN is a component-wide flag). The
mode (full or quick) and the way the set is frozen (the recording file and its SHA-256, the comparison script) are not stated; the
frozen 0.4.1 baseline for the 159 Phase A studies does not exist yet (`evaluation/baseline_v030` is a 0.3.0 baseline).

Fix. State an oracle computed from the 0.4.1 certificate only: let `E` = the sum over the K1 streams of the `errors` counts; a
component with `u_s > 0` on a K1 stream, no `BAD_RETURN` flag and no `K7_COMPONENT_MISMATCH` involving it must have
`hard_undefined == E` in 0.5.0 exactly, and then bullets 2/3 of section 4 are decided by `E` and `u_plus`; components with
`BAD_RETURN` or a mismatch are a separate reported group (0.5.0's `hard_undefined >= E`, and `u_s - hard_undefined` must be the
number of `None` returns, checked on a hand-built set). Freeze the recording (`evaluation/phase_c`-style path, SHA-256 in the
prereg), the comparison script and the mode (full, as Phase B ran). Say that no study in the regression set may be expected
to contain a hard BAD_RETURN or missing component, which is why section 5 carries the per-cause tests.

---

## Minor

### 5. Plus rule: a cliff to the most severe verdict, and an integer form (minor)

Passage (2.1 rule 2): "`a_plus / n_plus > 0.5` ... the same point-rate threshold as the inconclusive rules of K3, K4 and K5".

Reason. For K3-K5 the cliff separates FALSIFIABLE from WEAK. Here it separates WEAK (50% abstention gives `K2_LOW_POWER` at
the default power 0.8, because `holds <= n/2`) from UNDEFINED, exit 3, the most severe verdict, for the same behaviour that is
"no claim" on `minus`. With a declared `targets.power <= 0.5` (allowed: `0 < power <= 1`) 50% abstention on plus is clean. Also
write the test as `2 * a_plus > n_plus` (integers), as `StreamStats.inconclusive` does.

Fix. Either state why UNDEFINED is intended (the criterion makes no claim where the claim is true; 0.4.1 behaviour kept for
compatibility) or make it a capping flag like finding 2 (this would change section 4 bullet 2). Use the integer form in the text.

### 6. The soft class contains wiring defects, and the hard class is bypassable by `try/except` (minor)

Reason. By `patterns.py` (and spec 0.6 section 4) "a value is not finite", "the types do not fit" are soft, so a generator that
emits NaN or the wrong dtype in `minus` or `null` is soft (finding 2 treats the consequence). A Python criterion that wraps its
body in `try/except Exception: return None` turns every hard failure into a soft one; this cannot be detected and changes nothing
statistically (None is False), but the spec should say that hard means "unhandled by the criterion". For command criteria the
class depends on the wrapper: the reference `tg_line.js` answers `{"error"}` for a caught exception (hard), a wrapper that
answers `"UNDEFINED"` for it makes it soft. Section 1's command list also repeats one item (`{"error": ...}` is `ExternalError`)
and omits `ExternalEncodingError` and an invalid outcome string (BAD_RETURN).

Fix. One sentence on each, and the protocol text states that an uncaught exception must be answered with `error`.

### 7. `K1_UNDEFINED` now has two causes and one name (minor)

Reason. A component UNDEFINED by a hard failure and one UNDEFINED because plus abstains more than half look identical in the
flag list; the user guidance of 2.5 treats them differently.

Fix. `explain K1_UNDEFINED` and the certificate state which rule fired, derivable from `counts` (`hard_undefined > 0` on a K1
stream, else plus majority); say so in 2.4 and test it.

### 8. Informational-flag mechanics and one inaccurate sentence (minor)

Reason. `INFORMATIONAL_FLAGS` is an exact-name frozenset and `explain.py:243` tests membership by name; `K1_ABSTAINED:world:minus`
needs a prefix entry (like `CAPPING_PREFIXES`) and an `explain` branch for the two-colon key. The revisions table says the
prefix is "handled by the name"; it is not. Section 2.4 "the CLI table and the CI summary print the information flags": both
already print every component flag (`cli.py:88`, `ci.py:135`), so this describes existing behaviour, not a change. The extra
identical-minus recording call (review 1, finding 12) is still not stated as uncounted.

Fix. Add the prefix registry and the `explain` branch to 2.5 and the tests; reword the CLI sentence ("no change needed; tested");
state that the identical-minus analysis calls are not counted.

### 9. R3 details that a pre-registration must fix now (minor)

Reason, one item each.
* "new briefs only: written by fresh criterion-author agents": in Phase B briefs, criteria, worlds and audits had different
  authors; say who writes the briefs and who the criteria.
* Which gate documentation the criterion authors read (0.4.1 or 0.5.0): the 0.5 guidance ("return `None` when there is nothing to
  claim", 2.5) changes how they write guards, which is the only thing the primary comparison measures. Fix it in the instruction
  text with the guard rules.
* The Phase B source list reused with new briefs gives overlapping errors; say that overlap with Phase B briefs is reported and
  that such cases are flagged in the table.
* The primary comparison has no decision rule: what counts against 0.5 (for example any fixed twin that is NOT_FALSIFIABLE under
  0.5.0 and not under 0.4.1) and what is merely reported. "No change" is covered; "a new false alarm" is not.
* The model id and run dates of Fable and the 0.5.0 build hash (not only the version) go into the record.

### 10. R2: freeze the prediction as data (minor)

Reason. The R2 text says the effect "was computed before freezing"; the computation is two lines over the certificates (I
reproduced it). Freeze it as a file (component, expected verdict, expected flags, SHA-256) so that R2 compares against a frozen
artefact. State that 0.4.0 and 0.4.1 certificates agree on these files (CHANGELOG 0.4.1: "no change to verdicts, flags, counts").

### 11. Tests missing from section 5 (minor)

* **Metamorphic None = False test:** for each fixture, replace every `None` by `False` in the criterion; every flag that is not
  `K1_*`, `K3/K4/K5_INCONCLUSIVE`, `K8_*` and the verdict implied by them must be identical, in stochastic and deterministic mode.
  This tests the soundness argument of 2.2 directly; the three listed gaming tests only test single cases, and the first reads
  ambiguously ("holds in 30% of minus samples and returns None on half of them": say 15% overall).
* Abstention on `plus` of 40% with 60% FAILS: NOT_FALSIFIABLE with `K2_HOLDS_UNREACHABLE` (pins the cascade assertion).
* Command criterion with components: one component `"UNDEFINED"` (soft), one missing (hard).
* K8 with abstention (finding 1) and the deterministic minus abstention with an invariance declared.
* Quick mode (n = 20): boundary 10 vs 11.
* Identical-minus study with abstentions: UNTESTED, not UNDEFINED.

### 12. User-visible severity changes should be listed (minor)

Reason. A component can move from UNDEFINED (exit 3, in the default `fail-on`) to WEAK or FALSIFIABLE (not in it). That is the
intended effect, but section 2.5 and the CHANGELOG should say "CI jobs that failed on UNDEFINED because of a guard may now pass"
and that a fixed criterion with a guard is now judged by its other flags.

---

## Gaming argument of 2.2: result of the attempt to break it

* The argument is sound for every HOLDS-count statistic: `None` and `False` are the same in `_stats`, `sl`, `wilson_*`, K2, K2_FAILS_UNREACHABLE (`holds == n`), HIGH_RATE, K3-K5 SL parts and the premise map; the only differences are the inconclusive caps (where `None` is worse for the author), K1 (the subject), K8 (finding 1) and the stored `fails`. `StreamStats.fails` is not read by any check.
* `None` on probes versus K1 streams: no advantage; abstention on a probe lowers its HOLDS rate like False and above 50% caps.
* `None` on plus to dodge `K2_HOLDS_UNREACHABLE` or its suppression: impossible; `K2_HOLDS_UNREACHABLE` needs `plus.holds == 0`, is mandatory and is never suppressed, and abstention can only lower plus HOLDS. With 1-50% abstention and no HOLDS the verdict is NOT_FALSIFIABLE (was UNDEFINED), and the cascade assertion holds.
* Identical-minus: the analysis reads the criterion's keys and the two samples, never outcomes; with abstentions the verdict can be UNTESTED where 0.4.1 gave UNDEFINED (covered by section 4 bullet 3).
* Components dicts: each component is classified separately; a whole-`None` return is soft for every component; a missing key is hard for that component only.
* Regimes: K7_REGIME_UNCOVERED depends on declared criteria, not on outcomes; unchanged.
* Remaining holes: K8 (finding 1) and abstention on a broken minus/null world (finding 2).

## Verdict

**Freeze after these fixes.** No blocking finding; the main design (soft/hard, abstention counted as not-HOLDS, statistics
unchanged, exact compatibility) is correct against the code as it stands, including the cascade, the suppressions, the
deterministic SL rule and the claim that every flag is computed when K1 fires. Required before the freeze: findings 1 to 4
(finding 2 needs the author's choice between the cap and an explicit accepted limitation; either choice is a text change), plus
the corrections of findings 5 to 8 and the R3 details of 9. Findings 10 to 12 can be done in the same edit. Because the edit
touches sections 2.1, 2.3, 2.4, 4 and 5, the designer should re-check section 4 bullet by bullet against it; a third full
review is not needed.
