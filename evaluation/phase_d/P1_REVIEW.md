# Review of P-1 (world-author model Claude Opus 5.5 instead of Fable)

Inputs read: every file under `in/` and `INSTRUCTIONS.md`. Nothing else was read, and no code was run.

## Counts

| Severity | Count | Ids |
|---|---|---|
| Blocking (P-1 cannot stand) | 0 | none |
| Major (fix before any skeleton exists) | 5 | P1R-1 to P1R-5 |
| Minor | 9 | P1R-6 to P1R-14 |

P1R-5 must be in place even earlier, before the first brief author starts.

## Question 1: coverage of passages that name Fable, the world-author line or a property of the world-author model

| # | File and passage | Settled by P-1? | Finding |
|---|---|---|---|
| 1 | PREREG §0.3 Main: "a world author who is not told the error, the class or the source" | No model is named. The claim side is open | P1R-3 |
| 2 | PREREG §0.3 Arm comparison: "against the same world-author model without it" | Yes. Both arms use Opus, and a batch on another model is invalid | none |
| 3 | PREREG §3 item 0 "as PC §4 item 0": (d) Fable pre-flight; (f) freeze of (a) to (e) | (d) yes; (f) no | P1R-7 |
| 4 | PREREG §3 item 0 Sandbox: "Every transcript is checked for these points with the designer's transcript tools." | No. The tool and the model string are not named | P1R-6 |
| 5 | PREREG §3 item 9: "of PC's world-author line (Fable)" | Yes (renamed by P-1 item 1) | none |
| 6 | PREREG §3 item 9: "PC §4 item 3 (identification, invalid batch, stops) applies to every world-author agent" | In wording only. What the rule proves is weaker now | P1R-1, P1R-2, P1R-6 |
| 7 | PREREG §3 items 9 and 10: rejected skeleton and timing redo "to a fresh agent of that arm" | Yes ("redos, timing redos") | none |
| 8 | PREREG §6 Power: planning argued from the worlds of Phases B and C | No | P1R-10 |
| 9 | PREREG §6 Descriptive: "Arm W-0 with all scorings, against PB and PC" | Mostly. The Phase B model is probably misnamed | P1R-9 |
| 10 | PREREG §6 Descriptive: "Awareness: P/C/N as PC, with two readers" | No | P1R-11 |
| 11 | PREREG §8 I-D2 and I-D3 (adoption, the checklist effect) | No | P1R-4 |
| 12 | PREREG §8 I-D6 W-1 claim; the W-0 claim "with PC's wording for the world author"; the "Not allowed" list | W-1 in part; W-0 and the list no | P1R-3 |
| 13 | PC §0 ("Fable, a different Claude model line from the one that wrote the gate and the criteria"), PC §4 item 7, PC I-6, PC I-8, which Phase D reaches through item 12 | No. P-1's blanket "read Claude Opus 5.5" turns them into false statements | P1R-3 |
| 14 | PC §4 item 3: `claude-fable-…`, "redone once by a fresh Fable agent", "Stops" | Yes (P-1 item 1). Wording residue remains | P1R-6 |
| 15 | PC §2 timing remedy and PC §4 items 4 and 5 ("a fresh Fable agent") | Yes ("every agent that writes or changes a skeleton") | none |
| 16 | `WORLD_INSTRUCTIONS_D0.md`, `WORLD_INSTRUCTIONS_D1.md` | No passage names Fable, a line or a model property. "Do not start any other agent or any tool that runs a model" does not depend on the model. The launch prompt is not in the frozen set | P1R-1 |
| 17 | `AWARENESS_RULE_D.md`: "copied unchanged from PC"; "Two readers apply it" | No model is named. The readers' model is open | P1R-11 |
| 18 | `FIDELITY_AUDIT_D.md`: the reading list holds `PREREG_PHASE_D.md` (which says "Fable"); part B item (o) judges Opus-written skeletons | No | P1R-11, P1R-12 |
| 19 | `REVISIONS_D.md` | No passage names Fable or the world-author model. R1-7 ("PC §4 item 3 for every agent") is row 6. R1-10 ("Model line named") concerns the Sonnet structure author, a separation that P-1 item 3 now relies on | P1R-5 |

## Findings

### P1R-1 (major): the identification rule no longer shows that a world author is fresh

