# Phase C fidelity audits (PREREG_PHASE_C §5; AUDIT_PHASE_C.md; REVISIONS-post-freeze P-1, P-5)

Mechanical check first: `tools/mech_check_twins.py` per class with the 54 frozen skeletons collected (hash-checked) in
`designer/skeletons_all/`; reports `designer/mech/MECH_CHECK_<F>.json` (B-1, B-3, B-6, O: all cases pass; B-2 after its
author finishes). Sandboxes by `designer/audit_build.py`: `audit/<F>/` with read-only copies of what AUDIT_PHASE_C.md
lists, the class folder as `class\`, the audit folder `out\` and `scratch\` for helper computations. Auditors: one fresh
agent per class (Claude, Opus line), blind to the gate (no gate result exists).

## Task prompt (identical except CLASS and FOLDER)

> You are the blind fidelity auditor of class CLASS in a pre-registered evaluation. Your sandbox folder is
> `E:\Claude Projects\Kapi\phase_c_private\audit\FOLDER\`; your class folder is `class\` inside it and your audit folder
> (for `AUDIT.json` and `AUDIT.md`) is `out\` inside it. Read `AUDIT_PHASE_C.md` there first and follow it exactly. The
> context-mode tools read a store shared by every session on this machine. You may use `ctx_fetch_and_index` to fetch an
> online source (log the URL), and `ctx_search` only with a `source` filter that names a label you indexed yourself in this
> run; do not call `ctx_search` without such a filter, and do not call `ctx_batch_execute` or `ctx_index`. The harness may
> suggest a session scratchpad folder; do not use it: a helper script, if you need one, goes in `scratch\` inside your
> sandbox folder. Final message as the instruction file says.

## Runs

(filled in by the designer per auditor: agent id, models, tools, context-mode calls, outside paths, transcript SHA-256)

**Stop and resume.** All five auditors stopped on the account's 5-hour usage limit (2026-11-15, about 06:10 UTC); O and B-3 had written `AUDIT.json` but not `AUDIT.md`, the others nothing. After the reset each was resumed by a message with no new information ("interrupted by an account usage limit; continue from where you stopped; nothing in your sandbox has changed; follow AUDIT_PHASE_C.md"), two or three at a time. The prereg's fresh-agent rule for stops applies to the Fable world authors only; the brief authors of step 1 were resumed the same way.

| Class | Agent id | Model | Assistant-message models (entries) | Context-mode calls | Outside-sandbox paths | Transcript SHA-256 (first 16) | Result |
|---|---|---|---|---|---|---|---|
| O | a9bc0c0445193b39f | opus | claude-opus-5-5 ×63, <synthetic> ×1 | fetch 1 (own labels), search 1 (all filtered to own labels: yes), ctx_execute 5 | none | be57fbf33062dc2d | 6/6 pass; fail: none |
| B-3 | aed25618ad66102ab | opus | claude-opus-5-5 ×62, <synthetic> ×1 | fetch 1 (own labels), search 3 (all filtered to own labels: yes), ctx_execute 2 | none | 5839615fe688b8ed | 10/12 pass; fail: B3-07, B3-10 |
| B-6 | afdcdd978c5d1980e | opus | claude-opus-5-5 ×88, <synthetic> ×1 | fetch 2 (own labels), search 5 (all filtered to own labels: yes) | none | f0442f41a1f1c787 | 12/12 pass; fail: none |

`ctx_execute` (O 5, B-3 2) fetched the logged URLs as text or ran checks on sandbox files; P-5 does not forbid it and it reads nothing from the shared store. `<synthetic>` ×1 in each is the usage-limit error message. Transcripts in `designer/audit_transcripts/`.

| B-1 | ad07ebced9460ae72 | opus | claude-opus-5-5 ×89, <synthetic> ×1 | fetch 6 (own labels), search 3 (all filtered to own labels: yes) | none | 965b791a644b7e02 | 11/12 pass; fail: B1-09 |
| B-2 | a693a1ac7914ecc63 | opus | claude-opus-5-5 ×87, <synthetic> ×1 | fetch 1 (own labels), search 8 (6 filtered to one own label; 2 filtered to `zq7auditB2x`, the common prefix of its own three labels: results came only from those labels, see below) | none | e01f68cf83a0f032 | 9/12 pass; fail: B2-01, B2-06, B2-10 |

B-2 auditor: two `ctx_search` calls used `zq7auditB2x`, the common prefix of its own labels (`zq7auditB2x-amb02`, `-kap23`,
`-var06`), as the source filter. The designer read the results (`designer/ctx_search_results.py`): every chunk came from
those three labels; nothing else in the shared store was returned. The letter of P-5 (a filter naming one label) is not
met; its purpose (no other agent's content read) is. Recorded; no consequence.

## Audit result before the repair round

| Class | Pairs | Pass | Fail (item) | Defect in |
|---|---|---|---|---|
| B-1 | 12 | 11 | B1-09 (b) | fixed body: selection and test on two sessions of the same 16 participants is not independent at the group level |
| B-2 | 12 | 9 | B2-01, B2-06, B2-10 (c) | fixed guards: `-(n) // k` parses as `(-n) // k`, so the fixed guard differs from the faulty one |
| B-3 | 12 | 10 | B3-07 (f), B3-10 (h) | brief/sizes (B3-07: the source states sizes, brief far smaller; B3-10: brief states the column order); not repairable in the bodies, dropped after the repair round (PB §5.3) |
| B-6 | 12 | 12 | — | — |
| O | 6 | 6 | — | — |

## Repair round (2026-11-15)

PB §5.3: a "no" goes back to the criterion author once (criterion bodies only); a "no" after the repair, or a dispute, is a
drop. The four body defects went to the same criterion authors (B-1 a602619fe2d711567, B-2 a9cf679166b180a9c), resumed
with a message quoting the auditor's `repair_request` verbatim, "repair only that pair, criterion bodies only, under the
same rules; do not change any other case; update CASE.md (Repair paragraph) and LOG.md; if you disagree change no file and
say why (a disputed pair is dropped)". After the repair: the mechanical check again, then the same auditor audits the
repaired pairs only (as in Phase B, where the post-repair audit answered the items again).

**Repairs made (2026-11-15).** Designer checked by byte comparison with the audited copies that only the repaired pairs
changed, and reran the mechanical check (B-1 and B-2: all cases pass; `designer/mech/MECH_CHECK_<F>_repair.json`).
* B1-09: `fixed.py` body (voxels chosen on participants 0–7, correlation measured on participants 8–15, sessions averaged;
  threshold and guards kept) and CASE.md; `faulty.py` unchanged. New fixed pre-check: plus 193/200, minus 6/200.
* B2-01, B2-10: the fixed guard now computes n − ceil(n/k); faulty unchanged. B2-06: both bodies use the same patient-level
  guard, as the request said. CASE.md "Repair" paragraphs; LOG.md "Repair round".
* The B-2 author asked whether to repair the same expression in six passing pairs (B2-02, 03, 08, 09, 11, 12), where both
  twins' guards behave alike and the guard is an allowed one. Designer (Claude under the author's delegation): no. PB §5.3
  repairs pairs with a "no" only; the six passed the audit, and changing them would void their audit.

**Post-repair audit.** The audit sandboxes received the repaired files (previous versions in `class\cases\<id>\prerepair\`),
the new LOG.md and the new MECH_CHECK.json; the same auditors were resumed to audit the repaired pairs only, on all nine
items, writing `out\AUDIT_REPAIR.json` and `.md` (the first-round files unchanged).
