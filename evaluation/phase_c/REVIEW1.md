# Blind review 1 of `PREREG_PHASE_C.md` (draft v1)

Reviewer read: the draft, spec 0.7 (sections 4 and 6 R3 especially), PB (`PREREG_PHASE_B.md`), `REVISIONS-post-freeze.md`,
`REPORT.md`, `record/world/AWARENESS.md`, `WORLD_INSTRUCTIONS.md`, `AUTHOR_PHASE1/2.md`, `AUDIT_PHASE.md`, and (to
check one contamination path) the top-level `README.md`, `CHANGELOG.md`, `docs/EVALUATION.md`. Nothing was executed.
Severity: **blocking** = do not freeze with this text; **major** = fix before freeze, the pre-registration is weaker or
ambiguous without it; **minor** = clarity.

Counts: blocking 5, major 9, minor 7 (21 findings).

## Blocking

**1. The "public documentation" given to authors contains the Phase B results.** Passages: section 4 items 1 and 3
("the public documentation of the frozen 0.5.0"); spec 0.7 R3 ("receive ... the 0.5.0 public documentation").
Reason: the public documentation set in PB and `WORLD_INSTRUCTIONS.md` is `README.md`, `docs/GATE.md`,
`docs/MANIFEST.md`, `docs/SPEC.md`. The repository's `README.md` (Evaluation section, "Phase B ... 54 pairs ... B-6 11 of
12 ... the world author had inferred the error for most briefs"), `CHANGELOG.md` ("Evaluation, Phase B") and
`docs/EVALUATION.md` (per-class table, why B-1 and B-3 failed, the K1 story) state which classes failed, why, and that
the world author inferred the error. An author who reads "the public documentation" reads the Phase B findings. That
breaks R3's "read neither the Phase B cases nor the Phase B record" in spirit and hands criterion authors the K1/guard
and ratio-world lessons, and hands the world author the awareness result.
Fix: name the exact files (path and SHA-256) that the Phase C agents may read, in the freeze: `docs/GATE.md`,
`docs/MANIFEST.md`, `docs/SPEC.md` and the 0.5.0 sections of the README that describe the tool, taken from a copy
in which every sentence that reports Phase A/B results is removed or from the tag `v0.5.0` with that removal declared.
Scan the set mechanically for "Phase B", "B-1".."B-6", "world author", "UNDEFINED" in a results context, and record the
scan. `CHANGELOG.md` and `docs/EVALUATION.md` are excluded.

**2. Nothing says what happens if Fable is unavailable, silently replaced, or mis-identified.** Passage: section 4 item 3
("The model id reported by the agent runtime ... no other model may write or edit a skeleton"); item 7.
Reason: R3 fixes the world author as Fable. The draft covers only rate limit and session end. It does not say (a) how
the model is identified (an agent's own report of its id is not evidence; a requested `model: fable` can be overridden
or fall back to the inherited model); (b) what the designer does if Fable cannot be run at all, for days, or only
under a fallback; (c) that no other Claude model may be substituted without a new frozen revision. An executor would
decide this on the fly, after seeing the cost or the delay, which is the post hoc freedom the freeze is meant to
remove.
Fix: state (a) identification evidence = the model field recorded by the harness for the agent run (transcript or run
metadata), copied into `WORLD_RUN.md` per agent, with a pre-flight check before any brief is shown (a throw-away
agent request with `model: fable` on a dummy prompt that contains no brief, whose recorded model id must name Fable);
(b) if the recorded id is not Fable, or Fable cannot be started, Phase C does not start under this text; waiting is
allowed without limit; a substitute model is a new pre-registration (the claim "different model line" is the point
of R3), recorded in `REVISIONS-post-freeze.md` before any skeleton exists; (c) a world author run whose recorded id
is not Fable invalidates every skeleton it wrote.