- **File:** `in/REVISIONS-post-freeze.md`, P-1 items 1 and 4, and `in/SOFTWARE_STATE.json` `opus_preflight`.
- **Quote:** "The transcript must record `claude-opus-5-5` for every assistant message (`<synthetic>` entries excepted)." Also: "They read only the frozen world instructions, their batch file, `agent_docs/` and `pkg/`."
- **Reason:**
  - In Claude Code, a fork-type subagent inherits the parent's whole conversation and always runs on the parent's model.
  - With Fable, the model-id check also excluded a fork of the designer's session, because a fork cannot run on a model other than its parent's.
  - The designer is now Claude Opus 5.5. A fork, or an agent resumed with designer messages, would record `claude-opus-5-5` on every assistant message and pass the rule while holding the designer's knowledge of errors, classes and sources.
  - Nothing else checks freshness:
    - The launch prompt is not frozen.
    - The pre-flight record has no subagent-type field, no prompt hash and no first-message check.
    - Phase D's frozen text has no scan of the context the harness injects. PC's P-2 found that the harness injects the user's `CLAUDE.md` files and the memory index.
  - The P-1 sentence "They read only…" states blinding as a fact. No check backs it.
- **Fix:** add a rule in P-1 before any skeleton exists:
  - (a) One launch prompt for every world-author agent of both arms, identical except for the sandbox path and naming no arm. Record its SHA-256 in `REVISIONS-post-freeze.md` now.
  - (b) For every world-author transcript, record in `WORLD_RUN.md`:
    - the subagent type (general-purpose, not fork);
    - that the first user message equals the frozen prompt and that no earlier conversation is present;
    - that no designer message follows the prompt;
    - a scan of the injected context (`CLAUDE.md` files, memory index, hook text) for source keys, class labels, error names and designer file names, as in PC P-2 event 3.
  - (c) A transcript that fails (b) makes the batch invalid under PC §4 item 3.
  - (d) Extend the pre-flight record with these fields. If the existing transcript cannot show them, rerun the pre-flight under them.

### P1R-2 (major): the model id no longer ties a skeleton to its world author

- **File:** `in/REVISIONS-post-freeze.md`, P-1 item 1.
- **Quote:** "World authors (section 3 item 9) and every agent that writes or changes a skeleton (redos, timing redos) are fresh Claude Code general-purpose agents started with the model parameter `opus`."
- **Reason:** with Fable, a skeleton written or edited in the designer's own session could not carry a Fable transcript. The designer's session now records the same model id as a world author. So the id cannot show who wrote a skeleton, a `WORLD_LOG.md` or a `CHECKLIST_LOG.md`, and the awareness readings depend on those logs. Skeleton authorship is central to the claims ("worlds declared by …") and to H-D3.
- **Fix:** for every frozen skeleton and log:
  - record its SHA-256 next to the content of the world author's last Write or Edit of that file in its transcript, and require them to match;
  - take the files only from the world author's sandbox;
  - the designer writes nothing there. The only sanctioned edit is the logged sentence removal of `AWARENESS_RULE_D.md`, kept as a diff;
  - a mismatch makes the batch invalid.

### P1R-3 (major): the claim wording drops the separation from the designer, and the limitation is not fixed

- **File:** `in/REVISIONS-post-freeze.md`, P-1 items 3 and 4; `in/PREREG_PHASE_D.md` §8 I-D6; `in/phase_c/PREREG_PHASE_C.md` §0 and §4 item 7.
- **Quote:**
  - "so world authors are still of a different Claude line from those authors"
  - "with worlds declared by Claude Opus 5.5, a model of a different Claude line from the authors of the briefs, criteria and reference worlds, that was not told the error"
  - "That the world authors and the designer are the same model is reported as a limitation."
  - I-D6: "**W-0:** the same, with PC's wording for the world author."
  - PC §4 item 7: "All agents other than the world author are Claude models of the Opus and Sonnet lines, the family that wrote the gate".
- **Reason:**
  - The "different line" in the frozen claim came from PC, where Fable differed from every other agent and from the line that wrote the gate (PC §0). P-1 re-anchors it to the Sonnet authors only.
  - The world author is now the same model as the designer. The designer wrote the pre-registration, the world instructions and the checklist. On PC's own description, the world author is also of a line that took part in writing the gate.
  - A same-model world author may share the designer's idea of "realistic dependence" and of the checklist's terms. It may follow a checklist and documents written in its own style more readily. It may infer the designer's intent more easily. All of this favours detection and the checklist effect, and the separation is by instructions and sandbox alone.
  - Under P-1, this sits only in an unworded "limitation". The claim sentence itself still reads as a separation. The W-0 sentence points to "PC's wording", which carries PC's Fable premise. The "Not allowed" list does not exclude the new over-readings.
