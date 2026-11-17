# Review 3b: verification of the review-3 fixes (Phase D pre-registration, draft 4)

Reviewer: an independent agent working only from `E:\Independent\tasks\phase_d_review3b\`. I did not write the
pre-registration, the tools or any earlier review.

What I did:
- Read review 3, the draft 3 → draft 4 diff (line endings normalised), the "Review 3" and "R4 tool interpretations" rows
  of `REVISIONS_D.md`, `TOOLS_SPEC_D_round4.md`, every `# D-R4-` line in `phase_d/tools/tools/` (and the functions
  around them), the new `check_validity_log_d.py`, the new and changed tests, the acceptance `README.md`, `EXPECTED.md`
  and `EXPECTED.json`, `recompute_d/COMPARISON.md`, `recompute_d/round4/`, `MAP_P_ids.json`, the two designer scripts
  and their outputs, and the instruction files where a fix touches them.
- Compared the ported checks with Phase C's `repo/evaluation/phase_c/tools/mech_check_twins.py` and the gate's
  `repo/truth_gate/checks.py`.
- Ran the full suite with the allowed interpreter from `scratch/tools` (`KAPI_PACKAGE_ROOT` = the task's `repo`,
  `TMP`/`TEMP` in `scratch/tmp`): **380 tests, 380 pass, 0 fail** (80 s). No `__pycache__` left.
- Recomputed all 20 acceptance pairs from draft 4 §5 with my own script (`scratch/my_recompute.py`, exact hypergeometric
  Fisher, no use of `attributable.py`), and re-derived every synthetic certificate's flags, verdict, m and bounds with the
  gate's own check functions (output `scratch/my_recompute_output.txt`).
- Ran my rule, the agent's `RESULTS.json` and the tool on the 22 Phase C pairs (`scratch/probe_misc.py`).
- Probed the new free-name check (`scratch/probe_free_names.py`) and the new log check (`scratch/probe_misc.py`).

Inputs were not modified.

## Counts of new findings

| Severity | Count |
|---|---|
| blocking | 0 |
| major | 0 |
| minor | 8 |
| total | 8 |

## New findings

### R3B-1 (minor): the free-name check still passes bodies that read skeleton names

- **File and passage.**
  - `phase_d/tools/tools/mech_check_bodies.py`, `local_names`: "Parameters and every name bound anywhere inside ``fn``
    (flat, nested functions and lambdas included)."
  - `free_name_issues`: `if x.id not in loc and x.id not in allowed_module and not hasattr(builtins, x.id):`
  - Draft 4 §2.3 V3: "the free names (a body reads only its own locals and functions, `np` and builtins, never a
    skeleton's names)".
- **Reason.** Two routes stay open. I checked each with `scratch/probe_free_names.py`. The probe skeleton is the toy
  reference plus `THRESHOLD = 0.9` and a module-level `def max(*a): return 99`. All four bodies get no name issue from
  `check_body` and are accepted by `assemble`, and the assembled criterion reads the skeleton's value:
  1. **Scope.** `local_names` is flat over the whole function, so a name bound only in an inner scope counts as a
     local of the outer function. Python resolves such a name in the outer function as a global, that is, from the
     skeleton. Three cases:
     - a comprehension variable used after the comprehension (`[N for N in range(3)]`, then `N`): this read the
       skeleton's `N = 300`;
     - a name bound only inside a nested function;
     - a name bound only as a lambda parameter (`lambda THRESHOLD: ...`).

     The last two read the skeleton's `THRESHOLD`. Phase C's `local_names` has the same flat logic, so this gap is
     inherited.
  2. **Shadowed builtins.** A body may call a builtin (`max`, `sum`, `len`, `abs`, `round`, ...) that a skeleton redefines
     at module level. The builtin test comes first, so `skeleton_names` is never consulted. Phase C's `check_body`
     tested `x.id in modnames` *before* the builtin test, so this is a deviation from the port. In the probe,
     `max(1, 2) > 50` returned `True` through the skeleton's `max`.

  This is the arm-specific behaviour R3-1 was about. A W-0 or W-1 skeleton is written after validity by a different
  agent, so one body can behave differently in R, W-0 and W-1 while the per-arm single-difference check still passes. An
  accidental trigger is uncommon, but the frozen text states an absolute guarantee that the tool does not give.
