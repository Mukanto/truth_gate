# Instructions for the fidelity auditor, Phase D

You are the **blind fidelity auditor** of one class (B-2, B-3, or the decoys). You wrote none of the cases. Each case
consists of:
- a pair of criterion bodies: `faulty_body.py`, meant to carry an error documented in the published literature, and
  `fixed_body.py`, meant to apply the documented or a standard correction and nothing else;
- a reference world, `reference.py`, written by an agent that was told the error.

The audit has three parts. Your task says which part you do.
- **Part A0** comes before the reference worlds and the criteria exist.
- **Part A** comes before any world author starts. A "no" leads to one repair, then a drop.
- **Part B** comes after the world authors. It has no repair.

No gate result exists, and nobody has run the gate on these files.

## What you may read

- Your sandbox folder:
  - this file, `PREREG_PHASE_D.md` and `P2_READING_D.md` (how item (f) is read);
  - `SOURCES.md` and `SOURCES_D.md`;
  - `agent_docs/`;
  - your class folder;
  - in part A, `MECH_CHECK.json` from `tools/mech_check_bodies.py`, which lists every comparison of a computed summary
    with a constant.
- The sources online. Log every URL; fetch nothing from the project's repository or its evaluations.
- You never see the results of the validity checks: no count, rate or p value.

Do not read anything else on this machine. Do not run Truth_Gate. Do not call either criterion on any data. You may run
a helper computation in isolation; say so.

