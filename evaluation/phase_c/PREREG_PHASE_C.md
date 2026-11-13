# Phase C: errors documented in the literature, worlds by a different Claude model line — pre-registration

Status: **v3 with the review-3 fixes, 2026-11-13, for freeze.** Designer: Claude, under the author's delegation.
Required by spec 0.7 section 6 R3 (`docs/design/spec-0.7.md`, frozen), whose fixed differences this document may not
weaken; where this text is stricter than R3 (for example the wording of allowed claims, §8 I-8) the stricter text
governs. v1, v2 and v3 were reviewed blind (`REVIEW1.md`, `REVIEW2.md`, `REVIEW3.md`); the changes are in `REVISIONS.md`. Phase B's frozen pre-registration
(`evaluation/phase_b/PREREG_PHASE_B.md`) is "PB"; "as PB §n" means the rule applies unchanged. No Phase C case exists when
this text is written.

**Frozen with this text** (`FREEZE_PREREG_C.json`): this file, `REVIEW1.md`, `REVIEW2.md`, `REVIEW3.md`, `REVISIONS.md`, the instruction
files `AUTHOR_PHASE1_C.md`, `WORLD_INSTRUCTIONS_PHASE_C.md`, `AUTHOR_PHASE2_C.md`, `AUDIT_PHASE_C.md`,
`AWARENESS_RULE_C.md`, `P2_READING.md`, the sources `SOURCES_ADDENDUM.md`, the reference table `PHASE_B_TABLE.json`, and
the scripts `tools/check_skeletons.py`, `tools/term_check.py`, `tools/scan_docs.py`, `tools/mech_check_twins.py`,
`tools/shuffle.py`. After the freeze nothing above changes; process events and readings go to `REVISIONS-post-freeze.md`.

## 0. Questions

* **Main.** Does Truth_Gate 0.5.0, together with worlds and controls declared by a model that **is not told** the error,
  the class or the source (Fable, a different Claude model line from the one that wrote the gate and the criteria), flag
  acceptance criteria that contain errors documented in the published literature, and does it pass the corrected
  criteria, when the analysis is written inside the criterion?
* **Primary comparison (spec 0.7 R3).** On the same frozen files, what does 0.5.0 change relative to 0.4.1?

Every detection is labelled by what found it (as PB §6). The classes are the claimed scope, as in Phase B.

## 1. Classes, sources, overlap with Phase B

* In scope, each with a threshold: **B-1** circular analysis, **B-2** procedure-level leakage (subtypes L1.1, L1.2, L1.3,
  L1.4, L3.1, L3.2), **B-3** coupling by construction, **B-6** inflated-size decision rules; decision rules and precedence
  as PB §1. Out of scope, no threshold: **O-1**, **O-2**, **O-3** as PB §1. The designer fixes each pair's class and
  subtype at the shuffle; they never change, even when an author or auditor disagrees (the disagreement is reported).
