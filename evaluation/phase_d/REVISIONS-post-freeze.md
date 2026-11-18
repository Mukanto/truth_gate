# Phase D: process events and revisions after the freeze

The pre-registration is frozen (`FREEZE_PREREG_D.json`, core `80c5e543f48e6953`, commit 77e5c1d). This file records
process events and revisions that the frozen text does not settle. Each one is written, with its reasons, before the
step it could affect. Decisions are the author's where stated; otherwise they are Claude's under the author's
delegation.

## P-1 (2026-11-17, during item 0, before any brief exists): the world-author model is Claude Opus 5.5, not Fable

**Event.** The Fable pre-flight of section 3 item 0, as PC §4 item 0(d), could not start. The API answered: "Fable 5.2
requires usage credits". The transcript records one synthetic message and no assistant message from any model. It is
kept private, and its SHA-256 is in `record/SOFTWARE_STATE.json`. The frozen text says that if Fable cannot be started, Phase D
waits, and that a substitute model needs a pre-registration revision reviewed before any skeleton exists.

**Author's decision (2026-11-17):** "Kredi yenilemeyeceğim. Opus-5-5 ile ilerle." (No usage credits will be bought;
proceed with Opus 5.5.)

**Revision.**
1. **Model.** World authors (section 3 item 9) and every agent that writes or changes a skeleton (redos, timing
   redos) are fresh Claude Code general-purpose agents started with the model parameter `opus`. The transcript must
   record `claude-opus-5-5` for every assistant message (`<synthetic>` entries excepted). Wherever the frozen text says
   "Fable" or "PC's world-author line", read "Claude Opus 5.5".
2. **Pre-flight and the other rules.**
   - The pre-flight of item 0 is run with that model, under PC's identification and invalid-run rules.
   - A batch whose transcript records another model is invalid.
   - If Opus 5.5 cannot be started, Phase D waits.
3. **Nothing else changes.** The world instructions, the arms, the batches, the checklist, the hypotheses, the
   thresholds, the scoring and every tool stay as frozen. The brief, criterion and structure authors stay on the Sonnet
   line, so world authors are still of a different Claude line from those authors.