- **Fix.**
  - In `free_name_issues`, resolve names by Python's scoping rules, not by a flat set. Either use the `symtable` module
    (every symbol of a function, lambda or comprehension scope that resolves as global must be a module-level function
    of the body, `np` or a builtin), or write an AST pass that treats each function, lambda and comprehension as its own
    scope and resolves a load to the innermost scope that binds it.
  - Test `x.id in skeleton_names` before the builtin test, as `mech_check_twins.check_body` lines 188–191 do. A body
    that loads a builtin name that the skeleton defines is then "reads module-level name".
  - Add the four probe bodies as tests, both for `check_body` and for `assemble`.

### R3B-2 (minor): an error in the V1 stage still opens a second V1 draw for a pair whose error-free rate fails V1

- **File and passage.** Draft 4 §2.4: "When the V1 stage errs, the tool still records the V1 rate on the samples without
  error and the label it would give (`v1_rate_label`); it is reported next to the result after the repair."
  `validity_check.py`: `if fe or xe: result["v1"], result["reasons"]["v1"] = False, "error"`.
- **Reason.** The precedence rule closes the cross-row route of R3-3, but one exception in 1000 `minus` samples still
  sends the pair to the error-repair row. This holds even when `v1_rate_label` is V1a or V1b, that is, when the faulty
  rate on the other 999 samples already fails V1.
  - After a body repair, V1 is computed again on the same samples, with changed bodies.
  - After a `reference.py` repair (a failed generation), V1 is computed on new samples.

  Either way, a pair that would have been dropped can pass, and the text only requires that the earlier label be
  reported. The repair author sees no rate, so the risk is small, but it is the forking path that R2-10 removed. The
  text does not say whether such a pair is reported anywhere other than "next to the result".
- **Fix.** Pick one, and write it into §2.4.
  - (a) "If the V1 stage errs on at most 5 % of the samples and `v1_rate_label` is V1a or V1b, the pair is dropped with
    that label; otherwise the error row applies."
  - (b) Keep the repair, but count such pairs separately in the drop table ("passed V1 after an error repair whose
    `v1_rate_label` was V1a/V1b"), list them under I-D1 and I-D4, and record `v1_rate_label` in `FREEZE_VALIDITY.json`.

### R3B-3 (minor): the log check cannot see a re-run on changed files, and the log location is free

- **File and passage.**
  - `check_validity_log_d.py`: the candidate runs are
    `standard = [e for e in entries if is_standard_entry(e) and isinstance(e.get("sha256"), dict) and {n: e["sha256"].get(n) for n in INPUT_FILES} == want]`.
  - Docstring: "``first_is_decisive``: the first such run in the log has ``"decisive": true``".
  - Draft 4 §2.3: "`tools/check_validity_log_d.py` confirms, for every pair of `FREEZE_VALIDITY.json`, that its result
    is the decisive logged run on the current input hashes."
  - §2.4: "Every run, repair, drop and substitution is frozen in `FREEZE_VALIDITY.json`".
- **Reason.**
  - "Decisive" is defined per set of five hashes, and the check looks only at runs with the cited hashes.
  - **The probe.** In `scratch/probe_misc.py` the log holds two runs of case D-001. The first is decisive, on hashes
    H1, with a final V1b drop. The second is decisive, on hashes H2 after an unlogged edit of `reference.py`, and passes.
    A freeze that cites the second run passes all five checks.
  - So the tool does not detect the one thing "first run decides" is meant to stop: a changed file after a final drop,
    with no repair recorded.
  - Also, `validity_check.py` fixes only the log's base name (`os.path.basename(a.log) != LOG_NAME`). Two
    `validity_log.jsonl` files in different folders would each make every first run "decisive".
- **Fix.**
  - In `check_validity_log_d.py`, for each pair, list every standard run whose `case` equals the id, in log order.
  - Refuse the pair when an earlier decisive run on other hashes has a V1, V2 or timing failure computed without an
    error in that stage (a final drop under §2.4 Precedence).
  - Refuse the pair when the number of earlier decisive runs exceeds the repairs recorded for it. To make this
    possible, give `FREEZE_VALIDITY.json` a `repairs` list per pair, with the file and the row.
  - Fix the log location to `<parent of the case folder>/validity_log.jsonl`, in both tools, and have the check read
    `<cases>/validity_log.jsonl`.
  - Add a test with the probe log.

### R3B-4 (minor): the per-arm timing has no "first run decides"

- **File and passage.**
  - Draft 4 §3 item 10: "measured on each arm's skeleton with `tools/validity_check.py --arm W0|W1` (… logged with the
    hashes). A skeleton whose estimate is above 30 minutes goes back once to a fresh agent of that arm."
  - `validity_check.py` docstring: "``--dev`` runs and ``timing_arm`` runs carry no ``decisive`` field." and "(The
    estimate depends on the machine's clock; it is the only field that is not reproducible.)"