**What your class folder holds:**
- **Part A0:** for each case, `brief.json`, the private note and the source passage.
- **Part A:** `cases\<id>\` with `brief.json`, `CASE.md`, `faulty_body.py`, `fixed_body.py`, `reference.py` and
  `STRUCTURE_LOG.md`; the private notes, `LOG.md` and source extracts.
- **Part B:** the world skeletons of each case, under random labels (`X.py`, `Y.py`), and the files of part A.

## Part A0: the structure value (yes / no, one line of reason each)

For each case whose note says `note_value_source: "source states none"`:
- **(l)** Is the proposed structure value justified as a realistic value for the setting, and consistent with the
  source's setting? Answer yes (approved) or no (rejected, with what is unrealistic).

For each other case:
- **(l)** Does the value match its quote and its location? Answer yes or no.

For a decoy whose structure statistic is null: write "(l): n/a".

## Part A: the questions (yes / no, one line of reason each)

- **(a)** The faulty body contains the error documented in the cited passage, with the documented or typical parameters.
- **(b)** The fixed body applies the documented or a standard correction, and nothing else.
- **(c)** The only difference between the bodies is that error and its correction. The mapping in `CASE.md` is right.
- **(d)** There is no gate-aware code beyond the allowed guards: non-finite values; an empty selection or one below the
  minimum stated in the private note (which is no more than the smallest size at which the statistic is defined); a
  zero variance; each returning `None`. Nothing else inspects whether the input looks like noise, zeros or a shuffle,
  and no branch exists whose purpose is to behave differently on the gate's probes. Judge every comparison listed in
  `MECH_CHECK.json`.
- **(e)** The brief passed the term check: the designer's script did, and you confirm that none of the banned terms of
  PB §4 occurs. The brief states no negation of the claim (it does not say what "claim false" means).
- **(f)** The sizes in the brief are within the range the source describes, read as in `P2_READING_D.md`, and within the
  limits of at most 2000 per axis and at most 2 000 000 values per array. Say what you compared them with.
- **(g)** The two bodies have the same computational structure apart from the error: the same statistic, threshold,
  decision rule, model family and comparable cost.
- **(h)** The brief keeps to "what a brief may state" (verbatim; answer by the text, not by a guess at its purpose):
  > A brief may state (i) the sizes, (ii) the axes named in the shape of each key and what each key measured, and (iii)
  > what the claim itself states. It may not state any other fact about how rows, units, splits, repetitions or
  > variables are related, ordered, duplicated, shared or selected. An axis named in a shape (subjects, trials, time in
  > order) is setting; a statement about how the data on that axis are arranged beyond its name is not. Naming a
  > quantity in the claim is allowed only where the claim's estimand requires it (the estimand line of the private note
  > says which). No data key names a variable by its role in the error.
- **(i)** The claim is about the quantity that the fixed body estimates.
- **(j)** The reference world's `minus` sets only the claim's quantity to null. Every other quantity keeps its `plus`
  value.
- **(k)** No key, variable or dependence of the reference world is read only by the faulty body, unless the documented
  error needs it.
- **(m)** The structure statistic is a function of the brief's data keys only, measures the exploited structure, and is
  computed from parts of the data that `minus` leaves unchanged. Decoys with no statistic: write "n/a".
- **(p)** The reference world uses the approved structure value of part A0.

Also report, without a yes or no:
- whether the criterion returns `True` exactly when the claim, with its statistic and threshold, is supported;
- whether the class and the subtype or tag follow PB §1 and PC's lists. A disagreement is reported; it changes nothing.
  For VAR06 pairs, the subtype is L1.3 as PC's `SOURCES_ADDENDUM.md` fixes it (an extension of PB §1's L1.3 to
  classifier parameters); this is not a disagreement.

## Part B: the question (yes / no per world file)

- **(o)** Neither world skeleton (X, Y) leaks the error. That means the file names no variable by its role in the error,
  adds no key that only the faulty body reads, and builds no dependence aimed at one twin. Ordinary realistic
  dependence is not a leak, even where the error exploits it.

## Output (only these files, in the audit folder given in your task)

- `AUDIT_A0.json`: a list of `{"case", "l", "reason", "approved_value"}`.
- `AUDIT_A.json`: a list of `{"case", "a", ..., "p", "reasons": {...}, "overall": "pass|fail", "repair_request": "..."}`.
  - `overall` is `pass` only if all the items are "yes" (or "n/a").
  - For a "no", `repair_request` names the file and quotes only the failing item. It never cites a count, a rate or a
    validity result.
  - The bodies can be repaired by the criterion author, `reference.py` by the structure author, and the statistic by
    the brief author. A defect in the brief or the sizes cannot be repaired.
- `AUDIT_B.json`: a list of `{"case", "X": "yes|no", "Y": "yes|no", "reasons": {...}}`.
- `AUDIT_A0.md`, `AUDIT_A.md` and `AUDIT_B.md`: the same in prose. `AUDIT_A.md` adds the class and subtype remarks, and
  the list of pairs whose sizes are "not documented by the source" or "reduced for timing".

## Final message

Report the number of pairs passing and failing. For each failed pair, give the items and a one-line reason. Confirm that
you called no criterion on data, ran no gate and saw no validity result. List what you read (files and URLs).

## Differences from Phase C's `AUDIT_PHASE_C.md`

| Phase C | Phase D |
|---|---|
| one audit, after the worlds, before the run | part A0 (structure values) before the authors; part A before the worlds; part B after the worlds |
| nine items (a)–(i) | (a)–(i) as PC, with (f)'s limits changed; plus (j), (k), (m), (p) on the reference world and the statistic; (l) in part A0; (o) in part B |
| bodies inside skeleton copies; one auditor per class | separate body files and `reference.py`; one auditor per class (B-2, B-3, decoys) |
| (f) at most 1000 per axis and 500 000 values | (f) at most 2000 per axis and 2 000 000 values |
| repairs: criterion bodies only | part A: the bodies, `reference.py` or the statistic, once; repair requests carry no rates; part B: no repair |
| — | no validity results are shown to the auditor; part B skeletons under random labels |
| everything else | the same: (d), (e), (f) and (h) wording; `P2_READING_D.md`; size list; VAR06 note; no criterion on data; no gate; helper computations declared |
