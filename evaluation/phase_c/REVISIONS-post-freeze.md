# Phase C: process events and readings after the freeze

The pre-registration is frozen (`FREEZE_PREREG_C.json`, core `0B8CC8F9F726103A`). Process events and readings that the
frozen text does not settle are recorded here, with reasons, before the step they could affect. Decisions by Claude
under the author's delegation.

## P-1 (2026-11-13, after the briefs, before the shuffle and before any world author): the shared context-mode store

**Event.** The machine runs a context-mode plugin whose search tools (`ctx_search`, and `ctx_batch_execute` with
queries) read one full-text store shared by every Claude Code session on the machine, and whose `ctx_fetch_and_index`
fetches a URL into that store. Four of the five brief authors used these tools to index and search the sources they
fetched (their own `source` labels). The B-3 author made one search without a `source` filter and reported it. The
designer read that search's result in the B-3 transcript: it returned the designer's own Europe PMC search for CUR13
(2026-11-13, made when the addendum was written) and a 2026-11-12 batch with public bibliographic search results for
MAK19, ARC81 and a Bland–Altman paper (Phase B source verification). No Phase B brief, note, skeleton, case or result
was in it. The author says it used only its own fetches afterwards. Recorded as an honour-system event; no brief is
changed or rejected for it.

**Why it matters later.** The store now also holds the brief authors' fetched source texts, labelled by source key
(for example `ARC81-epmc`, `LAZ10-epmc`). A world author who searched it could learn a source or an error.

**Decision (before any Fable agent of Phase C starts).**

1. The task prompt of every Fable agent of Phase C carries, in addition to the frozen
   `WORLD_INSTRUCTIONS_PHASE_C.md`, this sentence, identical for all: "The context-mode tools (`ctx_search`,
   `ctx_batch_execute`, `ctx_fetch_and_index`, `ctx_index`) read a store shared by every session on this machine or
   fetch from the internet; using them counts as reading outside your sandbox. Do not call them." It applies the frozen
   rule "Do not read anything else on this machine and do not fetch anything from the internet"; the exact prompt is
   copied into `WORLD_RUN.md`.
2. A Fable batch (or any Fable agent of Phase C) whose transcript records a call of one of these four tools is treated
   as an **invalid batch** under §4 item 3 (skeletons deleted unread, one redo by a fresh Fable agent; a second invalid
   run stops Phase C until a revision decides). The tool list per batch, already required in `WORLD_RUN.md`, shows it.
3. The criterion authors of part 2 and the fidelity auditors, who read sources online, get the same sentence with one
   exception: `ctx_search` with a `source` filter that names a label the agent itself indexed in its own run is allowed
   (the same use the brief authors made). The designer lists every such call per agent from the transcripts and reports
   any unfiltered search.
