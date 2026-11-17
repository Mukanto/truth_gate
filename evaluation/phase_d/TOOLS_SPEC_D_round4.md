# Phase D tools, round 4: fixes from review 3 (designer's specification, 2026-11-17)

Review 3 is `E:\Independent\tasks\phase_d_review3\out\REVIEW3.md` (0 blocking, 5 major, 9 minor). The designer
accepted every finding. This file states the tool changes. The text changes are made by the designer in the draft.

Work only in `E:\Claude Projects\Kapi\phase_d_private\tools\`. Do not read or touch `recompute_d/`. Do not edit
`tests/acceptance_d/EXPECTED.md` or `tests/acceptance_d/EXPECTED.json`. Do not change the rule in `attributable.py`.
Every change comes with tests. Mark changed lines `# D-R4-<n>`, where n is the item number below.

## 1. `mech_check_bodies.py` (R3-1)

Port the following from PC's `evaluation/phase_c/tools/mech_check_twins.py`, citing file and line in the docstring.
Apply each check to the whole body file, not only to `criterion`.

- **Free names.** Every name the file loads must be one of these:
  - a parameter or local of the enclosing function (or of an enclosing function);
  - a module-level function of the body file;
  - `np`;
  - a Python builtin.

  Report anything else as "reads module-level name X" or "undefined name X", with the line number, following PC's
  `local_names` logic. A body that reads `THRESHOLD`, `N` or `rng` from a skeleton must be refused.
- **No `global` and no `nonlocal`** anywhere.
- **Signatures.**
  - `criterion` has no default values and no annotations, as in PC's `signature_issues`.
  - Helper functions may have default values only if they are literals: numbers, strings, `None`, `True`/`False`, or
    tuples of these. Mutable or computed defaults are refused.
- **Listed calls.** `SUMMARY_CALLS` becomes PC's `DIST_CALLS` together with `isnan`, `isfinite` and `linalg.norm`. Keep
  the built-in forms `min`, `max`, `all`, `any` and add `sum`, `abs` and `len`. The comparison rule of round 3 stays:
  - a side that contains a listed call anywhere;
  - against a literal, a negated literal, arithmetic of literals, or a bare name.
- **Tests.** Add tests for each case. Include the reviewer's demo body: a free name `THRESHOLD`, a `global`
  statement, a mutable default, `np.sum(np.abs(y)) == 0`, `len(np.unique(y)) == 2` and `np.count_nonzero(y) < 3`.
  Each of its problems must be reported and each of its comparisons listed.

## 2. `assemble.py` (R3-1)

- **Docstring.** Correct it: the module-level rule alone does not stop a body from reading skeleton globals. The
  free-name check in `mech_check_bodies.py` does that.
- **Free names at assembly.** `assemble` calls the free-name check of item 1 on each body and refuses to assemble a body
  that fails it.
- **Test.** Add a test with a body that reads a skeleton-level name.

## 3. `validity_check.py` (R3-2, R3-3, R3-8)

- **(a) Per-arm timing, R3-2.**
  - Add `--arm reference|W0|W1`, default `reference`. With `--arm W0` or `--arm W1`, the tool assembles
    `fixed_body.py` into `skeletons/W0.py` or `skeletons/W1.py` of the case folder with `assemble.py`.
  - It then runs only the timing measurement:
    - stream `timing:plus`, seed 20261117, 20 samples, outcomes not recorded;
    - `S` is the stream count of that arm's study;
    - the estimate is `2·200·(S+1)·(t+g)`, recorded as `estimate_s` and `timing_ok` (≤ 1800 s).
  - It logs to `validity_log.jsonl` with `"mode": "timing_arm"`, the arm, and the SHA-256 of the skeleton and the fixed
    body.
  - No V1, V2 or structure check runs in this mode.
