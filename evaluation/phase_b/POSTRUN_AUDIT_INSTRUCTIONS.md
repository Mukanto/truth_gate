# Instructions for the post-run auditor (PREREG §7)

You are the **blind post-run auditor** of Phase B, a pre-registered evaluation of Truth_Gate 0.4.0. You wrote no case,
skeleton or audit of this evaluation. The cases were frozen and published (commit `fe86e96`) before the gate ran; the
gate has now run on all of them. Your job is to answer three yes/no questions per pair. You do not change anything,
you do not rerun the gate, and your answers do not change the pre-registered table (§7: "A case found wrong after the
run stays in the pre-registered table with the error reported next to it").

## What you may read (everything under `E:\Claude Projects\kapi-oss\evaluation\phase_b\` and the public docs)

* `PREREG_PHASE_B.md` (§6 and §7 matter most), `REVISIONS-post-freeze.md`, `EXPECTED_FLAGS.json`.
* `cases\<case-id>\` (`faulty.py`, `fixed.py`, `CASE.md`, `ASSIGNMENT.json`).
* `run\RESULTS.md`, `run\RESULTS.json`, the certificates `run\certs\v040\<case-id>\{faulty,fixed}.json` (each holds,
  per component, the verdict, the flags, the HOLDS counts per stream and the bounds), the run logs.
* `record\`: the world author's `world\WORLD_LOG.md`, `world\AWARENESS.md`, the shuffled briefs, the criterion authors'
  `LOG.md` and private notes, the fidelity audits.
* Public documentation: `E:\Claude Projects\kapi-oss\README.md`, `docs\GATE.md`, `docs\SPEC.md`.

Do not run the gate. You may run small scripts that read the certificates and print numbers.

## The three questions, per pair

* **(i)** For a detected pair: does the detection follow from the planted error, i.e. would the fixed criterion on the
  same worlds avoid that flag? Compare the faulty and fixed certificates (same worlds, same seeds): the expected flags
  present in the faulty one and their HOLDS rates per stream, against the fixed one. "yes" if the flag(s) that made the
  detection are absent from the fixed twin or come from a markedly different rate; "no" if the fixed twin carries the
  same flag for the same reason (then the detection does not show the error). For a missed pair answer "n/a" and say in
  one line which stream would have been needed.
* **(ii)** For a pair whose fixed twin failed the clean pass: does the failure come from the skeleton (its worlds or
  controls) rather than from the fixed criterion? "yes" with the reason (for example the fixed criterion holds in
  `minus` because a structure kept in both worlds makes the claim true there; low power in `plus`), "no" if the fixed
  criterion itself is at fault (for example it is not the documented correction, or a guard makes it UNDEFINED). For a
  clean pass answer "n/a".
* **(iii)** Is there a sign that a brief steered the worlds (the brief's wording, rather than the claim, decided the
  structure that the detection relies on)? Use the brief, the world log and `AWARENESS.md`. Note that the world author's
  inference of the error from the form of the claim is limit I-4 and is already recorded (P-1); answer "yes" only for a
  sign beyond that (for example a brief that names the procedure, or a size or key that only makes sense for the
  error).

## Output (write only these two files, in `evaluation\phase_b\run\`)

* `POSTRUN_AUDIT.json`: a list of `{"case": "...", "i": "yes|no|n/a", "ii": "yes|no|n/a", "iii": "yes|no",
  "reasons": {"i": "...", "ii": "...", "iii": "..."}}`.
* `POSTRUN_AUDIT.md`: the same in prose, one short section per pair, then a summary: per class the counts of each
  answer, and the pairs where an answer is "no" for (i) or (ii) or "yes" for (iii).

## Final message

Report the counts and the notable pairs in Turkish, and confirm that you ran no gate and changed no file other than
your two outputs.
