# Phase D pre-registration: revisions before the freeze

## Draft 1 → draft 2 (blind review 1, 2026-11-17)

Review 1 found 2 blocking, 15 major and 7 minor problems, 24 in all. All were accepted.

**Process notes**
- The reviewer was told that nothing needed to be executed. It still ran two small scripts with the `python` on its
  path (`scratch/checks.py` for the power and threshold figures, `scratch/build.py` for the JSON). Its transcript shows
  no read outside the task folder, and the inputs were unchanged (SHA-256).
- The reviewer's flag thresholds were one count low. The gate uses `a = alpha_family / (2m)`, so the first flagged
  count of 200 is 17 (m = 1 to 2), 18 (m = 3 to 5), 19 (m = 6 to 14) and 20 (m ≥ 15). The point it supported stands.
- The designer reproduced the reviewer's H-D3 powers by simulation.

| Finding | Severity | Change in draft 2 |
|---|---|---|
| R1-1 Arm R repeats V1/V2 | blocking | V1/V2 use a seed stream disjoint from the gate's (§2.3). Arm R is a consistency check, not a ceiling (I-D4). It has at least one control (§2.2). The main question names the system of gate and world author, with the noise-probe share reported apart (§0.3). Draft 1's open decision 4 is removed. |
| R1-2 Primary endpoint defined twice | blocking | New rule: (a) the fixed twin carries no rate flag on s, and (b) Fisher p < 0.05 (§5). Draft 1's rule becomes a secondary scoring. The fixture was computed from the PC certificates and written into §5. |
| R1-3 I-D1 misdescribes V1 failures | major | V1 failures are split into V1a (faulty rate below `kstar/200`, the smallest rate the gate would flag) and V1b (§2.3). I-D1 gives both readings. |
| R1-4 W-1 clean-pass failures are not false alarms | major | Failed clean passes are classified mechanically (§5). New reading I-D5. |
| R1-5 Adoption rules, outcome map | major | One adoption rule with a clean-pass guard and a decoy guard (I-D2). An outcome table for all 8 combinations (I-D3). H-D3 is stated as pooled (§6). |
| R1-6 Checklist names the mechanisms | major | §4 says so. The claims wording for W-1 names the checklist's content (I-D6). |
| R1-7 Homogeneous batches; matching | major | 8 decoy pairs (B-1, B-6) go to both arms (§1). One shuffle, matched batches, alternated in time, and PC §4 item 3 for every agent (§3 item 8). |
| R1-8 Forking paths in repair | major | A decision table applied by the designer, with no change to claim, statistic, threshold, model or brief (§2.4). A logged validity run (§2.3). `FREEZE_VALIDITY.json` before the world authors. Reserves within subtype or tag. |
| R1-9 Reading permissions, V3 timing | major | A frozen instruction file per role with an explicit reading list (§3). Fidelity audit split into A (before the worlds) and B (after). |
| R1-10 Reference world unconstrained | major | The structure author does not see or emulate the criteria. Mechanical checks before V1. Fidelity A items on the reference world. Model line named (§2.2, §3 item 6). |
| R1-11 Attrition | major | The bar at the actual n. "Insufficient cases" below 16. 10 reserves per class. Intention to treat for H-D1/H-D2; "not comparable" for H-D3 (§1, §6). |
| R1-12 V2 at the flag threshold | major | V2 on 1000 samples, at most 0.065 on `minus` and noise, at least 0.70 on `plus` (§2.3). |
| R1-13 Sizes and timing in the W arms | major | Both arms get PC's world instructions with the new limits, and a new check script (§3 item 8). Timing measured per arm, one redo (§3 item 9). A compute budget (§3). |
| R1-14 Contamination routes | major | Sandbox, no repository fetch, URL logs checked, no context-mode cross-search, no scratchpad, transcript checks (§3 item 0). |
| R1-15 Source rules, B-3 tags | major | PC's caps scaled to 20 and the PB §4 difference rule (§1). PC's closed B-3 tag list with its precedence, used directly. PC's overlap rule (marking, the wording rule above half, tables without overlapping pairs), with no cap; see the designer changes below. |
| R1-16 Structure statistic, miss labels | major | The statistic is a function of the data keys, with direction and null value (§2.1). It must be computable on the reference world (§2.3). Miss labels (a) to (d) (§5). |
| R1-17 Power assumptions; noise probe in H-D3 | major | Power at 0.80, 0.85 and 0.90; the planning value argued; FAILS read through the intervals (§6). H-D3 counts declared attribution only. Its power is given for concordant shares 0, 0.3 and 0.5. Baselines and generic/declared labels per arm (§5). |
| R1-18 Tag mismatch | minor | `v0.5.1` throughout, with the recorded differences from `v0.5.0` (§3 item 0). |
| R1-19 Rate-flag list | minor | `K5_HOLDS_ON_NULL` added; `K2_FAILS_UNREACHABLE` on `minus`; any control stream; a missing-counts rule; the Fisher pairing note (§5). |
| R1-20 Expected flags | minor | As PC §6, enumerated per pair and per arm (`EXPECTED_FLAGS_D.json`). |
| R1-21 §0.2 overstates the audit | minor | §0.2 says "consistent with", gives the exact counts, and names the audit's limits. Decision 1 no longer cites it. |
| R1-22 Assembly unspecified | minor | Criteria are bodies (§2.1). `assemble.py` splices them and checks per arm that the twins differ only inside the body, which replaces `mech_check_twins.py`. `check_skeletons_d.py` checks the skeletons (§2.3 V3, §3, §10). |
| R1-23 Awareness confounded | minor | Checklist answers go in `CHECKLIST_LOG.md`. P/C/N is read on `WORLD_LOG.md` by arm-blind readers, with a second reading for W-1 (§4, §6). |
| R1-24 Open decisions, tools, push | minor | §9 is closed and recorded in the register. Tools and instruction files are listed as frozen with the text and go to review 2. Public push with the author's approval, and the runner check (§3 item 11). |