- **(b) V1 label recorded separately from errors, R3-3.**
  - When the V1 stage has an error (an exception or a bad return on some samples), still compute the faulty and fixed
    counts on the samples without error.
  - Record them as `v1_rate_on_error_free` (holds, n), with the V1a/V1b label that the rule would give on them
    (`v1_rate_label`).
  - `v1` stays False with reason "error", and `v1_label` stays null.
  - Test: a faulty rate below kstar/200 plus one exception gives `v1_rate_label` "V1a" and `v1_label` null.
- **(c) `--no-structure` only for decoys, R3-8.** Refuse it, as a usage error with exit 2, unless `PRIVATE.json` `class`
  is `B-1` or `B-6`.
- **(d) Direction check, R3-8.** Refuse, as a usage error, a structure statistic whose `direction` contradicts the
  sign of `note_value − null_value`. Read the direction vocabulary from the current code and state it in the docstring.
- **(e) Decisive run, R3-8.**
  - The log path must have the base name `validity_log.jsonl`; refuse anything else.
  - Before a standard run (`--samples 1000 --seed 20261117`, not `--dev`), read the log. If a standard run with the
    same five input hashes is already logged, run anyway and log it with `"decisive": false`. Otherwise log it with
    `"decisive": true`.
  - `--dev` runs and `timing_arm` runs carry no `decisive` field.
- **(f) Docstring.** State that the `--dev` guard works by folder name (any path component `cases`), and that `--dev`
  runs are logged to the same `validity_log.jsonl`.

## 4. New `check_validity_log_d.py` (R3-2)

- **Inputs:** `--freeze FREEZE_VALIDITY.json --log validity_log.jsonl --cases DIR`.
  - `FREEZE_VALIDITY.json` has the form `{"pairs": [{"id": "<neutral id>", "result": {...the validity_check JSON
    output...}}, ...]}`. Define this schema in the docstring; the designer writes the file.
- **For every pair, confirm:**
  - the result's five input hashes equal the current files in `<cases>/<id>/`;
  - the log holds a standard run (`--samples 1000 --seed 20261117`, not dev) with those hashes and `"decisive": true`;
  - that run is the first standard run with those hashes in the log;
  - its logged outcome fields (`valid`, `v1`, `v2`, `mech_a`, `mech_b`, `timing_ok`, `v1_label`) equal the result in
    the freeze.
- **Output:** a per-pair JSON report. Exit 0 if every pair passes and 1 otherwise.
- **Tests:** synthetic logs that cover a pass, a missing run, a hash mismatch, a non-decisive run cited, and an outcome
  mismatch.

## 5. `miss_label.py` (R3-4)

- The (e) label through the **fixed** twin applies only when the faulty twin is PB-detected. The fixed-twin cases are
  `--fixed-attrition`, a fixed load error and no fixed certificate.
- When the faulty twin is not PB-detected, the labels (a), (b) and (d) apply as usual and need no fixed certificate.
  Record `fixed_attrition` as a note.
- The faulty twin's causes stay first.
- **Tests:** fixed attrition with a PB-detected faulty twin gives (e). Fixed attrition with a faulty twin that is not
  PB-detected gives (a), (b) or (d) as the inputs imply.

## 6. `clean_pass_class.py` (R3-5, R3-14)

New class rule, in this order:
- **(e)** As now, plus a new option `--attrition CAUSE`, for an invalid skeleton, a part-B "no" or any other cause
  given by the designer. It needs no certificate.
- **(1)** As now: some flagged rate stream has a fresh 95% interval above the size. A rate flag is `K2_HIGH_SIZE`
  (on `world:minus`) or `HIGH_RATE:<s>`.
- **(2)** There is a rate flag, and (1) does not apply. In addition, apart from the rate flags, the component carries
  no mandatory flag and no study-level flag.
