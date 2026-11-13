# Blind review 2 of `PREREG_PHASE_C.md` (draft v2)

Reviewer read: v2, `REVIEW1.md`, `REVISIONS.md`, the five instruction files, `P2_READING.md`, `tools/check_skeletons.py`,
`PHASE_B_TABLE.json`, spec 0.7 section 6 R3, PB, the Phase B instruction files in `evaluation/phase_b/record/` (diffed
line by line against the Phase C files), `truth_gate/study.py` (dataclass fields only, to check the script's attribute
use) and the docs that will feed the agent document set (grep only). Nothing was run except a read-only listing of
`PHASE_B_TABLE.json`; the script was read, not executed. Severity: **blocking** = do not freeze with this text;
**major** = fix before freeze; **minor** = clarity or cheap hardening.

Counts: blocking 1, major 9, minor 10 (20 findings).

## 1. Status of review 1

| Review 1 | Status in v2 |
|---|---|
| 1 docs carry Phase B results (blocking) | Resolved in design (agent document set from the tag, scan, freeze). The set does not exist yet, so the scan cannot be judged; the term list has gaps (finding 17). |
| 2 Fable identification (blocking) | Resolved (transcript model ids, pre-flight, invalid batch, wait without limit). Residual: a batch agent that starts sub-agents, and no freeze of the evidence (finding 7). |
| 3 invalid skeletons (blocking) | Resolved (frozen script, one redo, drop). Residual: script/instruction mismatches that cause drops (findings 9, 12-14). |
| 4 "does not know" (blocking) | Resolved (section 0, 6, I-8). |
| 5 brief steering (blocking) | **Not resolved as a rule with one reading**: the new text contradicts the encoding rule and the prereg and audit versions of item (h) differ (finding 1). |
| 6 overlap (major) | Partly: a written key now exists, but it is too coarse to be applied with one reading and will almost always exceed one half (finding 3). |
| 7 primary comparison (major) | Resolved, with a wording point against R3 (finding 10) and a note that "not informative" is the likely outcome (finding 19). |
| 8 guard rule (major) | Resolved (exhaustive list, minimum in the note, audit (d), abstention shares). |
| 9 size caps (major) | Partly: caps raised and ratio reported, but no remedy when the timing rule is not met after the skeleton freeze, and P-2 reading 1 still lets small sizes pass when the source states none (findings 5, 11). |
| 10 B-3 estimand (major) | Partly: rule and item (i) exist; feasibility of B-3 under the other new rules is not shown, and B-3 has no slack (finding 4). |
| 11 prompts pinned (major) | Partly: files exist and are frozen, but the difference tables are not complete (finding 8). |
| 12 contamination (major) | Mostly: sandboxes, URL logs, designer limits. Open: how the package is provided, and the "used passages" list (findings 2, 6). |
| 13 awareness (major) | Resolved (second reader, rule copied, verified identical to Phase B `AWARENESS.md`). Minor: which reading is quoted (finding 18). |
| 14 continuity (major) | Resolved (batches, fresh agents). Minor: cut points, stop versus redo (finding 15). |
| 15-21 (minor) | Resolved. 16 ("read") is fine; 19 and 20 are fine except the freeze list (finding 16). |

## Blocking