**3. Invalid or unusable Fable skeletons: no rule.** Passage: section 4 item 4 ("checks the skeletons mechanically (as
the Phase B step-3 script) ... freezes the skeletons"); step 5 last sentence.
Reason: Phase B had 54/54 valid skeletons, so no rule was ever written. For Fable a failure is plausible (wrong keys,
dtype, `minus` identical to `plus`, a control that returns a partial dict, a world over the time limit, the `minus`
rule not followed). Options (redo, drop, let a Sonnet agent fix it) change class sizes and which pairs count, and are
chosen after seeing the failure. "A skeleton change is granted only for a defect that makes the fixed criterion
impossible to write" does not cover a skeleton that is invalid before any criterion exists.
Fix: pre-register: a skeleton that fails the mechanical script goes back once to a fresh Fable agent with only the
script's error list (no other information); a skeleton still failing is dropped as "skeleton invalid" (counts nowhere,
reported by id, not by class); a class falling below 10 pairs is "insufficient cases" (section 5). Plan 14 briefs per
in-scope class instead of 12, or state that the set is as planned and drops are accepted. Mechanical checks that cannot
be scripted (whether `minus` follows the fixed rule) are not grounds for a redo; the world author's log decides
nothing. Freeze the mechanical script (path, hash) with the prereg; "Phase B step-3 script" is also a wrong reference
(it is PB section 4 step 4, `REVISIONS-post-freeze.md` P-1).

**4. The permitted claim and the main question presuppose that the world author "does not know the error"; Phase B
measured that it did.** Passages: section 0 Main ("a model that does not know the error"); I-8 ("worlds declared by a
different Claude model line that did not know the error").
Reason: Phase B `REPORT.md` section 3: 41 of 48 in-scope pairs (45 of 54 overall) were level P, and the report section
6 says the author "inferred the error for 45 of 54 briefs". The Phase C text makes the same claim about a stronger
model without a limit. The only thing that can be said before the run is that Fable "was not told the error, the class
or the source". The draft also pre-registers no use of the awareness breakdown: no statement of how a class verdict
is to be worded when most pairs are P.
Fix: replace "does not know" by "is not told" in section 0 and I-8; add to I-8 that every statement of a class verdict
carries the share of P/C/N pairs of that class (from the frozen classification) and the wording "declared worlds that
may contain what the error exploits"; add a banned-wording list (as the current one for "independent"): "unaware",
"did not know", "blind world author". Decide now whether the classification is also run as a descriptive subset result
(C and N only) next to each class table (it will be tiny; say so, no interval).

**5. Brief steering has no preventive rule; the term check bans words, the steering was structural.** Passage: section 4
item 1 ("banned terms of PB §4 checked by script").
Reason: Phase B post-run audit (iii) found the B2-07 brief stating that about a quarter of the rows repeat an earlier
entry (that is the error structure), the O1a data keys naming the leaking variable, the O2a brief naming the secondary
outcome and its correlation with the primary, and B3-05 the world author leaving the artefact near the threshold "on
purpose". None of these contain a banned stem. The draft copies the mechanism that failed and finds out afterwards
through audit (iii), when the pairs are already in the table. R3 says "same design", but nothing forbids a stricter
check.
Fix: add to the brief rules: a brief states only the setting a researcher would state about the data (sizes, axes,
what the measurements are); it does not state frequencies, overlaps, repetitions, selections, orderings, shared
quantities or dependencies between rows, units, splits or variables unless the claim itself is about them. Add a
fidelity-audit item **(h)** "the brief states no structural fact whose only role is to be what the error exploits;
data keys do not name a variable by its role in the error" (an added yes/no item strengthens, does not weaken, PB §5;
a "no" follows the PB repair/drop rule). Keep audit (iii) after the run.

## Major

**6. Overlap with Phase B is not operational and has no consequence.** Passage: section 1 "Overlap with Phase B".
Reason: "the same kind of setting (statistic and data structure)" has two readings (family of statistic or the exact
one; axis structure or sizes), and the designer who marks it has read all of Phase B. Authors that start from the
same `SOURCES.md`, the same cap of 4 pairs per source and the same class definitions will, with Sonnet, reproduce many
Phase B pairs; B-3 has only three sources (PEA97, ARC81, KRO93), each supplied 4 pairs in Phase B, so overlap there is
nearly certain. Pairs stay and are flagged, but if most pairs overlap the set is a second draw of Phase B, and the
interpretation (I-6) is silent about this.
Fix: define overlap by a written key: same source key AND same B-2 subtype or same error mechanism AND same statistic
(by name) in the private notes; any one different means "not overlapping". The marking is made from a table of
Phase B (source, mechanism, statistic) built by the designer before the briefs, frozen with hash. Pre-register what is
said if overlap in a class exceeds a share (suggest one half): that class's Phase C result "is largely a repeat of
Phase B settings with a new world author" and no sentence of the report may call the Phase B and Phase C classes
different evidence. Require, per class, at least one source not used in Phase B or at least 1/3 of the pairs from
passages not used in Phase B (the addendum mechanism in section 1 allows this; use it, and decide now, because after
briefs exist adding a source is not allowed).

