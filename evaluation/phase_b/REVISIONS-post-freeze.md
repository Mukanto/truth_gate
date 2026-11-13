# Phase B: notes and revisions after the pre-registration freeze

The pre-registration (`PREREG_PHASE_B.md` v3, `FREEZE_PREREG.json`, core `31F2415AB2990D37`) is frozen. This file records,
in order and before the results they could affect, every process event and every reading of a rule that the frozen text
leaves open. Nothing here changes a threshold, an expected flag or a drop rule. Decisions by Claude under the author's
delegation.

## P-1 (2026-11-13): skeletons frozen; world-author awareness recorded

* **Process.** The first world-author agent stopped at a rate limit having written no skeleton and could not be resumed
  after a session change. A second, fresh agent received the same two files and the same instructions and wrote all 54
  skeletons and `WORLD_LOG.md`. It reports having read only its instructions, the shuffled briefs, `docs/GATE.md` and
  `docs/SPEC.md`, and having imported the package only to build each `Study`.
* **Mechanical check (§4 step 4).** 54/54 skeletons pass: only `numpy` and `kapi` imported; no file, network, process or
  global-random access; `criterion` body exactly `raise NotImplementedError`; `Study(name=<id>)` with
  `[Criterion("C", criterion)]`; `plus` and `minus` (derived from `plus`, with a stated change) present; at least one
  control returning the full data dict; default budget, targets and options; keys, dtypes and dimensions as in the
  brief; at most 6.6 ms per world call.
* **Freeze.** `FREEZE_SKELETONS.json` (59 files: the world folder and the check report), core `375F46C3AB4659C1`. It
  will be published with the cases.
* **Awareness (limit I-4).** The world log shows that the world author inferred the error mechanism for most briefs and
  kept the corresponding structure in `minus`, as the fixed rule requires, choosing its size in `plus`. Before any
  criterion body existed, the designer classified every skeleton from the text of the log alone: **45 P** (the log names
  a mechanism by which `minus` could still appear to support the claim), **5 C** (mechanism considered, nothing left in
  `minus`), **4 N** (no sign). The rule and the list are in the frozen `world/AWARENESS.md`. The report adds one
  descriptive breakdown by level and class (pairs, detections by label, clean passes; no interval, no verdict). Declared
  detections on P cases are to be read as: the gate flags the criterion when the declared worlds contain the artefact
  that the error exploits, i.e. when whoever declares the worlds anticipates it.
* **Consequence for step 5.** The criterion authors of the earlier session cannot be resumed either. Fresh agents, one
  per class, write the criterion bodies from their class folder's private notes, logs and source extracts; they did not
  write the briefs themselves, and this is stated in the report.

## P-2 (2026-11-13, before any audit): reading of audit item (f)

Item (f) asks whether "the sizes in the brief are within the range the source describes". Two situations are not
settled by the frozen text; they are read as follows, before the fidelity audit starts and before any criterion is
audited:

1. **The source states no sizes** (a methodological paper, or a source read only as an abstract). Item (f) is answered
   "yes" when the sizes respect the caps of §2 and are of the order of the setting that the source describes, as the
   private note argues; the auditor writes what it compared them with. Every such pair is listed in the report as
   "sizes not documented by the source".
2. **The source's studies are larger than the caps of §2** (for example thousands of voxels or patients). A size reduced
   to the cap counts as within range, because §2 imposes the cap; the report lists these pairs too.

The purpose of item (f), that sizes are not chosen to favour detection, is unchanged; a size outside both readings is
a "no".

## P-3 (2026-11-13, before any audit): fixed criteria that the skeleton makes weak

Criterion authors reported, from their allowed pre-checks of the fixed criterion, cases in which the frozen skeleton
makes the fixed criterion rarely hold in `plus` (B-3: two cases near 0%, others between 50% and 75%) or hold often in
`minus` (one B-6 case at 27%, one out-of-scope case at 15%, several B-3 cases near 15%), because of structure that the
world author kept in both worlds (shared trends, confounding, a weak partial effect). One author asked whether to
request a skeleton change or to drop such cases. Designer's answer, before the audit and before any gate run:

* No skeleton change: §4 step 5 grants one only for a defect that makes the fixed criterion impossible to write, and
  these criteria could be written.
* No drop by the designer: §5.3 drops a pair only after a failed repair or a dispute in the fidelity audit. The cases
  stay; if their fixed twins fail the clean pass, the failure counts in the pre-registered table and the post-run
  audit question (ii) asks whether it comes from the skeleton.
* The authors did not change the documented correction to make it pass; the figures they measured are in each
  `CASE.md`.

## P-4 (2026-11-13, during the fidelity audit, before any gate run): one targeted re-examination

The five auditors passed all 54 pairs. Reading every `CASE.md` for changes that refer to the gate's probes, the
designer found one change of a **faulty** parameter: in one B-1 pair the selection threshold documented by the source
(`p < .01`, in the source's own illustration and in the private note) was replaced by `p < 0.05`, with a reason about
the noise probe. The B-1 auditor's answer to item (a) did not address the threshold. The designer sent that auditor the
two facts and asked it to re-examine item (a) for that pair and to check every parameter change listed in the B-1
`CASE.md` files; the auditor decides, and a "no" follows §5.3 (one repair of the criterion bodies, then drop). Other
probe-related changes found in the same reading touch only the fixed criterion or robustness (a bounded index, a
non-negative row count, `np.errstate`, ranks instead of logs in two partial correlations) and are reported as they
are.

Outcome: the auditor answered (a) "no" for that pair and for a second B-1 pair with the same source and the same
threshold change (there without a probe-related reason). The criterion author repaired both (both twins: `r > 0` and
two-sided `p < 0.01`; nothing else changed), the designer's mechanical check passed again, and the post-repair audit
answered "yes" on all seven items for both. No pair was dropped. The two pairs are reported as repaired.

## P-5 (2026-11-13): cases frozen; pre-run record published with the cases

* **Fidelity audit result.** 54/54 pairs pass all seven items (B-1 12, B-2 12, B-3 12, B-6 12, out of scope 6); two
  repaired, none dropped. Every class keeps at least 10 pairs and 3 independent sources; the B-2 subtype minima hold
  (2 pairs per subtype).
* **Cases.** `cases/<case-id>/` holds `faulty.py`, `fixed.py`, `CASE.md` and `ASSIGNMENT.json` (the brief, class,
  subtype, source and world id); the B-2 local ids `b2-NN` became `B2-NN`. `EXPECTED_FLAGS.json` lists, per case, the
  §6 list plus `HIGH_RATE:control:<id>` for each declared control (no relational pair or `null` world was declared).
  The out-of-scope cases carry the same list for descriptive reporting only. **`FREEZE_CASES.json`** (217 files),
  core `0811095AA6F7E824`.
* **Record.** `record/` holds what was private until now: the authors' briefs, private notes and logs, their scratch
  scripts and outputs (`work/`), the world folder (instructions, shuffled briefs, skeletons, world log,
  `AWARENESS.md`), `FREEZE_SKELETONS.json` (verifies from `record/`), the id map, the instructions of every role, the
  audits and the designer's scripts. Source texts (PDF, HTML, XML and full-text extracts) are not published.
  **`FREEZE_RECORD.json`** (143 files), core `21E1520ADD1F0C18`.
* Nobody has run Truth_Gate on any case. Next: the run (§6).