* **Sources.** The Phase B source list and the frozen `SOURCES_ADDENDUM.md` (KRI10, MOR03 for B-1; VAR06 for B-2; CUR13 for
  B-3; LAZ18 for B-6). A source counts as **read** when its documenting passage was read and is quoted or located in a
  private note or in the addendum; a passage read in an abstract counts. Every in-scope class rests on at least 3
  independent read sources (the addendum's own note says which addendum sources are not counted as independent). At most
  4 pairs per source per class; KAP23 up to 8 B-2 pairs. B-2 subtype minima: L1.1 ≥ 1, L1.3 ≥ 1, L1.4 ≥ 2, L3.1 ≥ 2,
  L3.2 ≥ 2 (VAR06 pairs count as L1.3, as the addendum fixes: an extension of PB §1's L1.3 from features to classifier
  parameters selected on the data of the error estimate, not a change of PB §1).
* **New sources.** In each in-scope class at least 4 of the 12 planned pairs rest on sources of `SOURCES_ADDENDUM.md`. If
  an author's set has fewer, the designer returns the set once with this rule; if it still has fewer, the class goes on
  with what it has and the report says "new-source minimum not met". The report gives the number among surviving pairs.
  B-2, B-3 and B-6 have one addendum source each (at most 4 pairs), so a single dropped addendum pair there gives "not
  met"; this outcome is expected to be common and is a report line, not a change of any verdict.
* **Overlap key.** Every private note carries a `mechanism_tag` and a `statistic_family` from the closed vocabularies in
  `PHASE_B_TABLE.json` (`vocabulary`), each with a one-line definition and a precedence order (copied in
  `AUTHOR_PHASE1_C.md`). A Phase C pair **overlaps** Phase B when some Phase B pair in that table has the same
  source key, the same `mechanism_tag` and the same `statistic_family`; the designer applies this mechanically, after the
  briefs and before the shuffle, from the Phase C note's own tag and family. An ambiguous label is resolved by the
  definitions; the designer may change a note's label only to the one the definitions require, and logs each change with
  its reason. The 54 Phase B rows were re-read against the definitions before the freeze (`REVISIONS.md`). The
  vocabulary is a designer's tool: some names come from Phase B's mechanisms, so the brief authors learn which
  mechanisms Phase B tagged (not its cases, settings or passages); this exposure is accepted and reported. A pair on an
  addendum source cannot overlap.
  The overlap mark is in `CASE.md` and in every table. If strictly more than half of the pairs entering a class table
  overlap, the report says that the class's Phase C result "largely repeats Phase B settings with a new world author" and
  does not present the Phase B and Phase C results of that class as separate evidence. Every table is also given without
  the overlapping pairs (descriptive).

## 2. What a case is

As PB §2, with these changes.

* Each study file imports `from truth_gate import Study, Criterion, World, Premise, Control` and `numpy`, nothing else,
  and has **exactly one** criterion `Criterion("C", criterion)` without components (one component under both versions).
* **Allowed guards** are PB §2's list, which is exhaustive: non-finite values, an empty selection or one below the smallest
  size at which the statistic is defined (for example 3 pairs for a correlation, 2 per group for a two-sample t statistic;
  the private note states the minimum used), a zero variance; each returns `None`. The 0.5.0 documentation's advice to
  return `None` when there is nothing to claim does not widen this list.
* **Sizes.** At most 1000 rows (or units) along any axis and at most 500 000 values in any array (for example 1000 × 500;
  there is no separate cap on the number of features), and the timing estimate of PB §2 (at most 15 minutes with the fixed criterion) binds. A brief uses the source's sizes
  where the timing rule allows, otherwise the largest that fits, and the private note says so; for a source that states
  no sizes, the note gives the largest size within the timing estimate or says why a smaller size is realistic for the
  setting. The note also cites what the source reports about how the error's size depends on the sample size or the
  number of features, or says "not stated". The `sizes` field states every array dimension as a number.
* **Timing remedy.** If the fixed criterion's estimate exceeds 900 s, the criterion author first makes the fixed criterion
  faster without changing what it computes (mirrored in the faulty one). If it still exceeds 900 s, the author asks the
  designer for a smaller size once; a fresh Fable agent regenerates that one skeleton with the new size and nothing else
  changed (logged, re-checked by the script, re-frozen); if the estimate still exceeds 900 s, the pair is dropped as
  "timing infeasible" (reported by id).
* **Estimand.** The claim of the brief is about the quantity that the **fixed** criterion estimates; the faulty criterion
  estimates it in the documented wrong way. (For coupling by construction, for example, the claim is about the relation
  between two quantities after accounting for a third, the data keys carry the measured components, the faulty criterion
  accounts for the third by dividing by it and correlating the ratios, the fixed one by a partial correlation or a
  regression with the third as a covariate.) The private note names the estimand of the faulty and of the fixed statistic.
  A brief for which this cannot be done is not written.
* **What a brief may state** (one text, used verbatim in `AUTHOR_PHASE1_C.md` and `AUDIT_PHASE_C.md` item (h)):
  > A brief may state (i) the sizes, (ii) the axes named in the shape of each key and what each key measured, and (iii)
  > what the claim itself states. It may not state any other fact about how rows, units, splits, repetitions or variables
  > are related, ordered, duplicated, shared or selected. An axis named in a shape (subjects, trials, time in order) is
  > setting; a statement about how the data on that axis are arranged beyond its name is not. Naming a quantity in the
  > claim is allowed only where the claim's estimand requires it (the estimand line of the private note says which). No
  > data key names a variable by its role in the error.

  Banned terms as PB §4, checked by `tools/term_check.py`.
* Fixed criteria that the skeleton makes weak (they fail often in `plus` or hold often in `minus`) are not repaired by a
  skeleton change and stay in the table (as Phase B's `REVISIONS-post-freeze.md` P-3).
* The 60-minute rule applies per check and per version.

## 3. `CASE.md`

As PB §3, plus: overlap with Phase B (yes/no, with the Phase B case it overlaps), the estimand line, the mechanism tag and
statistic family, the allowed-guard minimum, the size ratio (brief size to source size, or "source states none").

## 4. Roles and order of work

Each instruction file lists, as a table, its differences from the corresponding Phase B file.

0. **Start conditions** (before any agent of Phase C sees anything). 0.5.0 is released (tag `v0.5.0`). The designer:
   (a) builds the **agent document set** from the tag: `docs/GATE.md`, `docs/MANIFEST.md`, `docs/SPEC.md` and the parts of
   `README.md` that describe the tool, copied into `agent_docs/`, with every sentence that reports an evaluation result
   removed; runs `tools/scan_docs.py`, and every hit line is read by two readers, the designer and a fresh agent that
   sees only the document set and this rule: the sentence is **removed** (recorded) if either reader finds that it
   states an evaluation, a result, a count of cases or detections, a case, a source key, or a class of Phase B or C
   (B-1 to B-6, O-1 to O-3); otherwise it is tool vocabulary and is **listed** with its file, line text, tokens and the
   reason in `agent_docs/SCAN_REVIEW.json`, which the script reads (`--allow`); the set is ready when the script
   reports no unlisted hit (exit code 0); (b) builds the **package copy**: the
   folders `truth_gate/` and `kapi/` from the tag, copied as `pkg/`; every sandboxed agent and every Phase C script puts
   `pkg/` first on `sys.path` (the machine's own Python also has an editable install of the repository, which `pkg/`
   shadows; this is part of the honour-system limit of item 7); (c) runs a smoke test that loads a trivial non-case study
   with `pkg/` and with tag `v0.4.1`; (d) runs a new Fable **pre-flight** (item 3); (e) records the commits of `v0.5.0`
   and `v0.4.1`, the Python and numpy versions and the machine; (f) freezes (a)–(e), with `SCAN_REVIEW.json` and the
   scan report, in `FREEZE_AGENT_DOCS.json`.
1. **Criterion authors (briefs).** One fresh agent per class (B-1, B-2, B-3, B-6, and one for O-1 to O-3), Claude Code
   agent `kodlayici` (Sonnet line), each working in a **sandbox folder** that holds copies of only its allowed files: this
   document, PB, `SOURCES.md` stripped of Phase B notes (keys, references and DOIs only), `SOURCES_ADDENDUM.md`,
   `agent_docs/`, `pkg/`. They may read the sources online; they may not fetch anything from the project's repository or
   its published Phase A or Phase B material, and they log every URL they read. They are not told which passages Phase B
   used. They write 12 briefs per in-scope class (2 per out-of-scope class) with private notes as `AUTHOR_PHASE1_C.md`
   says, and log every brief, including abandoned ones.
2. **Designer.** `tools/term_check.py`; the brief half of items (h) and (i) (the "what a brief may state" text; the
   estimand line, tag and family present in the note); class and subtype; the new-source count; overlap marks;
   `tools/shuffle.py` (ids and order from the seed `int(SHA-256(bytes of FREEZE_PREREG_C.json + b"phase-c-shuffle"), 16)`
   driving a Fisher–Yates shuffle with Python's `random.Random`; the designer cannot choose it; the seed is fixed by the
   freeze and known before any brief exists, while the order also depends on the briefs' number and file order, which
   the authors set). The class folders are `B1`, `B2`, `B3`, `B6` and `O` (classes B-1, B-2, B-3, B-6 and O-1 to O-3, in
   the script's `CLASSES.json`); each batch file `BATCH_<nn>.json` is copied unchanged into its batch's sandbox as
   `BATCH.json`. The designer rejects a brief only for a term-check failure, a violation of §2, a missing estimand line,
   tag or family, class ambiguity or a cap violation, logs every rejection with its reason, and never edits a claim; a
   rejected brief goes back once to its author.
3. **World author: Fable**, in fixed batches. The shuffled briefs are cut into consecutive blocks of 15 in shuffle order
   (the last one shorter); each block goes to a fresh agent started with the Claude Code agent model parameter `fable`,
   with the identical file `WORLD_INSTRUCTIONS_PHASE_C.md`, its batch file, `agent_docs/` and `pkg/`, in a sandbox; no
   class, error or source information. Each batch writes its skeletons and its own world log. **Every Fable agent of
   Phase C** (the pre-flight, the batches, continuations after a stop, the redos of item 4, the regenerations of the §2
   timing remedy and the skeleton changes of item 5) is subject to the identification and invalid-run rules below, and
   its evidence goes into `WORLD_RUN.md`.
   * **Identification.** The pre-flight of item 0 (a `fable` agent whose prompt contains no brief) must show, in its
     harness transcript (`subagents/agent-<id>.jsonl`, field `model`), `claude-fable-…` for every assistant message
     (`<synthetic>` entries excepted). For every batch the designer copies into `WORLD_RUN.md` the model ids recorded in the
     batch's transcript, the request metadata, the dates and the list of tool names the batch called. The agent's own
     statement of its model is not evidence.
   * **Invalid batch.** A batch is invalid if its transcript records any other model for an assistant message, or if it
     called any tool that starts an agent (the instructions forbid it), or if any other agent transcript is linked to it.
     Its skeletons are deleted unread by anyone and the batch is redone once by a fresh Fable agent; a second invalid run
     stops Phase C until a revision in `REVISIONS-post-freeze.md` decides how to continue.
   * **If Fable cannot be started**, or the pre-flight records another model, Phase C waits; there is no time limit. A
     substitute model requires a new pre-registration revision, reviewed before any skeleton exists.
   * **Stops.** If a batch stops (rate limit, session end), the ids without a skeleton that passes the check script go to a
     new fresh Fable agent with the same instructions (logged in `WORLD_RUN.md`); this continuation counts as the first
     attempt for those ids.
4. **Designer: skeleton check, awareness, freeze.** `tools/check_skeletons.py` checks every skeleton. A skeleton that fails
   goes back once to a fresh Fable agent with only the script's error list for that id; a skeleton that still fails is
   **dropped as "skeleton invalid"** (counted nowhere, reported by id). Properties the script cannot check (whether `minus`
   follows the fixed rule) are not grounds for a redo. Then two readers classify every world log entry P, C or N by
   `AWARENESS_RULE_C.md`: the designer and a fresh agent that sees only the world logs and the rule; a disagreement goes to
   the higher level (the **resolved** reading); both readings are reported, with the length of the log per brief in both
   phases. Skeletons, logs, `WORLD_RUN.md`, the SHA-256 of every batch transcript and the classification are frozen
   (`FREEZE_SKELETONS.json`).
5. **Criterion authors (bodies).** Always fresh agents of the same kind, one per class, reading their class folder (the
   private notes and logs of the brief authors), as `AUTHOR_PHASE2_C.md` says: only the criterion bodies change; the
   faulty criterion uses the documented parameters; only the fixed criterion may be pre-checked, and every pre-check and
   revision is logged; never run, simulate or pre-check the faulty criterion. A skeleton change is granted only for a
   defect that makes the fixed criterion impossible to write, or by the timing remedy of §2, and is made by a fresh Fable
   agent.
6. Nobody runs Truth_Gate (any version) on a case before the case freeze and its public push.
7. All agents other than the world author are Claude models of the Opus and Sonnet lines, the family that wrote the
   gate; the world author is Fable, **from the same vendor and family (Anthropic Claude)**. No human domain reader takes
   part. The agents work under instructions and sandboxes on a machine where the repository and the Phase B material
   exist; the separation is an honour system, as in Phase B. These facts are stated in the report.

**Size.** 12 pairs planned per in-scope class (at least 10 after drops), from at least 3 independent read sources, within
the per-source pair caps and B-2 subtype minima of §1, at least 4 on addendum sources; 2 pairs per out-of-scope class.
Within a class every pair differs from every other as PB §4.

## 5. Fidelity audit and case freeze (before any gate run)

As PB §5: the designer's mechanical check (`tools/mech_check_twins.py`: twins equal the frozen skeleton outside the
criterion bodies; imports; no file, network or process access; default `Budget` and `Targets`; comparisons of a computed
summary with a constant listed for the auditor); a blind fidelity audit by one fresh agent per class with the yes/no items
(a)–(g) of PB §5 in Phase B's wording, item (f) read as in `P2_READING.md` with the size rule of §2; one repair round;
drops reported; a class with fewer than 10 pairs, fewer than 3 independent read sources or a missed B-2 subtype minimum is
"insufficient cases". Two items are added (an added item strengthens PB §5; a "no" follows its repair-or-drop rule):

* **(h)** the brief keeps to "what a brief may state" (§2, the quoted text);
* **(i)** the claim of the brief is about the quantity the fixed criterion estimates (§2, estimand).

Then the cases and `EXPECTED_FLAGS.json` are frozen (`FREEZE_CASES.json`) with the pre-run record (`FREEZE_RECORD.json`),
and the frozen state is pushed to the public repository with the author's approval. **Without that approval there is no
run.** The runner and the designer's recomputation script are written after the push and read only frozen files.

## 6. Run, metrics, thresholds, reporting

* **Run.** Truth_Gate at tag `v0.5.0` and at tag `v0.4.1`, full mode, every file, one check at a time, default settings
  (no other setting is ever run on a Phase C file). An infrastructure failure (a crash of the runner or the machine, not a
  verdict or a timeout) is rerun once; both attempts are logged. A timeout counts as a miss or a failed clean pass in that
  version's table and as "not comparable" in the primary comparison.
* **Expected flags.** As PB §6 for the in-scope classes (the same list), with `HIGH_RATE:control:<id>` and
  `HIGH_RATE:probe:shuffle:<a>,<b>` enumerated per case at the freeze. Information flags (`K1_ABSTAINED:*`,
  `K2_MINUS_UNREAD`, `K8_SOME_CHANGES`, `BAD_RETURN`) and the capping flag `K1_ABSTAINED_MAJORITY:*` never count. The
  out-of-scope cases carry the same list for description only.
* **Detection, labels, clean pass, thresholds** as PB §6, computed with **0.5.0** for the main question.
* **Baselines** on the same files: noise-only and declared-only computed from the 0.5.0 certificates (with a second line
  from 0.4.1), flag everything, and the full 0.4.1 table.
* **Primary comparison (spec 0.7 R3).** Unit: the one component of each file. Per class, from the 0.4.1 and 0.5.0
  certificates: components that 0.4.1 made UNDEFINED, with the cause (hard UNDEFINED, plus majority, soft only);
  detections and clean passes gained; faulty twins that move from UNDEFINED to FALSIFIABLE or WEAK (misses 0.4.1 hid) and
  fixed twins that move from UNDEFINED to NOT_FALSIFIABLE (false alarms 0.4.1 hid), each listed by name; components with
  `K1_ABSTAINED_MAJORITY`. **The v0.5.0 table is the pre-registered primary table.** By spec 0.7 section 4 no 0.4.1
  detection or clean pass can be lost; a loss counts against 0.5.0 whatever a later release does; it is reported in
  `REVISIONS-post-freeze.md`, and a patch release with the defect fixed may be run on the same files and reported next to
  it as secondary. If fewer than 5 of the Phase C study files (faulty and fixed, all classes) have a component whose
  verdict under 0.4.1 is UNDEFINED, the comparison is reported as **not informative**, with the list and no per-class
  statement. A "no change" outcome is reported as such.
* **Abstention.** Per class, the share of samples on which the fixed and the faulty criteria abstained under 0.5.0 (from the
  certificates' counts), next to Phase B's (descriptive).
* **Awareness breakdown** by P/C/N and class, both readings (descriptive). Every statement of a class verdict in the report
  carries that class's P/C/N shares from the resolved reading and the wording "declared worlds that may contain what the
  error exploits".
* **Overlap and new sources**: every table also without the overlapping pairs, and the count of addendum-source pairs per
  class (descriptive).
* **Phase B next to Phase C**: the class tables side by side, labelled descriptive (briefs, worlds, criteria and the size
  rule differ).
* **Report** as PB §6, plus the size ratio per pair and, for each miss whose faulty criterion fails in `minus` at about the
  nominal rate, the interpretation label "error too small in the declared worlds at this size" where it applies.

## 7. After the run

As PB §7: the designer recomputes every number from the certificates with a separate script written without reading the
runner; a blind post-run audit by a fresh agent answers (i)–(iii) per pair; the thresholds and expected flags never change
after the run; a case found wrong after the run stays in the table with the error reported next to it.

## 8. Interpretations fixed now

* **I-1 to I-5** as PB §8; I-4 applies to Fable as world author, I-5 to the Phase C source distribution (reported).
* **I-6.** Fable is a different Claude model line, not a different vendor or family. A difference between Phase B and
  Phase C may come from the world author, the briefs, the criteria, the size rule or chance; Phase C isolates none of them.
  B-3 briefs name the adjusted-for quantity in the claim, as the estimand rule requires, so the world author is told
  which quantity the claim accounts for (not that it is shared or measured with error), which the briefs of the other
  classes do not do; the B-3 P/C/N shares are read with this in mind.
* **I-7.** The primary comparison measures spec 0.7's effect on these files. 0.5.0 changes only components that 0.4.1 made
  UNDEFINED, so the comparison is informative only to the extent that the criteria abstain. With an exhaustive guard list
  and minima equal to the smallest defined size, abstention may be rare, and "not informative" is a probable outcome; it
  is a limit, not a failure of 0.5. The criterion authors read the 0.5.0 documentation, which describes abstention; within
  the guard list this may raise the abstention rate, which favours finding an effect of 0.5.0.
* **I-8.** Allowed claims in the report: what the gate did on errors documented in the literature, with worlds declared by
  a different Claude model line that was not told the error, each class verdict with its P/C/N shares. Not allowed:
  "independent of the gate's authors", "errors nobody anticipated", "external" without this qualifier, and any wording that
  the world author was "unaware", "did not know" or "blind" to the error. This replaces the shorter claims sentence of
  spec 0.7 R3 ("did not know the error") with a stricter one.
* **I-9.** In B-1, B-3 and B-6, where Phase B's sources and mechanisms are few, up to 8 of 12 pairs can overlap Phase B; an
  overlap above one half there is plausible and triggers the wording of §1.