**7. The primary comparison is deterministic by construction, has no informativeness rule and "counts against 0.5"
has no meaning.** Passage: section 6 "Primary comparison", I-7.
Reason: spec 0.7 section 4 proves that only components that 0.4.1 made UNDEFINED can change; in Phase B that was 10 of
108 files (about 5 per version; per class 0 to 2). The answer to "what does 0.5.0 change" is a count of those
components and where they land; at about 10% of files a per-class table of 0, 1 or 2 pairs is noise and the draft does not
say when the comparison is reported as "not informative". The text also says a lost 0.4.1 detection "counts against 0.5"
without saying what follows (it would be an implementation defect against spec 0.7 section 4 and R1, not a result about
the gate). Further: the criteria were written by authors who read the 0.5.0 documentation, which says to return `None`
when there is nothing to claim (finding 8), so the files may abstain more than in Phase B and the comparison is
favourable to 0.5.0 by design; the draft does not say that. Component-level statements (spec) and study-level verdicts
(the draft) are mixed; Phase B studies have one component, but the draft does not say Phase C studies have exactly one.
Fix: state that every Phase C study has exactly one `Criterion` (as the skeleton stub) or define the unit; define the
loss as "a regression against spec 0.7 section 4; the run is repeated after the defect is reported in
`REVISIONS-post-freeze.md`, results of both reported"; pre-register that when fewer than 5 files in total (all classes)
have an UNDEFINED component under 0.4.1 the comparison is reported as "not informative" with the list and no per-class
sentence; list the cause per component (hard vs soft abstention, `K1_ABSTAINED_MAJORITY` after the change); add the
limitation about doc exposure to I-7.

