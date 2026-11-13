# Blind review 3 of `PREREG_PHASE_C.md` (v3), short targeted look before the SHA-256 freeze

Reviewer read: `REVIEW2.md`, `REVISIONS.md` (v2 to v3), the v3 prereg, the five instruction files, `P2_READING.md`,
`SOURCES_ADDENDUM.md`, `PHASE_B_TABLE.json` (vocabulary and all 54 rows, counted by tag), the five scripts, spec 0.7 section 6
R3, and the Phase B files in `evaluation/phase_b/record/` (diffed). Run: `scan_docs.py` on a copy of the current `README.md`,
`docs/GATE.md`, `MANIFEST.md`, `SPEC.md`; `check_skeletons.py` on six toy skeletons in the reviewer's scratch folder; a script
that compares the three copies of the "what a brief may state" text. Nothing was written inside the repository except this file.
Severity: **blocking** = do not freeze; **major** = fix before freeze (the file is frozen afterwards); **minor** = cheap hardening.

Counts: **blocking 0, major 3, minor 12.**

## 1. Status of REVIEW2 findings 1 to 10

| # | Status | Passage / reason |
|---|---|---|
| 1 | yes | The text "A brief may state (i) ... No data key names a variable by its role in the error" is **byte-identical after whitespace normalisation** in prereg §2, `AUTHOR_PHASE1_C.md` and `AUDIT_PHASE_C.md` (h) (checked by script). "time in order" is declared setting; (h) is "answered by the text, not by a guess at purpose"; four pass/fail examples. Residual: m13. |
| 2 | yes | §1 "New sources": replaced by a source-based rule; authors are not told used passages; one return, then "new-source minimum not met"; counted on surviving pairs. Residual: m8. |
| 3 | partly | §1 "Overlap key": closed vocabularies in the table, key applied mechanically, "strictly more than half of the pairs entering a class table", I-9. All 54 rows carry both fields. But the tags have **no definitions** and the key is applied from the Phase C author's own tag (M3). |
| 4 | partly | CUR13 added (cap 16, plan 12), one B-3 example at the fixed estimand. Feasibility is shown for ratio mechanisms only; the shared-component, change-against-baseline and target-from-labels mechanisms have no example (m5). |
| 5 | yes | §2 "Timing remedy" and `AUTHOR_PHASE2_C.md` "Timing": faster criterion, one SIZE REQUEST, then "timing infeasible". Residual: m7 (the regenerating agent is not covered by the identification rule). |
| 6 | yes | §4 item 0(b): `pkg/` copy from tag `v0.5.0`, first on `sys.path`, frozen in `FREEZE_AGENT_DOCS.json`, honour-system limit stated. Residual: m2. |
| 7 | yes | World instructions forbid starting agents; §4 item 3 "Invalid batch" (tool names, linked transcripts), transcript hashes frozen, new pre-flight frozen. Residual: m7. |
| 8 | partly | Phase B wording of (d) and (g) restored; dropped sentences mostly restored; auditor gets stripped `SOURCES.md` and the addendum. Remaining omissions in section 2 below (m6). |
| 9 | yes | Rule 6 states "at most 100 milliseconds ... (the check script rejects slower ones)"; the script times worlds, control transforms and control worlds against 100 ms. |
| 10 | yes | §6: "The v0.5.0 table is the pre-registered primary table ... a loss counts against 0.5.0 whatever a later release does"; I-8 says it replaces R3's shorter sentence. |

## 2. Instruction files against the prereg and against Phase B

* **Verbatim text:** identical in the three places. The AWARENESS rule is identical to Phase B `AWARENESS.md` "Rule".
* **Rules agree with the prereg on:** import line, one criterion `C`, exhaustive guards with the stated minimum, URL logging,
  sandbox, estimand line, nine items, batches of 15, 100 ms, timing remedy, tag/family lists (the closed lists in
  `AUTHOR_PHASE1_C.md` equal `PHASE_B_TABLE.json` `vocabulary`, item by item), `np.random` ban.