4. The designer does not purge the store (it belongs to the user and holds other projects' material).

## P-2 (2026-11-15, after batches 01–02 of the second world-author attempt, before batches 03–04): the session scratchpad and harness-injected context

**Events.**

1. The harness tells every agent of the session, in its system prompt, to use the session scratchpad folder for
   temporary files. Batch01 wrote one check script of its own there (`chk.py`, by Bash) and batch02 one (`check_b02.py`,
   by Write); each ran its script from there. Running one's own file outside the sandbox breaks the letter of the
   sandbox rule ("Do not read anything else on this machine") but is not an invalid-batch criterion (§4 item 3: another
   model, an agent-starting tool, a linked transcript; P-1: the four context-mode tools). Neither transcript lists or
   reads any other scratchpad file (designer, `designer/transcript_check.py` plus reading every Bash command). Recorded
   as honour-system events, like the B-1 author's scratchpad writes in step 2.
2. At that time the scratchpad also held designer working files (0.5.0 and R1 work) and the plain-text source files that
   the B-1 brief author had written there in step 2 (three of its sources). A world author who listed the folder could
   have learnt source keys.
3. The harness also injects the user's `CLAUDE.md` files and the auto-memory index into every agent's context. The
   designer scanned the injected context of both transcripts (attachments, request prefix, first user message) for the
   22 source keys, the class labels, error names and designer file names: no hit. The index says only that Truth_Gate
   Phase C is under way with Fable batches. The memory files themselves (which hold Phase C details) were read by
   neither batch.

**Decision (before batches 03–04).**

1. The designer moved every file out of the session scratchpad into the private workspace
   (`designer/scratchpad_archive_2026-11-15/`, 43 items), leaving only files unrelated to Truth_Gate (text extracts of the
   author's literature folder). The two batch scripts are kept as records in `fable/transcripts/attempt2/`
   (`batch01_scratchpad_chk.py` SHA-256 e1bd6a9c…, `batch02_scratchpad_check_b02.py` b6017fc1…); they are given to no
   later agent.
2. The task prompt stays identical for all batches (`WORLD_RUN.md`); no sentence is added.
3. For the rest of Phase C the designer keeps Phase C working files in the private workspace, not in the session
   scratchpad, and keeps the memory index free of class, source and error information. Every later transcript is read
   for outside-sandbox reads and writes.

## P-3 (2026-11-15, after the first check-script run on batches 01–02, before any skeleton is returned): `sizes` given as an object

**Event.** The frozen `tools/check_skeletons.py` builds a text from each brief with `brief["sizes"] + " " + ...` (to
check that every array dimension appears in the brief text). 18 of the 54 accepted briefs give `sizes` as a JSON object
(for example `{"subjects": 12, "runs": 8, "voxels": 300}`), the others as a string. Neither the pre-registration (§2:
"The `sizes` field states every array dimension as a number") nor `AUTHOR_PHASE1_C.md` fixes the type, and the frozen
`term_check.py` reads the field with `str()`. On the first run every skeleton of an object-`sizes` brief failed with
"load/construct error: TypeError: unsupported operand type(s) for +: 'dict' and 'str'" (batch01: C05, C06, C11, C14;
batch02: C18, C19, C20, C28, C29), and no object-`sizes` brief passed. The error lies in the tool's handling of the brief,
not in any skeleton.

**Decision (Claude under the author's delegation).** The check script is not changed. It is given, as `--briefs`, a copy
of the batch file in which every non-string `sizes` is replaced by its JSON text (`json.dumps(sizes, ensure_ascii=False)`;
same names and numbers), written by `designer/sizes_as_text.py`; string `sizes` are copied unchanged. The world authors
keep the original batch files. The first reports (`fable/batch01_check_attempt2.json`, `fable/batch02_check_attempt2.json`)
are kept as records; no skeleton is returned for this error, and the run with the copied briefs is the check of §4 item 4.
The same copy is used for every later check-script run (batches 03–04, redos, regenerations) and for any other frozen tool
that reads `sizes` as text. Step 2 accepted object `sizes` (its script reads the field with `str()`); that gap is noted
here.

## P-4 (2026-11-15, after batches 03–04 of the second attempt stopped, before the awareness readings): skeletons without a world log

**Event.** Batches 03 and 04 (second attempt) stopped on the account's 5-hour usage limit. Batch04 wrote nothing; its 9
ids went to a new fresh Fable agent with the same prompt and batch file (§4 item 3, "Stops"). Batch03 had written all 15
skeletons (C31–C45), which all pass the check script (P-3 briefs copy), but stopped before writing `WORLD_LOG.md`. By §4
item 3 only ids without a passing skeleton go to a new agent, so C31–C45 stay; their world log entries do not exist. The
world log is read only for the awareness classification (§4 item 4; `AWARENESS_RULE_C.md`), which is descriptive (§6
"Awareness breakdown").

**Decision (Claude under the author's delegation).** For an id whose skeleton passes but has no world log entry, both
readers record "no log", and the resolved reading counts it as **P**: the rule's generous reading chooses the higher level
in doubt so that the N group is as free of awareness as the log allows, and with no text every level is in doubt. The
awareness breakdown reports "no log" as its own count beside P, C and N, the P share of every class includes it (so the
wording "declared worlds that may contain what the error exploits" covers it), and the log length is reported as 0.
Rejected: (i) a fresh Fable agent writing log entries for skeletons it did not write (the rule reads the world author's
own account); (ii) redoing passing skeletons (§4 item 3 sends only ids without a passing skeleton to a new agent).

## P-5 (2026-11-15, after the skeleton freeze, before any criterion author starts): the context-mode exception for part 2, and the scratchpad

**Reading of P-1 item 3.** P-1 item 3 gives the part-2 criterion authors and the fidelity auditors "the same sentence
with one exception": `ctx_search` with a `source` filter naming a label the agent itself indexed in its own run. Taken
literally, the same sentence also forbids `ctx_fetch_and_index`, so no label could ever be the agent's own and the
exception would be empty. P-1 states its purpose: "the same use the brief authors made" (fetch a source into the store
under one's own label, then search only that label). Decision (Claude under the author's delegation): for these agents
`ctx_fetch_and_index` of an online source (URL logged like any other) is allowed, and `ctx_search` only with a `source`
filter naming a label the agent indexed in its own run; `ctx_search` without such a filter, `ctx_batch_execute` and
`ctx_index` are not allowed. The designer lists every context-mode call per transcript and reports any other use.

**Scratchpad (P-2).** The frozen `AUTHOR_PHASE2_C.md` already says "Write only inside your class folder" with scratch
scripts in `work\`. Because the harness suggests the session scratchpad to every agent, the task prompt says so once more.

**Task prompt of every part-2 criterion author** (identical except the class and folder; copied into
`designer/PART2_RUN.md`):

> You are the criterion author of class CLASS in a pre-registered evaluation. Your sandbox folder is
> `E:\Claude Projects\Kapi\phase_c_private\authors\FOLDER\`; it is also your class folder. Read `AUTHOR_PHASE2_C.md` there
> first and follow it exactly. The context-mode tools read a store shared by every session on this machine. You may use
> `ctx_fetch_and_index` to fetch an online source (log the URL), and `ctx_search` only with a `source` filter that names a
> label you indexed yourself in this run; do not call `ctx_search` without such a filter, and do not call
> `ctx_batch_execute` or `ctx_index`. The harness may suggest a session scratchpad folder; do not use it: scratch scripts go
> in `work\` inside your class folder. Final message as the instruction file says.

## P-6 (2026-11-15, after the fidelity audit and the repair round, before the case freeze): audit stops, post-repair audit, published record

1. **Audit stops.** All five auditors stopped on the account's 5-hour usage limit. The fresh-agent rule for stops (§4 item 3)
   concerns the Fable world authors; the auditors, like the brief authors of step 1, were resumed by a message with no new
   information. Logged in `record/designer/AUDIT_RUN.md`.
2. **Repair round and post-repair audit (PB §5.3).** Four pairs had a defect in the criterion bodies (B1-09 item (b); B2-01,
   B2-06, B2-10 item (c)); the same criterion authors repaired them on the auditors' verbatim requests, the mechanical check
   passed again, and the same auditors audited the repaired pairs only, on all nine items: all four pass. Two pairs had a
   defect in the brief or its sizes (B3-07 item (f), B3-10 item (h)) and are dropped. No pair was disputed. The B-2 author
   asked whether to change the same guard expression in six pairs that had passed (both twins behave alike there); decision
   (Claude under the author's delegation): no, a passed pair is not changed. Result: 52 pairs (B-1 12, B-2 12, B-3 10, B-6
   12, O 6); every in-scope class has at least 10 pairs, at least 3 independent read sources and at least 4 addendum-source
   pairs, and the B-2 subtype minima hold. The designer read every brief at step 2 for the brief half of (h) and did not
   flag B3-10's column-order sentence; the audit caught it.
3. **Designer lines.** After the audit the designer appended to every surviving `CASE.md` the lines of §3 (overlap, tag and
   family, allowed-guard minimum, size ratio) from the step-2 report, the private notes and the notes' source sizes
   (`record/designer/DESIGNER_LINES.json`).
4. **Published record.** The pre-run record mirrors the private workspace with these exclusions: every agent transcript
   (`*.jsonl`, `.meta.json`, `.prefix.json`), because the harness injects the user's own instruction files and memory index
   into every agent's context; their SHA-256 values stay in `WORLD_RUN.md`, `PART2_RUN.md`, `AUDIT_RUN.md`,
   `AWARENESS_RUN.md` and `FREEZE_SKELETONS.json` (so that manifest cannot be fully re-verified from the published files);
   source texts and extracts; the package copies; the designer's archive of the session scratchpad; and the read-only copies
   in the audit and reader sandboxes. The designer's scan of the published files for personal data is logged in
   `record/designer/PUBLISH_SCAN.txt`.
