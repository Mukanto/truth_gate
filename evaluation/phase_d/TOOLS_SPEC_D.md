# Phase D tools: specification for the coding subagent

This is the work folder: `E:\Claude Projects\Kapi\phase_d_private\tools\`. Write everything there, under `tools/` and
`tests/`. It is private: do not write into the repository `E:\Claude Projects\kapi-oss`, and do not commit or push
anything. You may read the repository.

- **Python.** Use `py` (Python 3.14, numpy). Use the standard library and numpy only; no scipy in the tools.
- **The gate.** Every tool takes `--package-root DIR` and imports `truth_gate` from it, inserted first on `sys.path`.
  Like `evaluation/phase_c/tools/check_skeletons.py`, it refuses with exit code 2 if `truth_gate` resolves elsewhere.
  For development and tests the root is `E:\Claude Projects\kapi-oss` (the gate at 0.5.1).
- **Background.** Read `PREREG_PHASE_D_draft2.md` (in this folder's parent) sections 2, 3 and 5. The tools implement
  them. Where this spec and the draft disagree, stop and ask (report it); do not choose.

## Case folder layout (input to the tools)

```
<case>/brief.json          {"id", "claim", "data_keys": [{"key","shape","dtype","meaning"}], "sizes"}
<case>/PRIVATE.json        private note; contains "structure_statistic" (below) and "class", "subtype_or_tag"
<case>/faulty_body.py      helper functions + exactly one `def criterion(d):`; only `import numpy as np`
<case>/fixed_body.py       same form
<case>/reference.py        a skeleton in PC's format (see evaluation/phase_c/WORLD_INSTRUCTIONS_PHASE_C.md): plus, minus,
                           at least one Control, and the placeholder `def criterion(d): ... raise NotImplementedError`
<case>/skeletons/W0.py, W1.py   world-author skeletons, same format (later stage; the tools must accept them)
```

`PRIVATE.json["structure_statistic"]`:

```json
{"code": "def stat(d):\n    ...\n    return float(value)",
 "direction": "greater" | "less", "null_value": 0.0, "note_value": 0.4, "set_by_brief": false}