* **Disagreement: the feature cap.** `P2_READING.md` ("1000 rows or units, 500 features per sample") and `AUDIT_PHASE_C.md` (f)
  ("<= 1000 rows, <= 500 features") against prereg §2, `AUTHOR_PHASE1_C.md` and the script ("1000 on any axis, 500 000 values";
  500 only appears as the example 1000 x 500). See M2.
* **Tables against a diff with the Phase B files.** `WORLD_INSTRUCTIONS_PHASE_C.md`: complete (rules 1-4, 7 verbatim; rules 5, 6
  and the changed sentences listed). `AUTHOR_PHASE1_C.md`: complete except that "Nothing else in these objects (no source, no
  class, no error)" became "nothing else" (harmless). `AUDIT_PHASE_C.md`: (d) and (g) now in Phase B wording; **(e) lost the
  parenthetical "(it does not say what 'claim false' means)"** and the table does not list it; the prereg says (a)-(g) are in
  "Phase B's wording". `AUTHOR_PHASE2_C.md`: not listed and dropped: the syntax-check command for `faulty.py`, "the criterion must
  not know how the worlds were built", "(what, how many samples, the rates)" for pre-checks, `CASE.md` item 5 and 6 details
  (sample counts and rates; `t`, `g`, `S`, the estimate). The row "everything else the same" is therefore not exact (m6).

## 3. Scripts against prereg and instructions

