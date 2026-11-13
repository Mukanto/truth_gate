# Instructions for the world author

You write **study skeletons** for a set of scientific claims. A skeleton declares how a careful researcher would test a
claim with the tool Truth_Gate: what the data look like when the claim is true (`plus`), what they look like when it is
false (`minus`), and at least one control that breaks the theory behind the claim. Somebody else will later write the
criterion (the analysis) into each skeleton; you never write it.

## What you may read

* The two files in this folder: `WORLD_INSTRUCTIONS.md` (this file) and `BRIEFS_SHUFFLED.json` (54 briefs, ids W01–W54).
* The public documentation of the tool: `E:\Claude Projects\kapi-oss\README.md`, `docs\GATE.md`, `docs\MANIFEST.md`,
  `docs\SPEC.md`.

Do **not** read anything else: not the parent folder of this folder, not `E:\Claude Projects\Kapi\`, and nothing else in
`E:\Claude Projects\kapi-oss\` (no `truth_gate\`, `kapi\`, `tests\`, `examples\`, `evaluation\`). Do not run Truth_Gate
in any form (no `truth-gate`, no `python -m kapi`, no `python -m truth_gate`, no `run_gate`). You may import the
package only to construct the `Study` object of a skeleton and check that it loads.

## What to write

For every brief, one file `skeletons\<id>.py` (for example `skeletons\W07.py`) in this folder, of this form:

```python
"""<id>: <the claim, copied from the brief>."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control


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
   to your functions (no global random state, no files, no other imports).
6. Keep each world fast (well under 10 milliseconds per call if you can).
7. You may run your own world functions in plain Python to check shapes, dtypes and that the effect is present in
   `plus` and absent in `minus`, and you may simulate the documented probes (`docs\GATE.md`). You may not write or test
   any analysis that could serve as the criterion.

## Log

Write `WORLD_LOG.md` in this folder: for each id, two or three lines on what `plus`, `minus` and each control represent,
the effect size you chose and why, and any judgement call. If a brief cannot be modelled as written, say why and still
write the closest skeleton.

## Final message

Report the number of skeletons written, any brief you found ambiguous or impossible, and confirm that you read nothing
beyond the files allowed above.