- **Reason.**
  - The per-arm estimate decides an arm-specific redo by a fresh world author (H-D3) and enters the compute-budget
    rule.
  - It is not reproducible, so repeated `--arm` runs on the same skeleton give different numbers.
  - Nothing says which run counts, and `check_validity_log_d.py` ignores `timing_arm` runs.
- **Fix.**
  - In §3 item 10 write: "The first non-dev `--arm` run on a given skeleton and fixed-body hash decides."
  - Mark that run `"decisive": true` in the log, and later runs `false`, as for validity runs.
  - Have `check_validity_log_d.py` (with a `--timing` option, or by default) confirm that every redo decision and every
    budget estimate cites the decisive timing run.

### R3B-5 (minor): the new wording of miss label (e) leaves out pair-level attrition

- **File and passage.**
  - Draft 4 §5, miss labels: "**(e) attrition or no verdict**, with the cause: the faulty twin left no verdict, or the
    faulty twin is PB-detected and the fixed twin left no result (load error, timeout, no certificate)."
  - §6: "A skeleton that stays invalid, or a part-B "no", counts as a miss and a failed clean pass in that arm."
  - `miss_label.py`: "``--attrition CAUSE`` was given (an invalid skeleton, a part-B "no", a timeout, a load error
    recorded by the runner)".
- **Reason.**
  - Draft 3 said only "(e) attrition or no verdict, with the cause". Draft 4 enumerates the causes, but the list covers
    only twin-level ones.
  - A part-B "no" pair, whose faulty twin may have run and have a verdict, is (e) in the tool and in §6. It is not (e)
    under the frozen §5 text, which would send it to (c), (a), (b) or (d).
  - The clean-pass (e) in the same section does list "a skeleton that stays invalid, or a part-B "no"".
- **Fix.** Append to the miss-label (e): "; or the pair is attrition in that arm (a skeleton that stays invalid, or a
  part-B "no")".

### R3B-6 (minor): stale text left by the round-4 changes, and an incomplete tool-hash list