| Script | Result |
|---|---|
| `check_skeletons.py` imports | `import numpy` and `from truth_gate import` only the five names: as prereg §2. Any other import, `from x import *`, `numpy.random` module import: flagged. |
| criterion form | exactly `Criterion("C", criterion)`, body exactly docstring plus `raise NotImplementedError`, signature `(d)`: as prereg. |
| docstring | `"<id>: <claim>"` compared after outer `strip()` only: matches the instruction. A claim wrapped over several lines in the docstring fails (m3). |
| 100 ms | worlds (3 draws each), control transforms (on `plus` draws) and control worlds: yes. Premises not timed (trivial). |
| caps | any dimension > 1000 or any array > 500 000 values in worlds, control outputs, control worlds: yes (toy test: 1001 rows flagged in three places). |
| static banned names | `open`, `exec`, `__import__`, a non-allowed import, `np.random`, class statements, extra top-level statements: **module not loaded** (toy test: `open('zz.txt','w')` did not run, no file created). |
| gap | `import numpy` then `numpy.random.rand(...)` in a world **passes** (toy test G6): only the alias `np.random` is caught, while the instruction says "do not use `np.random` at all". Also not caught in twins when the name is `numpy` only inside a skeleton helper. (m1) |
| `term_check.py` | the 15 stems of PB §4 as regular expressions (double dip, non-independ, pseudorepl, regression to the mean with free separators), case-insensitive, over claim, sizes, and key/shape/dtype/meaning. Matches PB; "optimis" does not catch "optimiz" (PB's own list, not changed). |
| `scan_docs.py` | **crashes** under the Windows default console encoding (`UnicodeEncodeError` on "→") and is **too broad** (M1). |
| `mech_check_twins.py` | Phase B checks preserved (diffed), plus: signature without defaults/annotations/decorators, exactly one `Criterion("C", ...)`, `np.random` only as `default_rng(<int>)`, `__builtins__` banned, twins equal the skeleton outside the criterion, constants comparisons listed. Criterion C check present. |
| `shuffle.py` | seed `int(SHA-256(file bytes + b"phase-c-shuffle"), 16)`, Fisher-Yates over `random.Random(seed)` with `randrange(i+1)` from `n-1` to 1, consecutive blocks of 15 (last shorter): exactly §4 item 2 and item 3. Writes `BATCH_01.json`; the instruction says `BATCH.json` (m10). |

## 4. Findings

### Major

**M1. `scan_docs.py` crashes on Windows and its token list makes the prereg rule "no hit" unattainable.**
Passage: §4 item 0(a) ("runs `tools/scan_docs.py` until it reports no hit ... a hit that cannot be removed without losing tool
documentation blocks the first agent until a revision decides it"); `tools/scan_docs.py` `SUBSTRING_TOKENS`.
Reason: (a) On a copy of the current `README.md`, `docs/GATE.md`, `docs/MANIFEST.md`, `docs/SPEC.md` the script died with
`UnicodeEncodeError: 'charmap' codec can't encode character '→'` when stdout is not UTF-8 (the project shell is Windows
PowerShell 5.1); the exit code is then 1, the same as "hits found", and the list is cut short. (b) With `PYTHONUTF8=1` it reports
**150 hit lines in 4 files**: "evaluation" 43, "external" 27, "REPORT" 26 (case-insensitive: the word "report"), "E1" 21, "audit" 18,
"E2" 14, "E3" 10, "pilot" 7, "miss" 6, "private" 3, "Phase B" 3. Many are plain tool vocabulary (`[external] uses`,
`K6_EXTERNAL_UNGUARDED`, `sys.addaudithook`, "blind audit", "report"), which cannot be removed "without losing tool
documentation". As written, the rule either gutting the documentation the agents must read or stalls the first agent until an
unregistered revision decides; the decision is then the designer's, after seeing the text.
Fix: in `scan_docs.py` set `sys.stdout.reconfigure(encoding="utf-8")` (and `errors="replace"`) and return exit code 3 on any
exception; narrow the tokens to result-bearing ones (phase names, "world author", "B-1".."B-6", "E1".."E3", "detection rate",
"Tenkit", "pilot", "case study", "evaluation set", and the words "evaluation" and "report" only in the phrases that report
results) or keep them but add to §4 item 0(a) a pre-registered triage: every hit is reviewed by the designer and a fresh reader
(as the awareness reading); a hit is removed only if it states an evaluation, a result, a count or a case; a hit that is tool
vocabulary stays and is listed in `agent_docs/SCAN_REVIEW.md` (frozen with `FREEZE_AGENT_DOCS.json`); "no hit" is then replaced by
"no hit left that is not listed as tool vocabulary".

**M2. The feature cap is stated in two different ways.**
Passage: `P2_READING.md` ("500 features per sample"), `AUDIT_PHASE_C.md` (f) ("<= 1000 rows, <= 500 features") against §2 ("at
most 1000 rows (or units) along any axis and at most 500 000 values in any array"), `AUTHOR_PHASE1_C.md`, `check_skeletons.py`.
Reason: a brief with 200 samples x 1000 features respects the prereg, the author instruction and the script, but fails item (f)
as the auditor is told to read it; a "no" on (f) is a brief/size defect and the pair is dropped after the repair round (PB §5.3).
The designer's brief-half check does not include a features limit, so the contradiction is only found at audit, on pairs that have
already cost two agents' work. Two readings, decided after seeing the pairs.
Fix: one rule. Either delete "500 features" in both files and read (f) against §2 as written ("<= 1000 on any axis, <= 500 000
values"), or add "500 features" to §2, `AUTHOR_PHASE1_C.md`, the script and the REVISIONS row 9 text. The first is the smaller change.

**M3. The overlap vocabulary has no definitions, and the key is applied from the author's own label.**
Passage: §1 "Overlap key" (applied "mechanically ... from the Phase C note's own tag and family"); `AUTHOR_PHASE1_C.md` "Closed
lists"; `PHASE_B_TABLE.json` `vocabulary`.
Reason: the tags are names only. Several pairs of labels are not separable by the names: `statistic_family` `classification`
("accuracy, AUC, F1") against `proportion` (accuracy is a proportion; `proportion` is not defined anywhere); B-1
`extreme-group-change` against `split-by-baseline-compare-change` (both are change against a noisy baseline: KRI09 pair 3 and the
BAR05/MAK19 pairs sit on either side in the table); B-3 `ratio-shared-denominator` against `ratio-vs-denominator-proxy`;
`mean` against `regression-slope` for a group-difference coded as a slope. The authors do not see the Phase B rows, so they
cannot know which label the table used; two authors (or the author and the designer's table) can tag the same mechanism
differently and the overlap count, which decides whether a class may be presented as evidence at all (§1, I-9), moves with a
label choice made without information. "Mechanical" is true of the comparison, not of the label.
Fix: add to `AUTHOR_PHASE1_C.md` one line per tag and per family (what is in, what is out, with the Phase B-independent examples
already in the file), freeze them, and add to §1: "an ambiguous label is resolved by the definition, and the designer may change a
label only to the one the definition requires, logging the change"; add the same one-line definitions to the table's
`vocabulary` before the freeze so that the 54 Phase B tags can be re-read against them (the reviewer found no Phase B row that
contradicts a plausible definition).

### Minor

**m1. `numpy.random` passes the skeleton check.** `import numpy` is allowed and `numpy.random.rand` is not an `np.random` attribute
access (toy skeleton G6 passed). Fix: also flag `Attribute(attr="random")` on any name, and `from numpy import random` (already
caught).

**m2. The package root is not verified.** `check_skeletons.py --package-root REPO_OR_WORKTREE` (usage text) and
`mech_check_twins.py` insert the path but never check that the imported `truth_gate` comes from `pkg/`; §4 item 0(b) relies on
shadowing of the editable install. Fix: print and record `truth_gate.__file__`, fail when it is not under the given root; correct
the usage text to `pkg/`.

**m3. The script enforces rules the world instruction does not state.** Banned names including `print`, `getattr`, `vars`;
module level limited to imports, assignments and functions (no `class`, no `if __name__`, no `sys.path.insert` in the skeleton,
which the instruction's "put it first on `sys.path`" invites); `World(...)` with one positional argument and only `derived_from`
and `change`; non-finite values; a control that returns the data unchanged on a draw; a docstring that wraps over lines.
Each costs one redo and, on a second failure, the pair, with no oversampling. Fix: add one short rule 8 to
`WORLD_INSTRUCTIONS_PHASE_C.md` listing these, and say that the `sys.path` line is for the author's own test scripts, not the
skeleton.

**m4. VAR06 as L1.3 against PB §1.** PB §1 defines L1.3 as "feature selection on all data" (and "feature selection before
cross-validation is L1.3"); the addendum reads VAR06 (selection of classifier parameters on the CV estimate) as L1.3, and the prereg
says "decision rules ... as PB §1" and "VAR06 pairs count as L1.3, as the addendum fixes". `AUDIT_PHASE_C.md` tells the auditor to
report whether subtype follows PB §1 and does not mention the addendum, so every VAR06 pair will be reported as a disagreement
by construction. Fix: one sentence in `AUDIT_PHASE_C.md` ("for VAR06 the subtype is as `SOURCES_ADDENDUM.md` fixes it") and in §1
("an extension of PB §1's L1.3 to parameter selection, not a change of PB §1"). The class (B-2) is not affected.

**m5. B-3 feasibility and steering.** The B-3 pass example is Pearson's own femur/tibia/vertebral-column setting (source PEA97),
which an author may copy; an author who does will produce a PEA97, `ratio-shared-denominator`, `correlation` pair that overlaps
a Phase B row (two such rows exist). The claim form "after accounting for X" tells the world author which quantity is shared, which
the other classes do not; §0 and I-6 should say so (the stricter I-8 wording already guards the report, but the B-3 P/C/N share
will be near all P). No example shows a brief for `shared-measured-component`, `change-vs-baseline` or `target-from-labels` under
the estimand rule. Fix: state in I-6 that B-3 briefs name the adjusted-for quantity by rule; replace the example by a
setting that is not a Phase B source; add one sentence per other mechanism saying how the estimand is named (or that the
mechanism is expected to be written by few pairs, with the cap of 4 per source and 16 available, at least 10 needed).

**m6. Remaining omissions in the difference tables** (section 2): audit (e) parenthetical; the `AUTHOR_PHASE2_C.md` items listed.
Fix: restore the sentences or add the rows; regenerate the tables from the diff output.

**m7. Identification covers batches only.** §4 item 3 requires transcript evidence for the batch agents; the redo of a failing
skeleton (item 4), the regeneration under the timing remedy (§2), and the skeleton change of item 5 use "a fresh Fable agent" with
no stated check. Fix: "every Fable agent of Phase C, including redos, continuations and regenerations, is subject to the
identification and invalid-run rules of item 3".

**m8. New-source minimum has no slack in B-2, B-3, B-6.** Each has one addendum source (VAR06, CUR13, LAZ18) and the cap is 4 pairs
per source, so "at least 4 of 12" means all four pairs on that source must survive term check, audit and timing; one drop gives
"new-source minimum not met" (a report line, not a verdict change). CUR13 is abstract-only and LAZ18 shares its first author with
LAZ10 (stated). Fix: add a second addendum source for those three classes, or state in §1 that "not met" is expected to be
common for them.

**m9. Independent source count.** The addendum says the count "is unchanged" and names only KRI10 and LAZ18 as not independent;
it does not say whether MOR03, VAR06, CUR13 count. B-3 then needs all three of PEA97, ARC81, KRO93 to be "read". Fix: one
sentence.

**m10. `shuffle.py` details.** It writes `BATCH_01.json` and the world instructions say `BATCH.json`; the item order depends on
sorted folder names chosen at run time, and the seed is computable from the freeze file before any brief exists. Fix: name the
batch copy rule; fix the folder names (`B1`, `B2`, `B3`, `B6`, `O`) and the class mapping in the prereg.

**m11. Freeze list and header.** The header says v1 and v2 "were reviewed blind" and the frozen list ends at `REVIEW2.md`; add
`REVIEW3.md` and "v3" to both (this file) before hashing.

**m12. "Closed lists" reveal Phase B structure.** Names such as `ratio-vs-denominator-proxy` and
`split-by-baseline-compare-change` come from the Phase B rows; spec R3 says authors do not read the Phase B record. The list is
needed for the key; say in §1 that the vocabulary is a designer's tool and that this exposure is accepted and reported.

**m13. B-2 pass example.** "one row per registry entry" states that rows are distinct entries, a fact about duplication that the
text forbids (and the fail example states the opposite). Fix: "rows: registry entries" or drop the sentence; keep the example
otherwise.

## 5. Contradictions introduced by v3, as asked

* **VAR06 as L1.3 against PB §1:** a labelling extension, not a verdict-changing contradiction (m4).
* **B-3 example against "what a brief may state" and the banned terms:** the example claim contains no banned stem and keeps to
  the text because the estimand names the third quantity; its fail example (a shared quantity measured with error) is correctly
  excluded. No contradiction; the steering and the source choice are m5.
* **Overlap key against the table's vocabulary:** the closed lists agree item by item and all 54 rows are tagged (12, 12, 12, 12,
  6); the weakness is definitions (M3), not mismatch. A pair on an addendum source "cannot overlap" even when its tag and family
  equal a Phase B row of a source by the same authors (KRI10/KRI09, LAZ18/LAZ10); this is stated in the addendum and I-9, so it
  is a reporting limit, not a contradiction.

## Verdict

**Freeze after the listed fixes.** No blocking finding. The three major findings (M1 scan script and rule, M2 feature cap,
M3 tag definitions) change frozen files, so they must be done before the hash; each is a text or script edit of a few lines and
needs no design change. Of the minors, m1, m2, m3, m4, m7 and m11 are cheap and touch frozen files, so do them in the same edit
(m11 is needed for the hash to cover this review). No further blind round is needed if the edits are limited to the above; a
check by the designer that the verbatim text is still identical in the three files (the reviewer's comparison script is
trivial to repeat) after the edits is enough.
