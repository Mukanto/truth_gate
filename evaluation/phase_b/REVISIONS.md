# Revisions to the Phase B pre-registration

Decisions by Claude under the author's delegation. Each line answers a finding of `REVIEW1.md`.

## Draft v1 → v2 (2026-11-12)

| # | Change | Reason |
|---|---|---|
| 1 | The headline becomes "the gate together with worlds and controls declared without knowledge of the error". Every detection is labelled **generic** (the noise probe fired: `K5_HOLDS_ON_NOISE` or `HIGH_RATE:probe:noise`) or **declared** (only declared streams fired). Two ablations are reported per class: noise-only detection and declared-only detection. | The finding is correct: for B-3, B-6 and the structured B-2 subtypes, detection can only come from declared streams. That is still the gate's design (K4 forces a control, K2 a `minus` world), but the report must say which part found what. |
| 2 | **Three roles.** A *world author* who never learns the error or the class writes every skeleton (worlds, controls, premises, a stub criterion) from a neutral brief; the skeletons are hashed before any criterion exists. A *criterion author* per class writes the briefs and, after the commit, only the two criterion bodies. The criterion author may pre-check the **fixed** criterion in plain Python, never the faulty one. Every brief, attempt, drop and pre-check is logged and reported. | Removes the author's knowledge of the error from the declarations that most detections rely on. |
| 3 | The 30-minute rule is replaced by a plain-Python estimate before the freeze (at most 15 minutes, formula in §2). After the freeze a run beyond 60 minutes counts as a miss or a failed clean pass; run times are reported. | A rule that cannot be checked before the freeze cannot be a construction rule. |
| 4 | §6 states that 10 pairs require 9 of 10 on both rates, that every non-dropped pair counts, and that the intervals are the result, the verdict a summary. | |
| 5 | Encoding rules (§2): group, subject and time structure in array axes, not in integer codes; binary labels as `bool`; positive claims only (the criterion holds when the effect is present). World and criterion authors may simulate the noise and zero probes as documented in `GATE.md`. Fixed-twin failures are reported by flag. | |
| 6 | Decision rules per class (§1); the designer assigns each pair's class from its brief before the audit; B-2 reported per subtype. | |
| 7 | B-2 subtype minima: L1.1 ≥ 1, L1.3 ≥ 1, L1.4 ≥ 2, L3.1 ≥ 2, L3.2 ≥ 2. KAP23 may supply up to 8 B-2 pairs (it is the taxonomy covering all subtypes); every other source at most 4 pairs per class. | |
| 8 | Recorded in `docs/design/spec-0.6-REVISIONS-post-freeze.md` as R-36: B-3 becomes "coupled by construction" (mathematical coupling, with §14's "target computed from the labels" as a special case); B-2 is procedure-level leakage with subtype minima; expected flags are listed per class (same content, by design) and the `HIGH_RATE` streams are enumerated per case at the freeze; B-4 is a non-evidence line. | The deviations from §14 must be declared, not implied. |
| 9 | MAK19 read (Europe PMC full text: the ten mistakes include circular analysis, comparisons of two effects without a direct test, inflating the units of analysis). ARC81 read (abstract, Europe PMC). OLD62 is not counted as a source. GEL06 is supporting material for NIE11, not an independent source. Every class still has at least three independent read sources. | |
| 10 | §2 lists the allowed guards; the designer's script flags any comparison of an input's mean, variance or distribution with a constant, for the auditor. | |
| 11 | Baselines: the 0.3.0 tool (expected identical; a sanity check), "flag everything", noise-only, declared-only. | |
| 12 | The fidelity audit is a yes/no checklist (§5); a pair the auditor rejects twice, or disputed, is dropped and reported. | |

## Draft v2 → v3, frozen (2026-11-12)

Answers `REVIEW2.md`. The designer confirmed the shuffle stream name in the code (`probes.shuffle_name` gives
`shuffle:<a>,<b>`, so the flag is `HIGH_RATE:probe:shuffle:<a>,<b>`).

| # | Change | Reason |
|---|---|---|
| B1 | `minus` follows a **fixed rule** applied by the world author: the claimed quantity at its null, everything else as in `plus` (for "one effect exceeds another": equal effects). Briefs state no negation. Faulty criteria use the documented parameters. Criterion authors may not run, simulate or pre-check the faulty criterion in any form. Sizes in briefs must lie within the source's range (audit item f). | Nobody chooses the negation; the author cannot tune the faulty variant against the worlds. |
| B2 | Audit item (e) is mechanical: a list of banned terms checked by script, and no negation in the brief. I-4 states that the world author may still infer the class from the claim's form. | Stated as a limit, not claimed as solved. |
| B3 | BAR05 moves to B-1 (selection on a noisy measurement is a form of circular analysis). B-3's third source is KRO93 (read: abstract). The B-2 rule covers resubstitution (L1.1). Subtype ties: copied rows L1.4, synthesised rows L1.2, selection before CV L1.3; the designer assigns subtypes. | Removes the contradictions; B-3 has three independent read sources. |
| B4 | No change to the counting; I-5 states that MAK19 counts in two classes and that the structured B-2 subtypes rest mostly on KAP23. | |
| B5 | Timing uses the fixed criterion only; the formula is derived in the text (`2 × 200 × (S + 1) × (t + g)`); audit item (g) requires the same computational structure for both twins. | |
| B6 | Shuffle name verified. The world author may declare relational pairs and a `null` world; whether it declares a label-shuffle control is part of the declared-world limit (I-4). | |
| B7 | K2-only detections are labelled and reported separately. | |
| B8 | Fixed-criterion pre-checks and the number of revisions are logged per pair. | |
| B9 | The post-run audit answers three yes/no questions per pair (§7). | |