- **File and passage, and the fix for each.**
  - `miss_label.py`, `TEXTS`: `"b": "structure present, error did not change decisions in these worlds",`. The
    module docstring repeats the same wording. Draft 4 renamed (b) (R3-9), but the tool still writes the old text into
    every label record. Replace it with "the error's minus rate stayed below the gate's flag threshold".
  - `mech_check_bodies.py`, docstring item 6: "a call of mean, var, std, min, max, all, any, ``linalg.norm``, isnan,
    isfinite, ptp or median (as … for the builtins min, max, all and any, ``f(...)``)". This is the round-3 list. Point
    to `SUMMARY_CALLS` and `BUILTIN_SUMMARY_CALLS` instead.
  - `check_skeletons_d.py`, line 1: "PREREG_PHASE_D sections 2.1 and 3 item 8". The skeleton check is item 9 (R3-13).
  - `STRUCTURE_AUTHOR_D.md`, rule 2: "it must be equal between the two worlds within sampling error". Draft 4 §2.2 and
    the tool use 3 standard errors. Write the same formula.
  - `validity_check.py`, `main`: `for sib in ("assemble.py", "structure_stat.py", "attributable.py"):`.
    - Since D-R4-2, `assemble` imports `mech_check_bodies.py`, which imports `check_skeletons_d.py`, and the free-name
      check now decides whether a case assembles.
    - Neither file is hashed in a full validity run. The docstring says the hashes cover "this file (and of the tools
      it imports)", and the `--arm` mode does hash `mech_check_bodies.py`.
    - Add both files to the full-run list.
  - `EXPECTED.md`, header: "Written on 2026-11-17 from the text of `PREREG_PHASE_D_draft3.md` §5" and
    "(`designer/fisher_hand.py`, private)". The second table carries no draft number, and the script is now frozen.
    State the draft used for the added rows, and drop "private".
  - `recompute_d/COMPARISON.md`: "the map is private (`recompute_d_MAP_private.json`)". The set holds it as
    `recompute_d/MAP_P_ids.json`. Name the frozen file.

### R3B-7 (minor): provenance gaps in the frozen evidence

- **File and passage.**
  - `EXPECTED.md`, added rows: "The Fisher p values are computed with `designer/fisher_hand.py`." Its list has eleven
    entries, and neither 70 vs 2 (`generic_and_declared`, p = 5.1e-22) nor 80 vs 17 (`fixed_k4_blocks_high_rate_control`,
    p = 4.4e-14) is among them. The frozen output does not contain these two values. I confirmed both values
    independently.
  - Draft 4, freeze list: "the whole folder `recompute_d/` (…), with its input manifest". `COMPARISON.md`: "85 of 85
    files match `MANIFEST_recompute_d.json`". No manifest is in the set, and `round4/` (106 input files) has none.
  - `designer/compare_recompute.py`: `PRIV = r"E:\Claude Projects\Kapi\phase_d_private"` and
    `recompute_d_MAP_private.json`. `fixture_attributable_pc.py`: `PC = r"E:\Claude Projects\kapi-oss\evaluation\phase_c"`.
    Neither script can be rerun from the frozen set as it is. I reproduced the comparison with task-folder paths: hand
    = my rule = recomputation = tool on 20 of 20, and recomputation = tool = my rule on 22 of 22 Phase C pairs (on
    stream sets).
- **Fix.**
  - Add the two pairs to `fisher_hand.py`, and rerun it into its output.
  - Put `MANIFEST_recompute_d.json` into `recompute_d/`. Add `round4/MANIFEST_round4.json` with the SHA-256 of every
    input, of `out/recompute.py` and of `out/RESULTS.json`.
  - Make `compare_recompute.py` take the set's root as an argument and read `recompute_d/MAP_P_ids.json`. Regenerate
    its output.

### R3B-8 (minor): the criterion authors are not told the new body rules

