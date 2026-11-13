# Instructions for the world author (Phase C)

You write **study skeletons** for a set of scientific claims. A skeleton declares how a careful researcher would test a
claim with the tool Truth_Gate: what the data look like when the claim is true (`plus`), what they look like when it is
false (`minus`), and at least one control that breaks the theory behind the claim. Somebody else will later write the
criterion (the analysis) into each skeleton; you never write it.

## What you may read

* The files in your sandbox folder: `WORLD_INSTRUCTIONS_PHASE_C.md` (this file), your batch file `BATCH.json` (briefs with
  ids), the folder `agent_docs/` (the tool's documentation) and the folder `pkg/` (the tool's code: in your own test
  scripts, put it first on `sys.path` before importing `truth_gate`; the skeleton itself has no `sys.path` line).

Do **not** read anything else on this machine and do not fetch anything from the internet. **Do not start any other agent
or any tool that runs a model**; do all the work yourself. Do not run Truth_Gate in any form (no `truth-gate`, no
`python -m truth_gate`, no `python -m kapi`, no `run_gate`). You may import the package only to construct the `Study`
object of a skeleton and check that it loads.

## What to write

For every brief, one file `skeletons\<id>.py` in your sandbox folder, of this form. The module docstring is the id, a
colon, a space and the claim exactly as in `BATCH.json`, with nothing after it.

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
        # optional: "null": World(...),
    },
    controls=[Control("<id>", ["C"], transform=lambda d, rng: {...})],   # at least one
    # optional: premises=[Premise(...)], relational=[("<key a>", "<key b>")],
)
```

## Rules

1. **Data.** Each world returns a `dict` with exactly the keys of the brief, with the stated shapes and dtypes (`float`
   arrays as float64, `bool` arrays as bool). Group, subject, trial and time structure is carried by array axes, never by
   integer codes. Use the sizes in the brief.
2. **`plus`:** realistic data in which the claim is true, with an effect of the size a well-designed study would expect,
   not a huge one. Include realistic noise, and realistic structure (for example between-subject variability,
   correlations between measurements, measurement error) where the brief's setting has it.
3. **`minus`, a fixed rule:** the quantity the claim is about is set to its null (no relationship, no difference, no
   predictive information), and **every other quantity keeps its `plus` value** (same sizes, same noise levels, same
   structure, same distributions of everything the claim is not about). For a claim that one effect exceeds another, the
   null is that the two effects are equal, each other quantity unchanged. Write in `change` what you set to null.
4. **Controls:** at least one control that breaks the theory of the claim, for example by permuting the variable that
   carries the claimed relationship across the units, within the study's own structure. A control is a `transform`
   that returns the **full** data dict (`{**d, "key": ...}`). Premises and relational pairs are optional.
5. Do not set `budget`, `targets` or `deterministic` (keep the defaults). Use only `numpy` and the generator `rng` passed
   to your functions (do not use `np.random` at all; no files, no other imports).
6. Keep each world and each control fast: a call must take at most 100 milliseconds (the check script rejects slower
   ones); aim for well under 10 milliseconds.
7. You may run your own world functions in plain Python to check shapes, dtypes and that the effect is present in
   `plus` and absent in `minus`, and you may simulate the documented probes (`agent_docs\GATE.md`). You may not write or
   test any analysis that could serve as the criterion.
8. **The check script also rejects** (a rejected skeleton goes back once with the error list, then it is dropped):
   module-level code other than the docstring, the two import lines, assignments and function definitions (no `class`,
   no `if` block, no `sys.path` line); the names `open`, `eval`, `exec`, `compile`, `__import__`, `input`, `breakpoint`,
   `globals`, `locals`, `vars`, `getattr`, `setattr`, `delattr`, `exit`, `quit`, `print`, `__builtins__`, numpy's file
   functions (`load`, `save`, `savez`, `savetxt`, `loadtxt`, `genfromtxt`, `fromfile`, `tofile`, `memmap`) and
   double-underscore attributes; `World` called other than as `World(fn)` or `World(fn, derived_from=..., change=...)`;
   `Study` keywords other than `name`, `criteria`, `worlds`, `controls`, `premises`, `relational`; a docstring that is not
   one line exactly `<id>: <claim>`; non-finite values in any generated array; shapes that differ between worlds or
   between draws; any dimension above 1000 or any array above 500 000 values; a control that returns the data unchanged
   on a draw, or does not return the full dict with the same shapes and dtypes; a premise that does not return the full
   dict.

## Log

Write `WORLD_LOG.md` in your sandbox folder: for each id, two or three lines on what `plus`, `minus` and each control
represent, the effect size you chose and why, and any judgement call. If a brief cannot be modelled as written, say why
and still write the closest skeleton.

## Final message

Report the number of skeletons written, any brief you found ambiguous or impossible, and confirm that you read nothing
beyond the files allowed above.

## Differences from Phase B's `WORLD_INSTRUCTIONS.md`

| Phase B | Phase C |
|---|---|
| `from kapi import ...` | `from truth_gate import ...`, from the sandbox `pkg/` |
| reads `BRIEFS_SHUFFLED.json` (all 54) | reads `BATCH.json` (its batch, at most 15) |
| reads the repository's README, GATE, MANIFEST, SPEC; forbidden-folder list | reads the sandbox `agent_docs/` (evaluation results removed) and `pkg/`; nothing else on the machine; no internet |
| — | do not start any other agent or tool that runs a model |
| docstring template `"""<id>: <the claim, copied from the brief>."""` | the id, a colon, a space and the claim exactly, nothing after it (the check script compares exactly) |
| rule 5: "no global random state" | rule 5: do not use `np.random` at all |
| rule 6: "well under 10 milliseconds per call if you can" | rule 6: at most 100 ms per world or control call (enforced), aim under 10 ms; note that the briefs' sizes may now reach 1000 per axis and 500 000 values per array |
| probes in `docs\GATE.md` | probes in `agent_docs\GATE.md` |
| — | rule 8: what the check script rejects, listed; `sys.path` only in the author's own test scripts |
| everything else | identical (rules 1–4 and 7, log, final message) |