- **Fix:** before any skeleton exists, fix in P-1:
  - (a) **W-1 claim:** "… with worlds declared by Claude Opus 5.5, the same model as the evaluation's designer (who wrote the pre-registration, the world instructions and the checklist) and of a line that took part in writing the gate, but of a different line from the Claude Sonnet agents that wrote the briefs, criteria and reference worlds; the world author was not told the error, but was given a checklist …". Name the Sonnet version recorded in the transcripts.
  - (b) **W-0 claim:** write it out in full: the same sentence without the checklist clause.
  - (c) **Not allowed, added:** "a different (Claude) line" without saying from whom; "independent", "external" or "separate" world author; any wording that the world author differs from the designer or the gate's authors.
  - (d) **Limitation text:** write it now. Put it in the limitations section and next to every class verdict sentence, as PC did with the P/C/N shares.
  - (e) **Role table:** a report table of every role with the model id from its transcripts, the counterpart of PC §4 item 7.

### P1R-4 (major): the readings of §8 do not say that the checklist effect was measured with the designer's model

- **File:** `in/PREREG_PHASE_D.md` §8 I-D2 and I-D3.
- **Quote:**
  - I-D2: "The checklist is proposed for a later version of the methods protocol (with its own review) only if all of these hold".
  - I-D3: "On these pairs of both classes, the system with the checklist detects the error and passes the correction. The checklist raises declared detection."
- **Reason:**
  - H-D3 compares two arms of the same model, so the comparison stays internally valid.
  - The adoption rule, however, carries a checklist into the methods protocol, and the I-D3 readings speak of "the system" and "the checklist" in general.
  - The evidence now comes from one world-author model, the same model that wrote the checklist. Its response to the checklist may not transfer to other world-author models, such as Fable, which Phase C used.
  - P-1 says "the hypotheses … stay as frozen" but does not qualify these readings. Readings must be fixed before world-author behaviour can be seen, and the first skeleton shows it.
- **Fix:** add to P-1, with no change to any threshold or rule:
  - (a) In I-D2: "The checklist effect is measured with Claude Opus 5.5 as world author, the designer's model; a proposal names that model and states that the effect is not shown for other world-author models."
  - (b) In every I-D3 reading: "with Claude Opus 5.5 as world author".

### P1R-5 (major): the Sonnet-line separation now carries the claim, but nothing checks it

- **File:** `in/REVISIONS-post-freeze.md`, P-1 item 3; `in/phase_c/PREREG_PHASE_C.md` §4 item 3.
- **Quote:**
  - P-1 item 3: "The brief, criterion and structure authors stay on the Sonnet line".
  - PC §4 item 3: "**Every Fable agent of Phase C** … is subject to the identification and invalid-run rules below".
- **Reason:**
  - After P-1, the only model separation in the claim is between the world authors and the brief, criterion and structure authors.
  - The identification rules apply only to world authors. No frozen rule checks that the other authors actually ran on Sonnet. A harness fallback, a changed agent definition or an inherited model would go unseen and would falsify the new claim.
- **Fix:** before the first brief author starts:
  - require for every brief, criterion and structure author at least one assistant message, and a Sonnet model id on every assistant message (`<synthetic>` excepted);
  - record the ids and the transcript SHA-256 in a run file;
  - an agent on another model is an invalid run: discard its output and redo it once with a fresh agent of the role;
  - record the model ids of the fidelity auditors, the awareness readers and the post-run auditor as well.

### P1R-6 (minor): the identification rule as written

- **File:** `in/REVISIONS-post-freeze.md`, P-1 items 1 and 2; `in/PREREG_PHASE_D.md` §3 item 0.
- **Quote:**
  - "The transcript must record `claude-opus-5-5` for every assistant message (`<synthetic>` entries excepted)."
  - "A batch whose transcript records another model is invalid."
- **Reason:**
  - (a) A transcript with no assistant message satisfies "every assistant message" without proving anything. The failed Fable attempt had exactly that form ("one <synthetic> message, no assistant message").
  - (b) Item 2 restates only one invalid-batch criterion, which could be read as replacing PC §4 item 3's other criteria (an agent-starting tool, a linked transcript).
  - (c) P-1 says "every tool stays as frozen", but does not name the transcript tool that applies the model check or its model string. PC's string was `claude-fable-…`.