- **(3)** Apart from rate flags that (1) did not confirm, the failure flags are only:
  - `K2_NO_SEPARATION`, `K2_HOLDS_UNREACHABLE`, `K2_LOW_POWER`;
  - `K4_CONTROL_ALSO_HOLDS`, `K5_HOLDS_ON_*`.

  The clause "whose stream carries no rate flag" is dropped. Since (1) runs first, any rate flag left at this point is
  one the fresh samples did not confirm.
- **(4)** Everything else.

Record `unconfirmed_rate_flags`, listing the streams with their relation, whenever rate flags were sampled and the
class is not (1).

Tests: a rate flag together with each of these other failure flags:
- `K2_NO_SEPARATION` → (3);
- `K5_HOLDS_ON_NOISE` on the same stream as an unconfirmed `HIGH_RATE:probe:noise` → (3);
- `K4_NO_CONTROL` → (4);
- a study-level flag → (4).

Also test `--attrition`.

## 7. `shuffle_d.py` (R3-7)

- **`--subset IDS.json`:** a JSON list of neutral ids, the pairs and decoys of `FREEZE_VALIDITY.json`.
- With `--subset`, re-cut batches of 12 over those ids, in neutral-id order; the last batch is shorter.
- Write the new batch files under a new name, `batches_subset_NN.json`, and leave the item-2 files unchanged.
- The neutral ids and the private map are never changed.
- **Tests.**

## 8. `scan_docs_d.py` (R3-13)

- Add the substring tokens "Phase D", "decoy" and "checklist".
- Update the difference table in the docstring.
- Update the test.

## 9. The acceptance set (R3-6)

**New folders.** Add seven folders to `tests/acceptance_d/`, built like the existing ones: gate-consistent flags and
bounds from the gate's own check functions; n = 200; `expected_flags.json` as now. Each must be gate-consistent. If one
cannot be, say why and build the closest consistent pair. The paths:
1. `k2_no_separation_only`: the faulty twin is NOT_FALSIFIABLE with `K2_NO_SEPARATION` as its only expected flag.
2. `faulty_not_nf_with_rate_flag`: the faulty verdict is not NOT_FALSIFIABLE (for example UNDEFINED or WEAK), yet it
   has components and carries an expected rate flag.
3. `faulty_nf_unexpected_mandatory`: the faulty twin is NOT_FALSIFIABLE only through a mandatory flag that is not
   expected, for example `K5_HOLDS_ON_DEGENERATE`.
4. `generic_and_declared`: a detection whose qualifying streams include `probe:noise` and a declared stream.
5. `fixed_missing_stream`: the faulty twin's expected rate flag is on a stream that has no count in the fixed twin.
6. `fixed_hard_undefined_other_stream`: the fixed twin has `hard_undefined > 0` on a stream other than the faulty
   twin's flagged stream s (so the fixed verdict may be UNDEFINED), and s itself would qualify.
7. `fixed_k4_blocks_high_rate_control`: a fixed `K4_CONTROL_ALSO_HOLDS` whose bounds condition maps to control c
   blocks a faulty `HIGH_RATE:control:c`.

Extend `README.md` with the same kind of description. State no expected outcome.

**New test** `tests/test_acceptance_d_expected.py`:
- It reads `tests/acceptance_d/EXPECTED.json`, which the designer writes, with the schema `{"<folder>":
  {"attributable": bool, "generic": bool, "declared": bool, "qualifying_streams": [sorted list]}}`.
- It runs `attributable.py` on every folder and asserts equality on those four fields.
- It asserts that every folder has an entry.

The designer has written entries for the 13 existing folders. The 7 new ones will be added after your report, so this
test is expected to fail on the 7 new folders until then. Report that failure as expected; do not write those entries.

## 10. Run and report

- Run the full suite with `py -I -B -m unittest discover -s tests` from `tools/`.
- Leave no `__pycache__`.
- Report:
  - the files changed or added;
  - the test count and the failures, which should be only the 7 expected ones;
  - for each new acceptance folder, the faulty and fixed flags and the counts on the relevant streams;
  - every interpretation you made.
