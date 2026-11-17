# Phase D tools, round 2: changes after review 2

Work in `E:\Claude Projects\Kapi\phase_d_private\tools\`, with the tools in `tools\` and the tests in `tests\`. Same
rules as `TOOLS_SPEC_D.md`: py 3.14 and numpy only; no git; do not write into `E:\Claude Projects\kapi-oss`. Read
`../review2_digest.txt`; it is the reviewer's text, and the finding ids (R2-n) below refer to it. Where this spec and the
digest differ, this spec decides. Where this spec is unclear, stop and report.

## Changes to existing tools

1. **`attributable.py`** (R2-2, R2-23).
   - If the faulty body has no component or carries `load_error`: return `pb_detected=False` with the reason "faulty
     load error". No exception.
   - If the fixed body has no component or carries `load_error`: no stream qualifies, with the reason "fixed load
     error".
   - If the fixed counts on s have `hard_undefined > 0`: s does not qualify, with the reason "fixed hard UNDEFINED on
     s".
   - `K4_CONTROL_ALSO_HOLDS` maps to the control streams s with `bounds[s]["upper"] >= bounds["world:plus"]["lower"]`
     in that certificate. `K5_HOLDS_ON_SHUFFLE` maps to the shuffle streams with the same condition. Check against
     `truth_gate/checks.py` (`check_k4`, `check_k5`, the SL rule) that this is the gate's condition. If it is not, report
     it and implement the gate's condition, citing file and line.
   - Tests: a real load-error body (`{"verdict": "UNDEFINED", "components": [], "load_error": {...}}`) for each twin; a
     fixed body with `hard_undefined > 0` on the qualifying stream; K4 with two controls, only one of them meeting the
     condition; a shuffle with two pairs.
   - The Phase C fixture must still hold.
2. **`validity_check.py`.**
   - (R2-14) Band: `|mean - note_value| <= 0.2 * |note_value - null_value|` for both worlds; no special case at 0.
     Equality between the worlds as before.
   - (R2-7) New flag `--no-structure`, accepted only when `PRIVATE.json["structure_statistic"]` is null. It skips
     mech_a and the structure check, records `"structure": "not used (decoy)"`, and `valid` no longer requires them.
   - (R2-19) Timing: measure t (the mean time of the fixed criterion on 20 reference plus samples from
     `stream_rng(seed, "timing:plus", i)`, outcomes not recorded) and g (the mean plus generation time over the same 20).
     Compute S as the gate's stream count for the fixed reference study (worlds + controls + premises + relational
     pairs + 2), and the estimate `2*200*(S+1)*(t+g)` in seconds. Add `timing_ok = estimate <= 1800` to `valid`.
   - (R2-25) Only `--samples 1000 --seed 20261117` are validity runs. Any other values require `--dev`, which writes
     `"dev": true` to the result and the log; `--dev` is refused when `--case` points into a folder named `cases`
     (case folders).
   - (R2-11) An exception, a bad return or a failed generation sets `error_in = "V1" | "V2" | "mech" | "structure" |
     "timing"`, with the error text; `valid` is false.
3. **`check_skeletons_d.py`** (R2-8). `brief.json` gets, per data key, `"dims": [int, ...]`. The check requires
   `a.shape == tuple(dims)` for every key, in every world draw, control output and premise output. In `--case` mode it
   also requires identical shapes across `reference.py`, `W0.py` and `W1.py`. Correct the docstring to 1000 ms (R2-31)
   and add the 250 ms target: keep `MAX_MS = 1000` as the hard rejection; world instructions will ask for at most
   250 ms. Tests: a transposed key; a key whose size equals a number in the claim; shapes differing between arms.
4. **`assemble.py`** (R2-29). Body files may contain only `import numpy as np` and function definitions at module
   level; anything else is refused. Exactly one of the functions must be `criterion`.

## New tools (each with tests)

5. **`mech_check_bodies.py`** (R2-17). For each body file:
   - the module-level rule of item 4;
   - the banned names, numpy file functions and dunder attributes, exactly as `check_skeletons_d.py` bans them;
   - every comparison (`<`, `<=`, `>`, `>=`, `==`, `!=`) in which one side is a call of mean, var, std, min, max, all,
     any, `linalg.norm`, `np.isnan`, `np.isfinite`, ptp or median (as `np.f(...)` or `x.f()`) and the other side is a
     numeric constant. List each with its file, line and text in `MECH_CHECK.json`;
   - for the assembled files: the default `Budget` and `Targets` (no budget, targets or deterministic keyword in
     `STUDY`).

   CLI: `--case DIR --out MECH_CHECK.json`.
6. **`clean_pass_class.py`** (R2-1). It runs only after the run. Inputs: the fixed study file of one arm, its
   certificate, the package root. For each failed clean pass it assigns the first class that applies:
   - **(e) attrition or no verdict:** a load error, K1_UNDEFINED, UNTESTED, or a timeout marker given by `--timeout`;
     the cause is listed.
   - **(1) fixed not clean in these worlds:** for each stream s with a rate flag of the fixed twin (K2_HIGH_SIZE, or
     `HIGH_RATE:*` on s), draw 1000 fresh samples of s from the same declared study, with the seed 20261117 and the
     stream name `classify:<s>`, and evaluate the fixed criterion. Class (1) applies when the 95% two-sided Wilson
     interval of that fresh rate lies entirely above the declared size.

     The gate builds the samples of control, noise, null and shuffle streams in a particular way. Mirror it, citing
     file and line (as in `validity_check`).
   - **(2) possible false alarm:** for every flagged rate stream, the fresh interval includes the size.
   - **(3) fixed weak in plus:** the failure comes only from `K2_NO_SEPARATION`, `K2_HOLDS_UNREACHABLE`,
     `K2_LOW_POWER`, or a relative flag (`K4_*`, `K5_HOLDS_ON_*`) whose stream does not carry a rate flag.
   - **(4) other:** listed with its flags.

   CLI and JSON output.
7. **`miss_label.py`** (R2-4). It runs only after the run, per pair and arm. Inputs: both certificates, the expected
   flags, the private note, the arm's faulty study file and `--attrition CAUSE` (optional). The labels, in this order:
   - **(e)** attrition or no verdict (the cause given, or the faulty verdict UNDEFINED or UNTESTED, or a load error);
   - **(c)** PB-detected but not attributable (use `attributable.classify`);
   - **(a)** structure share below 0.5 (`structure_stat` on 200 minus samples of the arm's world, stream
     `structure:minus`, seed 20261117); not applied when `set_by_brief` or no statistic. "structure not computable" if
     the statistic raises;
   - **(b)** faulty minus count below `kstar_arm`, computed from that arm's study through `count_comparisons`;
   - **(d)** "other: examined as a possible gate finding".

   Detected pairs get no label.
8. **`expected_flags_d.py`** (R2-18). From an assembled faulty study per arm, it enumerates PC §6's expected list:
   - the base list;
   - `HIGH_RATE:control:<id>` for each declared control;
   - `HIGH_RATE:probe:shuffle:<a>,<b>` for each relational pair.

   It writes `EXPECTED_FLAGS_D.json` with `{"cases": {"<id>/<arm>": {"expected": [...]}}}`. Check the base list against
   `E:\Claude Projects\kapi-oss\evaluation\phase_c\EXPECTED_FLAGS.json["base"]`.
9. **`shuffle_d.py`, `scan_docs_d.py`, `term_check_d.py`** (R2-18). Copies of `evaluation/phase_c/tools/shuffle.py`,
   `scan_docs.py` and `term_check.py`, each with a difference table in its docstring.
   - **`shuffle_d.py`:**
     - the seed is `int(sha256(bytes of FREEZE_PREREG_D.json + b"phase-d-shuffle"), 16)` and the shuffle is
       Fisher-Yates with `random.Random`;
     - the input is the list of all briefs and reserves (B-2, B-3 and decoys) with designer ids;
     - it assigns a neutral id `D-<3 digits>` in shuffled order;
     - it writes batches of 12 consecutive briefs (the last shorter), the same batch files for W-0 and W-1, and the
       private map file (neutral id → class, half, source, subtype or tag, reserve flag). The map never goes into a
       batch file.
   - **`scan_docs_d.py`:** PC's scan list plus "validity audit", "case-world", "case-size", "case-fixed",
     "sub-threshold", "attributable", the six B-2 subtype names, and the five B-3 tag names of PC's list.
   - **`term_check_d.py`:** PC's banned terms unchanged.

## The independent acceptance set (R2-3): you write only the synthetic certificates

Write `tests/acceptance_d/` with synthetic certificate pairs: minimal bodies in the gate's format, with `verdict`,
`components[0]` holding `flags`, `counts` (`holds`, `n`, `hard_undefined`) and `bounds`, and `load_error` when needed.
Write one pair per path, and name each folder after its path:
- (a) true and (b) false;
- (a) false through each flag kind: K2_HIGH_SIZE, HIGH_RATE control, HIGH_RATE noise, K5_HOLDS_ON_NULL, a shuffle;
- K4 with two controls, one meeting the bounds condition;
- a shuffle with two pairs;
- a fixed load error;
- a faulty load error;
- a fixed hard UNDEFINED;
- generic only, through `K5_HOLDS_ON_NOISE`;
- declared only.

Do **not** write the expected outcomes: the designer writes `tests/acceptance_d/EXPECTED.md` by hand from the
pre-registration text, and a separate agent writes an independent recomputation. Write a `README.md` there that lists,
for each folder, the counts, flags and bounds in plain words.

## Report

- The files changed or written.
- The test command and its full summary.
- How the gate's K4/K5 SL rule and the classify streams were mirrored (file and line).
- Anything unclear.
