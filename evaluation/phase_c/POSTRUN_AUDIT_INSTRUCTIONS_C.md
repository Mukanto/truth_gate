# Instructions for the post-run auditor of Phase C (PREREG_PHASE_C §7 = PB §7)

You are the **blind post-run auditor** of Phase C, a pre-registered evaluation of Truth_Gate 0.5.0 (with 0.4.1 run on the
same files for the primary comparison). You wrote no brief, world, criterion, case or audit of this evaluation. The cases
were frozen and published (commit `aecd613`) before the gate ran; the gate has now run on all of them with both versions.
Your job is to answer three questions per pair. You do not change anything, you do not rerun the gate, and your answers
do not change the pre-registered table (PB §7: a case found wrong after the run stays in the pre-registered table with the
error reported next to it).

All paths below are relative to this task folder (the folder that holds this file). Read nothing outside it.

## What you may read (only copies inside this task folder)

* `phase_c\PREREG_PHASE_C.md` (§6, §7 and §8 matter most), `phase_c\REVISIONS-post-freeze.md` (P-1 to P-8; P-7 and P-8
  are the readings used by the run and the report), `phase_c\EXPECTED_FLAGS.json`, and the other frozen files in
  `phase_c\`.
* `phase_b\PREREG_PHASE_B.md` ("PB"; §5, §6 and §7 matter most) and `phase_b\REVISIONS-post-freeze.md` (Phase B's P-1,
  the reading of limit I-4).
* `phase_c\cases\<case-id>\` (`faulty.py`, `fixed.py`, `CASE.md`, `ASSIGNMENT.json`; the brief is in `ASSIGNMENT.json`,
  its world id in `world_id`).
* `phase_c\run\RESULTS.md`, `phase_c\run\RESULTS.json`, the certificates `phase_c\run\certs\v050\<case-id>\{faulty,fixed}.json`
  and `phase_c\run\certs\v041\<case-id>\{faulty,fixed}.json`, the run logs (`phase_c\run\logs\`,
  `phase_c\run\runlog_v050.jsonl`, `phase_c\run\runlog_v041.jsonl`).
* `phase_c\record\`: the world authors' logs `fable\batchNN\WORLD_LOG.md` and skeletons `fable\batchNN\skeletons\`
  (batch 03 has no world log, see P-4), `fable\WORLD_RUN.md`, the shuffled briefs and batches `world\`, the awareness
  readings (`designer\AWARENESS_RESULT.json`, `designer\AWARENESS_RUN.md`, `designer\READING1.json`,
  `awareness_reader2\READING2.json`), the world-id map `designer\ID_MAP.json`, the brief authors' and criterion authors'
  `authors\<F>\` files (`BRIEFS.json`, `PRIVATE.json`, `LOG.md`, `work\`), the fidelity audits `audit\<F>\out\`
  (including the post-repair audits).
* `phase_c\REPORT.md`: the designer's draft report, written after the run. Its section 9 (this audit) is still empty.
* Public documentation: `docs\README.md`, `docs\GATE.md`, `docs\SPEC.md`.

Do not run the gate (no copy of it is in this folder, and you must not look for one). You may run small Python scripts
(`py -I`) that read the certificates and print numbers; keep such scripts and any other scratch files in `scratch\`.

## The three questions, per pair

Answer for every pair in `phase_c\cases\` (52 pairs). Use the **0.5.0** certificates, which make the pre-registered
primary table; you may look at the 0.4.1 certificates where they help. The out-of-scope pairs (`O-*` classes) are
answered in the same way, for description only.

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
  structure that the detection relies on)? Use the brief, the world log (where there is one), the skeleton and the
  awareness readings. Limits already recorded are not such a sign: the world author's inference of the error from the
  form of the claim (limit I-4, PB §8, applied to the world author in PREREG_PHASE_C §8; Phase B's P-1), and the B-3 briefs
  naming the adjusted-for quantity as the estimand rule requires (I-6). Answer "yes" only for a sign beyond those (for
  example a brief that names the procedure, or a size or key that only makes sense for the error).

## Output (write only these two files, in `out\`)

* `out\POSTRUN_AUDIT.json`: a list of `{"case": "...", "i": "yes|no|n/a", "ii": "yes|no|n/a", "iii": "yes|no",
  "reasons": {"i": "...", "ii": "...", "iii": "..."}}`, one entry per pair.
* `out\POSTRUN_AUDIT.md`: the same in prose, one short section per pair, then a summary: per class the counts of each
  answer, and the pairs where an answer is "no" for (i) or (ii) or "yes" for (iii). End with a list of every statement in
  `phase_c\REPORT.md` (sections 1 to 8) that the certificates or the other files contradict or do not support: the
  section, the statement, and what you found. Write "none" if there is none.

## Working rules

* Write nothing outside `out\` and `scratch\`. No git commands, no network access.
* Context-mode tools, if present: do not call `ctx_search` unless with a `source` filter naming a label you indexed
  yourself in this task; do not call `ctx_batch_execute` or `ctx_index`. If the harness suggests a session scratchpad
  folder, do not use it; use `scratch\`.
* Do not start other agents.

## Final message

Report in a few lines the counts per class and the notable pairs, and confirm that you ran no gate, started no agent and
wrote no file other than your two outputs and your scratch files.