- **File and passage.** `CRITERION_AUTHOR_D.md` item 1: "Each file holds, at module level, only the line `import numpy
  as np` and function definitions. One of them is `def criterion(d):` … No decorators."
- **Reason.**
  - `mech_check_bodies.py` now refuses four things:
    - annotations or defaults on `criterion` (`def criterion(d: dict) -> bool:` gives "signature has annotations");
    - `global` and `nonlocal`;
    - non-literal defaults on helpers;
    - any free name.
  - Item 4 ("Only `d`, `numpy`, and constants …") covers the free names only loosely, and the other three rules are
    not stated at all.
  - Type hints are common in model-written code. Each such refusal costs the pair its one body repair, and a second
    slip drops it.
- **Fix.** Add to item 1: "`criterion` takes exactly `d`, with no default value and no annotation. No `global` or
  `nonlocal`. A helper's default values are literals (numbers, strings, `None`, `True`/`False`, tuples of these). A
  function reads only its own parameters and locals, the file's functions, `np` and Python builtins."

## Review 3's findings

| Finding | Verdict | Quote of the fix | Note |
|---|---|---|---|
| R3-1 | partly fixed | §2.3: "the free names (a body reads only its own locals and functions, `np` and builtins, never a skeleton's names), and the signatures (no `global`; no defaults or annotations on `criterion`; literal defaults only on helpers). It lists every comparison of a listed summary call with a constant or a name". Code: `issues += free_name_issues(tree, skeleton_names)  # D-R4-1`, `issues += global_issues(tree)`, `issues += signature_issues(tree)`; `assemble`: `free = free_name_issues(body_tree, _top_level_names(sk_tree, skip=node))  # D-R4-2`; `DIST_CALLS` = PC's set, `SUMMARY_CALLS = DIST_CALLS \| {"isnan", "isfinite"}`. | Signatures, `global`/`nonlocal`, the call list and the §2.3 wording are fixed. The reviewer's demo body is tested: every issue is reported and every comparison listed. Direct reads of skeleton names are refused by both tools. Scope-based reads and skeleton-shadowed builtins still pass (R3B-1). |
| R3-2 | fixed | §3 item 10: "measured on each arm's skeleton with `tools/validity_check.py --arm W0\|W1`". §2.3: "`tools/check_validity_log_d.py` confirms, for every pair of `FREEZE_VALIDITY.json`, that its result is the decisive logged run on the current input hashes." Code: `run_timing_arm`, `main_timing_arm` (`"mode": "timing_arm"`, skeleton and body hashes); `check_validity_log_d.check_pair`. | Formula, stream, S per arm and the five log checks are tested. Residual scope gaps are listed separately: re-runs on changed hashes (R3B-3), and no decisive timing run (R3B-4). |
| R3-3 | fixed | §2.4: "**Precedence.** When one run fails several rows, a V1, V2 or timing failure computed without an error in that stage is final: the pair is dropped with its label, whatever other row also fails. A repair row applies only when no drop row applies." Also "**Fidelity part A** audits only pairs that passed validity." Code: `result["v1_rate_on_error_free"], result["v1_rate_label"] = v1_on_error_free(...)  # D-R4-3`. | Matches R3-3's own fix. The test with a faulty rate below kstar/200 plus exceptions gives `v1_rate_label` "V1a" and `v1_label` null. A same-stage V1 error still leads to a repair (R3B-2). |
| R3-4 | fixed | §6: "A timeout or load error of the fixed twin also makes the pair a miss in that arm, because attribution needs the fixed counts." and "…or load error of either twin." §5 (e): "the faulty twin is PB-detected and the fixed twin left no result (load error, timeout, no certificate). When the faulty twin is not PB-detected, a fixed twin without a result does not change its label". Code: `if fixed_problem and pb:  # D-R4-5`. | Tests cover both branches (PB-detected → (e); not PB-detected → (a), (b) or (d), with `fixed_attrition` as a note). The (e) wording drops pair-level attrition (R3B-5). |
| R3-5 | fixed | §5: "**(2) possible false alarm**: there is a rate flag, (1) does not apply, and apart from the rate flags the fixed twin carries no mandatory or study-level flag"; "Unconfirmed rate flags are recorded with the class whenever the class is not (1)." Code: `if not non_rate_failure:  # D-R4-6: (2) needs the rate flags to be the whole failure`; `res["unconfirmed_rate_flags"] = …`. | `is_mandatory` and the study-level flags are the gate's. The flag lists are checked against `checks.py`, since every study flag raises the verdict. Tested with `K2_NO_SEPARATION` → 3, `K5_HOLDS_ON_NOISE` on the same stream → 3, `K4_NO_CONTROL` → 4, study flags → 4, and other mandatory flags → 4. |
| R3-6 | fixed | §5 (ii): "one pair per path of the rule (20 pairs) … (`EXPECTED.md`, `EXPECTED.json`) … `tests/test_acceptance_d_expected.py` asserts the tool against `EXPECTED.json`". Precision: "A fixed verdict UNDEFINED blocks only the streams with `hard_undefined > 0`." | All seven paths are present and gate-consistent (re-derived). The outcomes are asserted by a frozen test. My recomputation agrees on all 20. The Fisher provenance of two added values is a gap (R3B-7). |
| R3-7 | fixed | §3 item 9: "`tools/shuffle_d.py --subset` re-cuts the pairs and decoys of `FREEZE_VALIDITY.json` into batches of 12 in neutral-id order (the last one shorter); dropped pairs and unused reserves are left out. The neutral ids do not change." Code: `subset_batches` (`chosen = [public[i] for i in sorted(ids)]`, writes `batches_subset_NN.json`, item-2 files untouched). | Tested (order, exact multiple, refusal without `--force`). |
| R3-8 | fixed | §2.3: "A decoy (B-1 or B-6) whose statistic is null runs with `--no-structure` … the tool refuses `--no-structure` for any other class. The tool also refuses a statistic whose direction contradicts the sign of `note_value − null_value`." and "the tool reads the log and marks it `"decisive": true` … the `--dev` guard works by folder name (a path component `cases`), and dev runs go to the same log." Code: `DECOY_CLASSES`, `statistic_problem`, `standard_run_logged`, `LOG_NAME`. | Only the log's base name is fixed, not its folder (R3B-3). |
| R3-9 | partly fixed | §5: "(b) "the error's `minus` rate stayed below the gate's flag threshold" (structure present, or not measured when the statistic is set by the brief or null)"; "(d) arises only when the certificate's K2 decision disagrees with `kstar`, and each (d) is a gate inconsistency to examine"; I-D3 row updated. | The text is fixed. `miss_label.py` still writes the old (b) text, "structure present, error did not change decisions in these worlds" (R3B-6). |
| R3-10 | fixed | §5: "**Rate flags and their streams** (for attribution; the clean-pass classes use a narrower term, below)" and "In these classes a **rate flag** is `K2_HIGH_SIZE` (on `world:minus`) or `HIGH_RATE:<s>` (on s)." | Matches `clean_pass_class.rate_flag_streams`. |
| R3-11 | partly fixed | Freeze list: "the Phase C fixture `fixture_attributable_pc.py` and its output …; the independent recomputation, the whole folder `recompute_d/` …, with its input manifest; the designer's scripts `designer/fisher_hand.py` and `designer/compare_recompute.py`, with their outputs." Fixture: "Note (draft 4): written for draft 2. …" `COMPARISON.md`: "as they stood before the T3-12 precisions and the review-3 changes were added". | The named manifest is not in the set. The frozen `fisher_hand.py` lacks the two new values. Both designer scripts use private paths (R3B-7). |
| R3-12 | fixed | §1: "For a B-3 source, the pairs and reserves allotted never exceed the number of distinct settings … For a B-2 or decoy source read from its abstract only, the cap is 4 slots (pairs and reserves together)"; "an L1.2 drop in half B cannot be replaced; it counts against the class." | Checked against `ALLOCATION_D.json`: SAN18 4, SIM03 3, ROB17 3, AMB02 2, SAE17 2, VAR06 1; decoy sources at most 2 (MAK19 and HUR84). |
| R3-13 | partly fixed | §2.1 "(sections 2.3 and 3 item 10)"; `AWARENESS_RULE_D.md` "Phase D changes four things:"; §2.2 "3 standard errors (`\|mean_plus − mean_minus\| ≤ 3·sqrt(sd_plus²/200 + sd_minus²/200)`)"; I-D2 "on the B-2 and B-3 pairs entering H-D3"; `scan_docs_d.py` `["Phase D", "decoy", "checklist"]  # … D-R4-8`. | Two items are left: `check_skeletons_d.py` still says "3 item 8", and `STRUCTURE_AUTHOR_D.md` still says "within sampling error" (R3B-6). |
| R3-14 | fixed | §2.4 row "`reference.py` rejected by `check_skeletons_d.py` (before validity) \| One return to the structure author; then drop."; "**Counting label.** A pair failing V2 is counted under V2"; §3 item 3 "A decoy whose statistic is null gets "(l): n/a" … dropped with the label "fidelity A0""; `FIDELITY_AUDIT_D.md` "write "(l): n/a""; `clean_pass_class.py --attrition`. | The `--attrition` tests cover no certificate, the order of causes, and the CLI. |