- **Fix:**
  - "at least one assistant message, and every assistant message records exactly `claude-opus-5-5`";
  - "in addition to PC §4 item 3's other invalid-batch criteria";
  - name the script that checks the id, and log the change of its string.

### P1R-7 (minor): the timing and record of the pre-flight

- **File:** `in/REVISIONS-post-freeze.md`, P-1 item 2; `in/SOFTWARE_STATE.json` `opus_preflight`.
- **Quote:** P-1: "The pre-flight of item 0 is run with that model, under PC's identification and invalid-run rules." Record: `"first_last_utc": ["2026-11-17T19:47:20.106Z", "2026-11-17T19:47:26.472Z"]`, `"result": "pass (every assistant message claude-opus-5-5)"`.
- **Reason:**
  - The pre-flight has already run, before this review. That is allowed, because no skeleton exists, but P-1 does not record it.
  - The record supports that `opus` resolved to `claude-opus-5-5` on 2026-11-17, in an agent whose prompt held no brief, with no agent-starting tool and no linked transcript.
  - It does not record:
    - the subagent type;
    - the prompt or its hash;
    - the working folder, or whether it was a sandbox, which matters because the agent made a `Glob` call;
    - the effort setting;
    - the harness version.
  - PC §4 item 0(f) freezes the start conditions. P-1 does not say that this freeze holds the failed Fable attempt, the author's decision and the Opus pre-flight.
- **Fix:**
  - Add a dated event line to P-1: the pre-flight was run at that time, with its result.
  - Extend the record with the missing fields, together with P1R-1 (d).
  - Name these three items in the item 0 freeze.

### P1R-8 (minor): settings beyond the model id are not fixed or recorded

- **File:** `in/REVISIONS-post-freeze.md`, P-1 item 1; `in/SOFTWARE_STATE.json`.
- **Quote:** "started with the model parameter `opus`"; `"meta_pickedEffortModel": "claude-opus-5-5"`.
- **Reason:** the id fixes the model, not its effort or reasoning setting or the harness version. Either can change between batches, for example when the session's effort is changed or the harness is updated. Such a change would differ between W-0 and W-1 batches and confound H-D3. The record holds no effort value.
- **Fix:**
  - State one setting for all world-author agents.
  - Record the setting and the harness version per batch in `WORLD_RUN.md`, as the harness records them.
  - Treat a deviation as an invalid batch, or log it next to the counterpart batch of the other arm.

### P1R-9 (minor): the world-author model of Phase B is probably misnamed

- **File:** `in/REVISIONS-post-freeze.md`, P-1 item 4.
- **Quote:** "(Fable there, Opus 5.5 here)".
- **Reason:** PC's title ("worlds by a different Claude model line"), PC §0 and PC I-6 ("A difference between Phase B and Phase C may come from the world author") imply that Phase B's world author was not Fable. If Phase B used an Opus-line author, W-0 shares its line with Phase B, and the report should say so.
- **Fix:** "(Phase B: <model from Phase B's record>; Phase C: Fable; Phase D: Claude Opus 5.5)", taken from each phase's record.

### P1R-10 (minor): the power planning value rests on other world-author models

- **File:** `in/PREREG_PHASE_D.md` §6, Power.
- **Quote:** "In Phases B and C, the pairs the audit judged adequate gave 21 of 22 PB-style detections and 22 of 22 clean passes, with worlds that happened to contain the structure."
- **Reason:** the planning value of 0.85 and the H-D3 discordance figures were argued from the world authors of Phases B and C. P-1 is right to keep the thresholds and figures, but their basis now concerns other models.
- **Fix:** add to P-1 item 4: "The power figures of §6 are unchanged; their planning argument rests on the world authors of Phases B and C, not on Claude Opus 5.5."

### P1R-11 (minor): the awareness readers and the part-B auditor may be the same model as the world author

- **File:** `in/AWARENESS_RULE_D.md`; `in/PREREG_PHASE_D.md` §6; `in/FIDELITY_AUDIT_D.md` part B; `in/phase_c/PREREG_PHASE_C.md` §4 item 4.
- **Quote:**
  - AWARENESS_RULE_D: "Two readers apply it, and a disagreement is resolved to the higher level."
  - PC §4 item 4: "the designer and a fresh agent that sees only the world logs and the rule".
