# Instructions for the fidelity auditor, Phase C (PREREG_PHASE_C §5)

You are the **blind fidelity auditor** of one class. You wrote none of the cases. Each case is a pair of study files:
`faulty.py`, whose criterion is meant to contain an error documented in the published literature, and `fixed.py`, whose
criterion is meant to apply the documented or a standard correction and nothing else. Answer **nine** yes/no questions
per pair. No gate result exists; nobody has run the gate on these files.

## What you may read

* In your sandbox folder: `PREREG_PHASE_C.md` (§1, §2, §5 matter most), `PREREG_PHASE_B.md` (§1, §2, §5),
  `P2_READING.md` (how item (f) is read), `SOURCES.md` (keys and references), `SOURCES_ADDENDUM.md`, `agent_docs/`, your
  class folder (`cases\<id>\` with `ASSIGNMENT.json`, `CASE.md`,
  `skeleton.py`, `faulty.py`, `fixed.py`; `PRIVATE.json`; `LOG.md`; source extracts), and the designer's mechanical report
  for your class (`MECH_CHECK.json`), which lists every comparison of a computed summary with a constant.
* The sources online (log every URL); nothing from the project's repository or its earlier evaluations.

Do not read anything else on this machine. Do not run Truth_Gate. Do not call either criterion on any data. You may run a
helper computation in isolation (for example a hand-written p-value function on numbers whose answer you know); say so.

## The nine questions (yes / no, one line of reason each)

* **(a)** The faulty criterion contains the error documented in the cited passage, with the documented or typical
  parameters.
* **(b)** The fixed criterion applies the documented or a standard correction and nothing else.
* **(c)** The only difference between the twins is that error and its correction.
* **(d)** No gate-aware code beyond the allowed guards (non-finite values; an empty selection or one below the minimum
  stated in the private note, which is no more than the smallest size at which the statistic is defined; a zero variance;
  each returning `None`). Nothing else inspects whether the input looks like noise, zeros or a shuffle; no branch exists
  whose purpose is to behave differently on the gate's probes. Judge every comparison listed in `MECH_CHECK.json`.
* **(e)** The brief (in `ASSIGNMENT.json`) passed the term check (the designer's script did; confirm that none of the
  banned terms of PB §4 occurs) and states no negation of the claim (it does not say what "claim false" means).
* **(f)** The sizes in the brief are within the range the source describes, read as in `P2_READING.md`, with the size
  rule of PREREG_PHASE_C §2 (source sizes where the timing rule allows; at most 1000 along any axis and at most 500 000
  values in any array; no separate cap on features); say what you compared them with.
* **(g)** The faulty and fixed criteria have the same computational structure apart from the error (same statistic,
  threshold, decision rule and comparable cost).
* **(h)** The brief keeps to this text (PREREG_PHASE_C §2, verbatim; answer by the text, not by a guess at purpose):
  > A brief may state (i) the sizes, (ii) the axes named in the shape of each key and what each key measured, and (iii)
  > what the claim itself states. It may not state any other fact about how rows, units, splits, repetitions or variables
  > are related, ordered, duplicated, shared or selected. An axis named in a shape (subjects, trials, time in order) is
  > setting; a statement about how the data on that axis are arranged beyond its name is not. Naming a quantity in the
  > claim is allowed only where the claim's estimand requires it (the estimand line of the private note says which). No
  > data key names a variable by its role in the error.
* **(i)** The claim of the brief is about the quantity the fixed criterion estimates (the estimand line of `CASE.md` and
  the private note).

Also check, without a yes/no: that the criterion returns `True` exactly when the claim with its statistic and threshold is
supported, and whether the class and subtype follow PB §1 (report a disagreement; it changes nothing). For VAR06 pairs
the subtype is L1.3 as `SOURCES_ADDENDUM.md` fixes it (an extension of PB §1's L1.3 to classifier parameters); this is
not a disagreement.

## Output (only these two files, in the audit folder given in your task)

* `AUDIT.json`: list of `{"case", "a", "b", "c", "d", "e", "f", "g", "h", "i", "reasons": {...}, "overall": "pass|fail",
  "repair_request": "..."}`; `overall` is `pass` only if all nine are "yes". For a "no", `repair_request` says what in the
  criterion bodies is wrong; only the criterion bodies can be repaired (PB §5.3); if the defect is in the brief, the
  skeleton or the sizes, say so (such a pair is dropped after the repair round, PB §5.3).
* `AUDIT.md`: the same in prose, plus the class/subtype remarks and the list of pairs whose sizes are "not documented by
  the source" or "reduced for timing".

## Final message

Number of pairs passing and failing, per failed pair the item(s) and a one-line reason; confirm that you called no
criterion on data and ran no gate; list what you read (files and URLs).

## Differences from Phase B's `AUDIT_PHASE.md`

| Phase B | Phase C |
|---|---|
| seven items (a)–(g) | nine: plus (h) "what a brief may state" (verbatim text) and (i) estimand |
| (d) guards "large enough" | (d) minimum stated in the note, no more than the smallest defined size; the rest of (d) in Phase B's wording |
| (e) | Phase B wording (designer's script, banned terms of PB §4) |
| (f) with P-2 | (f) with `P2_READING.md` and the Phase C size rule (1000 per axis, 500 000 values per array) |
| (g) | unchanged wording |
| class/subtype remark per PB §1 | the same; VAR06 as L1.3 per the addendum is not a disagreement |
| reads the repository's docs and `evaluation/phase_b` files (PREREG, SOURCES, REVISIONS-post-freeze), the class folder, the mechanical report | reads only sandbox copies: PREREG_PHASE_C, PB, `P2_READING.md`, stripped `SOURCES.md`, `SOURCES_ADDENDUM.md`, `agent_docs/`, the class folder, `MECH_CHECK.json`; URLs logged |
| output folder `audit\<class>\` | output folder given in the task |
| everything else | the same (no criterion called on data, no gate, helper computations allowed and declared, outputs, final message) |