4. **Reporting.**
   - **Allowed claims.** The allowed claims of I-D6 name the model ("with worlds declared by Claude Opus 5.5, a model of
     a different Claude line from the authors of the briefs, criteria and reference worlds, that was not told the
     error").
   - **Comparison with Phases B and C.** The descriptive comparison of arm W-0 with Phases B and C now also differs in
     the world-author model (Fable there, Opus 5.5 here). The report says so wherever W-0 is set next to them.
   - **Shared model.** The designer is also Claude Opus 5.5. The world authors are fresh agents that are not told the
     error, the class or the source. They read only the frozen world instructions, their batch file, `agent_docs/` and
     `pkg/`. That the world authors and the designer are the same model is reported as a limitation.
5. **Review.** This revision is reviewed by a fresh agent in the independent session before any skeleton exists. The
   review's findings, and how each was handled, are added below it.

**Why now.** No brief, private note, criterion, reference world or skeleton exists yet. The revision cannot be fitted
to any Phase D outcome.

### P-1, review and amendments (2026-11-17)

**Review.** A fresh agent in the independent session reviewed P-1 (`P1_REVIEW.md`). It found 0 blocking, 5 major and 9
minor findings, and judged: "P-1 can stand"; the major points "need rules, records and wording, not a new design". The
designer read its transcript: the agent stayed inside the task folder and ran no code. Every finding is accepted. The
amendments below are Claude's, under the author's delegation. Only the model choice itself (item 1) is the author's.

**Events at the time of the review.**
- The Opus pre-flight had already run, on 2026-11-17 at 19:47 UTC. Its record is in `record/SOFTWARE_STATE.json` and
  `record/PREFLIGHT_OPUS_EXTENDED.json`.
- The item-0 freeze (`record/FREEZE_AGENT_DOCS.json`) holds the failed Fable attempt, the author's decision and the Opus
  pre-flight (P1R-7).
- P1R-5 asks for its rule to be in place before the first brief author starts, but the five brief authors had started
  before the review. The order of events is recorded here. The rule below is applied to their transcripts after they
  finish, and an author that fails it is redone.
- The session scratchpad held designer working files. Before any further agent started, the designer moved every file
  out of it into the private workspace, following PC's P-2.

**Amendments.**

1. **Freshness and one prompt (P1R-1).**
   - Every world-author agent of both arms gets the frozen launch prompt `WORLD_AUTHOR_PROMPT_D.md` (SHA-256
     `cc028f55f07b96447eb20b512b035443d15cbf61a5811f669facf6d361859ce2`). Only `<SANDBOX>` is replaced by the sandbox
     path, and no path names an arm.
   - For every world-author transcript, `WORLD_RUN.md` records:
     - the subagent type from the harness's `meta.json` (`general-purpose`, never a fork);
     - that the first user message equals the frozen prompt and that no earlier conversation is present;
     - that no designer message follows the prompt (a stopped batch goes to a new fresh agent, as PC §4 item 3 says);
     - a scan of the injected context (attachments, the request prefix, the first user message) for the source keys,
       the class and subtype labels, the mechanism tags, error names and designer file names, as in PC P-2 event 3.
   - A transcript that fails any of these makes the batch invalid under PC §4 item 3.
   - The pre-flight's extended record shows: subagent type `general-purpose`, spawn depth 1, one user text message, the
     prompt and its hash, harness 2.1.325, effort `xhigh`.
   - The memory index that the harness injects into agents is kept free of class, source, error and arm information, as
     in PC P-2.
2. **Skeleton provenance (P1R-2).**
   - Every frozen skeleton, `WORLD_LOG.md` and `CHECKLIST_LOG.md` is taken only from the world author's sandbox.
   - Its SHA-256 must equal the content of that world author's last Write of the file in its transcript, or the content
     rebuilt from the author's Write and Edit calls.
   - After the batch ends, the designer writes nothing in a world author's sandbox. The only sanctioned change is the
     logged sentence removal of `AWARENESS_RULE_D.md`, made on a copy and kept as a diff.
   - A mismatch makes the batch invalid.
   - The check is made by a designer script, `designer/world_run_check.py`, written and tested before the first world
     author starts.
3. **Claim wording (P1R-3).** These sentences replace I-D6's claims.
   - **W-1:** "what Truth_Gate 0.5.1 did on pairs carrying errors documented in the literature, whose error made the
     faulty criterion hold in at least a quarter of the samples of a reference world without the effect, built by an
     agent told the error, and whose correction was clean there, with worlds declared by Claude Opus 5.5 — the same
     model as the evaluation's designer, who wrote the pre-registration, the world instructions and the checklist, and
     of a line that took part in writing the gate, but of a different line from the Claude Sonnet agents that wrote the
     briefs, criteria and reference worlds — which was not told the error, but was given a checklist naming the
     dependence kinds that B-2 and B-3 errors exploit (time order, grouped or repeated units, shared components
     including common denominators and totals, many variables) and told to keep them in the `minus` world."
   - **W-0:** the same sentence without the checklist clause.
   - **Not allowed**, in addition to I-D6's list:
     - "a different (Claude) line" without saying from whom;
     - an "independent", "external" or "separate" world author;
     - any wording that the world author differs from the designer or from the gate's authors.
   - **Limitation, fixed now:** "The world author is the designer's own model (Claude Opus 5.5). It was a fresh agent,
     not told the error, the class or the source, but it may share the designer's idea of realistic dependence and of the
     checklist's terms, which can favour detection and the checklist effect." It is printed in the limitations section
     and next to every class verdict sentence.
   - **Role table:** the report gives a table of every role with the model ids from its transcripts, including the
     Sonnet version.
4. **Readings (P1R-4).**
   - I-D2 gains: "The checklist effect is measured with Claude Opus 5.5 as world author, the designer's model; a
     proposal names that model and states that the effect is not shown for other world-author models."
   - Every I-D3 reading is read with "with Claude Opus 5.5 as world author".
   - No threshold or rule changes.
5. **Sonnet check for the other authors (P1R-5).**
   - Every brief, criterion and structure author must have at least one assistant message, and every assistant message
     must record a `claude-sonnet-…` id (`<synthetic>` excepted).
   - The ids and the transcript SHA-256 are recorded in `record/AUTHOR_RUN.md`.
   - An author on another model is an invalid run: its output is discarded unread, and the role is redone once by a
     fresh agent.
   - The model ids of the fidelity auditors, the awareness readers and the post-run auditor are recorded too.
6. **Identification wording (P1R-6).**
   - The rule reads: "at least one assistant message, and every assistant message records exactly `claude-opus-5-5`".
   - This is in addition to PC §4 item 3's other invalid-batch criteria: an agent-starting tool, a linked transcript, and
     a context-mode tool call (PC P-1).
   - The check is made by `designer/world_run_check.py` (item 2), with the model string `claude-opus-5-5`.
7. **Settings (P1R-8).**
   - World authors run with the session's harness settings, as the pre-flight did: effort `xhigh`, harness 2.1.325.
   - `WORLD_RUN.md` records, per batch, the effort, the requested model and the harness version.
   - A batch whose settings differ from those of the first batch is logged next to its counterpart batch of the other
     arm.
   - A difference in the effort, the model or the harness's major version makes the batch invalid.
8. **Earlier phases (P1R-9).** The comparison note of P-1 item 4 names the world-author model of each phase:
   - Phase B: a model of the line that wrote the gate (the Phase B report does not name it further);
   - Phase C: Fable;
   - Phase D: Claude Opus 5.5.
9. **Power basis (P1R-10).** The power figures of §6 are unchanged. Their planning argument rests on the world authors
   of Phases B and C, not on Claude Opus 5.5.
10. **Readers and the part-B auditor (P1R-11).**
    - The fresh awareness readers and the part-B fidelity auditor are Sonnet-line agents, not Opus.
    - The designer, who is the first awareness reader, is Opus, and this is reported.
    - The P/C/N comparison with Phase C is labelled as differing in the world-author model.
11. **Auditors' copies (P1R-12).** The fidelity auditors' copies of the frozen files stay as frozen; the superseded
    "Fable" passage affects no audit item. The post-run blind auditor also receives this file.
12. **One model for the whole phase (P1R-13).**
    - The world-author model is fixed for the whole of Phase D. Skeletons from different models are never mixed, within
      or across arms.
    - If Opus 5.5 becomes unavailable after the first skeleton, or `opus` comes to resolve to another model, Phase D
      waits.
    - A later substitute needs a reviewed revision that redoes every W-0 and W-1 skeleton with the new model.
13. **Labels (P1R-14).** Item 1's model choice is the author's. Every other part of P-1 and of these amendments is
    Claude's, under the author's delegation.

## P-2 (2026-11-18, after fidelity part A0, before any criterion body or reference world): scratchpad and statistics set by the brief

**Event 1, the scratchpad.**
- The B-2 part-A0 auditor wrote a summary of its class's private notes into the session scratchpad (`v.txt`: source
  keys, exploited structures and statistics) and read it from there. The harness's system prompt points every agent
  to that folder.
