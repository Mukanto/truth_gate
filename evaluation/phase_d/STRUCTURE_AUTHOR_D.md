# Instructions for structure authors, Phase D

You are a **structure author** in a pre-registered evaluation of Truth_Gate. Each case carries an analysis error
documented in the published literature. You are told that error. For each case of your class half you write a
**reference world**: data in which the structure that the error exploits is present at a realistic size.

The reference world is used only to check, before anything else happens, two things:
- that the error matters at the brief's size;
- that the correction is clean.

You never see the criteria. Do not try to guess or reproduce them.

## What you may read

- Your sandbox folder:
  - this file;
  - `cases\<id>\brief.json`;
  - for each case, these fields of the private note: source, passage, estimand, exploited_structure,
    structure_statistic, sizes_note, and the approved structure value (`approved_value`). You do not see the
    descriptions of the analyses;
  - the source passages in `SOURCES_D.md`;
  - `agent_docs/` (the tool's documentation) and `pkg/` (the tool's code).
- The sources themselves online, to find the size of the structure in the source's setting. Log every URL; fetch
  nothing from the project's code repository or its evaluations.

Do not read anything else on this machine. Do not run Truth_Gate in any form. Do not start any other agent or any tool
that runs a model. Do not use any context-mode tool (`ctx_*`), and no scratch folder outside your sandbox.

## What to write, per case: `cases\<id>\reference.py`

The form is the skeleton form below, with the placeholder criterion left as it is. The module docstring is the id, a
colon, a space and the claim exactly as in `brief.json`, with nothing after it.

```python
"""<id>: <the claim, exactly as in the brief>"""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    ...


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    ...


def criterion(d):
    """Data keys: <list every key with its shape and meaning>.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="<id>",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="<one line: what you set to null>"),
    },
    controls=[Control("<id>", ["C"], transform=lambda d, rng: {...})],   # at least one
)
```

## Rules

1. **Data.** Each world returns a `dict` with exactly the brief's keys and dtypes (`float` arrays as float64, `bool`
   arrays as bool). Each array has exactly the shape in `brief.json` (`dims`). Group, subject, trial and time structure
   is carried by array axes.
2. **The structure.** Both worlds carry the exploited structure (`exploited_structure` in the note), with the structure
   statistic at `approved_value`. On 200 samples of each world the statistic must meet
   `|mean − approved_value| ≤ 0.2 × |approved_value − null_value|`, and it must be equal between the two worlds within
   3 standard errors: `|mean_plus − mean_minus| ≤ 3 × sqrt(sd_plus²/200 + sd_minus²/200)`.
   - The world also carries the other realistic dependencies of the setting, at sizes you can justify (between-unit
     variability, correlated measurements, measurement error), in both worlds.
3. **`plus`.** Realistic data in which the claim is true, with an effect of the size a well-designed study would expect.
4. **`minus`, a fixed rule.** The quantity the claim is about is set to its null (no relationship, no difference, no
   predictive information). Every other quantity keeps its `plus` value: the same sizes, noise levels, structure and
   distributions of everything the claim is not about. Write in `change` what you set to null.
5. **No planting for one twin.** Do not add any key, variable or dependence that only the faulty analysis would read,
   unless the documented error itself needs it. Say in your log which keys the error needs.
6. **Controls.** At least one control that breaks the theory of the claim, for example by permuting the variable that
   carries the claimed relationship across the units, within the study's own structure. It returns the full data dict.
7. Use only `numpy` and the generator `rng` passed to your functions. Do not use `np.random` at all. No files, no other
   imports. Do not set `budget`, `targets` or `deterministic`. A world or control call must take at most 250 ms (the
   check script rejects any call above 1000 ms).
8. **What you may run.** You may run your world functions and the note's `stat` code on their samples, to check shapes,
   dtypes and the structure value. The claimed effect is set by the generator's parameters, which you state in
   `STRUCTURE_LOG.md`; you do not estimate it from samples. You may not write or run any analysis that could serve as a
   criterion.
9. The designer's check script rejects the same constructs as for the world authors: module-level code other than the
   docstring, the two import lines, assignments and function definitions; the banned names; numpy's file functions;
   non-finite values; shapes that differ between worlds or draws; a dimension above 2000 or an array above 2 000 000
   values; a control that returns the data unchanged. A rejected file goes back to you once.

## Decoys

If your task is the decoy cases, the same rules apply. A decoy whose note has no structure statistic needs only rules 1
and 3 to 9.

## Repairs

A later check may send one of your files back for one repair. The request names the file and quotes only the failing
item, or a script's error list. It never contains a count, a rate or a test result from any later check. Change only
that file, log the change, and confirm that you saw no rate. You may be resumed for this, or a fresh agent of your role
may do it after reading your log.

## Log

Write `STRUCTURE_LOG.md`. For each id, give:
- the structure value and where it comes from;
- the other dependencies and their sizes;
- what `minus` sets to null;
- the keys the error needs;
- the generator's parameters that set the claimed effect;
- the measured statistic on 200 samples of each world.

## Final message

Report:
- the number of reference worlds written;
- any case in which the note's structure value or the brief made a realistic world impossible.

Confirm that you saw no criterion and ran none. List what you read (files and URLs).