Fixed: 10; partly fixed: 4; not fixed: 0.

## Regressions

- **Draft 3 → draft 4 diff.** Every change maps to a review-3 row. I found no contradiction with the tools except these:
  - the narrowed miss-label (e) (R3B-5);
  - the (b) text that `miss_label.py` still writes (R3B-6).
- **Tools.**
  - `assemble` now imports `mech_check_bodies` lazily, which avoids a circular import, and refuses free names.
    `validity_check` and `mech_check_bodies` therefore apply the same rule. The full validity run does not hash the
    newly imported tool files (R3B-6).
  - No rule of `attributable.py` changed. Its tests and the Phase C fixture still pass.
  - The changes to `clean_pass_class`, `miss_label`, `shuffle_d` and `scan_docs_d` are confined to their D-R4 lines.
    Each matches `TOOLS_SPEC_D_round4.md` and the "R4 tool interpretations" row.
- **Instruction files.** `CRITERION_AUTHOR_D.md` does not state the new body rules (R3B-8). `STRUCTURE_AUTHOR_D.md`
  keeps "within sampling error" (R3B-6).

## The acceptance set

My recomputation of the seven new pairs, from draft 4 §5 alone, with exact hypergeometric p values:

| Pair | Attributable | Generic | Declared | Qualifying streams | Agrees with `EXPECTED.json` |
|---|---|---|---|---|---|
| k2_no_separation_only | no | no | no | none (no expected rate flag: `K2_NO_SEPARATION` is not in the table) | yes |
| faulty_not_nf_with_rate_flag | no | no | no | none (faulty verdict UNDEFINED) | yes |
| faulty_nf_unexpected_mandatory | no | no | no | none (`K5_HOLDS_ON_DEGENERATE` not expected) | yes |
| generic_and_declared | yes | yes | yes | `probe:noise` (70 vs 2, p = 5.1e-22), `world:minus` (60 vs 6, p = 1.8e-14) | yes |
| fixed_missing_stream | no | no | no | none (fixed has no count on `control:permute_x`) | yes |
| fixed_hard_undefined_other_stream | yes | no | yes | `world:minus` (60 vs 6, p = 1.8e-14; fixed hard UNDEFINED only on `world:null`) | yes |
| fixed_k4_blocks_high_rate_control | no | no | no | none (fixed `K4_CONTROL_ALSO_HOLDS` maps to `control:permute_y`: upper 0.148 ≥ plus lower 0.098; 80 vs 17, p = 4.4e-14) | yes |