- **Reason:**
  - The frozen texts fix no model for these readers or for the part-B auditor. If they are Opus, they judge Opus-written logs and skeletons. A judge of the same model may share the world author's framing and not see what it would itself write, which bears on P/C/N and on item (o).
  - The P/C/N comparison with Phase C now also differs in the world-author model.
- **Fix:** before the readers and the part-B auditor start:
  - name their models;
  - prefer a non-Opus line for at least one reader and for part B, or report the same-model judgement as a limitation;
  - label the P/C/N comparison with Phase C as differing in the world-author model.

### P1R-12 (minor): the auditors read the superseded "Fable" passage

- **File:** `in/FIDELITY_AUDIT_D.md`, "What you may read"; `in/PREREG_PHASE_D.md` §3 item 9.
- **Quote:** "this file, `PREREG_PHASE_D.md` and `P2_READING_D.md` (how item (f) is read);" and "The agents are fresh, of PC's world-author line (Fable), and disjoint between arms."
- **Reason:** the frozen reading list cannot take in P-1, so the auditors read a text that names Fable. No audit item depends on the model, so this is harmless. The post-run blind auditor (§7) does need P-1.
- **Fix:**
  - State in P-1 that the auditors' copies stay as frozen and that the superseded passage affects no audit item.
  - Give `REVISIONS-post-freeze.md` to the post-run auditor.

### P1R-13 (minor): unavailability after the first skeleton, and mixed models

- **File:** `in/REVISIONS-post-freeze.md`, P-1 item 2; `in/phase_c/PREREG_PHASE_C.md` §4 item 3.
- **Quote:** P-1: "If Opus 5.5 cannot be started, Phase D waits." PC: "A substitute model requires a new pre-registration revision, reviewed before any skeleton exists."
- **Reason:** the rule covers the start only. Opus 5.5 could become unavailable, or `opus` could come to resolve to another model, after some skeletons exist. Then PC's route ("before any skeleton exists") is closed, and the arms could end up holding skeletons from different models.
- **Fix:** "The world-author model is fixed for the whole of Phase D. Skeletons from different models are never mixed, within or across arms. If Opus 5.5 becomes unavailable after the first skeleton, Phase D waits. A later substitute needs a reviewed revision that redoes every W-0 and W-1 skeleton with the new model."

### P1R-14 (minor): parts of P-1 go beyond the author's decision and are not labelled

- **File:** `in/REVISIONS-post-freeze.md`, header and P-1.
- **Quote:** "Decisions are the author's where stated; otherwise they are Claude's under the author's delegation." and "Kredi yenilemeyeceğim. Opus-5-5 ile ilerle."
- **Reason:**
  - The author's decision covers buying no credits and using Opus 5.5. Extending the model to redos and timing redos follows from it.
  - Several items are the designer's own:
    - the general-purpose agent type;
    - re-anchoring "different line" to the Sonnet authors;
    - the wording of the limitation and of the claims.
  - The designer is the same model as the world author and has an interest in a "different line" wording.
  - None of these can be fitted to a Phase D outcome: no brief, skeleton or gate result exists, the pre-flight held no brief, and no threshold, scoring rule or hypothesis changes. The labelling still matters for the record.
- **Fix:**
  - Mark each P-1 item as the author's or as Claude's under delegation.
  - Take the claim wording through P1R-3.

## Judgment

P-1 can stand. The frozen text allows a substitute model with a reviewed revision, and the revision comes before any brief or skeleton. It is conservative: both arms keep one model, so H-D3 stays an internal comparison, and no threshold, scoring rule, tool or instruction file changes. P-1 also cannot be fitted to a Phase D outcome. The substitution matters because the world author is now the designer's own model.

- **Identification (question 3).** `claude-opus-5-5` on every assistant message is still adequate for its narrow purpose. It catches a fallback to another model, or a change in what `opus` resolves to. The pre-flight record supports that `opus` resolved correctly on 2026-11-17. But the check no longer shows that a world author is fresh or that it wrote a given skeleton (P1R-1, P1R-2). A designer fork or a designer edit would pass it.
- **Claims and readings (question 2).** The "different line" in the claims now holds only against the Sonnet authors, and nothing checks that they ran on Sonnet (P1R-5). The same-model limitation has to be part of the claim and adoption sentences, not an unworded note (P1R-3, P1R-4).

These five major points need rules, records and wording, not a new design. They should be added to P-1, and checked, before any skeleton exists; P1R-5 before the first brief author starts. The nine minor points tighten the wording and the record, and none of them changes a result.
