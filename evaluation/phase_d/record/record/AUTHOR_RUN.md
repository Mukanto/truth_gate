# Author runs (REVISIONS-post-freeze.md P-1, amendment 5)

Every brief author ran on the Sonnet line (at least one assistant message; every assistant message `claude-sonnet-…`; `<synthetic>` entries are harness error messages from the usage-limit stops). Checked with `designer/author_run_check.py`. Transcripts are kept private; their SHA-256 are listed.

| Role | Author | Agent id | Assistant-message models | Agent-starting or ctx_* calls | Paths outside the sandbox | URLs fetched | First / last (UTC) | Transcript SHA-256 (first 16) | Valid |
|---|---|---|---|---|---|---|---|---|---|
| brief author | B2A | a4a4a89eebcfe6026 | claude-sonnet-5-5 ×40 | 0 | 0 | 3 | 2026-11-17T19:50 / 2026-11-17T19:59 | 543e51475606edf9 | yes |
| brief author | B2B | af560fa650007dcf8 | claude-sonnet-5-5 ×50 | 0 | 0 | 11 | 2026-11-17T19:50 / 2026-11-17T19:58 | d99217874a65961a | yes |
| brief author | B3A | a66194589676ba09b | claude-sonnet-5-5 ×44, <synthetic> ×1 | 0 | 0 | 8 | 2026-11-17T19:50 / 2026-11-18T00:10 | 92ccec184c221e78 | yes |
| brief author | B3B | a2122ad113d9cffa9 | claude-sonnet-5-5 ×45 | 0 | 0 | 6 | 2026-11-17T19:50 / 2026-11-17T19:59 | 2a9c00a135be07c8 | yes |
| brief author | DEC | a125dd54bda6411e1 | claude-sonnet-5-5 ×73, <synthetic> ×1 | 0 | 0 | 33 | 2026-11-17T19:50 / 2026-11-18T00:09 | 979abafaeb49f31a | yes |

B3A and DEC stopped once on the account's usage limit and were resumed with one designer message each ("continue from where you stopped", no content); the rule of P-1 amendment 1 on designer messages applies to world authors only.

## Criterion authors (PREREG_PHASE_D section 3 item 4)

Same check (`designer/author_run_check.py`); inputs checked against `MANIFEST_criterion.json` with `designer/manifest_check.py` (no input changed or missing; `half\LOG.md` changed only by appending: the build-time file is a byte prefix of the final one).

| Role | Author | Agent id | Assistant-message models | Agent-starting or ctx_* calls | Paths outside the sandbox | URLs fetched | First / last (UTC) | Transcript SHA-256 (first 16) | Valid |
|---|---|---|---|---|---|---|---|---|---|
| criterion author | B2A | af71d71744b42e486 | claude-sonnet-5-5 ×50 | 0 | 0 | 0 | 2026-11-18T00:18 / 2026-11-18T00:27 | 551658bcfd1abdd2 | yes |
| criterion author | B2B | a7d3292312140f1a8 | claude-sonnet-5-5 ×49, <synthetic> ×1 | 0 | 0 | 0 | 2026-11-18T00:18 / 2026-11-18T05:03 | 797509a02cdd0c0e | yes |
| criterion author | B3A | a987caff7ebb6ec1f | claude-sonnet-5-5 ×67 | 0 | 0 | 0 | 2026-11-18T00:19 / 2026-11-18T00:27 | 79e5b2b4a885a568 | yes |
| criterion author | B3B | a32bf8196f7e404ae | claude-sonnet-5-5 ×36 | 0 | 0 | 0 | 2026-11-18T00:19 / 2026-11-18T00:26 | d81fd7ade472a1ac | yes |
| criterion author | DEC | abc58c474656d8fe0 | claude-sonnet-5-5 ×40 | 0 | 0 | 0 | 2026-11-18T00:19 / 2026-11-18T00:26 | 857d3bf78bec34d8 | yes |

B2A reported that the harness saved one large Bash output (its own sandbox's `PRIVATE.json`) to a tool-results file outside the sandbox; no tool input of the agent names that file (outside paths 0), and the agent says it did not open it. B2B stopped once on the account's usage limit and was resumed with the content-free message "Continue from where you stopped."

## Structure authors (PREREG_PHASE_D section 3 item 5)

Same check; inputs checked against `MANIFEST_structure.json` (no input changed or missing). All five stopped once on the account's usage limit and were resumed with the content-free message "Continue from where you stopped."; B2A was resumed once more for the return of D-014 and D-041 (§2.4 row "reference.py rejected by check_skeletons_d.py"; the message quoted only the script's issue list).

| Role | Author | Agent id | Assistant-message models | Agent-starting or ctx_* calls | Paths outside the sandbox | URLs fetched | First / last (UTC) | Transcript SHA-256 (first 16) | Valid |
|---|---|---|---|---|---|---|---|---|---|
| structure author | B2A | a11199196e334e5e0 | claude-sonnet-5-5 ×51, <synthetic> ×1 | 0 | 0 | 0 | 2026-11-18T00:21 / 2026-11-18T05:05 | 43872b34ba418f35 | yes |
| structure author | B2B | aa1f289e148303b66 | claude-sonnet-5-5 ×41, <synthetic> ×1 | 0 | 0 | 0 | 2026-11-18T00:21 / 2026-11-18T05:05 | 61501faf9ebec512 | yes |
| structure author | B3A | ae7959dba03f3368a | claude-sonnet-5-5 ×51, <synthetic> ×1 | 0 | 0 | 1 | 2026-11-18T00:21 / 2026-11-18T05:04 | 5cfadea33062a535 | yes |
| structure author | B3B | a1a5e977f194b55b8 | claude-sonnet-5-5 ×77, <synthetic> ×1 | 0 | 0 | 0 | 2026-11-18T00:21 / 2026-11-18T05:07 | 5a1c1f26ebfb31d2 | yes |
| structure author | DEC | a16327a1facfa3522 | claude-sonnet-5-5 ×57, <synthetic> ×1 | 0 | 0 | 0 | 2026-11-18T00:21 / 2026-11-18T05:05 | 0148257285eb7279 | yes |

The B2A row covers the transcript before the return; the return's transcript is checked with the same script below. B3A's one URL is a source page (PMC3854983), allowed by `STRUCTURE_AUTHOR_D.md`; its one ToolSearch loaded WebFetch/WebSearch. B3B reported a command that hung on an interactive prompt and went to the background; no Python process of it was running when checked.
| structure author (after the return) | B2A | a11199196e334e5e0 | claude-sonnet-5-5 ×54, <synthetic> ×1 | 0 | 0 | 0 | 2026-11-18T00:21 / 2026-11-18T05:09 | b126cd22a238ba2e | yes |