## Designer changes in draft 2, not from review 1

- Briefs are written by two agents per class (one per half, disjoint sources), not one agent per pair, so that the within-class difference rule can be kept. One criterion author and one structure author per class half.
- The world-instruction files carry no arm label and are both given to agents as `WORLD_INSTRUCTIONS_D.md`. A first build named the arms in a note, which would have told W-0 authors that a checklist arm exists; it was removed before any agent saw it.
- V3 is checked by `assemble.py` per arm and by fidelity part A, which replaces `mech_check_twins.py`.
- Overlap: review 1 (R1-15) proposed a hard cap of half per class. Draft 2 keeps PC's rule instead (marked, reported with and without overlapping pairs; above half, a wording rule) and adds a mitigation: brief authors get the (tag, family) combinations used before for their sources and prefer others. A hard cap would spend reserves on overlap rather than on validity.

## Draft 2 → draft 3 (review 2, 2026-11-17)

Review 2 found 0 blocking, 21 major and 15 minor problems, 36 in all, and judged the set freezable after fixes. Of
review 1's findings, 12 were fixed and 12 partly fixed; the partial ones are covered by the rows below. All 36 were
accepted.

**Process notes**
- The reviewer ran the tool tests with the allowed interpreter. Python's `tempfile` created temporary folders in the
  system temp directory and the tests deleted them; nothing else outside the task folder was touched, and the inputs
  were unchanged (SHA-256).
- The designer verified the corrected k* list and the exact H-D3 powers at n = 40 and n = 32.
- The designer re-checked the four new B-3 sources (STR87, MOR86, TU04, CHI13) in Europe PMC.

