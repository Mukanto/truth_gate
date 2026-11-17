# Review 3 of the Phase D pre-registration set (targeted)

Reviewer: an independent agent working only from the task folder `E:\Independent\tasks\phase_d_review3\`. I did not
write the pre-registration, the tools or reviews 1 and 2.

What I did:
- Read draft 3, `REVISIONS_D.md` (the R2 and Round 3 tables), review 2 and draft 2, all twelve tools, their tests, both
  tool specifications, the acceptance set (`README.md`, `EXPECTED.md`, all 13 pairs), the recomputation (`RULE.md`,
  `NOTES.md`, `RESULTS.*`, `recompute.py`, `COMPARISON.md`, `MAP_P_ids.json`), the fixture script and output, the seven
  instruction files, `ALLOCATION_D.json`, `SOURCES_D.md` and `P2_READING_D.md`.
- Compared the tools with the gate's code in `repo/truth_gate/` (`checks.py`, `stats.py`, `probes.py`, `sampling.py`,
  `study.py`) and with Phase C's tools in `repo/evaluation/phase_c/tools/`.
- Ran the test suite with the allowed interpreter from a writable copy (`scratch/tools`), with `KAPI_PACKAGE_ROOT` set
  to the task's `repo` and `TMP`/`TEMP` pointed at `scratch/tmp`. Result: 288 tests, all pass, in 51 s.
- Wrote my own recomputation of the 13 acceptance pairs from the §5 text (`scratch/my_recompute.py`), without using
  `attributable.py`. It also re-derives every synthetic certificate's flags, verdict, m and bounds with the gate's own
  check functions.
- Ran the same rule on the 22 Phase C B-2/B-3 certificates (`scratch/demo/pc_check.py`).
- Ran small probes of the tools (`scratch/demo/`): seven rule paths that the acceptance set lacks, run through the tool
  and through my rule; a body that `mech_check_bodies.py` passes; an assembly in which the body reads a name defined
  by the skeleton.

Inputs were not modified.

## Counts

| Severity | Count |
|---|---|
| blocking | 0 |
| major | 5 |
| minor | 9 |
| total | 14 |

## Major findings

### R3-1 (major): `mech_check_bodies.py` drops checks that Phase C's `mech_check_twins.py` made

- **File and passage.**
  - `phase_d/tools/tools/mech_check_bodies.py`, docstring: "Replaces the part of Phase C's `mech_check_twins.py` that
    the splice design does not cover."
  - Draft 3 §2.3 V3: "`tools/mech_check_bodies.py` checks the module-level rule and the banned names in the bodies,
    lists every comparison of a computed summary with a constant (`MECH_CHECK.json`)".
  - `assemble.py`, `module_level_problems`: "so that nothing runs when the assembled study is imported".
- **Reason.** Phase C's `mech_check_twins.py` (in `repo/evaluation/phase_c/tools/`) made three checks that the Phase D
  tools no longer make.
  1. **Free names.** PC's tool says: "the criterion reads no module-level name except `np` and no undefined name". Its
     `check_body` raised "reads module-level name" and "undefined name". Neither `mech_check_bodies.py` nor
     `assemble.py` checks free names.
     - In Phase D, one body is spliced unchanged into three skeletons written by different agents. A body that reads a
       name it does not define (for example `THRESHOLD`, `N` or `rng`) silently takes the value from whichever skeleton
       defines it. It then raises `NameError` (a hard UNDEFINED) in an arm that does not define the name.
     - That is an arm-specific difference in the criterion itself. It confounds H-D3, and it defeats the purpose of
       `differ_only_in_criterion`, because the two texts can be identical while the behaviour differs.
     - `CRITERION_AUTHOR_D.md` item 4 forbids it ("Only `d`, `numpy`, and constants from the claim or the source"), but
       nothing checks it.
  2. **Signature and state.** PC refused default values, annotations and decorators on `criterion`. Phase D refuses only
     decorators.
     - Default arguments are evaluated at import, which contradicts `assemble.py`'s "nothing runs" claim.
     - A mutable default (`def criterion(d, _seen=[])`), or a `global` statement inside a function, lets a criterion
       keep state across the gate's calls. The gate calls the streams in a fixed order per sample index, so such a
       criterion could tell the streams apart.
  3. **Listed calls.** PC's `DIST_CALLS` also listed `sum`, `abs`, `count_nonzero`, `unique`, `allclose`, `isclose`,
     `array_equal`, `nanmean`, `nanstd` and `nanvar`. Phase D drops all ten.
     - Comparisons such as `np.sum(np.abs(y)) == 0` (a test for the zeros probe), `len(np.unique(y)) == 2` (a test for
       Bernoulli noise) or `np.count_nonzero(y) < 3` are no longer listed for the auditor of item (d).
     - I checked this with `scratch/demo/demo_mech.py`. A body with all of the following gets `"issues": []` and
       `"listed_comparisons": []`: a free name `THRESHOLD`, a `global` statement, a mutable default, and the three
       comparisons above. `scratch/demo/demo_assemble.py` shows that `assemble` accepts a body that reads the
       skeleton's `THRESHOLD`.
  4. **Wording.** The draft's "lists every comparison of a computed summary with a constant" overstates what the tool
     does. A threshold applied to a name (`p < 0.05`, with `p` computed earlier) is never listed.
- **Fix.**
  - In `mech_check_bodies.check_body`, port PC's `local_names` / "reads module-level name" / "undefined name" logic to
    the whole body file. Every loaded name must be one of these:
    - a parameter or local of the enclosing function;
    - a function defined in the body;
    - `np`;
    - a builtin.

    Anything else is an issue.
  - Refuse `global` and `nonlocal` statements.
  - Refuse default values and annotations on `criterion`, as PC's `signature_issues` does. On helpers, refuse defaults
    that are not literals (or list them).
  - Set `SUMMARY_CALLS` to PC's `DIST_CALLS` plus the current set (`isnan`, `isfinite`, `linalg.norm`).
  - In §2.3 write "lists every comparison of a listed summary call (the list in the tool) with a constant or a name".
  - In `assemble.py`, correct the docstring: default values are evaluated at import.
  - Add tests with the demo body (each construct gives an issue, and the three comparisons are listed) and a test that
    a body reading a skeleton-level name is refused.

### R3-2 (major): no frozen tool for the per-arm timing (§3 item 10) or for the validity-log check (§3 item 7)

- **File and passage.**
  - Draft 3 §3 item 10: "After the skeleton check, t and g are measured on each arm's skeleton (fixed criterion, 20
    `plus` samples of stream `timing:plus`, seed 20261117, outcomes not recorded). A skeleton whose estimate is above 30
    minutes goes back once to a fresh agent of that arm."
  - §10: "`validity_check.py` | V1, V2, timing, …".
  - §3 item 7: "The designer checks mechanically that every validity result has its logged run, with the required
    settings and matching input hashes."
- **Reason.**
  - `validity_check.py` reads only `reference.py` (`INPUT_FILES`). `measure_timing` is not exposed for the W skeletons,
    and no tool assembles `fixed_body.py` into `skeletons/W0.py` or `W1.py` to time it.
  - Review 2 (R2-18) named "the per-arm timing estimate" as a step without a tool. The round-2 tool list does not include
    one.
  - The per-arm estimate decides two things: an arm-specific redo by a fresh world author, which matters for H-D3; and
    the compute budget rule (72 h / 120 h). Both would rest on an improvised measurement.
  - The log check of item 7 has no tool either. This includes the "first run decides" rule of §2.3; see R3-8.
- **Fix.**
  - Add `--arm reference|W0|W1` to `validity_check.py`, or a small `timing_arm_d.py`. It assembles the fixed body into the
    named skeleton, runs `measure_timing` (stream `timing:plus`, seed 20261117, 20 samples, outcomes not recorded) and
    appends the estimate, S, t, g and input hashes to a timing log. Add tests (formula, stream, S per arm).
  - Add a `check_validity_log_d.py`. For each pair in `FREEZE_VALIDITY.json` it confirms three things: a logged run with
    `--samples 1000 --seed 20261117` and `dev: false`; matching hashes; and that the decisive result is the first such
    run on those hashes.
  - List both tools in §10 and in the freeze list.

### R3-3 (major): the §2.4 decision table has no precedence when one validity run fails several rows

- **File and passage.**
  - Draft 3 §2.4: "| V1 (V1a or V1b) | Drop, with the label. |"; "| An error in V1, V2 or timing (an exception, a bad
    return or a failed generation) | One repair, by the author of the failing file; then drop. |"; "| Mechanical check
    (a), or a structure statistic that cannot be computed | One repair … |".
  - `validity_check.py`: `if fe or xe: result["v1"], result["reasons"]["v1"] = False, "error"` (no `v1_label`, even when
    the faulty rate is below 0.25).
- **Reason.**
  - `validity_check.py` computes every check in one run, and the designer sees all of them. When a pair fails a drop row
    (V1, V2, timing) and a repair row (an error, mechanical (a) or (b), V3) in the same run, the table does not say
    which applies.
  - If the repair applies, the repaired files have new hashes and V1 is run again. A pair whose faulty rate was below
    0.25 gets a second draw:
    - a new `reference.py` after a mechanical (a) repair;
    - new bodies after an error repair.

    That reopens the V1 repair that R2-10 removed. It also leaves the designer a choice after seeing V1.
  - The tool already imposes one precedence that the text does not state: a single exception in 1000 samples turns any
    V1 result into "error", so the pair is repaired instead of being dropped with V1a or V1b.
  - The same gap applies to fidelity part A, which runs after validity. The text does not say whether pairs already
    dropped at validity are audited, or whether a part-A repair re-runs V1 on a pair that failed it.
- **Fix.**
  - Add to §2.4: "When a run fails several rows: a V1, V2 or timing failure computed without an error in that stage is
    final, and the pair is dropped with its label, whatever other row also fails. A repair row applies only when no drop
    row applies. Fidelity part A audits only pairs that passed validity. After a repair, the next logged run is judged on
    every row again."
  - In `validity_check.py`, record the V1 rate result (and its V1a/V1b label) separately from the error flag, for
    example `v1_rate_label`, so that the table can be applied mechanically. Add a test with a faulty rate below kstar/200
    plus one exception.

### R3-4 (major): a fixed-twin timeout or load error is not handled consistently (§5, §6, `miss_label.py`)

- **File and passage.**
  - Draft 3 §6: "A timeout or a load error counts as a miss for the faulty twin and as a failed clean pass for the fixed
    twin." and "For H-D3, a pair is "not comparable" when either arm has a skeleton that stays invalid, a part-B "no", or
    a timeout or load error of the faulty twin."
  - §5: "A stream does not qualify if the fixed study has a load error … or has no count on s."
  - `REVISIONS_D.md` T3-13: "`miss_label` gives (e) when the fixed twin has no verdict, even if the faulty twin raised
    nothing."
- **Reason.**
  1. Attribution needs the fixed twin's counts. A timeout or load error of the fixed twin alone therefore makes the pair
     a miss in that arm as well as a failed clean pass. §6 describes only the clean-pass side.
  2. For H-D3, a fixed-only timeout or load error in one arm is not "not comparable", so it enters the primary McNemar
     test as a non-detection of that arm.
     - Fixed criteria are often the heavier ones (nested cross-validation, block resampling, a covariate adjustment).
     - W-1 worlds may declare more streams.
     - So this attrition is plausible and arm-specific: exactly what the "not comparable" rule was written to keep out.
  3. T3-6 and T3-13 put "(e) through the fixed twin" into the tool, but §5's (e) does not say so.
  4. T3-13's third bullet gives (e) even when the faulty twin was not PB-detected. In that case the miss did not depend
     on the fixed twin, and (a), (b) or (d) can be computed from the faulty certificate and the structure statistic.
     Labelling it attrition removes it from the I-D3 reading "whether the structure was missing".
- **Fix.**
  - In §6, add: "A timeout or load error of the fixed twin also makes the pair a miss in that arm (attribution needs the
    fixed counts). For H-D3, such a pair is not comparable."
  - In §5, under miss labels, add: "(e) also applies when the fixed twin left no result (load error, timeout, no
    certificate) and the faulty twin is PB-detected. When the faulty twin is not PB-detected, labels (a), (b) and (d)
    apply as usual."
  - Change `miss_label.label_miss` to match: try the fixed-attrition branch only after `pb_detected` is known. Add a
    test.

### R3-5 (major): clean-pass class (2) does not require the rate flags to be the only cause, so it inflates "the gate's own share"

- **File and passage.**
  - Draft 3 §5: "(2) possible false alarm: no flagged rate stream has a fresh interval above the size (each interval
    includes the size or lies below it; the relation is recorded per stream)".
  - I-D5: "Class 2 (possible false alarm) is the gate's own share."
  - `clean_pass_class.py`: `if rates: … return done("2", …)`. This is reached whatever other failure flags the
    component carries.
- **Reason.**
  - A fixed twin can carry a rate flag that fresh sampling does not confirm, and also one of these:
    - `K2_NO_SEPARATION`;
    - a relative flag on another stream;
    - `K4_NO_CONTROL`;
    - a study-level flag.
  - Any of these fails the clean pass by itself. Example: a fixed twin weak in a W-1 `plus` (30/200) with noise 18/200
    carries `HIGH_RATE:probe:noise` and `K5_HOLDS_ON_NOISE`. With a fresh noise rate near 0.06 it becomes class (2),
    although without the rate flag it would be class (3).
  - So class (2) absorbs failures that I-D5 Reading 2 (class 3) or class (4) should carry. The gate's share is
    overstated, which is exactly the separation (D-2) that Phase D is built to make.
- **Fix.**
  - Define class (2) as: "there is a rate flag, no flagged rate stream has a fresh interval above the size, and the
    failure flags left after removing those rate flags would give a clean pass (none is mandatory or study-level)."
  - Otherwise, classify the remaining failure flags by (3) and (4), and record that a non-confirmed rate flag was also
    present (for example `also_unconfirmed_rate_flags`).
  - Change `clean_pass_class.py` and add tests for rate flag + `K2_NO_SEPARATION`, rate flag + `K5_HOLDS_ON_NOISE` on a
    stream without a rate flag, and rate flag + a study-level flag.

## Minor findings

### R3-6 (minor): acceptance set: paths missing, and its outcomes are not asserted by any frozen test

- **File and passage.**
  - Draft 3 §5 (ii): "The synthetic acceptance set `tests/acceptance_d/`, one pair per path of the rule … Both must
    agree with the tool."
  - `tests/test_acceptance_d_inputs.py`: "They assert no outcome of the attribution rule".
- **Reason.**
  - The 13 pairs cover the list of R2-3. My recomputation agrees with `EXPECTED.md` on all 13 (table below). Every
    synthetic certificate is consistent with the gate's own check functions: flags, verdict, m and bounds.
  - Paths of the §5 text with no pair:
    - (1) `K2_NO_SEPARATION` alone, which is PB-detected but not attributable. §5 names this case explicitly.
    - (2) A faulty verdict other than NOT_FALSIFIABLE with components and an expected rate flag (for example
      `K1_UNDEFINED` + `K2_HIGH_SIZE`).
    - (3) A faulty NOT_FALSIFIABLE only through an unexpected mandatory flag (for example `K5_HOLDS_ON_DEGENERATE`).
    - (4) A detection that is both generic and declared ("A detection can be both").
    - (5) A fixed twin with no count on s.
    - (6) A fixed hard UNDEFINED on a stream other than s, which gives "attributable" although the fixed verdict is
      UNDEFINED.
    - (7) A bounds-mapped fixed `K4_CONTROL_ALSO_HOLDS` that blocks a faulty `HIGH_RATE:control`.

    I ran all seven through the tool and through my rule (`scratch/demo/paths.py`). They agree, and match §5.
  - The inputs were written by the tool author (`TOOLS_SPEC_D_round2.md`: "you write only the synthetic certificates").
  - The tool–hand–recomputation comparison is shown only by the designer's private `designer/compare_recompute.py`. No
    frozen test reproduces "Both must agree with the tool".
  - Path (6) shows a reading that the text leaves implicit: a fixed UNDEFINED verdict blocks only the streams with
    `hard_undefined > 0`.
- **Fix.**
  - The designer adds pairs (1) to (7) with hand-written outcomes.
  - Add a machine-readable `EXPECTED.json` and a test that asserts, for every folder, the tool's `attributable`,
    `generic`, `declared` and qualifying streams against it.
  - Freeze the comparison script and its output.
  - Add to §5: "A fixed UNDEFINED verdict blocks only the streams with `hard_undefined > 0`."

### R3-7 (minor): the world-author batches are cut before validity and include reserves and later drops

- **File and passage.**
  - Draft 3 §3 item 2: "`tools/shuffle_d.py` assigns the neutral ids".
  - Item 9: "`tools/shuffle_d.py` writes batches of 12 consecutive neutral ids (the last one shorter). W-0 and W-1 use
    the same batch files."
  - `shuffle_d.py`: ITEMS.json is "one list of all briefs and reserves".
- **Reason.**
  - The single run at item 2 writes batch files over all 72 items. After validity, only the frozen pairs should reach
    the world authors.
  - The text does not say whether the world authors receive the item-2 batch files as they are (about 24 unused or
    dropped briefs, about 50 % more world-writing than the budget assumes) or filtered ones. If filtered, the batches are
    no longer "of 12".
  - The tool cannot write filtered batches.
- **Fix.** Pick one and say it in item 9: either "world authors receive the item-2 batches filtered to the pairs of
  `FREEZE_VALIDITY.json`, in batch order, each keeping its number", or "`shuffle_d.py --subset FREEZE_VALIDITY.json`
  re-cuts batches of 12 in neutral-id order". Add a `--subset` option and a test.

### R3-8 (minor): `validity_check.py` guards that the text promises but the tool does not fully enforce

- **File and passage.**
  - Draft 3 §2.3: "A decoy whose statistic is null runs with `--no-structure`" and "The first such run on a given set of
    input hashes decides … Any other run on a case folder is refused by the tool."
- **Reason.**
  1. `--no-structure` is accepted for any pair whose statistic is null. It does not check that `PRIVATE.json` `class` is
     B-1 or B-6, so a B-2 or B-3 pair with a null statistic would skip mechanical check (a), and later miss label (a).
  2. Nothing checks that `direction` agrees with the sign of `note_value − null_value`. A mismatch silently inverts miss
     label (a) (`share_beyond_half`).
  3. The tool never reads the log. A second standard run on the same hashes is accepted and logged like the first. The
     `--log` path is free. The `--dev` refusal depends only on a path component named `cases`, so a copy of a case
     folder elsewhere accepts `--dev`.
- **Fix.**
  - Refuse `--no-structure` unless `class` is B-1 or B-6.
  - Refuse a statistic whose direction contradicts `note_value − null_value`, as a usage error. Fidelity (m) should
    also check it.
  - Before a standard run, read the log. If a standard run with the same five input hashes exists, either refuse, or
    write `"decisive": false`.
  - Say in §2.3 that the `--dev` guard is by folder name, and that every dev run is logged to the same
    `validity_log.jsonl`.

### R3-9 (minor): miss labels (b) and (d): what they can and cannot mean

- **File and passage.**
  - Draft 3 §5: "(b) "structure present, error did not change decisions in these worlds": the faulty `minus` count is
    below that arm's `kstar`" and "(d) "other: examined as a possible gate finding"".
  - `test_miss_label.py` `test_d_other` uses `cert("FALSIFIABLE", [], minus_holds=40)`.
- **Reason.**
  - On a certificate consistent with the gate, a faulty `minus` count at or above k* raises `K2_HIGH_SIZE`. That flag is
    in every expected list, so the pair is PB-detected and gets (c) or no label. (d) is therefore reached only when a
    certificate contradicts the gate's own K2 rule. The test does reach (d), but only with an impossible certificate
    (FALSIFIABLE with 40/200).
  - (b)'s text "error did not change decisions" misdescribes a count below k* that may still be well above the fixed
    count. The label means "below the flag threshold".
  - (b) says "structure present" even when the statistic is null or set by the brief, so that the structure was not
    measured.
- **Fix.**
  - In §5 and I-D3, state that (d) arises only when the certificate's K2 decision disagrees with k*, so any (d) is a gate
    inconsistency to examine.
  - Reword (b) as "the error's `minus` rate stayed below the gate's flag threshold (structure present, or not measured
    when the statistic is set by the brief or null)".

### R3-10 (minor): "rate flag" is used in two senses in §5

- **File and passage.**
  - The §5 table "Rate flags and their streams" includes `K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_NOISE`,
    `K5_HOLDS_ON_NULL` and `K5_HOLDS_ON_SHUFFLE`.
  - The clean-pass classes say "(1) … a flagged rate stream" and "(3) … a relative flag (`K4_CONTROL_ALSO_HOLDS`,
    `K5_HOLDS_ON_*`) whose stream carries no rate flag".
- **Reason.**
  - In the attribution rule, the relative flags are rate flags: a fixed `K5_HOLDS_ON_NOISE` blocks `probe:noise`.
  - In the clean-pass classes, "rate flag" means only `K2_HIGH_SIZE` and `HIGH_RATE:*`. That is how
    `clean_pass_class.rate_flag_streams` reads it, and it is the only reading under which class (3) is not empty.
  - The tools are right, but the frozen text supports both readings.
- **Fix.** Rename the §5 table "Flags with a stream (for attribution)". In the clean-pass classes write "a rate flag
  (`K2_HIGH_SIZE` or `HIGH_RATE:*`)".

### R3-11 (minor): freeze list omissions and a stale fixture script

- **File and passage.**
  - Draft 3 "Frozen with this text": "the acceptance set `tests/acceptance_d/`, with the designer's hand-written
    `EXPECTED.md` and the output of the independent recomputation (section 5)".
  - `fixture_attributable_pc.py`, docstring: "under the attributable rule proposed in review 1 (R1-2)"; its code:
    `return [s for s in counts if s.startswith("control:")]`.
  - `EXPECTED.md`: "(`designer/fisher_hand.py`, private)".
  - `COMPARISON.md`: "from `inputs/RULE.md` alone (draft 3 §5, lines 341–375 …)".
- **Reason.**
  - `fixture_attributable_pc.py` and its output are not in the freeze list, although §5 (i) cites the output and the
    tests read it.
  - The fixture script still implements the draft-1/2 mapping: K4 and shuffle mapped to every stream, no hard-UNDEFINED
    rule. It also reads `E:\Claude Projects\…` paths. Its output equals draft 3's on the Phase C data only because no
    Phase C pair exercises the difference.
  - `RULE.md`, `COMPARISON.md`, `MAP_P_ids.json`, `designer/compare_recompute.py`, `designer/fisher_hand.py` and
    `MANIFEST_recompute_d.json` are cited as evidence but are not frozen (the last three are private).
  - `RULE.md` lacks the "Precisions" list and "or has no count on s", which were added afterwards (T3-12), so "lines
    341–375" of the current draft is not what the agent received.
- **Fix.**
  - Add the fixture script and output, the whole `recompute_d/` folder, and the two designer scripts with their outputs
    to `FREEZE_PREREG_D.json`.
  - Add a header note to the fixture script: "written for draft 2; on the Phase C certificates its output equals the
    draft-3 rule".
  - In `COMPARISON.md`, say that `RULE.md` is §5 as it stood before the T3-12 precisions.

### R3-12 (minor): the settings inventory exists only for B-3

- **File and passage.**
  - Draft 3 §1: "The pairs and reserves allotted to a source never exceed the number of distinct settings its readable
    text describes, as listed in `SOURCES_D.md`."
  - `SOURCES_D.md` has a "Settings in the readable text | Slots" column only in the B-3 table.
- **Reason.**
  - The rule is stated for all sources, but it cannot be checked for these:
    - the abstract-only B-2 sources (SAN18 with 4 slots, the abstract-only maximum; SIM03 and ROB17 with 3 each; AMB02
      with 2);
    - the decoy sources (MAK19 is a reserve in both B-1 and B-6; HUR84 has a pair and a reserve).
  - Also, the only L1.2 reserve is KAP23's. KAP23 already supplies 10 B-2 pairs, so by the skip rule SAN18's two L1.2
    pairs have no usable reserve. The text should say so, not imply full coverage ("at least one reserve per subtype",
    R2-20).
- **Fix.**
  - Add the settings and slots columns to the B-2 and decoy tables, or restrict the §1 sentence to B-3.
  - State that L1.2 drops in half B are not replaceable.

### R3-13 (minor): cross-references and wording

- **File and passage.**
  - Draft 3 §2.1: "(sections 2.3 and 3 item 9)". The per-arm timing is item 10.
  - `check_skeletons_d.py` docstring: "PREREG_PHASE_D sections 2.1 and 3 item 8". The skeleton check is item 9.
  - `AWARENESS_RULE_D.md`: "Phase D changes three things:", followed by four bullets.
  - §2.2 (a): "equal between the two worlds within sampling error". The tool uses 3 standard errors; the text gives no
    number.
  - I-D2: "the pooled W-1 minus W-0 clean-pass difference is at least −2 pairs". Which pairs is not stated; R2-5 asked
    for "the B-2 and B-3 pairs entering H-D3".
  - `scan_docs_d.py`: the added vocabulary lacks "Phase D", "checklist" and "decoy".
- **Fix.**
  - Correct the item numbers and "three" to "four".
  - Write "within 3 standard errors (`|mean_plus − mean_minus| ≤ 3·sqrt(sd_p²/200 + sd_m²/200)`)".
  - Write "… on the B-2 and B-3 pairs entering H-D3".
  - Add the three tokens to the scan list (and to its difference table).

### R3-14 (minor): small rule gaps around validity and attrition

- **File and passage.**
  - `STRUCTURE_AUTHOR_D.md` rule 9: "A rejected file goes back to you once."
  - Draft 3 §2.4 (no row for it).
  - §2.4: "The drop rates are reported by subtype, tag and label (V1a, V1b, V2, timing, V3, fidelity)".
  - `FIDELITY_AUDIT_D.md` part A0.
  - `clean_pass_class.py` (only `--timeout`).
- **Reason.**
  1. The skeleton check of `reference.py` and its single return are in the instruction file but not in §2.2 or §2.4.
  2. A pair failing both V1 and V2 is reported by `validity_check.py` as V1b plus a V2 failure. The text does not say
     which label it counts under. A V1 failure through the Fisher condition alone implies a fixed `minus` rate far above
     0.065, so it is really a V2 failure.
  3. Part A0 gives no answer for a decoy whose statistic is null. A pair dropped at A0 has no drop label.
  4. §5 class (e) includes attrition by an invalid skeleton or a part-B "no", but `clean_pass_class.py` can mark only a
     timeout. `miss_label.py` has a general `--attrition CAUSE`.
- **Fix.**
  - Add a §2.4 row: "`reference.py` rejected by `check_skeletons_d.py`: one return to the structure author; then drop."
  - Count a pair that fails V2 under V2, and use V1a/V1b only when V2 passes.
  - Add "(l): n/a" for null statistics in A0, and the label "fidelity A0".
  - Add `--attrition CAUSE` to `clean_pass_class.py`.

## Review 2's findings

| Finding | Verdict | Note |
|---|---|---|
| R2-1 | fixed | Fresh 1000-sample classification on `classify:<stream>`, classes (e), (1)–(4) in order, two I-D5 readings. New problem: class (2) is not exclusive (R3-5); "rate flag" is used in two senses (R3-10). |
| R2-2 | fixed | Load errors of either twin and `hard_undefined > 0` on s are handled without exception, as §5 says; tests use real load-error bodies. |
| R2-3 | fixed | 13 synthetic pairs, a hand-written `EXPECTED.md`, and an independent recomputation (neutral ids, `RULE.md` only, no access to `tools/`). I agree on all 13. Coverage gaps and the missing frozen assertion: R3-6. |
| R2-4 | fixed | Ordered labels (e), (c), (a), (b), (d) with k* from the arm's study, in `miss_label.py`. (d) is reachable only on a gate inconsistency (R3-9). T3-13's (e) without a faulty flag: R3-4. |
| R2-5 | partly fixed | I-D2 now needs H-D1 or H-D2, the table follows, "no verdict" reads "fails", the guard uses the H-D3 pairs. The −2-pair rule still does not name its pairs (R3-13). |
| R2-6 | fixed | Decoys described as partly named; detection and clean pass reported per arm and mechanism; the guard is a guard on clean pass. |
| R2-7 | fixed | `--no-structure`, decoy authors and auditor named, reserves written with the main set, decoy sections in the instruction files. `--no-structure` is not restricted to decoy classes (R3-8). |
| R2-8 | fixed | `dims` in `brief.json`, exact shapes for every draw and control output, identical shapes across arms, tests for a transposed key. |
| R2-9 | fixed | Neutral ids `D-nnn` from the freeze hash; private map. The batch composition after drops is open (R3-7). |
| R2-10 | fixed | No V1 repair. New problem: without a precedence rule, a V1-failing pair can be re-run through another row (R3-3). |
| R2-11 | partly fixed | Repair sections without rates, "same author" defined, rows for errors, the statistic and brief defects. The precedence among rows and the tool's error-over-rate precedence are missing (R3-3). |
| R2-12 | fixed | Part A0 approves the values before the structure authors; the value is written to `note_value`. |
| R2-13 | fixed | Rule 8 forbids effect checks; the author no longer reads the analysis descriptions. |
| R2-14 | fixed | Invariance requirement and examples; band `0.2·|note − null|` in the text, tool and instructions; the brief author may run its statistic. The direction is not checked against `note − null` (R3-8). |
| R2-15 | fixed | PB §1 rules with precedence, PC §2's estimand paragraph, "Naming the estimand in B-3", B-1/B-6 examples, the `TASK.json` exposure: all in `BRIEF_AUTHOR_D.md`. |
| R2-16 | fixed | (d) probe clause, (e) banned terms, (f) with `P2_READING_D.md`, the size list, the VAR06 note, and "does not widen it" are restored. |
| R2-17 | partly fixed | `mech_check_bodies.py` and `MECH_CHECK.json` exist, with PC's randomness rule and decorators. PC's free-name, signature and wider call-list checks are lost (R3-1). |
| R2-18 | partly fixed | `shuffle_d`, `scan_docs_d`, `term_check_d`, `expected_flags_d`, `clean_pass_class` and `miss_label` were written and match their difference tables. The per-arm timing and the log check still have no tool (R3-2). |
| R2-19 | fixed | Timing at validity on `timing:plus`, 250 ms per call, outcome after a redo, 60-minute timeout, closed budget rule. The tool gap for item 10 is counted under R3-2. |
| R2-20 | fixed | Own half first, then the other half, skip on a cap, minima with consequence. The L1.2 reserve is usable only for a KAP23 drop (R3-12). |
| R2-21 | fixed | B-3 settings inventory and slot caps match the allocation (checked); ARC81 at 3; four new sources. Inventory missing for B-2 and decoys (R3-12). |
| R2-22 | partly fixed | Twin-specific scoring and "not comparable" are in. Fixed-twin attrition is not handled for attribution or H-D3 (R3-4). |
| R2-23 | fixed | K4 and shuffle flags are mapped through the carrying certificate's bounds. Checked against `check_k4`, `check_k5`, `sl` and `sl_stochastic`: "not SL" is `upper(s) ≥ lower(plus)`. |
| R2-24 | fixed | B3-04 and B3-05 annotated; the D-3 difference stated. My rule on the Phase C certificates gives the §5 table. |
| R2-25 | fixed | Only `--samples 1000 --seed 20261117`; `--dev` refused under `cases`. "First run decides" is not enforced by the tool (R3-8). |
| R2-26 | fixed | Part-B skeletons under X/Y labels. |
| R2-27 | fixed | "Do not refer to this list in WORLD_LOG.md"; sentences removed before the first reading; other readers for the second. |
| R2-28 | fixed | §2.2's list matches `STRUCTURE_AUTHOR_D.md`. |
| R2-29 | fixed | One module-level rule everywhere. |
| R2-30 | fixed | k* list, R1-15 and R1-3 rows corrected; k* recomputed: 17 (m 1–2), 18 (3–5), 19 (6–14), 20 (≥15). |
| R2-31 | fixed | Docstring 1000 ms; designer-built case files with renamed fields; 250 ms / 100 ms in both difference tables. |
| R2-32 | fixed | Reviews, both specs, `P2_READING_D.md` and the `TASK.json` rule are listed. New omissions: R3-11. |
| R2-33 | fixed | I-D6 states what validity means and bans the bare word. |
| R2-34 | fixed | Structure labels after the run; "structure not computable" defined. |
| R2-35 | fixed | The known part is listed in §6, with clean pass also reported without the noise stream. |
| R2-36 | fixed | Exact powers at n = 32 added. I reproduced the H-D1/H-D2 joint power (0.40, 0.69, 0.92) and the bar at the actual n (16/20, 15/19, 15/18, 14/17, 13/16). |

Fixed: 31; partly fixed: 5; not fixed: 0.

## The Round 3 decisions

- **Consistency with the draft.**
  - T3-1, T3-2, T3-5, T3-7 to T3-11 and T3-12 match draft 3 and the tools.
  - T3-3 and T3-4 match the tools. The draft's description of the listing overstates it (R3-1).
  - T3-6 and the fixed-twin parts of T3-13 are in the tool, but not in §5's (e); T3-13's third bullet is questionable on
    substance (R3-4).
- **Outcome-driven?** I found no outcome-driven choice. No Phase D data exist.
  - The Phase C certificates have no fixed UNDEFINED, no multi-control K4 and no load error, so none of T3-6, T3-12 or
    T3-13 can have been tuned to them.
  - T3-12's "No outcome changes" refers to the acceptance and fixture outcomes, which are not Phase D numbers.

## The tools against draft 3: what I checked and found right

- **`validity_check.py`.**
  - V1 (0.25, one-sided Fisher p < 0.01 on 1000 `minus` samples) is right.
  - V1a (`faulty rate < kstar/200`, with kstar from the faulty study's `count_comparisons`) is right.
  - V2 (0.065 / 0.065 / 0.70; noise as `noise_probe(copy_data(plus_i), stream_rng(seed, "validity:noise", i))`, which
    is the gate's construction) is right.
  - The band, the 3-SE equality, mechanical (b) (paired as in `_minus_analysis`), S as `len(build_plan)` (= PB §2's S),
    the estimate `2·200·(S+1)·(t+g)`, the streams `validity:*`, `structure:*`, `timing:plus` with seed 20261117
    (the gate's `base_seed` is 20261105), `--dev` and `--no-structure` all match §2.2 and §2.3. The exceptions are
    R3-3 and R3-8.
- **`attributable.py`.**
  - The mapping, condition (a) on the fixed twin's own bounds, condition (b), the load-error and hard-UNDEFINED
    exclusions and the generic/declared labels match §5 and its Precisions.
  - `HIGH_RATE:premise:*` and `HIGH_RATE:probe:zeros` are mapped too. That is harmless, because no expected flag maps to
    those streams.
- **`clean_pass_class.py`.**
  - Its `classify:` streams mirror the gate exactly: `checks.stream_rng` is replaced, so `make_sample` builds world,
    control, premise, noise, zeros and shuffle samples from `classify:world:plus` and `classify:<s>`, and
    `checks.stream_rng` is restored afterwards.
  - The order (e), (1), (2), (3), (4) and the relative-flag list match T3-2. The exceptions are R3-5 and R3-14.
- **`miss_label.py`.** The order is (e), (c), (a), (b), (d); the structure share uses stream `structure:minus` with 200
  samples; kstar comes from the arm's own study and the certificate's n. The exceptions are R3-4 and R3-9.
- **`mech_check_bodies.py` and `assemble.py`.** The module-level rule, the banned names (whole tree), the randomness
  rule (PC's, plus captured `default_rng` and imports), decorators, and the single difference per arm all work. The
  exception is R3-1.
- **The other tools.**
  - `check_skeletons_d.py`, `shuffle_d.py`, `scan_docs_d.py` and `term_check_d.py` differ from Phase C's scripts exactly
    as their difference tables say (diffed).
  - `expected_flags_d.py`'s base list equals Phase C's `EXPECTED_FLAGS.json["base"]`.
- **The tests.**
  - They test behaviour, not just execution, in most places. Examples: an independent recomputation of the V1/V2 counts
    and of the `classify:` streams; spies on stream names and seeds; gate consistency of the acceptance certificates;
    k* against the gate.
  - The gaps are the ones above: no assertion of the acceptance outcomes (R3-6); no test for free names, defaults or the
    lost calls (R3-1); the (d) test uses an impossible certificate (R3-9).

## Acceptance set recomputed

I recomputed each pair from the §5 text alone (`scratch/my_recompute.py`), with exact Fisher p values. The certificates
are consistent with the gate's own rules.

| Pair | Attributable | Generic | Declared | Qualifying streams | Agrees with `EXPECTED.md` |
|---|---|---|---|---|---|
| a_true_b_false | no | no | no | none (18 vs 17, p = 0.50) | yes |
| a_false_k2_high_size | no | no | no | none (fixed `K2_HIGH_SIZE`) | yes |
| a_false_high_rate_control | no | no | no | none (fixed `HIGH_RATE:control:permute_y`) | yes |
| a_false_high_rate_noise | no | no | no | none (fixed `HIGH_RATE:probe:noise`) | yes |
| a_false_k5_holds_on_null | no | no | no | none (fixed `K5_HOLDS_ON_NULL`) | yes |
| a_false_shuffle | no | no | no | none (fixed `HIGH_RATE:probe:shuffle:x,y`) | yes |
| k4_two_controls_one_meets_bounds | yes | no | yes | `control:permute_y` (17 vs 1, p = 5.3e-5) | yes |
| shuffle_two_pairs | yes | no | yes | `probe:shuffle:x,y` (17 vs 1, p = 5.3e-5) | yes |
| fixed_load_error | no | no | no | none (fixed load error, listed) | yes |
| faulty_load_error | no | no | no | none (faulty load error, listed) | yes |
| fixed_hard_undefined | no | no | no | none (fixed `hard_undefined = 50` on `world:minus`, listed) | yes |
| generic_only_k5_holds_on_noise | yes | yes | no | `probe:noise` (17 vs 1, p = 5.3e-5) | yes |
| declared_only | yes | no | yes | `world:minus` (60 vs 6, p = 1.8e-14) | yes |

Totals: 4 attributable, 1 generic, 3 declared, the same as `EXPECTED.md` and the recomputation.

- **Independence of the recomputation.** As far as the files show, it was independent of the tool.
  - The agent was given `RULE.md` (§5 without the fixture table) and the certificates under neutral ids P01–P13. The
    neutral id was also used as the key inside each `expected_flags.json`.
  - Its code is structurally different from `attributable.py` (exact `Fraction` arithmetic, its own data model).
  - Its 27 notes name the four choices that draft 3 later fixed in the Precisions.
- **Open ambiguity in the recomputation's notes.** They reveal none that draft 3 still leaves open for real certificates.
  The remaining silent points do not occur in full mode: a missing `world:plus` bound, and a hard UNDEFINED on the
  faulty side. One reading is worth writing down: a fixed UNDEFINED verdict blocks only the streams with
  `hard_undefined > 0` (R3-6).

## Overall judgment

Draft 3 and the round-2 tools answer review 2 in substance: 31 of 36 findings fixed, 5 partly fixed, none open. The
core of the confirmatory machinery is right:
- `attributable.py` implements §5 exactly, including the gate's own SL rule for K4 and shuffle flags, the load-error and
  hard-UNDEFINED exclusions and the generic/declared labels. The hand-written `EXPECTED.md`, the independent
  recomputation, my own recomputation and the tool agree on all 13 synthetic pairs and on the Phase C fixture.
- `validity_check.py` mirrors the gate's sample construction on disjoint streams and a disjoint seed.
- `clean_pass_class.py` reuses the gate's own `make_sample` under renamed streams.
- The 288 tests pass.

I found no blocking defect. The five major findings are local and each has a concrete fix:
1. `mech_check_bodies.py` lost PC's free-name, signature and call-list checks. This matters more in Phase D, where one
   body runs in three skeletons (R3-1).
2. The per-arm timing of §3 item 10 and the validity-log check have no frozen tool (R3-2).
3. §2.4 has no precedence when a run fails several rows, which quietly reopens a V1 second chance (R3-3).
4. A fixed-twin timeout or load error is a miss that H-D3 does not treat as "not comparable" (R3-4).
5. Clean-pass class (2) can absorb failures with other causes and so overstates the gate's share (R3-5).

The minor findings are coverage, wording and freeze-list items. Once the major findings are fixed, and the fixes are
checked against the tests, the set can be frozen without another full review.

Freezable after the fixes: **yes**.
