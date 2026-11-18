You are a blind fidelity auditor in a pre-registered evaluation. Your sandbox folder is:
`E:\Claude Projects\Kapi\phase_d_work\audit_a0\<G>\`

1. Read `FIDELITY_AUDIT_D.md` in that folder. It is your instruction.
2. Your task is **Part A0** for every case in `class\` (each case folder holds `brief.json`, `PRIVATE.json` and
   `PASSAGE.md`). Answer item (l) for each case as the instruction file says. A decoy whose structure statistic is null
   gets "(l): n/a".
3. Write `AUDIT_A0.json` (a list of `{"case", "l", "reason", "approved_value"}`) and `AUDIT_A0.md` in your sandbox
   folder.
   - `approved_value` is the note's `note_value` when (l) is "yes", and null otherwise.
   - List every URL you read in `AUDIT_A0.md`.

Rules:
- Read only files inside your sandbox folder. Do not read, list or search any other path on this machine.
- You may read the sources online (WebSearch, WebFetch). If a hook redirects WebFetch, download with `curl -sL` into
  your sandbox instead.
- Fetch nothing from the project's code repository or its published evaluations.
- Never call any context-mode tool (any tool whose name contains `ctx_`).
- Do not start any other agent, do not use git, and do not run Truth_Gate.
- Write scratch files only inside your sandbox folder.

Final message: the counts of yes, no and n/a, and the cases with "no", each with one line of reason.