| Finding | Severity | Change |
|---|---|---|
| R2-1 Clean-pass classes circular | major | `clean_pass_class.py` classifies on 1000 fresh samples per flagged stream, with classes (e), (1), (2), (3), (4) in order (§5). I-D5 has two readings. |
| R2-2 attributable.py on load errors and hard UNDEFINED | major | Fixed in the tool, with tests on real load-error bodies; §5 states the hard-UNDEFINED reading (`hard_undefined > 0` on s). |
| R2-3 The fixture only checks a copy | major | A synthetic acceptance set, one pair per path; expected outcomes written by hand from §5 (`EXPECTED.md`); an independent recomputation by a fresh agent from §5 alone (§5). |
| R2-4 Miss labels overlap; (d) unreachable | major | An ordered list (e), (c), (a), (b), (d), with `kstar` per arm, computed by `miss_label.py` after the run (§5). (d) is "other: examined as a possible gate finding". |
| R2-5 Two adoption rules again | major | I-D2 requires that at least one of H-D1 and H-D2 holds; the outcome table follows it; "no verdict" is read as "fails"; the guards use the B-2 and B-3 pairs of H-D3 (§6, §8). |
| R2-6 The checklist names the decoys' mechanisms | major | The decoys are described as partly named by the checklist; their guard is a guard on clean pass in these decoys, not a test of genericity (§0.3, §1, §8). |
| R2-7 Decoys cannot pass validity; decoy roles missing | major | `--no-structure` for a decoy whose statistic is null; decoy criterion, structure and fidelity agents named; reserves written with the main set (§1, §2.3, §3). |
| R2-8 Shapes not checked | major | `brief.json` carries `dims`; `check_skeletons_d.py` requires the exact shape and identical shapes across the arms (§2.1, §3 item 9). |
| R2-9 Case ids leak the class | major | `shuffle_d.py` assigns neutral ids from the freeze hash; the designer keeps the map (§2.1, §3 item 2). |
| R2-10 The V1 repair rewrites the brief | major | No V1 repair: a V1 failure is a drop with its label (§2.4). |
| R2-11 Repair procedures and error rows missing | major | Repair sections in the author files (no rates in any request; "the same author" is the resumed agent, else a fresh agent of the role); new rows for errors, the statistic, and brief defects (§2.4). |
| R2-12 "Source states none" approved after validity | major | Part A0 approves the structure values before the structure authors and before any validity run (§3 item 3; `FIDELITY_AUDIT_D.md`). |
| R2-13 The structure author may check the effect | major | Rule 8 forbids estimating the effect from samples; the author no longer reads the faulty and fixed descriptions (§2.2; `STRUCTURE_AUTHOR_D.md`). |
| R2-14 Effect-dependent statistics; the band | major | The statistic is computed from parts of the data that `minus` leaves unchanged; band `|mean − value| ≤ 0.2·|value − null|`; the brief author may run its statistic on its own arrays (§2.1, §2.2). |
| R2-15 Brief authors lack the class and estimand rules | major | PB §1's decision rules, PC §2's estimand paragraph, PC's "Naming the estimand in B-3", and the B-1 and B-6 examples copied in; the `TASK.json` combinations declared as accepted exposure (`BRIEF_AUTHOR_D.md`, §1). |
| R2-16 Clauses dropped from PC's audit and author files | major | Restored: (d)'s probe clause, (e)'s banned-term check, (f) with `P2_READING_D.md`, the size list, the VAR06 note, and "does not widen it". |
| R2-17 `mech_check_twins.py` checks lost | major | New `mech_check_bodies.py` with `MECH_CHECK.json`; `assemble.py` allows only imports and function definitions at module level (§2.3). |
| R2-18 Unreviewed scripts; missing tools | major | `shuffle_d.py` (seed from the freeze hash, batches of 12), `scan_docs_d.py`, `term_check_d.py`, `expected_flags_d.py`, `clean_pass_class.py` and `miss_label.py` written and given to review 3. |
| R2-19 Timing and budget | major | A timing check at validity (stream `timing:plus`); world calls at most 250 ms; the outcome after a redo; a 60-minute run timeout; a closed budget rule (§2.3, §3). |
| R2-20 The reserve order | major | Own half first, then the other half; skip a reserve that breaks a cap; at least one reserve per subtype; minima with their consequence (§1, `ALLOCATION_D.json`). |
| R2-21 Abstract-only B-3 sources | major | The settings inventory; at most 4 slots per abstract-only source; four new sources (CHI13 full text, STR87, MOR86, TU04); ARC81 cut from 7 to 3 slots (`SOURCES_D.md`, `ALLOCATION_D.json`). |
| R2-22 Attrition | minor | Twin-specific scoring of timeouts and load errors; "not comparable" defined; a sensitivity analysis for H-D3 (§6). |
| R2-23 K4/K5 shuffle streams too broad | minor | Mapped through the certificate's bounds (the gate's rule), in §5 and in the tool. |
| R2-24 Fixture annotation; D-3 against the rule | minor | B3-04 and B3-05 annotated; the difference from D-3 stated (§0.2, §5). |
| R2-25 Which validity run counts | minor | Only `--samples 1000 --seed 20261117`; the first run on given input hashes decides; the tool refuses others on case folders (§2.3). |
| R2-26 The part-B auditor knows the arms | minor | Skeletons given under random labels X and Y (§3 item 11). |
| R2-27 Arm leak through WORLD_LOG; second reading | minor | "Do not refer to this list in WORLD_LOG.md" added to the checklist; sentences naming it are removed before the first reading; the second reading uses other readers after the first is frozen (`AWARENESS_RULE_D.md`). |
| R2-28 The structure author's reading list | minor | §2.2 matches the file. |
| R2-29 Module-level helpers | minor | One rule everywhere: only `import numpy as np` and function definitions at module level. |
| R2-30 REVISIONS errors | minor | The k* list and the R1-3 and R1-15 rows corrected. |
| R2-31 Docstring, field names, difference tables | minor | The docstring says 1000 ms; the case files are built by the designer with renamed fields and neutral ids (§2.1); the 250 ms target is in both difference tables. |
| R2-32 Freeze list | minor | The reviews, both tool specs, `P2_READING_D.md` and the `TASK.json` rule added. |
| R2-33 "Validated" | minor | I-D6 states what validity means and bans the bare word. |
| R2-34 When the structure labels run | minor | After the run; "structure not computable" defined (§5). |
| R2-35 The known part | minor | Listed in §6, with clean pass also reported without the noise stream. |
| R2-36 H-D3 power with attrition | minor | Exact powers at n = 32 added (§6). |

