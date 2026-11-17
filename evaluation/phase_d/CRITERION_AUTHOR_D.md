# Instructions for criterion authors, Phase D

You are the **criterion author** of one half of one class in a pre-registered evaluation of Truth_Gate. Another agent
wrote the briefs and private notes of your cases. For each case you write two criterion bodies:
- the **faulty** one carries the documented error;
- the **fixed** one carries the documented correction.

No worlds exist yet. Other agents write them later, from the brief alone.

## What you may read

- Your sandbox folder:
  - this file;
  - your half's folder: `BRIEFS.json`, `PRIVATE.json`, `LOG.md` and source extracts from the brief author, and
    `cases\<id>\brief.json`;
  - `SOURCES.md`, `SOURCES_D.md`;
  - `agent_docs/` (the tool's documentation) and `pkg/` (the tool's code).
- The sources themselves online. Log every URL. Fetch nothing from the project's code repository or its evaluations.

Do not read anything else on this machine. Do not run Truth_Gate in any form. Do not start any other agent or any tool
that runs a model. Do not use any context-mode tool (`ctx_*`), and no scratch folder outside your sandbox. Write only
inside your half's folder: the case files, `LOG.md` (append a "Criteria" section), and scratch scripts in `work\`, which
are kept as part of the record.

## What to write, per case: `cases\<id>\faulty_body.py` and `cases\<id>\fixed_body.py`

1. **Form.** Each file holds, at module level, only the line `import numpy as np` and function definitions. One of
   them is `def criterion(d):`, with a docstring that lists every data key with its shape and meaning. Helper functions
   may be module-level functions or be defined inside `criterion`. No decorators. `criterion` takes exactly `d`, with
   no default value and no annotation. No `global` or `nonlocal`. A helper's default values are literals (numbers,
   strings, `None`, `True`/`False`, or tuples of these). A function reads only its own parameters and locals, the
   file's functions, `np` and Python builtins. The two files are identical except for the error and its correction. A
   script checks this form; anything else at module level is rejected.
2. **Faulty:** the error documented in the private note, with the documented parameters, or the typical values the
   source states.
3. **Fixed:** the documented or a standard correction, and nothing else. It keeps the same statistic family, threshold,
   decision rule and model family, and the same computational structure apart from the error. The fixed criterion
   estimates the quantity the claim is about; the private note names it.
4. **Inputs.** Only `d`, `numpy`, and constants from the claim or the source (thresholds, documented parameters). The
   criterion must not depend on how any world will be built.
5. **Return value.**
   - `True` when the claim, with its statistic and threshold, is supported; `False` when it is not.
   - `None` only from an **allowed guard**. The list is exhaustive: non-finite values; an empty selection or one below
     the minimum stated in the private note (no more than the smallest size at which the statistic is defined); a zero
     variance.
   - The documentation's advice to return `None` when there is nothing to claim does not widen this list.
   - Nothing else may inspect the input's distribution; in particular, no test of whether the data look like noise or
     zeros, and no branch whose purpose is to behave differently on the tool's probes.
   - Let a genuine error raise.
6. **Randomness** only through `rng = np.random.default_rng(<integer>)`, created inside the criterion and the same in
   both files. Never `np.random.<function>`. The same data give the same answer.
7. **Speed.** A check of the fixed criterion must stay within about 30 minutes. Make the criterion as fast as it can be
   without changing what it computes, and mirror the speed-ups in the faulty one.

## Checks you may and may not run

- **Never run, simulate or pre-check the faulty body** in any form. The only operation allowed on `faulty_body.py` is a
  syntax check:
  `py -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" faulty_body.py`.
- You may run the **fixed** body on arrays that you generate yourself with the brief's keys, shapes and dtypes, to check
  that it runs, returns a bool and is fast. Do not tune it to any rate; there is no world to tune it to.
- Log every such run and every revision of the fixed body.

## `CASE.md` (one per case, written last)

1. Case id, class, subtype or tag.
2. Source key and documenting passage (a quote of at most 2 sentences, or its location; who read it and how).
3. The brief.
4. **Mapping**, line by line: which lines of `faulty_body.py` carry the error, with its parameters and where they are
   documented, and which lines of `fixed_body.py` carry the correction. Then the estimand line.
5. The allowed-guard minimum used.
6. The runs of the fixed body: what, how many, the timing on your own arrays.
7. Deviations from the private note, and problems (or "none").

## Decoys

If your task is the decoy cases, the same rules apply to them.

## Repairs

A later check may send one of your cases back for one repair. The request names the file and quotes only the failing
item, or a script's error list. It never contains a count, a rate or a test result from any later check. Change only
that file, log the change, and confirm that you saw no rate. You may be resumed for this, or a fresh agent of your role
may do it after reading your log.

## Order and interruptions

Work case by case and write `CASE.md` last; a successor continues with the cases that have no `CASE.md`.

## Final message

For each case, report:
- done or not, and the number of fixed-body revisions;
- deviations from the private note.

Confirm that you never ran the faulty body or Truth_Gate. List what you read (files and URLs).

## Differences from Phase C's `AUTHOR_PHASE2_C.md`

| Phase C | Phase D |
|---|---|
| criteria written into copies of a frozen skeleton, after the worlds | two body files written before any world; `tools/assemble.py` splices them into every skeleton |
| reads the pre-registration texts | reads no pre-registration text; the rules it needs are in this file |
| pre-checks of the fixed criterion on the skeleton's worlds | runs of the fixed body only on self-generated arrays, to check that it runs and how fast; no rates |
| timing on the skeleton (≤ 900 s), size request | about 30 minutes; the designer measures timing on every world set |
| one author per class | one author per class half (and one for the decoys), not the brief author |
| helpers inside the criterion | helpers at module level or nested; only `import numpy as np` and function definitions at module level |
| — | a repairs section; repair requests carry no rates |
| no context-mode rule | no context-mode tool, no scratch folder outside the sandbox, no other agent |
| everything else | the same (only the error differs; inputs; allowed guards; never run the faulty criterion; seeds; return values; `CASE.md`) |
