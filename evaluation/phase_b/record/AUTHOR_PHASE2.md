# Instructions for criterion authors, phase 2 (criterion bodies)

You are the **criterion author** of one class in a pre-registered evaluation of Truth_Gate, a tool that checks whether
the acceptance criteria of computational studies can fail. The rules are frozen in
`E:\Claude Projects\kapi-oss\evaluation\phase_b\PREREG_PHASE_B.md` (read all of it; §2, §3, §4 step 5 and §5 matter most
here) and the sources are listed in `E:\Claude Projects\kapi-oss\evaluation\phase_b\SOURCES.md`.

The briefs of your class were written earlier by another agent in the same role, whose session has ended. You continue
that role: its private notes (`PRIVATE.json`), its log (`LOG.md`) and the source extracts it saved (`src\`, `*.txt`) are
in your class folder. A separate world author, who never saw those notes, the class or the sources, wrote a study
skeleton for each brief; the skeletons are frozen. Your job is to write, for each case, the **faulty** and the **fixed**
criterion inside a copy of its skeleton.

## What you may read

* Your class folder (given in your task) and everything in it.
* `PREREG_PHASE_B.md` and `SOURCES.md` in `E:\Claude Projects\kapi-oss\evaluation\phase_b\`.
* Public documentation: `E:\Claude Projects\kapi-oss\README.md`, `docs\GATE.md`, `docs\MANIFEST.md`, `docs\SPEC.md`.
* The sources themselves (online), if you need to check a passage or a parameter.

Do **not** read anything else: not the other class folders, not the parent folder's other files or the `world\`
folder, nothing else under `E:\Claude Projects\kapi-oss\` (no `truth_gate\`, `kapi\`, `tests\`, `examples\`, other
`evaluation\` files) and nothing under `E:\Claude Projects\Kapi\`. Do **not run Truth_Gate** in any form or version (no
`truth-gate`, `python -m kapi`, `python -m truth_gate`, `run_gate`, no call of any gate function). You may import the
package only so that a case file loads (put `E:\Claude Projects\kapi-oss` on `sys.path`; `from kapi import ...` then
works) and call its world functions and the fixed criterion yourself.

Write only inside your class folder: the case files, `LOG.md` (append), and scratch scripts in `<class folder>\work\`
(they are kept as part of the record).

## Your cases

`<class folder>\cases\<case id>\` holds, per case:

* `ASSIGNMENT.json`: the case id, the world id, the class and subtype assigned by the designer, the source, and the
  brief exactly as the world author received it.
* `skeleton.py`: the frozen skeleton (reference copy; **never edit it**).
* `faulty.py` and `fixed.py`: two identical copies of the skeleton, in which you write the two criteria.

## What to write in `faulty.py` and `fixed.py`

1. **Replace only the line `    raise NotImplementedError`** of `criterion(d)` with your analysis. Keep the docstring.
   Nothing else in the file may change: no new imports, no module-level code, no change to worlds, controls, premises
   or `STUDY`. The two files must be byte-identical outside the body of `criterion`. Helper functions, if you need
   them, are defined inside the body.
2. **Faulty:** the error documented in your private note, with the parameters the source documents (or the typical
   values it states). **Fixed:** the documented or a standard correction **and nothing else**: same statistic, same
   threshold, same decision rule, the same computational structure apart from the error (audit items (a), (b), (c),
   (g) in §5).
3. The private note was written against the brief, before the skeleton existed. Adapt the analysis to the skeleton's
   actual keys and shapes; keep the error and its parameters. If you must deviate from the note, say how and why in
   `CASE.md`.
4. **Inputs.** The criterion uses only `d`, `numpy` and constants that come from the claim or the source (thresholds,
   documented parameters). It must not read any module-level name of the skeleton other than `np` (for example no
   `N`, no generator constants): the criterion must not know how the worlds were built.
5. **Return value:** `True` when the claim, with its statistic and threshold, is supported by the data; `False` when it
   is not; `None` only from an **allowed guard** (§2: non-finite values, an empty or too small selection, a zero
   variance). Nothing else may inspect the input's distribution; in particular no test of whether the data look like
   noise or zeros.
6. **Randomness** (folds, permutations, resampling) only through a generator created inside the criterion with a fixed
   integer seed, `rng = np.random.default_rng(<integer>)`, the same in both files. Never call `np.random.<function>`
   directly. The criterion must give the same answer when called twice on the same data.
7. Keep it fast (see Timing).

## Checks you may and may not run

* **Never run, simulate or pre-check the faulty criterion in any form**, on the worlds or elsewhere (not even "to see
  whether it works"). The only allowed operation on `faulty.py` is a syntax check: `py -c "import ast,sys;
  ast.parse(open(sys.argv[1],encoding='utf-8').read())" faulty.py`.
* You may pre-check the **fixed** criterion in plain Python: import `fixed.py` from a scratch script, draw samples from
  its `plus` and `minus` worlds (and, if you wish, the noise and zero probes as `docs\GATE.md` describes them) and count
  how often the criterion holds. Log every pre-check (what, how many samples, the rates) and every revision of the fixed
  criterion with its reason. If you revise the fixed criterion, the faulty one must mirror the final structure.
* If the fixed criterion often fails in `plus` or often holds in `minus`, do **not** change the skeleton and do not
  bend the analysis away from the documented correction to make it pass; record what you saw in `CASE.md`. A request to
  change a skeleton is granted only for a defect that makes the fixed criterion impossible to write (for example a
  missing key). In that case write the closest criterion you can, mark the case **SKELETON REQUEST** in `CASE.md` and
  `LOG.md`, and say why.

## Timing (§2)

On the final fixed criterion, measure the mean time `t` of one call on a `plus` sample (average over at least 20 calls)
and the mean time `g` of one `plus` generation. With `S` = number of worlds + controls + premises + relational pairs
declared in the skeleton, plus 2 for the probes, the estimate is `2 × 200 × (S + 1) × (t + g)` seconds. It must be at
most 900 seconds (15 minutes). If it is not, make the fixed criterion faster without changing what it computes, and
mirror the change in the faulty one.

## `CASE.md` (one per case, written last: it marks the case as done)

1. Case id, world id, class and subtype (from `ASSIGNMENT.json`).
2. The source key and the passage that documents the error: a quote of at most two sentences, or its location
   (section, page). Say whether you or the earlier author read it, and how (full text, abstract).
3. The brief exactly as in `ASSIGNMENT.json`.
4. One paragraph mapping the faulty criterion to the documented error (with its parameters and where they are
   documented) and the fixed criterion to the correction.
5. Pre-checks of the fixed criterion (each with its sample counts and rates) and the number of revisions.
6. Timing: `t`, `g`, `S`, the estimate.
7. Deviations from the private note, problems, skeleton requests (or "none").

## Order and interruptions

Work case by case and write `CASE.md` last. If your session is interrupted, a successor continues with the cases that
have no `CASE.md`. Append a "Phase 2" section to your class `LOG.md`: per case, the pre-checks, the revisions and any
problem.

## Final message

Report per case: done or not, the number of fixed-criterion revisions, the timing estimate, deviations and skeleton
requests; confirm that you never ran the faulty criterion and never ran Truth_Gate, and list what you read.