- **All 20 pairs.** My rule agrees with `EXPECTED.json` on all 20: 6 attributable, 2 generic, 5 declared.
- **Gate consistency.** Every new certificate is consistent with the gate. `check_k1`, `check_k2`, `check_k4`,
  `check_k5`, `check_high_rate`, the cascade suppression and `component_verdict` reproduce its flags and verdict, `m`
  equals `count_comparisons` for its streams, and the bounds match the gate's Wilson bounds to 1e-9.
- **The rerun inputs.** `round4/inputs/acceptance/P01`–`P20` equal the acceptance folders in content, apart from the
  neutral-id key, under `MAP_P_ids.json`. `round4/out/recompute.py` has the SHA-256 that `round4/README.md` states, which
  is also that of `out/recompute.py`.
- **The comparison's convention** (non-attributable pairs compared with empty qualifying streams). It hides no
  disagreement in the rule:
  - In the agent's `RESULTS.json`, only P19 (`faulty_not_nf_with_rate_flag`) is a non-attributable pair with a
    non-empty list (`world:minus`, note "stream-level qualifiers exist but faulty verdict is not NOT_FALSIFIABLE").
  - The agent's attributable, generic and declared for P19 are all false, as are the tool's and the hand's.
  - The stream-level result agrees with my rule with the verdict condition removed (60 vs 6, (a) holds).
  - The convention is applied only to the recomputation. The tool's lists are compared unaltered and are empty for
    every non-attributable pair.
