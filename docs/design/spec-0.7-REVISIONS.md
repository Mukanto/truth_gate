# Revisions to spec 0.7

Decisions by Claude under the author's delegation, except where the author decided.

## Draft v1 → v2 (2026-11-13), answering `spec-0.7-REVIEW1.md`

| # | Finding (severity) | Change |
|---|---|---|
| 1 | The threshold rescues 1 of 10 motivating files; exclusion biases the rest (blocking) | Put to the author with the reviewer's table. **The author chose abstention counting**: a deliberate `None` counts as not-HOLDS (no claim) on the K1 streams; nothing is left out of a count; `Targets.max_undefined` is dropped. Section 0 records the history; section 6 R2 states the computed development effect. |
| 2 | Hard UNDEFINED outcomes would become tolerated (blocking) | Section 1 defines soft (deliberate) and hard (failure) UNDEFINED; any hard UNDEFINED on a K1 stream keeps 0.4's K1; `counts[stream].hard_undefined` recorded; one test per cause. The GATE.md `EXTERNAL_DIED` guarantee stays true. |
| 3 | Statistics unspecified when K1 fires; R1 not meetable (blocking) | Moot: statistics never change (section 2.2); section 4 states the exact relation between 0.4.1 and 0.5.0 results. |
| 4 | Selective `None` can hide false positives (major) | Moot under abstention counting: `None` on `minus`/`null` counts as not-HOLDS, the same as `False`; on `plus` it can only lower power (section 2.2, "Why abstention cannot hide a false positive"). Gaming tests added to section 5, written before the code. |
| 5 | Sensitivity analysis underspecified (major) | Removed: with nothing left out there is nothing to be sensitive to (decision 4). |
| 6 | The 0.05 default not justified (major) | Moot: no configurable threshold; the only threshold is "abstains on more than half of `plus`", the existing inconclusive point rate (decision 2). |
| 7 | Compatibility and R1 not testable (major) | Section 4 defines "result", the ignored fields and the exact three-way relation; R1 tests it against frozen 0.4.1 recordings; no override knob is needed; deterministic studies reported separately. |
| 8 | R3 and the Fable claim (major) | Phase C uses **new briefs only** (decided here); Fable's vendor and family stated; model id and dates recorded; guard instructions fixed in advance; primary comparison 0.5.0 vs 0.4.1 with "no change" reported as such; allowed and disallowed claims listed; no setting other than the defaults. A separate adversarial test set is section 5's gaming tests. |
| 9 | Asymmetry between K1 streams and probes (minor) | Section 2.2 states and justifies it. |
| 10 | `max_undefined` value handling (minor) | Moot (no such target). |
| 11 | R2 label and expectation (minor) | R2 says the rule was chosen after the cases were seen, gives the computed effect, and says that R2 checks the implementation, not the rule. |
| 12 | Implementation details (minor) | `K2_FAILS_UNREACHABLE` named as in the code; information-flag prefix handled by the name `K1_ABSTAINED:<stream>` (no prefix clash with `K1_UNDEFINED`); counts stay raw. |
| 13 | Section 3's reason partly wrong (minor) | Corrected: only the `StudyError` text reaches certificates; the guard message is seen in tracebacks. Stated as independent of section 2. |
| 14 | Statements marked unchanged that change (minor) | Moot for the premise map and K8 (no counting change); deterministic and quick modes stated in 2.3, including the deterministic `minus` abstention that changes from K1 to `K1_ABSTAINED`. |
| 15 | Documentation and user-visible effects (minor) | Section 2.4 (CLI and CI print information flags) and 2.5 (GATE.md, MANIFEST.md, explain, user guidance); spec/package numbering explained in the status line. |

## Draft v2 → v3, for freeze (2026-11-13), answering `spec-0.7-REVIEW2.md` (0 blocking, 4 major, 8 minor)