**1. "Setting only" has two readings and the two statements of item (h) differ.** Passages: section 2 ("Briefs state only
the setting ... They do not state frequencies, overlaps, repetitions, selections, orderings, shared quantities or
dependencies between rows, units, splits or variables, unless the claim itself is about them"); section 5 (h);
`AUDIT_PHASE_C.md` (h); `AUTHOR_PHASE1_C.md` "Setting only".
Reason: (a) Every brief must give `data_keys` with shapes whose axes carry group, subject, trial and time structure
(`WORLD_INSTRUCTIONS_PHASE_C.md` rule 1, PB §2). A shape `(subjects, trials, features)` states a repetition and a
dependency between rows; `(days, features)` "in time order" states an ordering. Read literally, the "orderings" and
"repetitions" ban forbids what the encoding rule requires, and it hits exactly L3.1, L3.2 and B-6 (dependent units) and
the hierarchical B-1 briefs. Read as "axes named in the shape are setting", the ban is narrower but the text does not say
so. The designer rejects briefs for "a violation of section 2" and the auditor answers (h) per pair, so two readings
mean two sets of dropped pairs, decided after seeing the briefs. (b) The prereg's (h) says "no structural fact whose role
is to be what the error exploits" (a purpose test, needs the private note); section 2 and the audit file's (h) state a
list-based test with the "unless the claim is about them" exemption, which the prereg's (h) does not carry. The exemption
also lets a claim that names the shared quantity (B-3: "after allowing for body mass") or the selection ("units selected
by ...") pass whatever the brief then says. (c) Review 1's wording "whose only role" became "whose role" without a
reason.
Fix: one text, used verbatim in section 2, section 5 (h), `AUTHOR_PHASE1_C.md` and `AUDIT_PHASE_C.md`: "A brief may state
(i) the sizes, (ii) the axes named in the shape of each key and what each key measured, (iii) what the claim itself
states. It may not state any other fact about how rows, units, splits, repetitions or variables are related, ordered,
duplicated, shared or selected. An axis named in a shape (subjects, trials, time) is setting; a statement about how the
data on that axis are arranged beyond its name is not. Naming a quantity in the claim is allowed only where the claim's
estimand requires it (the estimand line of the private note says which)." Add two worked examples per class to
`AUTHOR_PHASE1_C.md` (one passing, one failing) so the authors and the designer apply the same reading, and state in
section 5 that (h) is answered by this text, not by a purpose test.

## Major

**2. The "new passage" rule is undefined, has no consequence, and its input contradicts the sandbox.** Passages: section 1
"New material"; section 4 items 1-2; `AUTHOR_PHASE1_C.md` ("the designer marks as new (your task lists the passages already
used; choose others)").
Reason: (a) "Passage" has no granularity: `PHASE_B_TABLE.json` stores a quote truncated at 400 characters (for example
B1-01 ends "Fig. 4 policy). E") and often only a section ("KRI09, Introduction"); three KRI09 pairs share one section, so
"a new passage" could mean a new section, paragraph, table or figure. (b) The authors are told, in their task, which
passages Phase B used. That is Phase B record content that R3 says authors do not read, it is not in the sandbox list of
section 4 item 1, and it also pushes authors away from Phase B and so lowers overlap. The prereg must say it or the
instruction must not do it. (c) If an author delivers fewer than 4 new-passage pairs, nothing follows: the designer's
rejection reasons (section 4 item 2) do not include it and sources cannot be added after the briefs. (d) The count is on
"planned" pairs, not surviving pairs. (e) A pair on a new passage can still overlap (same source, mechanism, statistic),
so the two notions are not nested.
Fix: define a passage as the smallest numbered section, table or figure of the source that the private note cites; store
that location (not a truncated quote) in the table; either give authors the list of used locations and say so in section
4 item 1 (and in R3's reading) or give them nothing and let the designer count after the briefs; make "fewer than 4 new
passages" a reason for one return of the whole set to the author, and, failing that, "new-material minimum not met" in
the report with the class still tested; count on surviving pairs in the report.

**3. The overlap key is not applicable with one reading and will almost always exceed one half.** Passage: section 1
"Overlap key".
Reason: the key is source key AND mechanism AND "a statistic of the same name in the claim". In the frozen table,
`statistic_terms` is a keyword list with generic entries: "mean" appears in 16 of 54 rows and is the only term of 8 of
the 12 B-1 and 6 of the 12 B-6 rows; 5 rows have no term. "Same name" does not say whether "t test", "Welch" and "mean
difference" are the same. "Mechanism" is free text in the table, so "the same faulty procedure in the private notes"
is a judgement by the designer who read all of Phase B. All B-1 pairs of one source share the mechanism (selection and
test on the same data), and all B-3 pairs of one source share it (shared component), so with "mean" or "correlation" in
the claim almost every Phase C pair on a reused source overlaps. B-3 has three sources, each supplied exactly 4 pairs in
Phase B, with the statistics Pearson, Spearman, slope, R squared: a Phase C PEA97 or ARC81 or KRO93 pair using any of
these overlaps. The "more than half" wording then applies to B-1, B-3 and probably B-6 by construction, and "may not
present the results as separate evidence" removes the point of Phase C for those classes. Also unstated: the denominator
(pairs in the table after drops?) and whether "more than half" of 12 means 7.
Fix: add to the frozen table a closed `mechanism_tag` (for B-2 the subtype; for others a short vocabulary fixed now, for
example `select-same-data`, `select-top-k-same-data`, `split-by-baseline`, `ratio-shared-denominator`,
`change-vs-baseline`, `cell-as-unit`, `significant-here-not-there`) and a `statistic_family` from a closed list (t/mean
difference, correlation, regression slope, R squared, accuracy/AUC/F1, other); overlap = same source AND same tag AND
same family; state that the key is applied mechanically from the Phase C private note's own tag and family. State the
denominator (pairs entering the class table) and "more than half" as "strictly more than the integer half, rounded up".
Say now, in section 8, that for B-1 and B-3 an overlap above one half is expected, and add at least one new source per class
in `SOURCES_ADDENDUM.md` before the briefs (the designer is free to do so, section 1) so that the rule is not decided by
the source list.

**4. B-3 cannot absorb a single bad outcome, and its feasibility under the new rules is not shown.** Passages: section 1
(cap 4 per source; B-3 sources); section 4 Size ("12 planned, at least 10 after drops"); section 2 "Estimand".
Reason: B-3 has three sources and the cap is 4 per source, so 12 is the maximum; there is no oversampling. Drops can now
arise from the term check, a section 2 violation, the Fable skeleton check, audit items (a)-(i) including the new
(h) and (i), the timing estimate and a timeout. Two drops are tolerated, three make B-3 "insufficient cases". A source
whose pairs are all dropped also breaks "at least 3 independent read sources" (ARC81 and KRO93 were abstract-only in
Phase B). Review 1 suggested 14 planned pairs; v2 chose 12 without saying why oversampling is unavailable. Separately, the
estimand rule asks for a B-3 claim about "the relation between the underlying quantities" with the components as keys and
no banned term, while rule (h) forbids stating shared quantities unless the claim is about them. The two are reconcilable
(name the quantity the estimand is conditional on) but no example shows it, and "a brief for which this cannot be done is
not written" can empty the class (change score against baseline needs reliability or repeated baselines in the keys;
target computed from labels needs the labels as keys).
Fix: add a fourth and fifth B-3 source to the addendum before any brief (the designer must name them in the freeze or in
a frozen addendum stub; the review cannot identify them from the files) and plan 14 pairs for B-3 (cap 4 per source
allows 20); or state in section 4 that B-3 is planned at its maximum and that "insufficient cases" is a likely
outcome. Have the designer write, before the freeze, one B-3 brief per mechanism (ratio, change score, shared error,
target from labels) as a feasibility check against sections 2 and 5 and the banned-term script, kept in the record and
not used as cases.

**5. After the skeleton freeze the timing rule has no remedy.** Passages: section 2 "Sizes" ("the timing estimate of PB §2
... binds"); `AUTHOR_PHASE2_C.md` "Timing"; section 4 item 5.
Reason: Phase B's part 2 instruction said "If it is not, make the fixed criterion faster without changing what it
computes"; Phase C's instruction drops that sentence (not in its difference table) and states only the limit. With caps
at 1000 rows and 500 features the limit will bind: S is about 7-9, so 400 × (S+1) × (t+g) ≤ 900 s needs t+g of about
0.25-0.3 s, and cross-validation with feature selection on 1000 × 500 is of that order. The size is fixed in a brief that
the author timed "roughly" before the world existed, and `g` is the world author's code, outside the criterion author's
control (the check script allows up to 100 ms per world call, which alone uses a third of the budget). When the estimate
is exceeded, sizes cannot be changed (skeleton change is granted only if the fixed criterion is impossible to write), and
nothing says what happens: drop, ignore, or an exception.
Fix: restore the sentence on making the criterion faster; add a pre-registered outcome for "estimate above 900 s after
making the criterion as fast as the correction allows": a size request to the designer, granted once, executed by a
fresh Fable agent on that id with the new size (the other keys unchanged), logged; failing that, the pair is dropped as
"timing infeasible" and reported by id. Lower the script's world limit or state in the world instructions that the
limit is 100 ms and the reason (finding 9).

**6. The package that skeletons and criteria import is not specified.** Passages: section 4 items 0, 3, 5;
`WORLD_INSTRUCTIONS_PHASE_C.md` ("You may import the package only to construct the Study object"); `AUTHOR_PHASE2_C.md`
("You may import the package only so that a case file loads"); `check_skeletons.py --package-root REPO_OR_WORKTREE`.
Reason: the sandbox folders hold no package. On this machine `truth_gate` resolves through an editable install of the
repository (`kapi.egg-info` at the root), that is, the working tree at an arbitrary commit with `evaluation/phase_b/`
beside it; tag `v0.5.0` does not exist yet (the repository lists `v0.3.0`, `v0.4.0`, `v0.4.1`). If the agents import from
the working tree they are one directory away from the Phase B record and the source of the gate, which the sandbox is
meant to remove, and the version they test against is not pinned. The same package root is used by the skeleton check.
Fix: in section 4 item 0, build a wheel (or a clean tree without `evaluation/`, `tests/`, `docs/design/`) from tag
`v0.5.0`, install it in a dedicated virtual environment, record its SHA-256 in the freeze, and say that every sandboxed
agent and the check script use that interpreter only; state that the environment contains no repository checkout.

**7. Identification of Fable has two loose ends.** Passage: section 4 item 3 "Identification".
Reason: (a) The instruction file does not forbid starting other agents. A batch agent (tools unrestricted) that delegates
skeletons to a sub-agent runs on the default sub-agent model, which in this project's settings is Sonnet; the batch
transcript would show Fable for its own messages while the skeletons came from another model. The prereg checks "every
assistant message in the batch's transcript", not who wrote the files. (b) The evidence (transcripts, request metadata) is
copied into `WORLD_RUN.md` by the designer; the transcripts themselves are not hashed or frozen, and the pre-flight
recorded on 2026-11-13 predates the freeze and is not in the freeze list.
Fix: add to the world instructions "Do not start any other agent or tool that runs a model"; add to section 4 item 3 that
the designer lists the tool names called in each batch transcript and that any agent-start call, or any other
`agent-<id>.jsonl` linked to the batch, invalidates it; freeze the SHA-256 of each batch transcript with
`FREEZE_SKELETONS.json`; re-run or freeze the pre-flight record.

**8. The difference tables are not complete, and one omission weakens an audit item.** Passages: the last table of each
instruction file; section 4 ("Each lists, as a table, its differences").
Reason (found by diffing against the Phase B files):
* `AUDIT_PHASE_C.md` (d) drops Phase B's "Nothing else inspects whether the input looks like noise, zeros or a shuffle; no
  branch exists whose purpose is to behave differently on the gate's probes", and (g) drops "(same statistic, threshold,
  decision rule and comparable cost)". The table lists only the guard change. Dropping text from an audit item weakens it;
  section 5 says additions strengthen and nothing may weaken.
* `AUTHOR_PHASE1_C.md` drops "Base each case on a setting the source actually describes", "most have open full texts or
  abstracts ...", "Do not read other authors' folders" and shortens "avoid words that describe the faulty procedure itself
  (how items are chosen, how data are split)"; the table lists none of these.
* `AUTHOR_PHASE2_C.md` drops "Write only inside your class folder (scratch scripts in `work\`, kept as record)" and the
  timing remedy (finding 5); neither is in the table. It also says the world author "was not told the notes" where Phase B
  said "never saw those notes, the class or the sources".
* `AUDIT_PHASE_C.md` does not give the auditor `SOURCES.md` (stripped) or the addendum, which Phase B's auditor had.
* `WORLD_INSTRUCTIONS_PHASE_C.md`: the table is accurate for the text, but "identical (rules 1-7)" hides that rule 1's
  sizes and rule 6's "well under 10 ms" now apply to caps 11 times (rows) and 8 times (features) larger, and to the script
  limit of finding 9; say so in the table.
Fix: restore the dropped sentences (or list them as differences with a reason), regenerate each table from a mechanical
diff and paste the diff output into the file; for (g) and (d) copy the Phase B wording.

**9. The check script enforces a limit the world instruction does not state.** Passages: `check_skeletons.py` `MAX_MS =
100.0` (and the issue "world call takes ... ms"); `WORLD_INSTRUCTIONS_PHASE_C.md` rule 6 ("well under 10 milliseconds per
call if you can").
Reason: "if you can" is soft, 100 ms is a hard fail that sends the skeleton back and, on a second failure, drops the pair
as "skeleton invalid". With 1000 units and 500 features, 500 000 normal draws take about 5-15 ms and any per-unit Python
loop or a second matrix operation exceeds 10 ms easily; the author is told 10 ms is the aim and is not told 100 ms is the
line. With no oversampling (finding 4) a hidden limit costs pairs. The script also leaves the controls' time unmeasured.
Fix: put the numbers in the instruction ("a world call must take at most 100 ms on a laptop; aim for 10 ms"), time the
control transforms in the script with the same limit, and reconcile with finding 5.

**10. The loss rule restates R3 in a way that could be read as weaker.** Passage: section 6 "Primary comparison" ("a loss
is a regression against spec 0.7 section 4: ... the defect is fixed in a patch release, the run is repeated with it, and
both results are reported"); spec 0.7 R3 ("any such loss counts against 0.5").
Reason: R3 is frozen and must not be weakened. The prereg's text is compatible with it but does not say that the loss
stays against v0.5.0 in the primary table and that the patch result is secondary. A reader could take the rerun as replacing
the first.
Fix: add: "The v0.5.0 table is the pre-registered primary table; a loss in it counts against 0.5.0 whatever a patch release
later does; the patch result is reported next to it as secondary." Also note in section 8 that the spec's R3 sentence on
allowed claims ("did not know the error") is superseded by the stricter I-8 wording, so that nobody reads the two as in
conflict.

## Minor

**11. P-2 reading 1 still passes small sizes when the source states none.** `P2_READING.md` (1): "of the order of the
setting that the source describes". With no stated size the section 2 rule ("source's sizes where the timing rule allows")
has nothing to apply and the "largest that fits" rule is not applied to such sources, so a methodological source can get
100 rows while the timing would allow 1000. Fix: for sources with no stated sizes the note must give the largest size
within the timing estimate, or state why the lower size is realistic for the setting; the auditor answers (f) against that.

**12. Docstring template.** `WORLD_INSTRUCTIONS_PHASE_C.md` shows `"""<id>: <the claim, copied from the brief>."""`; the
script requires the docstring to equal `<id>: ` plus the claim after whitespace stripping. A claim ending in "." plus the
template's "." fails; a claim without it and no "." fails if the author follows the template. Fix: "docstring = the id,
a colon, a space and the claim exactly as in BATCH.json, nothing after it" in the instruction, and in the template drop
the period.

**13. `np.random`.** The script flags any `np.random` attribute (including `np.random.default_rng(seed)` for a sub-stream or
`np.random.Generator` in a type position); the instruction only says "no global random state". Say "do not use
`np.random` at all; use `rng`".

**14. Script hardening and false failures.** (a) `main()` loads (executes) every skeleton even when `static_check` found
banned names (`open`, `exec`, `__import__`), so the module runs before it is reported; skip `load` when the static issues
contain a banned name. (b) The dimension check needs every array dimension to appear as an integer in the brief text; a
pooled dimension (for example 600 = 400 + 200 or 20 × 6) not written in the brief fails a correct skeleton; the brief rule
should require that each shape dimension is stated numerically in `sizes`, and the author instruction should say so.
(c) The script does not check the caps of section 2 (any dimension above 1000, or the row-by-feature product); the designer's
cap check is not scripted and not frozen. (d) Controls given as `Control(..., world=World(...))` are not shape-checked.
(e) `ndim` is checked but a mismatch between the brief's named sizes and the shapes is not (only presence).

**15. Batches and redo.** "Batches of at most 15" in shuffle order gives 4 batches for 54 briefs but not their sizes
(15/15/15/9 or 14/14/13/13); state the rule ("consecutive blocks of 15, the last one shorter"). The stop rule sends ids
"without a skeleton that passes the check script" to a new agent without an error list, and section 4 item 4 gives a failing
skeleton one redo with the error list; a skeleton in a stopped batch that really fails could get two redos. Say that a
continuation after a stop is the first attempt and that item 4's redo follows it.

**16. Freeze list.** Section 4 lists the instruction files, the check script and the table. Missing from the freeze (and so
from the hash): `P2_READING.md` (referred to by `AUDIT_PHASE_C.md`), the term-check script, the document-scan script, the
`MECH_CHECK` script, the shuffle (the seed and who draws it: the designer knows the classes), the numeric rule for batch
cut, the pre-flight record, the package environment (finding 6). Add them, and fix the shuffle seed from a value the
designer cannot choose (for example the SHA-256 of the frozen table concatenated with the date).

**17. Scan terms.** The scan list (`Phase A`, `Phase B`, `B-1`...`B-6`, `world author`, `evaluation`, `REPORT`) will remove
`SPEC.md` section 12 and similar, but the docs also mention a "private pilot", "Tenkit" and "evaluation set E2" (SPEC.md
header and section 12), and results-in-passing may use words such as "pilot", "case study", "E1", "E2", "E3", "external",
"detection rate", "miss". Add them. The set must be built and its scan output reviewed before the freeze of the prereg is
final, or the prereg must say that a failed scan blocks the first agent.

**18. P/C/N statement.** Section 6 requires every class verdict to carry "that class's P/C/N shares" and both readings
are reported; say which reading appears in the verdict sentence (suggest the resolved, higher-level one) and that the other is
in the table.

**19. "Not informative".** "Fewer than 5 files in total have an UNDEFINED component under 0.4.1" needs "files" defined
(all 108 files including the out-of-scope ones? study verdict UNDEFINED or any component?). With the exhaustive guard
list, a minimum equal to the smallest defined size and one component per file, UNDEFINED will be rare (Phase B: about 10
of 108 with looser guards), so "not informative" is the probable outcome. State the expectation in I-7 so that it is not
read as a failure.

**20. Smaller points.** (a) Section 4 item 4 refers to "Phase B `REVISIONS-post-freeze.md` P-1", a file the sandboxed agents
and auditors do not have; copy P-1, or drop the reference since the script is frozen. P-3 (fixed criteria made weak by the
skeleton: no skeleton change, stay in the table) is not carried over; `AUTHOR_PHASE2_C.md` has the effect, say so in the
prereg. (b) "At least 4 of the planned 12 pairs rest on a new passage": the report should give the count among surviving
pairs. (c) The audit item (h) "no" (a brief defect) can only be repaired by dropping the pair after the repair round; run
the brief half of (h) and (i) at step 2 (designer) so that Fable and the criterion authors do not spend work on pairs that
will be dropped.

## Answers to the targeted questions

* **Instruction files vs prereg.** They agree on the import line, one criterion `C`, exhaustive guards with the stated
  minimum, URL logging, sandbox, estimand line, nine audit items, batches of at most 15, the second awareness reader and
  the Phase B awareness rule (identical to `AWARENESS.md`). They disagree or are silent on: the "used passages" list
  (finding 2), the package (6), the timing remedy and size changes (5), sub-agents (7), the 100 ms limit (9), item (h)
  wording (1), and several dropped sentences (8). The difference tables are not complete (8).
* **New rules: checkable, one reading?** Estimand rule and (i): checkable (the estimand line is in the private note and
  `CASE.md`). Setting-only and (h): not one reading (1). Raised caps: checkable, but see 5, 11, 14(c). Batches: one reading
  after finding 15. Sandbox: one reading only after finding 6. Identification: checkable, with finding 7. "Not informative":
  needs 19. Overlap key and "more than half": not applicable with one reading (3). New-passage rule: not (2).
* **Impossible or biased?** Not impossible. B-3 at the fixed estimand can be written without banned terms if the claim names
  the conditioned quantity, which the rule (h) exemption allows but does not show (finding 4); "setting only" does not forbid
  the structure a claim needs once axes are declared setting (finding 1). Twelve pairs per class with at least 4 on new
  passages are achievable for B-1, B-2 (KAP23 8 + AMB02 2 + SIM03 2 meets the minima) and B-6; B-3 is at its maximum (3 sources
  times 4) with no slack, and its overlap with Phase B is near certain (findings 3, 4). A bias: the instruction to the authors
  to avoid used passages lowers overlap and is Phase B information (finding 2); a smaller bias favouring detection is the
  P-2 reading for sources without sizes, which leaves sizes free (finding 11).
* **Check script vs instructions.** Imports (`numpy`; `from truth_gate import Study, Criterion, World, Premise, Control`),
  the criterion form (`Criterion("C", criterion)` with exactly docstring plus `raise NotImplementedError`), the `World`
  keywords, `Control` fields and `Study` keywords match the instruction template and `truth_gate/study.py` (fields `id`,
  `fn`, `regime`, `components`, `tolerances`, `control_waiver`; `Study.deterministic`, `allow_paths`, `regimes`, `budget`,
  `targets`). Mismatches: docstring period (12), `np.random` (13), 100 ms against "if you can" (9), no cap check and the
  dimension-in-text rule (14).

## Verdict

**Freeze after fixes; not as v2.** One blocking finding (1) and nine major findings (2-10) need text or file changes; none
needs a new design. Findings 1, 2, 3, 5, 6 and 8 touch frozen files and must be fixed before the SHA-256 freeze because the
instruction files cannot change afterwards. Finding 4 needs a decision about sources before the briefs and a plan count now.
A short third look at findings 1-6 and 8 after the fixes should suffice.
