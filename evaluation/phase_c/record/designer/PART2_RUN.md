# Phase C part 2: criterion author runs (PREREG_PHASE_C §4 item 5; AUTHOR_PHASE2_C.md; REVISIONS-post-freeze P-1, P-5)

Setup: `designer/part2_build.py` (2026-11-15) made `authors/<folder>/cases/<case id>/` for the 54 ids of `ID_MAP.json`
(skeleton.py read-only, faulty.py and fixed.py writable, all equal to the frozen skeleton by SHA-256), ASSIGNMENT.json,
`AUTHOR_PHASE2_C.md` and `work/` in every class folder, and the B-1 brief author's own extracts in `authors/B1/src/`.
Agents: fresh `kodlayici` (Sonnet line), one per class, the same kind as the brief authors. A stopped author is followed
by a fresh one with the same prompt; it continues with the cases without `CASE.md`.

## Task prompt (identical except CLASS and FOLDER)

> You are the criterion author of class CLASS in a pre-registered evaluation. Your sandbox folder is
> `E:\Claude Projects\Kapi\phase_c_private\authors\FOLDER\`; it is also your class folder. Read `AUTHOR_PHASE2_C.md` there
> first and follow it exactly. The context-mode tools read a store shared by every session on this machine. You may use
> `ctx_fetch_and_index` to fetch an online source (log the URL), and `ctx_search` only with a `source` filter that names a
> label you indexed yourself in this run; do not call `ctx_search` without such a filter, and do not call
> `ctx_batch_execute` or `ctx_index`. The harness may suggest a session scratchpad folder; do not use it: scratch scripts go
> in `work\` inside your class folder. Final message as the instruction file says.

## Runs

(filled in by the designer per agent: agent id, request model, assistant-message models, tools called, context-mode calls,
outside-class-folder paths, transcript SHA-256, cases with CASE.md)

| Class | Agent id | Type | Assistant-message models (entries) | Tools | Context-mode calls | Outside-folder paths | Transcript SHA-256 (first 16) | Time (UTC, 2026-11-15) | CASE.md |
|---|---|---|---|---|---|---|---|---|---|
| B-1 | a602619fe2d711567 | kodlayici | claude-sonnet-5-5 ×57 | Read 19, Glob 1, Grep 1, Bash 11, Write 4 | none | none | 8725ae20c1156be8 | 05:55:52 – 06:05:14 | 12/12 |
| B-3 | ad4066f264930da43 | kodlayici | claude-sonnet-5-5 ×49 | Read 3, Bash 23, Write 3 | none | none | ecae3b9f5ec4e571 | 05:55:57 – 06:01:43 | 12/12 |
| B-6 | aac5ddcc980f25b35 | kodlayici | claude-sonnet-5-5 ×67 | Read 6, Bash 24, TaskStop 1, Write 4, Edit 2 | none | none | 5022fd892aef316b | 05:55:59 – 06:04:49 | 12/12 |
| O | ab6efdd903689516e | kodlayici | claude-sonnet-5-5 ×67 | Read 6, PowerShell 1, Bash 16, Edit 12, Write 6 | none | none | 568cc073d62baa45 | 05:56:02 – 06:02:23 | 6/6 |
| B-2 | a9cf679166b180a9c | kodlayici | claude-sonnet-5-5 ×73 | Read 1, Bash 34, ToolSearch 1, ctx_fetch_and_index 1, Write 3 | 1 `ctx_fetch_and_index` (own label `b2-part2-var06`; allowed by P-5) | none | a3149da50bbaa8e9 | 05:55:54 – 06:10:41 | 12/12 |

Outside-folder paths: the checker's flags were relative paths inside the class folder (`../cases`, `../../agent_docs`) and URLs quoted in written text; no tool call reads or writes outside the class folder; no WebFetch or fetch command. `faulty.py` was touched only as text (body generation, syntax check, byte comparison with the skeleton); every pre-check script imports only `fixed.py` (designer read every Bash command naming `faulty` and the `work/` scripts). The B-6 author's one `TaskStop` stopped its own hung Bash task. Transcripts and per-transcript summaries in `designer/part2_transcripts/`. B-2: its one context-mode call fetched the VAR06 page under its own label (the page returned a reCAPTCHA; no bypass was tried); it read back once its own large command output (the sandbox `PREREG_PHASE_C.md`) from the harness `tool-results` folder, a harness side effect as in step 2.