- **Phase C.** On the 22 Phase C pairs my rule, the agent's results and the tool agree on the stream sets, and give
  §5's fixture table.
  - The tool and the agent list a stream once per qualifying flag, so B2-12, B3-08, B3-09 and B3-11 carry duplicates;
    `compare_recompute.py` compares sets.
  - `test_acceptance_d_expected.py` compares the sorted list instead. It would fail spuriously on a pair where two
    expected flags qualify on one stream (for example `K5_HOLDS_ON_NOISE` and `HIGH_RATE:probe:noise`). No current pair
    has this. Comparing sets is the safer form.

## The tests

The full suite gives 380 tests: 380 pass, 0 fail.

The new tests check stated behaviour, not only that the code runs. Examples:
- every issue of the reviewer's demo body is reported, and its three comparisons are listed with their calls;
- signature, default and `global` cases are tested;
- `--arm` uses its own skeleton (S = 5 against 7), stream `timing:plus` with seed 20261117 over 20 samples (spied), and
  a fake clock decides `timing_ok`;
- the first standard run is decisive and the second is not, new hashes start again, and dev runs carry no decisive
  field;
- `v1_rate_label` is V1a, V1b or null as the rate implies, while `v1_label` stays null;
- `--no-structure` is accepted only for B-1 and B-6, and a contradicting direction exits with code 2;
- the synthetic logs of `check_validity_log_d` cover a pass, a missing run, hash mismatches, a non-decisive run, an
  outcome mismatch and a duplicate id;
- `miss_label` is tested on both branches of the fixed-attrition rule;
- `clean_pass_class` is tested with a rate flag combined with every listed and unlisted flag kind;
- the acceptance outcomes are asserted.

Gaps:
- no test for scope-based or shadowed-builtin free names (R3B-1);
- no test for an earlier final drop on other hashes (R3B-3);
- the list comparison of qualifying streams noted above.

## Freezability

The set is close but should not be frozen exactly as it is.

**The review-3 fixes are in place and tested.** The confirmatory machinery is right:
- `attributable.py`, the hand-written outcomes, the unchanged independent recomputation and my own recomputation agree
  on all 20 synthetic pairs and the 22 Phase C pairs;
- the new certificates are gate-consistent;
- the 380 tests pass.

None of the eight new findings is blocking or major, but four should change before the freeze, because the frozen text
promises something that the frozen tools or files do not deliver:
1. Make the free-name check follow Python's scoping, and test skeleton names before builtins (R3B-1).
2. Make `check_validity_log_d.py` see earlier decisive runs of the same case on other hashes, and fix the log location
   (R3B-3).
3. Add pair-level attrition to the miss-label (e) text (R3B-5).
4. Put the named recomputation manifest (and a round-4 manifest) into the set, add the two missing Fisher values to
   `fisher_hand.py`, and make the designer scripts runnable from the set (R3B-7).

Two rule choices should also be written down now, because they cannot be added after the freeze:
- what happens to a pair whose V1 stage errs while its error-free label is V1a or V1b (R3B-2);
- which per-arm timing run decides (R3B-4).

The rest are editorial: stale tool and instruction text, the tool-hash list (R3B-6), and the criterion authors' rules
(R3B-8).

All of these are one-sentence text changes or small, local tool changes with tests. No further full review is needed: a
check of the diffs and a rerun of the suite would suffice.