## Round 3: points left open by the tool author (round-2 tools, 2026-11-17)

The tool author listed eleven points where the specification left a choice. The designer decided them before any Phase D case exists:

| Point | Decision | Change |
|---|---|---|
| T3-1 Fresh interval below the size | It belongs to "possible false alarm". | §5 class (2): no flagged rate stream has a fresh interval above the size; relation recorded per stream. |
| T3-2 Which flags are relative | `K4_CONTROL_ALSO_HOLDS` and `K5_HOLDS_ON_*`; `K4_NO_CONTROL` goes to (4). `K2_LOW_POWER` alone gives WEAK, which is a clean pass (PB §6), so it only appears in combinations. | §5 class (3) names the flags. |
| T3-3 Comparisons listed by `mech_check_bodies` | A side that contains a listed call anywhere in its expression (also inside `float(...)` or arithmetic), against a numeric literal, a negated literal, arithmetic of literals, or a bare name (marked "name"). The list is for review, so over-listing is harmless. | Tool change. |
| T3-4 Randomness and decorators | PC's randomness rule is carried over: only `np.random.default_rng(<integer literal>)`, no other `np.random` attribute, no alias of `np.random` or `default_rng`. Decorators are refused anywhere. Banned names are searched in the whole tree, including decorators and default arguments. | Tool change; `CRITERION_AUTHOR_D.md` item 1 says "no decorators". |
| T3-5 Module docstring, `async def` | Refused, as the module-level rule says. | None. |
| T3-6 Miss label when the fixed twin has no verdict | (e), with the cause: a fixed load error, a fixed timeout (`--fixed-attrition CAUSE`), or no fixed certificate. The tool does not stop. | Tool change. |
| T3-7 to T3-11 | Accepted as the tool author implemented them: setup errors under `reasons["setup"]`; `--dev` refuses any path component `cases`; with no `bounds` the K4 and shuffle flags map to no stream, with the reason written; `shuffle_d` input format; `expected_flags_d` arm keys `reference`, `W0`, `W1`; `expected_flags.json` in the acceptance folders is an input. | None. |
| T3-12 Precisions from the independent recomputation | The fresh agent's notes (`recompute_d/out/NOTES.md`, 27 points) named four places where §5 left a choice open: which twin's bounds map a bounds-based flag; whether (a) counts unexpected fixed flags; what "its expected rate flags" are; and a stream missing from the fixed counts. The tool and the recomputation chose the same in each, and the text now states that choice. No outcome changes. | §5 "Precisions" list; "or has no count on s". |
| T3-13 Round-3 tool interpretations | Accepted, because each lists more cases for review or labels more conservatively:<br>• `mech_check_bodies` also counts the built-ins `min`, `max`, `all` and `any` called as `f(...)`.<br>• It refuses `default_rng(-1)`, as PC's `mech_check_twins.py` does.<br>• `miss_label` gives (e) when the fixed twin has no verdict, even if the faulty twin raised nothing.<br>• A fixed certificate with K1_UNDEFINED that has components does not give (e); the attributable rule's exclusions apply, so a PB-detected pair is labelled (c). | Tool changes as described. |

