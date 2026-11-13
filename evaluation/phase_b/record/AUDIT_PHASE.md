# Instructions for the fidelity auditor (PREREG §5, step 2)

You are the **blind fidelity auditor** of one class in a pre-registered evaluation of Truth_Gate, a tool that checks
whether the acceptance criteria of computational studies can fail. You did not write any of the cases. Each case is a
pair of study files: `faulty.py`, whose criterion is meant to contain an error documented in the published literature,
and `fixed.py`, whose criterion is meant to apply the documented or a standard correction and nothing else. Your job is
to answer seven yes/no questions per pair. No gate result exists yet; nobody has run the gate on these files.

## What you may read

* `E:\Claude Projects\kapi-oss\evaluation\phase_b\PREREG_PHASE_B.md` (all of it; §1, §2 and §5 matter most),
  `SOURCES.md` and `REVISIONS-post-freeze.md` (entry P-2 fixes how item (f) is read) in the same folder.
* Public documentation: `E:\Claude Projects\kapi-oss\README.md`, `docs\GATE.md`, `docs\MANIFEST.md`, `docs\SPEC.md`.
* Your class folder (given in your task): `cases\<case id>\` (`ASSIGNMENT.json`, `CASE.md`, `skeleton.py`,
  `faulty.py`, `fixed.py`), `PRIVATE.json` (the authors' private error notes), `LOG.md`, `src\` and the `*.txt` source
  extracts.
* The designer's mechanical report `STEP5_MECH_CHECK.json` in the parent folder (only the entries of your class): it
  lists, per twin, every comparison of a computed summary with a constant, for item (d).
* The sources themselves (online, DOIs in `SOURCES.md`), to check a passage or a parameter.

Do **not** read anything else (no other class folder, no `world\` folder, nothing else under
`E:\Claude Projects\kapi-oss\` or `E:\Claude Projects\Kapi\`). Do **not** run Truth_Gate in any form. Do **not** call
either criterion on any data (not on samples of the case's worlds, not on noise, not on data you construct): the
question is what the code says, not what it does on the worlds. You may run a helper computation in isolation (for
example a hand-written p-value function on a few numbers whose answer you know) to check that it computes what it
claims; say so when you do.

## The seven questions (yes / no, one line of reason each)

* **(a)** The faulty criterion contains the error documented in the cited passage (with the documented or typical
  parameters).
* **(b)** The fixed criterion applies the documented or a standard correction and nothing else.
* **(c)** The only difference between the twins is that error and its correction.
* **(d)** No gate-aware code beyond the allowed guards (§2: non-finite values, an empty or too small selection, a zero
  variance, each returning `None`). Nothing else inspects whether the input looks like noise, zeros or a shuffle; no
  branch exists whose purpose is to behave differently on the gate's probes. Judge every comparison listed by the
  designer for your class.
* **(e)** The brief (in `ASSIGNMENT.json`) passed the term check (the designer's script did; confirm that none of the
  banned terms of §4 occurs) and states no negation of the claim (it does not say what "claim false" means).
* **(f)** The sizes in the brief are within the range the source describes, read as in entry P-2 of
  `REVISIONS-post-freeze.md`; say what you compared them with.
* **(g)** The faulty and fixed criteria have the same computational structure apart from the error (same statistic,
  threshold, decision rule and comparable cost).

Also check, without a yes/no: that the criterion returns `True` exactly when the claim with its statistic and threshold
is supported, and whether the class and subtype in `ASSIGNMENT.json` follow the decision rules of §1 (report a
disagreement; it does not change your answers).

## Output (write only these two files, in `E:\...\phase_b\audit\<class>\`, folder given in your task)

* `AUDIT.json`: a list of objects `{"case": "...", "a": "yes|no", "b": ..., "c": ..., "d": ..., "e": ..., "f": ...,
  "g": ..., "reasons": {"a": "...", ...}, "overall": "pass|fail", "repair_request": "..."}`. `overall` is `pass` only
  if all seven are "yes". For a "no", `repair_request` says precisely what in the criterion bodies is wrong; only the
  criterion bodies can be repaired (§5.3), so if the defect lies elsewhere (brief, skeleton, sizes), say so.
* `AUDIT.md`: the same in prose, one short section per case, plus the class and subtype remarks and the list of pairs
  whose sizes are "not documented by the source" or "reduced to the cap" (entry P-2).

## Final message

Report the number of pairs that pass and fail, per failed pair the item(s) and a one-line reason, and confirm that you
called no criterion on any data and ran no gate; list what you read.
