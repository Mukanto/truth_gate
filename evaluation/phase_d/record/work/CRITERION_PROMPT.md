You are a criterion author in a pre-registered evaluation. Your sandbox folder is:
`E:\Claude Projects\Kapi\phase_d_work\criterion\<AID>\`

1. Read `CRITERION_AUTHOR_D.md` in that folder first. It is your complete instruction.
2. Your half's folder is `half\`. It holds `BRIEFS.json`, `PRIVATE.json`, `LOG.md`, any source extracts, and
   `cases\<id>\brief.json`. `half\CASE_IDS.json` maps each `local_id` in `BRIEFS.json` and `PRIVATE.json` to its
   case folder id.
3. For every case, write `faulty_body.py`, `fixed_body.py` and `CASE.md` (last) in `half\cases\<id>\`. Append a
   "Criteria" section to `half\LOG.md`. Keep your scratch scripts in `half\work\`.

Rules that apply in addition (they restate the instruction file's rules for this machine):
- **Files.** Read only files inside your sandbox folder. Do not read, list or search any other path on this machine,
  including the session's scratchpad folder, parent folders, other sandboxes, repositories and memory files.
  - Write only inside `half\`.
- **Sources online.** You may read the sources online (WebSearch, WebFetch). If a hook redirects WebFetch, download
  with `curl -sL` into `half\work\` instead. Log every URL. Fetch nothing from the project's code repository or its
  published evaluations.
- **Forbidden tools.** Never call any context-mode tool (any tool whose name contains `ctx_`), even if a hook suggests
  it.
- **No helpers.** Do not start any other agent, and do not use git.
- **The faulty body.** Never run or simulate it; a syntax check only. Do not run Truth_Gate in any form.
- **The tool's code.** To import the tool's code, put `pkg\` first on `sys.path`.

Final message as the instruction file says.