```

`code` defines `stat(d)` from the brief's data keys only. It is executed with `numpy` (as `np`) as the only global. It
must return a finite float.

## 1. `tools/assemble.py`

- **Function** `assemble(skeleton_src: str, body_src: str) -> str`.
- **What it does.**
  - Finds, with `ast`, the module-level function `criterion` of the skeleton. It must have exactly one statement after
    an optional docstring, and that statement must be `raise NotImplementedError`.
  - Replaces that function's full line range (decorators: none allowed) with the body file's source, minus its own
    `import numpy as np` line (the skeleton imports numpy).
  - Checks the result: it parses; it has exactly one module-level `criterion`; it has no duplicate top-level names
    between the skeleton and the body (raise on conflict); and the skeleton's `STUDY` still refers to
    `Criterion("C", criterion)`.
- **CLI.** `assemble.py --skeleton S --body B --out OUT`.
- **Function** `differ_only_in_criterion(study_a_src, study_b_src) -> bool`. It is true when two assembled files differ
  only inside the inserted body region. It is used as the per-arm single-difference check.

## 2. `tools/structure_stat.py`

- **Function** `structure_stat(study_module, private, world, samples, seed, package_root)`.
  - `world` is "plus" or "minus". The samples are drawn with `truth_gate.sampling.stream_rng(seed, f"structure:{world}", i)`,
    i = 0..samples-1, from the module's world function.
  - It applies `stat` to each sample.
  - It returns `{"mean", "sd", "values_head": first 5, "share_beyond_half"}`. The share counts samples at or beyond
    `null + 0.5*(note_value - null)` in the stated direction (`>=` for greater, `<=` for less). When `set_by_brief` is
    true it returns `{"set_by_brief": true, "mean"}` and no share.
- **CLI.** `structure_stat.py --study FILE --private PRIVATE.json --world minus --samples 200 --seed 20261117
  --package-root DIR`. It prints JSON.

## 3. `tools/validity_check.py`

- **CLI.** `validity_check.py --case DIR --package-root DIR --samples 1000 --seed 20261117 --log validity_log.jsonl
  --out RESULT.json`.
- **Steps**, all on samples from `stream_rng(seed, "validity:<stream>", i)`. These stream names are never used by the
  gate, and the seed 20261117 is not the gate's default base seed.
  1. Assemble `faulty_R` and `fixed_R` in memory from `reference.py` and the two bodies (`assemble`), and load each as
     a module (module name unique per call).
  2. **Mechanical checks of PREREG §2.2.**
     - (a) `structure_stat` on 200 `plus` and 200 `minus` samples, each mean within ±20% of `note_value`. When
       `note_value` is 0, use an absolute tolerance of 0.05. The two means are equal within sampling error:
       |mean_plus − mean_minus| ≤ 3·sqrt(sd_p²/200 + sd_m²/200).
     - (b) The gate's own minus analysis (`truth_gate.minus.analyse`, as `truth_gate/checks.py` calls it) on the fixed
       study reports at least one changed key among the keys the fixed criterion reads. Mirror the gate's call; do not
       re-implement it.
     - With `set_by_brief`, (a) checks only that the statistic is computable.
  3. **V1.** Faulty and fixed on `samples` minus samples. It passes when `faulty_holds/samples >= 0.25` and the
     one-sided Fisher exact p (faulty > fixed) is below 0.01. On failure it labels:
     - **V1a**: `faulty_holds/samples < kstar/200`, where `kstar` is the smallest k of 200 with
       `wilson_lower(k, 200, bonferroni_a(alpha_family, m)) > size`. `m` comes from the gate's `count_comparisons` on
       the faulty study, and `alpha_family` and `size` from its targets.
     - **V1b**: every other failure.
  4. **V2.** Fixed on `samples` minus samples (at most 0.065), on `samples` noise-probe samples (at most 0.065), and on
     `samples` plus samples (at least 0.70). A noise-probe sample is the gate's `noise_probe` applied to a plus sample,
     with an rng from `stream_rng(seed, "validity:noise", i)`; follow how `truth_gate/checks.py` builds the noise
     stream, with the validity seeds.
  5. A criterion returning `None` counts as not-holds (as the gate's K2 does). An exception is recorded, and makes the
     check fail with the reason "error".
- **Output.**
  - `RESULT.json` holds every count, rate, p, `m`, `kstar` and pass/fail with the reason (`v1`, `v1_label`, `v2`,
    `mech_a`, `mech_b`, `structure_computable`, `valid`).
  - The log gets one JSON line appended: case id, UTC time, SHA-256 of each input file and of `validity_check.py`
    itself, seed, samples, and the result.
  - The exit code is 0 if valid, 1 if not, 2 on a usage error.
- **Speed.** Generate each sample once per stream and reuse it for both twins.

## 4. `tools/attributable.py`

- **Function** `classify(faulty_cert: dict, fixed_cert: dict, expected: list[str]) -> dict` (bodies as in a gate
  certificate's `body`).
- **Rate flags and their streams:**
  - `K2_HIGH_SIZE`, `K2_FAILS_UNREACHABLE` → `world:minus`;
  - `K5_HOLDS_ON_NOISE`, `HIGH_RATE:probe:noise` → `probe:noise`;
  - `K5_HOLDS_ON_NULL`, `HIGH_RATE:world:null` → `world:null`;
  - `K5_HOLDS_ON_SHUFFLE` → every `probe:shuffle:*` stream in the counts;
  - `K4_CONTROL_ALSO_HOLDS` → every `control:*` stream in the counts;
  - `HIGH_RATE:<stream>` → `<stream>`.
  - Anything else is not a rate flag.
- **Rule.** The pair is detected (PB-style) if the faulty verdict is NOT_FALSIFIABLE and a faulty flag is in
  `expected`. It is attributable if, in addition, some expected rate flag of the faulty twin on a stream s has both:
  - (a) no rate flag of the fixed twin mapping to s;
  - (b) faulty holds on s greater than fixed holds, with a one-sided Fisher exact p < 0.05, from the counts' `holds`
    and `n`.

  If the fixed twin has no counts for s, s does not qualify, and the reason is listed.
- **Labels.** `generic` is true if `probe:noise` qualifies; `declared` is true if a qualifying stream other than
  `probe:noise` exists. Also compute `draft1_rule`: some expected rate flag on s with faulty − fixed ≥ 20 (of 200) and
  Fisher p < 0.05.
- **Returns** `{"pb_detected", "attributable", "generic", "declared", "draft1_rule", "qualifying": [...],
  "reasons": [...]}`.
- **CLI.** `attributable.py --faulty F.json --fixed X.json --expected-file EXPECTED.json --case ID`. The expected file
  is in PC's `EXPECTED_FLAGS.json` format (a dict with "cases"; each case has "expected").
- **Acceptance test** (`tests/test_attributable.py`), on the read-only Phase C files
  (`E:\Claude Projects\kapi-oss\evaluation\phase_c\run\certs\v050\<id>\{faulty,fixed}.json` and that folder's
  `EXPECTED_FLAGS.json`). Over all B2-* and B3-* pairs, exactly:
  - PB-detected: B2-01, B2-02, B2-08, B2-09, B2-10, B2-11, B2-12, B3-01, B3-04, B3-05, B3-06, B3-08, B3-09, B3-11,
    B3-12;
  - attributable: B2-01, B2-02, B2-12, B3-01, B3-04, B3-05, B3-06, B3-08, B3-09, B3-11;
  - attributable and declared: as above, without B3-04 and B3-05;
  - not attributable among the PB-detected: B2-08, B2-09, B2-10, B2-11, B3-12.

  (The designer's own computation, `../fixture_attributable_pc_output.txt`, gives these. If your tool disagrees, report
  the disagreement with the numbers; do not change the expected lists.)
- **Fisher's test.** Implement it exactly with `math.comb`. Test it against at least three hand-checked values, for
  example a = 86, n1 = 200, b = 47, n2 = 200 gives p ≈ 2.53e-05.

## 5. `tools/check_skeletons_d.py`

A copy of `evaluation/phase_c/tools/check_skeletons.py`, with only these changes:
- the size caps are 2000 per axis and 2 000 000 elements per array;
- the time limit per world call or control is 1000 ms;
- it accepts `reference.py`, `W0.py` and `W1.py` from a case folder (`--case DIR`) as well as the PC layout.

Keep a short table of differences at the top of its docstring.

## Tests and report

- `tests/` holds unittest tests for every tool, and they run with `py -I -B -m unittest discover -s tests` from the work
  folder. Build a small toy case in a temporary folder for `assemble`, `structure_stat` and `validity_check`. It needs:
  - a time-series brief;
  - a faulty body that uses shuffled folds;
  - a fixed body that uses forward folds;
  - a reference world with AR(1) structure.

  It should show V1 passing when the autocorrelation is strong and failing (V1a) when it is 0. Keep the toy quick: use
  `--samples 200` in tests.
- Run the tests yourself and report their output.
- Report: the files written; how you mirrored the gate's minus analysis and noise stream (file and line); any point
  where this spec was unclear or contradicted the draft.