**8. The guard rule and the 0.5.0 documentation pull in opposite directions; the draft's stated aim is not met.**
Passage: section 2 ("the guard rules given to the criterion authors are PB's, unchanged, so that the authors' use of
guards is not tuned to the new rule"); section 4 item 1.
Reason: the authors read the 0.5.0 documentation, which (spec 0.7 section 2.5) tells users to return `None` when the
analysis has nothing to claim and which explains `K1_ABSTAINED_MAJORITY` and the plus-majority rule. That is the
tuning the draft says it avoids. PB's allowed-guard list also contains "a selection ... large enough", with no
minimum, so an author can raise the abstention rate by a high minimum size; under 0.5.0 abstentions on `minus` count as
not-HOLDS, so a faulty criterion with a generous guard abstains instead of holding.
Fix: state which text governs: PB section 2's list is exhaustive and the documentation's "return None" advice does not
widen it; "large enough" means no more than the smallest size at which the statistic is defined (for example 3 pairs for a
correlation, 2 per group for a t statistic), stated per brief in the private note and checked by fidelity item (d);
the report gives, per class, the share of samples on which each fixed and faulty criterion abstained under 0.5.0
(from `hard_undefined` and `undefined` counts) next to Phase B's, descriptive.

**9. Sizes capped below the source's range keep the errors too small, and the audit reading makes it count.** Passage:
section 2 ("At most 300 rows ... 60 features"), section 5 ("item-(f) reading of P-2").
Reason: `REPORT.md` 5.2 attributes at least ten faulty WEAK outcomes to errors that were too small in the declared worlds
(B2-03: 60 features where AMB02's bias needs thousands; B2-06, B2-09, B2-10, B2-12, B3-*, B6-10). P-2 lets a size "reduced to the cap" pass
item (f), so the cap makes the error small, the audit passes it, and the miss counts against the gate in the
pre-registered table. Phase B run times were 0.38 to 29 s per check, so the cap is not forced by the 15-minute
timing budget.
Fix: either raise the caps for Phase C to what the timing rule allows (for example up to 3000 rows and 1000 features,
with the 15-minute estimate unchanged) and require the brief's sizes to be those of the source where the timing
estimate allows, or keep the cap and require that each private note states, from the source's own formula or reported
numbers (no running of the faulty criterion), the expected inflation or bias at the chosen size; the designer drops
a brief (before the shuffle) whose documented effect at the cap is below the nominal level, as "error not reproducible at
the cap", reported. Either way, add to the report, per pair, the ratio of the brief's size to the source's size and
list the misses with an "error too small at this size" label as the interpretation of record.

**10. B-3 corrections change the estimand; the draft ignores it.** Passage: section 5 (items (a)-(g)), section 4 item 5.
Reason: `REPORT.md` 5.3: in B3-11 and B3-12 the fixed criterion tests a different quantity from the one the world author
made true (fixed holds in `plus` 4/200 and 1/200), and the generic statement: "the documented correction changes the
estimand". Items (b) and (c) check "the correction and nothing else" but not that the corrected statistic is the one the
brief claims, so a Phase C B-3 pair can be audited as faithful and fail the clean pass for a reason the audit cannot
see, and the world author cannot know which level to make true.
Fix: add to fidelity audit (item (h) or a separate (i)): "the fixed criterion tests the same estimand as the claim of
the brief (the quantity the world author's fixed `minus` rule nulls)"; require the private note to name the estimand of
the faulty and the fixed statistic and the brief to state the claim at the fixed one (for a correlation of ratios, for
instance, a claim about the quantity after the shared component is accounted for may be written without any banned term
only if the data keys carry the components; if not, the brief is dropped); pre-register that a pair for which the
auditor answers "no" to this item is a repair/drop under PB 5.3, not a pair that counts.

**11. World-author prompt equality with Phase B is not pinned.** Passage: section 4 item 3 ("the instructions (the Phase B
world instructions with the import line of section 2)").
Reason: the Phase B instructions hold three things that change: the import line (`kapi` vs `truth_gate`), the list of
documents (README, GATE, MANIFEST, SPEC; see finding 1), and the paths to forbidden folders (`kapi\`, `truth_gate\`,
`evaluation\`, whose names appear in the instructions themselves). "With the import line" is not a text; an executor
edits the instructions after reading the doc set, and equality with Phase B cannot be verified by the report's reader.
Also the Phase B instructions asked for a log with "any judgement call", which shaped what P/C/N could be read from it.
Fix: write `evaluation/phase_c/WORLD_INSTRUCTIONS_PHASE_C.md` before freeze (or specify its construction as an
exact patch) and freeze its SHA-256 with the prereg; list as a table every difference from Phase B's file (import
line, doc list, nothing else); the same for the criterion-author instruction files (R3 requires the guard rules "fixed
before any skeleton exists"; the draft does not say when the instructions are fixed). State that the log requirement is
unchanged so that P/C/N are comparable, and that a log length or style difference is reported next to the awareness
table.

**12. Contamination paths other than local files.** Passage: section 4 item 1 ("nothing of Phase B except ...").
Reason: (a) the prohibition is by instruction only; the agents run on a machine where `evaluation/phase_b/cases/`,
`record/` and the world log are present; Phase B relied on the same honour system but its agents had no Phase B to
read. (b) The authors read the sources online, and the repository is public with the Phase B cases (pushed as `fe86e96`);
a web search for a source key or DOI can reach it. (c) The designer, who wrote the spec and read all of Phase B, runs the
term check, assigns classes, marks overlaps and shuffles; the draft does not say that the designer may not reject,
reword or reorder briefs for any reason other than rule violation. (d) `PREREG_PHASE_B.md` section 4 is allowed reading
and contains the Phase B size caps and the minus rule but also the class tables; acceptable, but `SOURCES.md` should be
checked for Phase B-specific notes ("read as abstract only" and such).
Fix: give each agent a sandbox folder holding only its allowed files (a copy), and state the sandbox as the rule rather
than the instruction; forbid fetching anything from the project's repository or the Phase B record on the web, and
require that each author's log lists every URL read (the source texts only); state that the designer rejects a brief
only for term-check failure, class ambiguity, cap violation or finding 9, logs every rejection with the reason, and
never edits a claim; strip Phase B notes from the copy of `SOURCES.md` given to authors, keeping the keys and DOIs.

**13. The awareness classification is a single-reader judgement on a log whose style may differ.** Passage: section 4
item 4.
Reason: P/C/N is decided from prose by the designer, in Phase B too. A different model writes a log with a different
amount of commentary; P/C/N rates may differ because of verbosity, not awareness, and the Phase B/Phase C
side-by-side (section 6) would then compare logs. Also "same rule, generous reading" leaves the rule outside this text.
Fix: copy the rule into the freeze (or cite the Phase B file by hash) and add a second blind classifier (a fresh agent
that sees only the log and the rule) with disagreements resolved to the higher level, both readings reported; state in
the report the length of the log per brief in both phases.

**14. Fresh-agent continuity is only half specified.** Passage: section 4 item 3 (last sentence), item 5 ("the same agents
if they are still available, otherwise fresh agents").
Reason: Phase B lost two agents (the first world author at a rate limit, writing nothing; the criterion authors could
not be resumed). The draft covers a Fable stop with "a fresh Fable agent continues from the same files". It does not say
what files hold the state (which skeletons are complete), how the continuation is told which briefs remain, that
partial files are re-checked, or whether batches are used. One agent for 54 skeletons is a single point of failure in
exactly the way Phase B had; "if still available" leaves a choice to the executor.
Fix: state a fixed batch plan (for example 4 batches of about 14 briefs, each a fresh Fable agent with the identical
instructions, batch composition fixed by the shuffle order, no class information); progress is the set of skeleton
files that pass the mechanical script; a stopped batch's remaining ids go to a new fresh Fable agent; the log of each
batch is separate and every batch's model id is recorded. For criterion authors: the body authors are always fresh
agents reading the class folder (as in Phase B), not "the same agents if available".

## Minor

**15. "Size ... within the source caps" ambiguous.** Passage: section 4 Size paragraph. "Source caps" can mean the
per-source pair caps or the size caps of section 2. Say "per-source pair caps (section 1)".

**16. "Independent read sources" is undefined.** Passage: sections 1 and 5. Phase B read ARC81, KRO93 and BAR05 as abstracts
only. State what "read" means (full text of the documenting passage, quoted in `SOURCES_ADDENDUM.md` or the private
note) and whether abstract-only sources count towards the three.

**17. Guard-return timing and per-version timeouts.** Passage: section 2 ("the 60-minute rule applies per check and per
version"). If a file times out under one version and not the other the comparison cell is undefined; say that a timeout is a miss or a failed
clean pass in that version's table and "not comparable" in the primary comparison.

**18. Baselines and out-of-scope flag lists are not tied to a version.** Passage: section 6. State that noise-only and
declared-only are computed from the 0.5.0 certificates (with the 0.4.1 version as a second line), and that the
out-of-scope cases carry the in-scope list for description only (as Phase B did, `REVISIONS-post-freeze.md` P-5).

**19. Software state not pinned.** Passage: section 6 "The 0.5.0 commit is recorded". Pin the commits of `v0.5.0` and
`v0.4.1`, the Python and numpy versions and the machine in the freeze, and run a smoke test on a trivial non-case
study under both tags before the freeze (both import `truth_gate`; the package name exists since 0.4.0, but the
claim "Both load it" in section 2 is untested). Say how an infrastructure failure (crash not a timeout) is handled
(one rerun, both logged).

**20. Public push and approval.** Passage: section 5 ("with the author's approval"). Say what happens if the approval is
not given: no run. Also say that the runner and the recomputation script are written after the push and read only the
frozen files (as in Phase B P-6); otherwise the executor decides the order.

**21. Section order of work contains an unlabelled dependency.** Passage: section 4 items 2 and 5: the designer assigns
subtypes before the shuffle but class changes after audit are forbidden ("they never change after the run" in PB
section 1, not repeated here). Repeat that class and subtype are fixed at the shuffle and never change, even if the
criterion author or an auditor disagrees (the disagreement is reported).

## Checks that passed

* Spec 0.7 R3: classes, 10 pairs per class, same thresholds, expected flags without information flags, fresh Sonnet
  authors per class, Fable as world author with same-vendor statement, 0.4.1 comparison with the listed outcome
  categories, claims-allowed sentence: all present, nothing weakened. The one item R3 requires and the draft does not
  carry is "fixed before any skeleton exists" for the guard rules (finding 11).
* `K1_ABSTAINED_MAJORITY` is correctly excluded from expected flags (it caps; a faulty twin held at WEAK is a miss, as
  spec 0.7 intends); `K2_MINUS_UNREAD`, `K8_SOME_CHANGES` and `BAD_RETURN` are listed as information flags, consistent
  with spec.
* The "no change reported as such" rule and the Phase B/Phase C side-by-side labelled descriptive are fine.

## Verdict

**Another round.** Five blocking findings (1 to 5) and the major findings 6 to 14 need text changes; none requires new
design, but several (1, 2, 3, 9, 11) need files or decisions that must exist before the freeze (the exact document set,
the frozen instruction files, the identification procedure, the size policy). After the fixes a short targeted second
review of findings 1 to 5 and 9 to 11 should be enough.