## Review 3 (draft 3 → draft 4)

Review 3 is `REVIEW3.md`: 0 blocking, 5 major, 9 minor, "freezable after fixes"; 31 of review 2's findings fixed, 5 partly fixed. The designer verified the five major findings in the code before accepting them. All fourteen were accepted. The tool changes are specified in `TOOLS_SPEC_D_round4.md`.

| Finding | Severity | Change |
|---|---|---|
| R3-1 `mech_check_bodies` lost PC's free-name, signature and call-list checks | major | Ported: free names over the whole body (a body never reads a skeleton's names), no `global`/`nonlocal`, no defaults or annotations on `criterion`, literal defaults only on helpers, PC's call list plus `isnan`, `isfinite`, `linalg.norm`, `sum`, `abs`, `len`. `assemble` refuses a body that fails the free-name check. §2.3 V3 reworded. |
| R3-2 No tool for the per-arm timing and the log check | major | `validity_check.py --arm W0\|W1` (timing only, logged); new `check_validity_log_d.py`; §3 items 7 and 10, §10. |
| R3-3 No precedence among the §2.4 rows | major | §2.4 "Precedence": a V1, V2 or timing failure without an error in its stage is final; a repair row applies only when no drop row applies; `v1_rate_label` on the error-free samples is recorded and reported. Fidelity A audits only pairs that passed validity. |
| R3-4 Fixed-twin attrition | major | §6: a fixed timeout or load error is a miss in that arm, and the pair is not comparable for H-D3. §5 (e) through the fixed twin applies only when the faulty twin is PB-detected; `miss_label.py` changed. This revises T3-13's third bullet. |
| R3-5 Class (2) not exclusive | major | §5: (2) needs the rate flags to be the only failure; otherwise (3) or (4) on the other flags, with the unconfirmed rate flags recorded. `clean_pass_class.py` changed. |
| R3-6 Missing acceptance paths; no frozen assertion | minor | Seven pairs added (20 in all), with hand-written outcomes in `EXPECTED.md` and `EXPECTED.json`; `test_acceptance_d_expected.py`; the comparison script is frozen; §5 precision "a fixed UNDEFINED verdict blocks only the streams with `hard_undefined > 0`". |
| R3-7 Batches over unused items | minor | `shuffle_d.py --subset` re-cuts the validated pairs and decoys into batches of 12; §3 item 9. |
| R3-8 `--no-structure`, direction, decisive run | minor | `--no-structure` only for B-1/B-6; direction checked against the sign of `note_value − null_value`; the log marks the decisive run; §2.3 states the `--dev` guard and the shared log. |
| R3-9 Labels (b) and (d) | minor | (b) reworded; (d) defined as a gate inconsistency; I-D3 row updated. |
| R3-10 Two meanings of "rate flag" | minor | §5 table titled "for attribution"; the clean-pass classes define their narrower term. |
| R3-11 Freeze list and provenance | minor | Fixture script and output, `recompute_d/`, the designer's scripts and outputs added to the freeze list; header note in the fixture script; `COMPARISON.md` says `RULE.md` predates the precisions. |
| R3-12 Source caps for B-2 and decoys; L1.2 reserve | minor | §1: the distinct-settings cap applies to B-3; abstract-only B-2 and decoy sources keep the 4-slot cap; an L1.2 drop in half B cannot be replaced. |
| R3-13 Numbers and wording | minor | Item numbers; "four" in `AWARENESS_RULE_D.md`; the 3-standard-error equality stated; the −2-pair rule on the pairs entering H-D3; "Phase D", "decoy", "checklist" added to `scan_docs_d.py`. |
| R3-14 Small gaps | minor | §2.4 row for `reference.py` rejected by the skeleton check; a pair failing V2 counts under V2; part A0 "(l): n/a" for a null statistic and the label "fidelity A0"; `clean_pass_class.py --attrition`. |
| R4 tool interpretations | — | Accepted as the tool author implemented them:<br>• Class names and `async def` names count as locals for the free-name check.<br>• Defaults, decorators and annotations may read only `np`, the file's functions and builtins.<br>• `check_case` separates "reads module-level name" from "undefined name" with the skeletons' names.<br>• `RESULT.json` carries `input_sha256` and `decisive`.<br>• The error-free V1 rate uses the samples where neither twin erred.<br>• `note_value = null_value` is not refused, because its band of zero makes check (a) fail.<br>• `shuffle_d --subset` needs `--force` to overwrite earlier subset batches.<br>• Acceptance pair 6 puts the fixed hard UNDEFINED on `world:null`. |