| # | Finding (severity) | Change |
|---|---|---|
| 1 | K8 leaves UNDEFINED pairs out; abstention can hide K8 changes (major) | Option (a): K8 keeps its 0.4 rule; section 2.2 states the limitation (up to half of the pairs; deterministic consequence `K8_INCONCLUSIVE`), `known_limitations` gains a sentence, section 5 a test that records the behaviour. The sentence "nothing is left out of any count" is restricted to the HOLDS-based statistics. |
| 2 | No limit on abstention on `minus`/`null`; a broken world reads as a clean pass (major, author's choice) | Decided under delegation in the spirit of the author's rule that high UNDEFINED rates must not pass silently: capping flag `K1_ABSTAINED_MAJORITY:<s>` for `2 * a_s > n_s` on `minus` and `null` (rule 2.1(3)); deterministic abstention on these streams caps at WEAK. Effect on the development data: none on verdicts (checked; it appears on B1-04 and B1-05, whose verdicts are already NOT_FALSIFIABLE or WEAK). |
| 3 | Soft/hard split not computable from today's records (major) | Section 2.4: `collect` records the kind of every UNDEFINED outcome; `hard_undefined` over the counted indices; validation invariants; `errors` gains `BAD_RETURN` and `MISSING_COMPONENT` counts; per-cause tests in both modes (section 5). |
| 4 | R1 circular and under-specified (major) | New R0: the regression set recorded with tag `v0.4.1` (full mode) and frozen before any code change, with the comparison script. R1 classifies from the 0.4.1 certificate only (`E`, `u_plus`), requires `hard_undefined == E`, reports BAD_RETURN/mismatch components separately. |
| 5 | Plus rule: cliff to UNDEFINED; integer form (minor) | Kept as UNDEFINED (the author's rule; the criterion is not a test of the claim where the claim is true), reason stated; written as `2 * a_plus > n_plus`. |
| 6 | Wiring defects in the soft class; `try/except` bypass (minor) | Section 1: hard means unhandled; the bypass is stated and discouraged; the command list completed (`ExternalEncodingError`, invalid outcome string); the protocol states that uncaught exceptions are answered with `error`. `K1_ABSTAINED_MAJORITY` covers the NaN/dtype minus world. |
| 7 | `K1_UNDEFINED` has two causes (minor) | Section 2.1: the cause is derivable from `counts`; `explain K1_UNDEFINED` explains both; tested. |
| 8 | Informational-flag mechanics; CLI sentence; identical-minus calls (minor) | Section 2.5: prefix registries and `explain` branch; 2.4: CLI/CI already print all flags (tested, no change); 2.2: identical-minus recording calls are not counted. The v2 revisions line claiming the prefix was "handled by the name" was wrong. |
| 9 | R3 details (minor) | R3: who writes briefs and criteria (fresh Sonnet criterion authors per class), which documentation they read (0.5.0) and which guard rules, overlap with Phase B flagged, decision rule (any lost 0.4.1 detection or clean pass counts against 0.5; hidden misses and false alarms reported by name), Fable model id, run dates and the 0.5.0 commit recorded. |
| 10 | Freeze the R2 prediction as data (minor) | `spec-0.7-R2-prediction.json` (ten components, expected verdicts and flags), frozen with the spec; 0.4.0/0.4.1 agreement recorded by R0. |
| 11 | Tests missing (minor) | Section 5: metamorphic None = False test (G), the gaming cases made precise (G), plus-abstention 40%/60%, command components, K8 cases, quick-mode boundary, identical-minus with abstentions. |
| 12 | User-visible severity changes (minor) | Section 2.5: CHANGELOG and GATE.md say that guarded components move from UNDEFINED to their other flags' verdict and that CI jobs may change outcome. |

Designer's check of section 4 after the edit, item by item: (1) no UNDEFINED on a K1 stream → no K1 rule fires, no
`K1_ABSTAINED*` flag, statistics unchanged → same result; (2) rule 1 fires → `K1_UNDEFINED`, rules 2–3 do not apply
("otherwise") → same result; (3) soft only, at most half of `plus` → flags = 0.4.1 flags − `K1_UNDEFINED` +
`K1_ABSTAINED:<s>` + `K1_ABSTAINED_MAJORITY:<s>` where applicable, counts and bounds unchanged; (4) study level unchanged.
