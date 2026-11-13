# Instructions for criterion authors, Phase C, part 2 (criterion bodies)

You are the **criterion author** of one class in a pre-registered evaluation of Truth_Gate. The rules are frozen in
`PREREG_PHASE_C.md` (read all of it; §2, §4 item 5 and §5 matter most) and `PREREG_PHASE_B.md` (for the rules it cites),
both in your sandbox folder.

The briefs of your class were written by another agent in the same role. You continue that role: its private notes
(`PRIVATE.json`), its log (`LOG.md`) and any source extracts are in your class folder. A separate world author (a
different model, which never saw those notes, the class or the sources) wrote a study skeleton for each brief; the
skeletons are frozen. You write, for each case, the **faulty** and the **fixed** criterion inside copies of its skeleton.

## What you may read

* Your sandbox folder: your class folder, `PREREG_PHASE_C.md`, `PREREG_PHASE_B.md`, `SOURCES.md` (keys and references),
  `SOURCES_ADDENDUM.md`, `agent_docs/` (the documentation of Truth_Gate 0.5.0) and `pkg/` (its code).
* The sources themselves online (log every URL); nothing from the project's code repository or its earlier evaluations.

Do not read anything else on this machine. Do **not run Truth_Gate** in any form or version. You may import the package
only so that a case file loads (put `pkg/` first on `sys.path`), and call its world functions and the fixed criterion
yourself. Write only inside your class folder: the case files, `LOG.md` (append), and scratch scripts in
`<class folder>\work\` (they are kept as part of the record).

## Your cases

`<class folder>\cases\<case id>\` holds `ASSIGNMENT.json` (case id, world id, class, subtype, source, the brief),
`skeleton.py` (frozen reference copy; never edit it), and `faulty.py`, `fixed.py` (two identical copies of the skeleton).

## What to write in `faulty.py` and `fixed.py`

1. **Replace only the line `    raise NotImplementedError`** of `criterion(d)`; keep the docstring. Nothing else in the
   file may change: no new imports, no module-level code, no change to worlds, controls, premises or `STUDY`. The two
   files are byte-identical outside the body of `criterion`. Helper functions are defined inside the body.
2. **Faulty:** the error documented in the private note, with the documented parameters (or the typical values the
   source states). **Fixed:** the documented or a standard correction and nothing else: same statistic family, same
   threshold, same decision rule, the same computational structure apart from the error (audit items (a), (b), (c), (g)).
   The fixed criterion estimates the quantity the claim is about (audit item (i)); the private note names it.
3. The private note was written against the brief, before the skeleton existed. Adapt the analysis to the skeleton's
   actual keys and shapes; keep the error and its parameters; report deviations from the note in `CASE.md`.
4. **Inputs.** Only `d`, `numpy`, and constants from the claim or the source (thresholds, documented parameters). Do not
   read any module-level name of the skeleton other than `np` (for example no `N`, no generator constants): the
   criterion must not know how the worlds were built.
5. **Return value:** `True` when the claim with its statistic and threshold is supported; `False` when not; `None` only
   from an **allowed guard**: non-finite values, an empty selection or one below the minimum stated in the private note
   (no more than the smallest size at which the statistic is defined), a zero variance. This list is exhaustive. The
   documentation's advice to return `None` when there is nothing to claim does not widen it. Nothing else may inspect the
   input's distribution; in particular no test of whether the data look like noise or zeros. Let a genuine error raise.
6. **Randomness** only through `rng = np.random.default_rng(<integer>)` created inside the criterion, the same in both
   files; never `np.random.<function>`. Same answer on the same data.
7. Keep it fast (Timing).

## Checks you may and may not run

* **Never run, simulate or pre-check the faulty criterion in any form**, on the worlds or elsewhere (not even "to see
  whether it works"). The only allowed operation on `faulty.py` is a syntax check: `py -c "import ast,sys;
  ast.parse(open(sys.argv[1],encoding='utf-8').read())" faulty.py`.
