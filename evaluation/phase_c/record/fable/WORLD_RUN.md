# Phase C world author runs (PREREG_PHASE_C §4 item 3; REVISIONS-post-freeze P-1)

Batches: consecutive blocks of 15 in shuffle order (seed hex 3a02a4aabbb519dfba488e1b2af5802ab02398b57a42917ba74be4dd1d1c8e04
from FREEZE_PREREG_C.json): batch01 C01–C15, batch02 C16–C30, batch03 C31–C45, batch04 C46–C54. Each batch: a fresh
Claude Code agent started with the model parameter `fable` (agent type general-purpose), sandbox
`fable/batchNN/` holding `WORLD_INSTRUCTIONS_PHASE_C.md` (frozen), `BATCH.json` (= `world/BATCH_NN.json`, unchanged),
`agent_docs/`, `pkg/`. A stopped batch is continued by a new fresh Fable agent for the ids without a passing skeleton.

## Task prompt (identical for every batch except the folder name)

> You are the world author for a batch of scientific claims. Your sandbox folder is
> `E:\Claude Projects\Kapi\phase_c_private\fable\batchNN\`. Read `WORLD_INSTRUCTIONS_PHASE_C.md` there first and follow
> it exactly; your batch file is `BATCH.json` in that folder. The context-mode tools (`ctx_search`,
> `ctx_batch_execute`, `ctx_fetch_and_index`, `ctx_index`) read a store shared by every session on this machine or
> fetch from the internet; using them counts as reading outside your sandbox. Do not call them. Write your skeletons
> into the folder `skeletons\` inside your sandbox folder and your log as `WORLD_LOG.md` there. Final message as the
> instruction file says.

## Runs

(filled in by the designer from each batch's harness transcript: agent id, request metadata model, assistant-message
model ids, dates, tool names called, linked agent transcripts, transcript SHA-256, validity)

### Attempt 1 (2026-11-13 20:35 UTC): all four batches stopped by the account's weekly usage limit, no skeleton

| Batch | Agent id | Request model | Assistant-message models | Tools called | Linked agents | Transcript SHA-256 (first 16) | Skeletons | Validity |
|---|---|---|---|---|---|---|---|---|
| batch01 | aee45efbd5c73a671 | fable (meta pickedEffortModel claude-opus-5-5) | claude-fable-5-2 ×7, `<synthetic>` ×1 (the error message) | Read 3, Bash 2 (all inside the sandbox) | 0 | 5091ae9a0104273f | 0 | valid, stopped |
| batch02 | ad0b63ace4acff5f1 | fable (same meta) | claude-fable-5-2 ×6, `<synthetic>` ×1 | Read 4, Bash 1 (inside) | 0 | 930d4535e5ec4ffa | 0 | valid, stopped |
| batch03 | ab200377006386a0d | fable (same meta) | claude-fable-5-2 ×4, `<synthetic>` ×1 | Read 2, Bash 1 (inside) | 0 | e3d0114c9943e1a3 | 0 | valid, stopped |
| batch04 | a5b4e03061c8182ef | fable (same meta) | claude-fable-5-2 ×2, `<synthetic>` ×1 | Read 2 (inside) | 0 | dd58c528fb86c21b | 0 | valid, stopped |

Each agent read only its instruction file, `BATCH.json`, the folder listing, `agent_docs/GATE.md` and parts of `pkg/`.
Transcripts copied to `transcripts/attempt1/`. By §4 item 3 ("Stops"), every id of the four batches goes to a **new
fresh Fable agent** with the same prompt and the same batch file; that continuation counts as the first attempt for
those ids. (The stopped agents are not resumed.)

### Attempt 2 (2026-11-15): new fresh Fable agents, two at a time, same prompt and batch files

| Batch | Agent id | Request model | Assistant-message models (entries) | Tools called | Linked agents | Transcript SHA-256 (first 16) | Dates (UTC) | Skeletons | Check script (P-3 briefs copy) | Validity |
|---|---|---|---|---|---|---|---|---|---|---|
| batch01 | adf73007a9e97d170 | fable (meta pickedEffortModel claude-opus-5-5) | claude-fable-5-2 ×33 | Read 4, Bash 4, Write 16 | 0 | 89af052c950ed987 | 2026-11-15 00:47:07 – 00:56:32 | 15 (C01–C15) | 15/15 pass | valid |
| batch02 | a0fc2b410a8f7365f | fable (same meta) | claude-fable-5-2 ×35 | Read 4, Bash 5, Write 17, Edit 1 | 0 | d1867b2b3d1c96ed | 2026-11-15 00:47:09 – 00:57:43 | 15 (C16–C30) | 15/15 pass | valid |

* Neither transcript calls a context-mode tool, an agent-starting tool, WebFetch or WebSearch (P-1; §4 item 3). Reads:
  only the instruction file, `BATCH.json`, `agent_docs/GATE.md`, `pkg/truth_gate/study.py` and folder listings inside
  the sandbox.
* Outside the sandbox: each batch wrote and ran one own check script in the session scratchpad (honour-system event,
  `REVISIONS-post-freeze.md` P-2); the scripts are kept in `transcripts/attempt2/` and given to no later agent. The
  harness-injected context (user `CLAUDE.md` files, memory index) holds no class, source or error term (P-2, item 3).
* The first check-script run failed the 9 skeletons whose brief gives `sizes` as an object, from a tool/brief type
  mismatch (P-3); with the P-3 briefs copy all 30 pass. No skeleton was returned.
* Transcripts (with `.meta.json` and `.prefix.json`) copied to `transcripts/attempt2/`; per-transcript summaries by
  `designer/transcript_check.py`.
* batch03 and batch04 started after the scratchpad was emptied (P-2), 2026-11-15.

| Batch | Agent id | Request model | Assistant-message models (entries) | Tools called | Linked agents | Transcript SHA-256 (first 16) | Dates (UTC) | Skeletons | Check script (P-3 briefs copy) | Validity |
|---|---|---|---|---|---|---|---|---|---|---|
| batch03 | a19c89c727a5f89de | fable (same meta) | claude-fable-5-2 ×23, `<synthetic>` ×1 (the error message) | Read 4, Bash 1, Write 15 | 0 | 5550b33f089cfa69 | 2026-11-15 01:00:53 – 01:07:44 | 15 (C31–C45), no `WORLD_LOG.md` | 15/15 pass | valid, stopped (5-hour limit) |
| batch04 | a0f3d13f3b9afb825 | fable (same meta) | claude-fable-5-2 ×10, `<synthetic>` ×1 | Read 5, Bash 2 | 0 | 8b1265b8163596d2 | 2026-11-15 01:00:55 – 01:05:13 | 0 | — | valid, stopped (5-hour limit) |

* Both read only sandbox files; no outside-sandbox path; nothing written to the session scratchpad.
* batch03: all ids have a passing skeleton, so none goes to a new agent (§4 item 3); the missing world log is handled by
  `REVISIONS-post-freeze.md` P-4 ("no log", resolved P).
* batch04: all 9 ids (C46–C54) go to a new fresh Fable agent with the same prompt and the same batch file in the same
  sandbox (the stopped agent wrote nothing there); this continuation counts as the first attempt for those ids.

### Continuation of batch04 (2026-11-15): new fresh Fable agent, ids C46–C54

| Batch | Agent id | Request model | Assistant-message models (entries) | Tools called | Linked agents | Transcript SHA-256 (first 16) | Dates (UTC) | Skeletons | Check script (P-3 briefs copy) | Validity |
|---|---|---|---|---|---|---|---|---|---|---|
| batch04 (cont.) | aa8c84923f96b3413 | fable (same meta) | claude-fable-5-2 ×26 | Read 4, Bash 4, Write 10 | 0 | 2a2a8caae8375ec7 | 2026-11-15 05:41:57 – 05:48:40 | 9 (C46–C54) + `WORLD_LOG.md` | 9/9 pass | valid |

* Reads only inside the sandbox; no context-mode, agent-starting, WebFetch or WebSearch call. Outside the sandbox it
  wrote and ran one own check script in the session scratchpad (honour-system event as in P-2; kept as
  `transcripts/attempt2/batch04cont_scratchpad_chk.py`, SHA-256 088e1a83…, given to no later agent).
* Its log says that for C46 it computed the claim's statistic once on a 200 000-row calibration population to size the
  effect (not on study-sized draws). Instruction rule 7 allows checking that the effect is present in `plus` and absent in
  `minus` and forbids writing or testing an analysis that could serve as the criterion; recorded as a fact, not a ground
  for a redo (§4 item 4: properties the script cannot check are not grounds for a redo).

**Item 3 complete.** All 54 ids have a skeleton that passes the check script (P-3 briefs copy) at the first check; no
skeleton went back. World logs: batch01, batch02, batch04; none for batch03 (C31–C45; P-4).
