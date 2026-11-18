# Instructions for the post-run auditor of Phase D (PREREG_PHASE_D section 7, as PC §7 = PB §7)

You are the **blind post-run auditor** of Phase D, a pre-registered evaluation of Truth_Gate 0.5.1 on 20 pairs of
criteria. Each pair has a faulty twin carrying an error documented in the literature and a fixed twin with its
correction. Each pair was run in three arms of synthetic worlds:
- **R:** the reference world, written by an agent told the error;
- **W0:** world skeletons by a fresh agent, not told the error;
- **W1:** the same as W0, with a dependence checklist added to the instructions.

You wrote no brief, world, criterion, case or audit of this evaluation. The cases were frozen and published before the
gate ran, and the gate has now run on all of them.

You answer questions per pair and arm. You do not change anything and you do not rerun the gate. Your answers do not
change the pre-registered table: a case found wrong after the run stays in it, with the error reported next to it.

All paths below are relative to this task folder (the folder that holds this file). Read nothing outside it.

## Part 1 (write it before you open `part2\`)

### What you may read in part 1 (copies inside this task folder)
- `phase_d\`:
  - `PREREG_PHASE_D.md` (sections 5, 6 and 8 matter most);
  - `REVISIONS-post-freeze.md` (P-1 to P-6);
  - `EXPECTED_FLAGS_D.json`, `WORLD_INSTRUCTIONS_D0.md`, `WORLD_INSTRUCTIONS_D1.md`, `AWARENESS_RULE_D.md`,
    `FIDELITY_AUDIT_D.md`, `P2_READING_D.md`, `SOURCES_D.md`.
- `phase_b\PREREG_PHASE_B.md` (PB; sections 5 to 7) and `phase_c\PREREG_PHASE_C.md` (PC; sections 5 to 7).
- `phase_d\cases\<id>\`, one folder per pair (20):
  - `brief.json` (what the world author saw);
  - `PRIVATE.json` (the error, its source, the structure statistic);
  - `CASE.md`, `faulty_body.py`, `fixed_body.py`;
  - `reference.py` (arm R), `skeletons\W0.py`, `skeletons\W1.py`.
- `phase_d\run\`: the studies as run (`studies\<ARM>\<id>_<twin>.py`), the certificates
  (`certs\<ARM>\<id>_<twin>.json`) and the run log (`RUNLOG.jsonl`).
- `phase_d\record\`:
  - the world authors' logs: `world\<arm>_batch<n>\WORLD_LOG.md`, plus `CHECKLIST_LOG.md` for W1;
  - `WORLD_RUN.md`;
  - the fidelity audit part B (`audit_b\<G>\AUDIT_B.json`, `AUDIT_B_MAP.json`);
  - the awareness readings (`awareness\r1b|r2|r3|r4\READING.json` and the label maps `AWARENESS_MAP_first.json` and
    `AWARENESS_MAP_second.json`).
- Public documentation: `docs\README_TOOL.md`, `docs\GATE.md`, `docs\SPEC.md`.

Do not run the gate (no copy of it is in this folder, and you must not look for one). You may run small Python scripts
(`py -I`) that read the certificates and print numbers; keep them and any other scratch files in `scratch\`.

### The questions
Answer for every pair in arms W0 and W1 (40 pair-arms), using the certificates of that arm. Arm R is a consistency
check: answer (i) and (ii) for it too, in one line per pair.
- **(i) Detection follows from the error.** For a pair-arm whose faulty twin is NOT_FALSIFIABLE: does the detection
  follow from the planted error? That is, would the fixed criterion on the same worlds avoid that flag? Compare the
  faulty and fixed certificates (same worlds, same seeds): the expected flags in the faulty one and their counts per
  stream, against the fixed one.
  - "yes" if the flags that made the detection are absent from the fixed twin, or come from a markedly different count.
  - "no" if the fixed twin carries the same flag for the same reason.
  - Say which streams carry it, and whether `probe:noise` is the only one.
  - For a pair-arm whose faulty twin is not NOT_FALSIFIABLE, answer "n/a" and say in one line which stream would have
    been needed.
- **(ii) Clean-pass failures.** For a pair-arm whose fixed twin did not pass clean (verdict not FALSIFIABLE or WEAK, or
  an expected flag present): does the failure come from the skeleton (its worlds or controls) rather than from the fixed
  criterion?
  - "yes" with the reason, for example low power in `plus`, or a structure kept in both worlds.
  - "no" if the fixed criterion itself is at fault.
  - For a clean pass, answer "n/a".
- **(iii) Brief steering.** Is there a sign that the brief steered the world (the brief's wording, rather than the
  claim, decided the structure the detection relies on)?
  - Use the brief, the world log, the checklist log (W1), the skeleton and the awareness readings.
  - These do not count as a sign:
    - the world author's inference of the error from the form of the claim (limit I-4 of PB §8, applied to the world
      author);
    - in W1, the checklist's own effect (it names dependence kinds on purpose).
  - Answer "yes" only for a sign beyond those, for example a brief that names the procedure, or a size or key that only
    makes sense for the error.

### Part 1 output (write these two files in `out\` before opening `part2\`)
- **`out\POSTRUN_AUDIT.json`:** a list of
  `{"case": "D-xxx", "arm": "R|W0|W1", "i": "yes|no|n/a", "ii": "yes|no|n/a", "iii": "yes|no|n/a", "reasons": {...}}`.
  Use "n/a" for (iii) in arm R.
- **`out\POSTRUN_AUDIT.md`:**
  - the same in prose;
  - then a summary: per class and arm, the counts of each answer;
  - then the pair-arms where (i) or (ii) is "no", or (iii) is "yes".

## Part 2 (only after both part-1 files are written)
Open `part2\`. It holds:
- `REPORT.md`: the designer's draft report, written after the run;
- `RESULTS_D.md` and `RESULTS_D.json`: the scoring output.

List every statement in `REPORT.md`, sections 1 to 10, that the certificates or the other files contradict or do not
support. Give the section, the statement and what you found. Also check that every number in the report's tables equals
the scoring output and the certificates. Write this list as `out\POSTRUN_AUDIT_PART2.md`, or "none" if there is none.
Do not change the part-1 files after opening `part2\`. If part 2 changes your view of a part-1 answer, say so in the
part-2 file.

## Working rules
- Write nothing outside `out\` and `scratch\`. Make your scratch copies writable; the inputs are read-only.
- No git commands, no network access.
- Do not call any context-mode tool (any tool whose name contains `ctx_`).
- If the harness suggests a session scratchpad folder, do not use it; use `scratch\`.
- Do not start other agents.

## Final message
Report in a few lines:
- the counts per class and arm, and the notable pair-arms;
- the number of part-2 findings;
- confirmation that you ran no gate, started no agent, opened `part2\` only after writing the part-1 files, and wrote no
  file other than your outputs and scratch files.