* You may pre-check the **fixed** criterion in plain Python: import `fixed.py` from a scratch script, draw samples from its
  `plus` and `minus` worlds (and, if you wish, the probes as `agent_docs\GATE.md` describes them) and count how often the
  criterion holds. Log every pre-check (what, how many samples, the rates) and every revision of the fixed criterion with
  its reason; the faulty criterion mirrors the final structure.
* If the fixed criterion often fails in `plus` or often holds in `minus`, do not change the skeleton and do not bend the
  correction; record it in `CASE.md`. A skeleton change is granted only for a defect that makes the fixed criterion
  impossible to write (for example a missing key): write the closest criterion, mark **SKELETON REQUEST** in `CASE.md`
  and `LOG.md`, and say why.

## Timing

As PB §2: on the final fixed criterion, `t` (mean of at least 20 calls on `plus` samples) and `g` (mean `plus`
generation); `S` = worlds + controls + premises + relational pairs declared, plus 2; the estimate `2 × 200 × (S + 1) ×
(t + g)` seconds must be at most 900. If it is not, make the fixed criterion faster without changing what it computes, and
mirror the change in the faulty one. If it still is not, write **SIZE REQUEST** in `CASE.md` and `LOG.md` with the
measured estimate; the designer grants it once (PREREG_PHASE_C §2, timing remedy: a fresh world-author agent regenerates
that skeleton with a smaller size and nothing else changed); if the estimate still exceeds 900 s, the pair is dropped as
"timing infeasible".

## `CASE.md` (one per case, written last)

1. Case id, world id, class, subtype. 2. Source key and documenting passage (quote ≤ 2 sentences or location; who read
it and how). 3. The brief as in `ASSIGNMENT.json`. 4. Mapping paragraph: faulty → documented error (parameters, where
documented); fixed → correction; the estimand line. 5. Pre-checks of the fixed criterion (each with its sample counts and
rates) and the number of revisions. 6. Timing: `t`, `g`, `S`, the estimate. 7. Deviations, problems, skeleton requests
(or "none"). (The designer adds the overlap line and the size ratio.)

## Order and interruptions

Work case by case and write `CASE.md` last; a successor continues with cases without `CASE.md`. Append a "Part 2"
section to your class `LOG.md`.

## Final message

Per case: done or not, number of fixed-criterion revisions, timing estimate, deviations, skeleton requests; confirm that
you never ran the faulty criterion or Truth_Gate; list what you read (files and URLs).

## Differences from Phase B's `AUTHOR_PHASE2.md`

| Phase B | Phase C |
|---|---|
| public docs of the repository; package from the repository | sandbox `agent_docs/` (0.5.0, results removed) and `pkg/`; URLs logged; no repository access |
| `from kapi import` skeletons | `from truth_gate import` skeletons |
| allowed guards "large enough" | minimum stated in the note, no more than the smallest size at which the statistic is defined; list exhaustive; docs advice does not widen it |
| — | the fixed criterion estimates the claim's quantity (item (i)); estimand line in `CASE.md` |
| — | "let a genuine error raise" |
| timing: make the fixed criterion faster | the same, then one SIZE REQUEST, then drop as "timing infeasible" |
| `CASE.md` items 1–7 | the same; the designer adds overlap, tag/family, guard minimum and size ratio lines |
| previous author's "session has ended"; source extracts in `src\`, `*.txt` | the brief authors' notes, log and source extracts in the class folder (no statement about their session) |
| syntax check, pre-check and skeleton-request wording | the same sentences (the probes as `agent_docs\GATE.md` describes them) |
| a "Phase 2" section in `LOG.md` | a "Part 2" section |
| final message: list what you read | the same, with every URL |
| everything else | the same (only criterion bodies change, inputs, never run the faulty criterion, fixed pre-checks logged, skeleton requests, seeds, return values, order and interruptions) |