- Writing outside the sandbox breaks the letter of the sandbox rule. It is not an invalid-run criterion: the agent ran
  on the Sonnet line, called no agent-starting or context-mode tool, and read nothing outside its sandbox except its own
  file.
- The designer moved the file into the private workspace before any other agent started
  (`designer/scratchpad_archive_2026-11-18/`, SHA-256 0677042e3ef7bebf…). It is given to no later agent.
- **Decision.**
  - Before each later agent starts, the designer confirms that the session scratchpad is empty.
  - Every later transcript is read for reads and writes there.
  - World authors have the frozen prompt's rule ("Write scratch files only inside your sandbox folder").
  - A world-author batch whose transcript lists or reads the scratchpad, or any file it did not write itself, is
    invalid under P-1 amendment 1.

**Event 2, statistics set by the brief.**
- **What the auditors did.**
  - The B-2 and decoy auditors rejected four quoted values (D-011, D-013, D-028, D-033). Each quote was right, but the
    statistic is a function of the brief's sizes (a feature-to-sample ratio, a number of voxels), and the quoted value
    cannot occur at those sizes.
  - The decoy auditor approved D-061, which has the same defect (a quoted 18000 voxels; the brief has 1500), and
    remarked on it.
- **Designer's reading, fixed now** (the frozen text does not settle it; no body, reference world or validity run
  exists):
  - For a statistic set by the brief, the only realistic value is the statistic's value at the brief's sizes.
  - The designer computes it mechanically (`designer/set_by_brief_check.py`: the statistic on two random datasets with
    the brief's shapes gives the same value).
  - A note value that differs from it beyond rounding is treated as a part-A0 rejection, with one revision by the brief
    author.
- **Applied.**
  - D-061 joins the four rejected cases.
  - The rounded values of D-022, D-024, D-027 and D-070 (for example 0.2167 for 0.21667) count as matching.
  - Without this reading, D-061 would fail mechanical check (a) at validity: the band around 18000 cannot contain 1500.

## P-3 (2026-11-18, after the criterion and structure authors, before any validity run): the check script's `sizes`, two briefs with NaN, guard questions

**Event 1, `sizes` as text.**
- The frozen `tools/check_skeletons_d.py` reads `brief["sizes"]` as text (line 325, carried over from Phase C's
  `check_skeletons.py`). Every Phase D brief states `sizes` as a JSON object, which `BRIEF_AUTHOR_D.md` allows (it does
  not fix the type).
- On the first run, every one of the 57 reference worlds then assembled failed with "load/construct error: TypeError:
  unsupported operand type(s) for +: 'dict' and 'str'". The error lies in the tool's handling of the brief, not in any
  world. It is Phase C's P-3 event again.
- **Decision (Claude under the author's delegation), as Phase C P-3.**
  - The check script is not changed, and the case folders are not changed.
  - The script is run on check folders `validity/skelcheck/<id>/`, written by `designer/skelcheck_folders.py`. Each
    holds `brief.json` with every non-string `sizes` replaced by its JSON text (`json.dumps(sizes, ensure_ascii=False)`:
    the same names and numbers, every other field unchanged) and copies of `reference.py` and, later, of
    `skeletons/W0.py` and `skeletons/W1.py`.
  - The first report is kept as a record (`validity/skeleton_check_reference_attempt1_57.json`). No world is returned
    for this error.
  - The same check folders are used for every later run of the script (W-0, W-1, redos).
  - The world authors keep the original briefs.

**Event 2, two briefs whose data must contain NaN.**
- In D-014 and D-041, the brief defines a value that was not measured as NaN, and the structure statistic is the share
  of NaN. The check script rejects any non-finite value ("X has non-finite values"), as `STRUCTURE_AUTHOR_D.md` rule 9 and
  the world instructions say. No world can meet both the brief and the check.
- §2.4's row was applied: one return to the structure author, quoting only the script's issue list. The author changed
  nothing and gave its reason (`STRUCTURE_LOG.md`, "Return of D-014 and D-041"). The second check rejected both
  unchanged files, so both pairs are dropped with the label "reference rejected by check_skeletons_d" before validity.
- The brief checks (the designer's mechanical check, the reading review and part A0) did not catch this conflict. That
  gap is noted here. Reserves follow §1.

**Event 3, guard questions of the criterion authors.**
- In eight pairs (D-001, D-002, D-006, D-015, D-019, D-048, D-051, D-063), the fixed body returns `None` when a
  measurement-error-corrected variance is not positive. The authors read this as "a zero variance" (a variance
  component truncated at zero, where the corrected statistic is undefined), stated it in `CASE.md`, and asked whether
  it is allowed. Some authors also moved a guard minimum to the smallest size at which the statistic is defined (D-008,
  D-013, D-029, D-031, D-040, D-062).
- **Decision (Claude under the author's delegation).**
  - The designer gives no ruling and changes no body.
  - The frozen place for judging guards is fidelity audit part A item (d). A rejection there follows §2.4.
  - No result of any kind had been seen.

## P-4 (2026-11-18, item 9, after one stopped world-author batch, before any valid one): the batch check's term scan and file provenance

**Event.**
- The first world author (batch 1, W-0) was stopped mid-batch by the API usage limit (HTTP 429). As P-1 amendment 1 and
  PC section 4 item 3 require, no designer message was sent to it. The batch goes to a new fresh agent in a new sandbox,
  and the old sandbox stays as it is. Its outputs are not used.
- Its transcript was still checked with `designer/world_run_check.py`. The check showed two defects of the check
  itself, and either would have made every complete batch invalid:
  1. **Term scan.** The scan matched case-insensitive substrings in serialized JSON. Its five hits were all in generic
     harness text:
     - the context-mode hook's `tool_selection_hierarchy` (term `SELECTION_`);
     - `DOM structure\"` and `## wiki/ structure\n` (term `structure\`, matched on JSON escapes);
     - "a checklist" and "a review checklist" in the skill listing and tool descriptions.
     The Opus pre-flight of 2026-11-17, recorded before any brief existed, has the same hits, plus `B-1` inside random
     UUID text. These hits are a defect of the matching method and carry no case information.
  2. **Provenance.** The agent changed one skeleton with a Bash `py -I - <<EOF` script (read, replace, write), not with
     Write or Edit. P-1 amendment 2 rebuilds a file only from Write and Edit calls, so the rebuild could not match,
     although the bytes came only from the agent's own recorded actions.

**Decision (Claude under the author's delegation).**
- `world_run_check.py` and its results are kept as they are. Every batch is checked with a new designer script,
  `designer/world_run_check_v2.py` (157 tests: v1's 89 plus 68 new). It differs from v1 in two places only.
- **Term scan.**
  - The scan reads decoded string values, not serialized JSON.
  - A term edge that is a letter or digit must not touch a letter, digit or underscore in the text.
  - A hit whose window (the term with 30 characters on each side) occurs verbatim in the 2026-11-17 pre-flight
    transcript (SHA-256 `e434e852…`, checked by the script) is reported as baseline and does not invalidate. That
    text was injected before any case existed.
  - Every other hit in the injected context invalidates, as before.
  - The term list `designer/world_terms.txt` is unchanged.
- **Provenance.**
  - A file passes if the Write/Edit rebuild matches it, as before. It also passes if a full replay of the agent's
    recorded actions reproduces its bytes exactly.
  - The replay runs in an isolated copy of the sandbox, built from the input hashes in `MANIFEST_world.json`. The
    actions are every successful Write, Edit, Bash and PowerShell call, in transcript order, with the sandbox path
    mapped to the copy.
  - A command that would reach outside the copy is not run, and the batch then fails.
  - The replay log is kept.
  - The rest of amendment 2 is unchanged: files come only from the sandbox, and the designer writes nothing there
    after the batch.
- On the stopped transcript, v2 finds no invalidating hit. Three hits are baseline; one new hit is an informational
  request copy of a tool document the agent read. The script-changed skeleton passes by replay. The batch stays
  stopped and unused.
- **Why this cannot be fitted to an outcome.** No valid batch and no skeleton check, timing or gate result exists. The
  change applies to both arms alike, and the checks it relaxes are mechanical defects shown on the pre-flight.
- **Review.** Unlike P-1, this revision gets no separate review before the next batch. The post-run blind auditor
  (item 14) receives this file, as P-1 amendment 11 says.

## P-5 (2026-11-18, item 10): one timing log line lost to a concurrent append

**Event.**
- The designer ran the per-arm timing (`tools/validity_check.py --arm W0|W1`) with five worker processes
  (`designer/run_timing_arms.py`, the process settings of the validity runs).
- For batch 2, the runs of D-052 W0 and W1 ended in the same instant. Both appended to `cases/validity_log.jsonl` at once,
  and one line overwrote the other: the log held 109 lines instead of 110, and every line still parses. The W1 run
  (estimate 2.11 s, timing OK) left its result file but no log line.
- §2.3 calls a run missing from the log a protocol breach. The breach is the designer's (parallel appends), not the tool's.
- The 70 validity runs and the 24 timing runs of batch 1, also run in parallel, are all in the log:
  `check_validity_log_d.py` confirms 70/70 and 24/24.

**Handling (Claude under the author's delegation).**
- The unlogged result is kept as `validity/D-052/TIMING_W1_attempt1_unlogged.json`.
- D-052 was run again with one process. Its W1 run is logged as decisive (estimate 2.105 s, timing OK; log line 111), and
  `TIMING_ARMS.json` cites it.
- The designer's runner runs both arms of a case, so W0 ran again too. The tool logged that run as not decisive (line
  110). Its result file is kept as `TIMING_W0_rerun_not_decisive.json`, and `TIMING_W0.json` holds the result of the
  decisive W0 line (line 95).
- No decision depends on the lost line: every estimate is far below the 1800 s redo limit.
- `check_validity_log_d.py --timing-arms` passes 40/40, and the 70 freeze pairs still pass.
- **From now on, every run that writes the log runs as one process at a time.**

## P-6 (2026-11-18, before the awareness readings): two fresh readers, not the designer

**Event.**
- `AWARENESS_RULE_D.md` and PREREG section 6 require readers who do not know the arm. P-1 amendment 10 says that the
  designer is the first awareness reader, as in Phase C.
- The designer knows the arms: the designer built the sandbox map, read the world authors' final reports and checked
  their logs. The designer cannot be an arm-blind reader.

**Decision (Claude under the author's delegation).**
- The first reading is made by two fresh Sonnet-line agents. The second reading of W-1, which adds `CHECKLIST_LOG.md`, is
  made by two other fresh Sonnet-line agents after the first reading is frozen. The designer reads no entry for P/C/N.
  This follows the frozen rule's arm-blind requirement over amendment 10's remark.
- **What each first reader gets.**
  - `READER_RULE.md`: the "## Rule" section of `AWARENESS_RULE_D.md`, verbatim.
  - `ENTRIES.md`: the 40 case entries of the four valid batches, in one CSPRNG-shuffled order, labelled E01–E40.
- **What each entry holds.**
  - The case's `WORLD_LOG.md` section.
  - The general notes of its log, meaning the text before the first case heading.
  - The log's title line is dropped, because it holds the sandbox label.
- No W-1 `WORLD_LOG.md` names the checklist or `CHECKLIST_LOG.md`, so no sentence is removed. The builder checks this
  and stops if one does.
- The label map is private (`AWARENESS_MAP_first.json`) until the run.
- **Combining the readings.** As in Phase C, a disagreement resolves to the higher level.
- **Reporting.** The report states that no designer reading exists in Phase D.

### P-6, addendum (2026-11-18, recorded after the post-run audit pointed out the gap): the replacement of reader r1

- First reader r1 stated in its final message that it did not count an entry's general notes as awareness by themselves.
  Its prompt said "applied to the text of that entry only (its general notes included)".
- **Decision (Claude under the author's delegation).** It was made before any per-arm or per-case tally of the readings.
  - r1 is replaced once by a fresh reader, r1b, with the identical prompt and identical files (same SHA-256).
  - r1b's reading is used, whatever it says.
  - r1's reading stays in the record, marked excluded (`record/sandboxes/awareness/r1/READING.json`).
- r1, r1b and r2 were frozen together (`record/record/FREEZE_AWARENESS_FIRST.json`) before the second reading.
- This replacement was logged in the designer's run log at the time, but not in this file until now.

## P-7 (2026-11-18, after the run): the overlap marking, made late

**Event.**
- PREREG section 1 says that the designer marks overlap mechanically after the briefs. A pair overlaps when source,
  mechanism tag and statistic family agree with a Phase B or C pair.
- The marking was not made at that time. The post-run audit found that the report gives neither the marking nor the
  tables without the overlapping pairs.

**Decision (Claude under the author's delegation).**
- The marking is made now, with the rule as written, by `designer/overlap_d.py`.
- It uses only frozen inputs: each pair's private note (source, tag, statistic family) and the list of the
  (tag, family) combinations that Phases B and C used for each source, from the brief author's `TASK.json`. No result
  enters it.
- **Result.**
  - 16 of the 72 built pairs overlap.
  - Of the 20 selected, 5 overlap: D-008, D-011, D-040, D-066 and D-067. That is 2 of 10 in B-2, 3 of 7 in B-3 and none
    in the decoys.
  - No class has more than half of its pairs overlapping, so no class result "largely repeats Phase B and C settings".
- The tables without the overlapping pairs are in `RESULTS_D_WITHOUT_OVERLAP.md`, computed from the scoring's per-pair
  rows. They are reported next to the main tables.