## Review 3b (verification of the review-3 fixes)

Review 3b is `REVIEW3B.md`: 0 blocking, 0 major, 8 minor. Of the review-3 findings, 10 were fixed and 4 partly fixed. The suite gave 380 of 380 passing, and all 20 acceptance pairs and 22 Phase C pairs agree. The reviewer judged the set freezable after small fixes, checked by a diff and a suite rerun, with no further full review. All eight findings were accepted. The tool changes are in `TOOLS_SPEC_D_round5.md`.

| Finding | Change |
|---|---|
| R3B-1 Free-name scoping and builtin order | Names are resolved by Python's scoping rules (one scope per function, lambda and comprehension), and the skeleton's names are tested before builtins, as in PC. The reviewer's four probe bodies are tests. |
| R3B-2 Residual V1 second chance through an error | §2.4: when the V1 stage errs on at most 5% of the samples and the label on the error-free samples is V1a or V1b, the pair is dropped with that label (`v1_final_drop_label`). Otherwise the error row applies. |
| R3B-3 Log check blind to earlier runs; free log location | The log has one fixed location, the folder that holds the case folders. `check_validity_log_d.py` lists every run of a pair, refuses an earlier final drop on other hashes, and matches earlier decisive runs against the repairs listed in `FREEZE_VALIDITY.json`. |
| R3B-4 Which per-arm timing run decides | §3 item 10: the first non-dev `--arm` run on a given skeleton and fixed-body hash decides. It is recorded in `TIMING_ARMS.json` and checked by `check_validity_log_d.py --timing-arms`. |
| R3B-5 Miss label (e) lost pair-level attrition | §5 (e) adds "or the pair is attrition in that arm (a skeleton that stays invalid, or a part-B "no")". |
| R3B-6 Stale passages | The (b) text in `miss_label.py`; the docstrings of `mech_check_bodies.py` and `check_skeletons_d.py`; the 3-standard-error rule in `STRUCTURE_AUTHOR_D.md`; the draft cited for the added `EXPECTED.md` rows; `MAP_P_ids.json` named in `COMPARISON.md`. A full validity run hashes `mech_check_bodies.py` and `check_skeletons_d.py` too. |
| R3B-7 Provenance | `fisher_hand.py` holds the two added values (5.1e-22 and 4.4e-14) and its output is regenerated. `recompute_d/` holds `MAP_P_ids.json`, `MANIFEST_recompute_d.json` and `MANIFEST_recompute_d_round4.json`. `compare_recompute.py` takes the set root as an argument; it is rerun and gives 0 differences. The fixture script takes the Phase C folder as an argument and gives the same output. |
| R3B-8 Body rules not told to criterion authors | `CRITERION_AUTHOR_D.md` item 1 states the signature, `global`/`nonlocal`, default and free-name rules. |
| R5 tool interpretations | Accepted as the tool author implemented them:<br>• The log is matched by `case == id`, where the neutral id is both the folder name and the `id` in `brief.json`.<br>• An "earlier decisive run" is one that precedes, in log order, the pair's first standard run on its own hashes.<br>• A final drop needs the failing stage to have been computed without an error, or a non-null `v1_final_drop_label`. A setup error is never a final drop.<br>• An earlier final drop cannot be cured by a listed repair.<br>• `--log` is optional but must equal the fixed path.<br>• Timing-arm records must match the logged estimate exactly.<br>• Names are resolved with one scope per function, lambda, comprehension and class body. |
