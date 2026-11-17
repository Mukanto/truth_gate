# Validity audit of the B-2 and B-3 cases, Phase B

You are an independent auditor. You did not design these cases and you have not seen any report on them. Work only
with the files in this task folder.

## Background

Truth_Gate is a tool that checks a study's acceptance criterion before the study runs. The study declares synthetic
worlds: `plus`, where the claim is true, and `minus`, where it is false. It may also declare controls that break the
theory. The tool runs the criterion on samples from these worlds, on random noise and on all-zero data. It flags a
criterion that holds where the claim is false, that cannot be told apart across worlds, and similar problems. The flags
and verdicts are explained in `docs/GATE.md`.

In this evaluation each case is a **pair** of study files written from a literature source:
- `faulty.py` carries one documented analysis error;
- `fixed.py` is its twin with the documented correction.

The pre-registration (`PREREG_PHASE_B.md`) defines the scoring:
- a pair is **detected** when the faulty twin receives an expected flag (`EXPECTED_FLAGS.json`);
- it is a **clean pass** when the fixed twin receives no actionable flag.

Two classes did not meet the pre-registered bar: B-2 (procedure-level leakage) and B-3 (coupling by construction). This
audit asks how much of that result describes the tool, and how much describes the cases.

## The three questions

Ask them for every B-2 and B-3 pair in `cases/`:

- **(a) Adequacy of the synthetic worlds.** The documented error depends on some structure in the data. Is that
  structure present in the declared `minus` world (and, where relevant, in `plus`)? Is it present at a size comparable
  to the setting of the source?
- **(b) Representation of the error.** Does the faulty criterion implement the error that the source documents? Is that
  error the only difference from the fixed twin? For a detected pair: does the detection come from the error, or would
  the fixed twin have been flagged in the same way?
- **(c) Cleanliness of the correction.** Does the fixed criterion implement the documented correction? Is it a correct
  test of the claim on the declared worlds: does it rarely hold where the claim is false or on noise, and does it hold
  where the claim is true? If it is not clean, why not?

## Inputs (read-only; make your own writable scratch copy before running anything)

- `PREREG_PHASE_B.md`: rules and definitions.
- `EXPECTED_FLAGS.json`: the expected flags.
- `SOURCES.md`: the literature sources and what each documents.
- `cases/<id>/`: for each pair, `CASE.md` (source passage, brief, mapping, the criterion author's pre-checks),
  `faulty.py`, `fixed.py` and `ASSIGNMENT.json`.
- `certs/<id>/`: the binding certificates of the gate run (Truth_Gate 0.4.0). For each stream they give the number of
  samples on which the criterion held, out of 200, and the flags and verdicts.
- `RESULTS.json`: the scored outcome of every pair.
- `WORLD_INSTRUCTIONS.md`: what the world author was told.
- `docs/GATE.md`: the tool's reference.
- `truth_gate/` and `kapi/`: copies of the tool. You can import a case file and draw samples from its worlds. Running
  the gate again is not needed; the certificates hold its results.
- `after_part1/`: the evaluation's own report and its post-run audit. **Do not open anything in this folder until Part 1
  is written to `out/`.**

## Part 1: your own audit (before opening `after_part1/`)

For each pair, record the following. Give evidence for each answer: a file and line, a quoted passage, or a number from
a certificate or from your own computation.

- **id**, and the **outcome**: detected yes/no, and clean pass yes/no.
- **W1**: the structure that the error exploits, in one sentence.
- **W2**: is it present in the declared `minus` world? Answer yes, weak or no.
  - Where a single statistic captures the structure, draw samples and report the statistic. Examples: an
    autocorrelation, a within-group correlation, a number of features, a correlation induced by a shared term.
  - Say how you computed it (sample count, seed).
- **W3**: the data size (rows, features, time points) against the setting of the source. Quote the source line, or
  write "source states none".
- **R1**: does the faulty criterion implement the documented error, and differ from the fixed twin only by it? Answer
  yes, partly or no.
- **R2**: for a detected pair, is the detection attributable to the error? Answer yes, no or n/a.
  - Compare the faulty and fixed twins on the streams that carry the expected flags (counts from the certificates).
- **C1**: does the fixed criterion implement the documented correction? Answer yes, partly or no.
- **C2**: the fixed twin's counts on `minus`, the controls, the noise probe and `plus`, from the certificates. Then your
  judgment: clean, or not clean.
- **C3**: if not clean, the cause in your own words, with evidence.
- **Attribution** of the pair's scored result: does it describe the tool, or the case? Choose one:
  - `tool`: the case is adequate and the tool's behaviour decided the result;
  - `case-world`: the worlds lack the structure;
  - `case-size`: the structure is there but the data are too small to show it;
  - `case-error`: the error is not represented, or the twins differ by more than the error;
  - `case-fixed`: the fixed twin is not clean;
  - `mixed` or `unclear`.

  Add one line of reasons.

Then give a **class summary** for B-2 and for B-3:
- counts of each attribution, separately for misses, failed clean passes, and detections that are not attributable to
  the error;
- what the detection and clean-pass counts would be if every pair attributed to the case were left out.

Label this summary *post hoc*: it does not change the pre-registered result.

Write Part 1 to `out/AUDIT_PHASE_B.md` and `out/AUDIT_PHASE_B.json`. The JSON holds one object per pair with the fields
above, plus the class summary.

## Part 2: comparison (only after Part 1 is written)

Now read `after_part1/`. Append a section "Part 2" to `out/AUDIT_PHASE_B.md`, and a key `part2` to the JSON:
- for each pair where your attribution or explanation differs from the report's, state the difference and say which
  is better supported, with evidence;
- list any claim of the report about these pairs that you find unsupported or wrong;
- list anything the report explains that you missed.

Do not change Part 1 after you open `after_part1/`.

## Rules

- **Paths.** Read and write only inside this task folder. The one exception is the interpreter
  `E:\Claude Projects\.venv-qiskit\Scripts\python.exe`, which you may run (it has numpy). Run your scripts from your
  scratch folder, which holds copies of `truth_gate/`, `kapi/` and the cases.
- **No outside help.** No network, no git, no other agents. Do not try to find other versions of these files.
- **Do not edit the inputs.** Write only to `out/` and to your scratch folder.
- **Effort.** Prefer judging from the code. Compute a statistic only where it settles a W2 question. 200 samples per
  world is enough.
- **Honesty.** Write "unclear" when the evidence does not decide a question. Do not round a weak result into a strong
  one.
