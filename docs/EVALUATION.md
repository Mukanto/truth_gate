# Evaluation

> **Name.** Truth_Gate was called Kapı (Turkish for "gate") until its first public release on 2026-11-12. This
> record keeps the name used at the time. The Python package is still imported as `kapi`.

This page reports every pre-registered evaluation of Kapı, including the failures. The criteria were written down and
frozen before the cases were run (see [`SPEC.md`](SPEC.md), section 12 of the v0 spec and the evaluation sections of the
deltas). Where a criterion failed, it is reported as failed; no criterion was changed after its results were known.

Read this page with the limitation in mind: **the evaluation cases were written by AI sessions that knew the
specification (same model family). There is no human-authored external benchmark.**

## How the evaluation works

A *case* is a pair of study files: a **faulty** twin with one known flaw, and a **fixed** twin without it. Each case
states which check should catch the flaw. A faulty case is *detected* if its verdict is NOT_FALSIFIABLE or UNDEFINED and
at least one expected check was raised. A fixed twin is *cleared* if its verdict is FALSIFIABLE or WEAK. Criteria are
named `P1a`, `P2a`, ... (see the spec for each definition) and each is reported as **held** or **failed**, with the
count behind it. The harness that computes them is in `eval/`; it prints the Turkish words `Tuttu` (held) and
`Tutmadı` (failed).

The case sets are in `evaluation/cases/` and are published unchanged. Each set has a `CASES_SHA256.json` that was
written before the first run, and a `manifest.json` with the expected checks.

| Set | Role | Written by |
|---|---|---|
| E1E3 | E1: self-authored reconstructions of documented incidents; E3: two reconstructions of published cases. **Not published:** E1 reconstructs incidents from the author's unpublished research. Its results are reported here; the files are withheld | the drafting session |
| E2 | independent set, written from the spec text only | an independent reviewer session (Tenkit) |
| E4 | independent set with false-positive inflation, weak twins and adversarial cases | the independent reviewer session, spec text only |
| E5 | independent set for the identical-minus check, written from the spec text only | the independent reviewer session |

## v0 (spec 0.3, package 0.1.0)

| Criterion | Result |
|---|---|
| P1a | held, 26/26 |
| P1b | held, 14/14 |
| P1c | held, 23/23 |
| P2a | held, 26/26 |
| P2b | held, 14/14 |
| P3 | held, 3/3 |
| **P4** | **failed, 51/52** |

**P4 failed.** The criterion was that every case, run twice with `verify`, gives an identical `body_sha256`. The
designer defined it wrongly: it demanded identical hashes from a case that was deliberately non-reproducible, and the
gate correctly flagged that case. The criterion was not changed after the results; v0.2 introduced a corrected
criterion (P4') for later evaluations and the v0 result stays as failed.

## v0.2 (spec 0.4, package 0.2.0)

Changes under test: the declared alpha became mandatory, and cascade suppression was added. Regression set R is E1E3 and
E2 (known outcomes, so only a regression check); E4 is new.

All 9 pre-registered criteria held:

| Criterion | Result |
|---|---|
| P1a | held, 16/16 |
| P1b | held, 8/8 |
| P1c | held, 16/16 |
| P2 | held, 16/16 |
| P3 | held, 1/1 |
| P4' | held, 84/84 |
| P5 | held, 5/5 |
| R1 | held, 26/26 |
| R2 | held, 26/26 |

## Retrospective pilot (v0.2)

Twenty-five past studies by the author were converted **blind** into Kapı studies, giving 120 labelled units. Four of the five pilot criteria failed.

| Criterion | What it measures | Result |
|---|---|---|
| PP1 | in-scope flaws that were found after the fact, caught | failed, 3/7 |
| PP1d | declared tautologies, caught | failed, 11/16 |
| PP2 | clean criteria that passed | failed, 7/75 |
| PB | out-of-scope flaws that were not flagged | failed, 1/12 |
| PP3 | conversion fidelity | held, 118/120 |

**What a case review found.** Of the 37 clean units that were flagged, 35 are explained by how the converter built the
test worlds, not by defects in the criteria: weak or no-op `minus` worlds, and structural `plus` worlds. This is a
finding about world construction, and it is also a warning that a gate is only as good as the worlds the user
declares. It led to v0.3 and its new `UNTESTED` verdict for identical `minus` worlds. The pilot studies and their
certificates are private and are not published.

## v0.3 (spec 0.5, package 0.3.0)

New verdict `UNTESTED` for a `minus` world that is identical to `plus`. The new independent set E5 tests it; regression
set R is E1E3, E2 and E4.

| Criterion | Result |
|---|---|
| Q1 (identical minus detected) | held, 6/6 |
| Q2 (an unread change is not masked) | held, 5/5 |
| Q3 (traps stay NOT_FALSIFIABLE) | held, 5/5 |
| Q4 (near-identical worlds are not UNTESTED) | held, 4/4 |
| Q5 (`K2_MINUS_UNREAD` raised) | held, 5/5 |
| Q6 (clearance of fixed twins) | held, 15/15 |
| P4' (reproducibility) | held, 119/119 |
| R2 (regression, fixed twins cleared) | held, 42/42 |
| **R1** (regression, faulty cases detected) | **failed, 41/42** |

**R1 failed.** One regression case whose declared change was not implemented is now UNTESTED by design. The pre-registered rule counts an UNTESTED regression case as not detected, so the
criterion failed by one case. The criterion was not changed. This is the intended behaviour of the new verdict, and it
is also a visible cost of the change.

Some of the criteria above (Q2 to Q4) rest on very small denominators and are reported as they are.

## Prospective pilot (v0.3): one study, a case study, no rates

Kapı v0.3 was then used in one real study, from pre-registration to blind audit. It is described in
[`CASE_STUDY_PROSPECTIVE.md`](CASE_STUDY_PROSPECTIVE.md). One study gives no rates. What it showed:

* **First certificate (I1).** Kapı raised 10 flags. 6 were real and were fixed: missing controls, a bug in a control
  transform, and a `minus` world that could not fail one criterion. 4 were rejected with written reasons: vacuity probes
  applied to a precomputed scalar and to a conditional criterion.
* **Blind audit (I2).** A blind auditor made 8 substantive findings. Kapı had
  fully flagged 0 of them and partially touched 2.
* **Clean certificate, caveated verdict (I3).** The one criterion with a clean final certificate still had 3 audit
  caveats: dependence on a model interpretation, an unrealistic synthetic world, and a decision resting on two grid
  points.

## Second prospective case: GHZ states on IBM hardware (v0.3; a case study)

A pre-registered hardware study ([`examples/ghz_heron/`](../examples/ghz_heron/REPORT.md)): GHZ fidelity on a 156-qubit
Heron r2 processor against an independent-error model built from the device's calibration.

* **Kapı before the freeze.**
  * The first certificate raised 7 distinct flags on 3 criteria, all real and all fixed: missing controls, the grid passed as
    data, and a vacuous equality.
  * The second certificate raised 1 flag, a mis-sized control (a designer error), fixed.
  * The probes that produced non-positive model predictions were rejected with reasons.
  * The final certificate was WEAK.
* **Blind audit after the run.** The critical defect was a mismatch between the model and the estimator (readout error applied
  once to a fidelity whose coherence part loses it twice). Correcting it reverses two of the three pre-registered verdicts.
  Kapı could not see it: the defect is in the model, outside Kapı's scope. The audit also found a one-sided band and a
  directional hypothesis that generic error confirms.
* **Same pattern as the first case.** Kapı caught real defects in the logic of the criteria. The decisive defect sat in the model
  and was found by the blind audit and independent recomputation.

### Run 2 of the hardware study

A corrected model was pre-registered and run once on new shots ([`examples/ghz_heron_run2/`](../examples/ghz_heron_run2/REPORT.md)).
* **Kapı before the freeze.** 2 actionable flags, both fixed: a criterion that held on random data, and a control that a
  fix had made inconsistent. The designer caught 3 errors in their own first draft before any certificate.
* **After the run.** The blind audit found four decisive weaknesses, all outside Kapı's scope:
  * the device had not been recalibrated, so the run was a data replicate, not a model test;
  * run-to-run drift exceeded the shot-noise intervals at small n;
  * the confirmatory test had low power;
  * one identification argument was incomplete.
  It also found that one of the designer's controls guarded against a failure that cannot affect the estimator.

### Run 3 of the hardware study: the model test (Truth_Gate 0.5.0, 2026-11-16)

Run 2's frozen design was run once more after the calibration had changed, as the first out-of-sample test of model M2
([`examples/ghz_heron_run3/`](../examples/ghz_heron_run3/REPORT.md)). The pre-registration was frozen and pushed before
the submission, after three reviews by fresh agents. Those reviews found 2 blocking and 12 major defects (power misread,
a new-calibration condition that did not guarantee a model test, forking paths at submission, no verdict mapping, no
check of the calibration at execution), all fixed before the freeze. Kapı raised no actionable flag.
* **Pre-registered answer.** The controls passed and the result is interpretable.
  * H1 (M2 accurate within 0.05 for 4 and 8 qubits) FAILS, labelled "within drift". Only n = 8 exceeds the band, by
    0.016.
  * H4 (M2 overpredicts at every n) HOLDS.
  * Reported only: the GME reach fell to 8 qubits with confidence (16 in runs 1 and 2), and H3's direction reversed.
* **After the run.** The blind audit localised most of the shortfall to two qubits whose readout or relaxation error at
  execution was far above their calibration: qubit 89 (15–18% against 5%) and qubit 72 (21–32% against 4%).
  * The calibration record was 3.6 days old.
  * Q1's status as a model test rested on qubit 89's readout entry.
  * The "fails" reading of H1 is not robust to the pre-registered "drift × 2" sensitivity row.
  * H4 shows that the fidelity was below M2's prediction at every n on this calibration. It does not show that the
    flat bias of runs 1 and 2 persisted.
  * None of K1–K3 can detect such qubit faults; the audit found them in the run's own population counts.
* **Process.** The run plan's step of publishing the submission record before fetching the data was skipped, and the
  code did not enforce it. A separate recomputation and the audit reproduced every number.

## 0.4 (spec 0.6, package 0.4.0): Phase A

Phase A checks that 0.4 keeps 0.3's behaviour and that its new parts give the same answers as hand-written studies.
It is an internal check on the project's own examples, not external evidence. The criteria were written and frozen
before implementation ([`design/spec-0.6.md`](design/spec-0.6.md), section 14; freeze `design/FREEZE_SPEC_0.6.json`).
The 0.3.0 results were recorded from tag `v0.3.0` before any code changed and frozen
(`../evaluation/FREEZE_BASELINE_V030.json`).

| id | Claim | Result | |
|---|---|---|---|
| A1 | Python studies behave exactly as in 0.3 | **HOLDS** | 159 of 159 studies (95 evaluation cases, 55 test studies, 9 examples) give the same certificate body as 0.3.0 after the pre-registered strip rule; for the 4 studies that use unseeded randomness on purpose, the same verdict and flags |
| A2 | Manifests reproduce hand-written studies | **HOLDS** | 7 of 7 pairs (examples 01, 02 and 03, both twins each, and the convergence study): same verdict, flags and tolerance declarations. The required coverage was met: the criteria of example 03 and C3 of the convergence study are patterns, and every control and premise of examples 01–03 is a mutation |
| A3 | Any language gives the same answer | **HOLDS** | 6 of 6 pairs: the criteria rewritten as Node programs give the same verdict, flags (apart from `K2_MINUS_UNREAD`) and per-stream counts as the A2 manifests, over 200 samples per stream |
| A4 | K8 catches order dependence and changes the verdict | **HOLDS** | The faulty twin (reads the first 10 of 40 exchangeable rows) changed its outcome under row permutation in 34 of 200 plus samples (Wilson lower bound 0.124 > 0.05): NOT_FALSIFIABLE with `K8_NOT_INVARIANT` as its only mandatory flag; without K8 it would have been FALSIFIABLE. The fixed twin (mean of all rows) was FALSIFIABLE and never changed |

**How the results were obtained.** The evaluation scripts in [`../evaluation/`](../evaluation/) produced the results,
and the designer recomputed all four with separate scripts. Environment: Python 3.14.2, numpy 2.4.1, Node 26.12.1,
Windows 11. Four tests that need a POSIX system were skipped.

**What happened on the way, without changing a criterion:**

* The specification went through three blind reviews before the freeze. The first found 19 problems, two of them
  critical. The third found one that blocked the freeze: A1 could not be met as written for studies with unseeded
  randomness.
* During implementation, 34 points that the frozen text left open were decided and logged with reasons
  ([`design/spec-0.6-REVISIONS-post-freeze.md`](design/spec-0.6-REVISIONS-post-freeze.md)). The coding agent stopped
  and asked each time instead of choosing.
* A blind audit of the code found two real defects, both reproduced and fixed before the final run. A command criterion
  whose own child process held its output pipe made `check` hang. A blank line in a single-column CSV file was dropped
  instead of read as a missing value. The audit also found that A2 and A3 had left out the fixed twin of example 02,
  which section 14 includes. It was added before the final run (revision R-34).

**What Phase A does not show.** It says nothing about whether the gate catches real errors in real studies. That is
Phase B: an external test set built from errors documented in the literature, with criteria pre-registered before the
set is built (section 14 of the spec).

## 0.4 (spec 0.6, package 0.4.0): Phase B, errors documented in the literature

Phase B asks whether Truth_Gate 0.4.0, with worlds and controls declared by someone who does not know the error, flags
acceptance criteria that contain errors documented in published research, and passes the corrected criteria. The rules
were pre-registered and frozen before any case existed ([`../evaluation/phase_b/PREREG_PHASE_B.md`](../evaluation/phase_b/PREREG_PHASE_B.md));
the cases were frozen and pushed (commit `fe86e96`) before the gate ran. Full report:
[`../evaluation/phase_b/REPORT.md`](../evaluation/phase_b/REPORT.md).

**How the cases were built.** Each case is a pair of studies, a faulty criterion with a documented error and a fixed
one with its correction, in the same skeleton. Three roles kept the error away from the worlds: criterion authors who
knew the error wrote neutral briefs; one world author who saw only the shuffled briefs wrote the worlds and controls
(`minus` sets the claimed quantity to its null, everything else unchanged); the criterion authors then wrote only the
two criterion bodies and could pre-check only the fixed one. A blind fidelity audit passed all 54 pairs after one
repair round.

| Class (sources) | Pairs | Detected | Clean passes | Wilson lower bounds | Verdict |
|---|---|---|---|---|---|
| B-1 circular analysis (KRI09, VUL09, MAK19, BAR05) | 12 | 7 | 7 | 0.36 / 0.36 | **FAILS** |
| B-2 procedure-level leakage (KAP23, AMB02, SIM03) | 12 | 7 | 11 | 0.36 / 0.70 | **FAILS** |
| B-3 coupling by construction (PEA97, ARC81, KRO93) | 12 | 8 | 8 | 0.43 / 0.43 | **FAILS** |
| B-6 inflated-size decision rules (NIE11, HUR84, LAZ10, MAK19) | 12 | 11 | 11 | 0.70 / 0.70 | **HOLDS** |
| Out of scope (data-level leakage, flexibility outside the criterion, data errors) | 6 | 2 | 5 | – | no threshold |

A class holds when both one-sided 95% Wilson lower bounds are at least 0.6. Truth_Gate 0.3.0 gave the same verdict on
all 108 files. Of the 33 in-scope detections, 13 came from the gate's own noise probe and 20 from the declared `minus`
world or control; every B-6 detection came from declarations. A blind post-run audit found that every detection
follows from the planted error.

**Why the three classes failed (interpretation, after the run).**

* **B-1:** five faulty criteria carried the flags of a detection but ended UNDEFINED, and four fixed ones too: the
  criteria return UNDEFINED when a selection is empty (an allowed guard), and K1 makes a study UNDEFINED as soon as
  one outcome on `plus` or `minus` is UNDEFINED. (Truth_Gate 0.5.0 changes this K1 rule, spec 0.7: a criterion's own
  UNDEFINED outcome counts as no claim, and only a failure or abstention on more than half of the `plus` samples gives
  `K1_UNDEFINED`. The Phase B record above describes 0.4.0 and is unchanged.)
* **B-2:** in five pairs the documented leak was too small in the declared worlds at the size cap (60 features, 300
  rows) for the faulty criterion to hold where the claim is false.
* **B-3:** four misses came from worlds without the shared measurement error that makes ratios couple; four fixed
  criteria failed because of the skeleton, two of them because the correction tests a different quantity than the one
  the world made true.

**What Phase B does and does not show.** The gate flagged documented errors when the declared worlds contained what the
error exploits, and only then. The world author, a model of the same family, inferred the error from the claim for 45
of the 54 briefs and kept the corresponding structure in `minus`; none of the pairs where it considered the structure
but left none was detected. Every role was played by models of the same family that wrote the gate; no human domain
reader took part. Twelve pairs per class give wide intervals. The result is evidence about the gate together with
anticipated declarations, not about finding errors nobody anticipated.

## 0.5 (spec 0.7, package 0.5.0): regression check

0.5.0 changes only how K1 treats a criterion's own UNDEFINED outcomes. Its pre-registered regression check (spec 0.7
section 6, R1) compared 0.5.0 with a frozen 0.4.1 baseline on 267 studies (the 159 studies of Phase A criterion A1 and
the 108 Phase B files), before the release was pushed: every component had the result that the spec's compatibility
statement prescribes, and no 0.4.1 detection or clean pass changed. Eleven components that 0.4.1 made UNDEFINED only
through abstentions now have verdicts: ten Phase B components (R2, five faulty twins detected, five fixed twins WEAK,
development data, not evidence, because the rule was chosen after these cases were seen) and one older evaluation case,
`E2-07_faulty`, which moves from UNDEFINED to WEAK. Details: [`../evaluation/r1_v050/RESULTS.md`](../evaluation/r1_v050/RESULTS.md).
Evidence for 0.5 on new cases is the job of Phase C (next section).

## 0.5 (spec 0.7, package 0.5.0): Phase C, documented errors with worlds by a different Claude model line

Phase C asks Phase B's question of Truth_Gate 0.5.0, with two changes. The worlds and controls were declared by Fable,
a different Claude model line from the one that wrote the gate and the criteria, which was not told the error, the class
or the source. And 0.4.1 ran on the same files, to measure what spec 0.7 changes. The rules were pre-registered and
frozen before any case existed ([`../evaluation/phase_c/PREREG_PHASE_C.md`](../evaluation/phase_c/PREREG_PHASE_C.md));
the cases were frozen and pushed (commit `aecd613`) before the gate ran. Full report:
[`../evaluation/phase_c/REPORT.md`](../evaluation/phase_c/REPORT.md).

**How the cases were built.** As in Phase B, with fresh agents in separate sandboxes: brief authors per class (at least
4 of 12 pairs per class on sources new to Phase C), Fable world authors in batches of 15 shuffled briefs, criterion
authors who wrote only the two criterion bodies, and a blind fidelity audit per class (nine items) with one repair round.
Two B-3 pairs were dropped for brief or size defects; 52 pairs remained.

Awareness P / C / N gives, per class, how many declared worlds may contain what the error exploits (P), how many were
considered and left without it (C), and how many show no sign (N). Every verdict below holds with these shares.

| Class (sources) | Pairs | Detected | Clean passes | Wilson lower bounds | Awareness P / C / N | Verdict (0.5.0) |
|---|---|---|---|---|---|---|
| B-1 circular analysis (MOR03, KRI10, KRI09, VUL09, MAK19, BAR05) | 12 | 12 | 11 | 0.82 / 0.70 | 10 / 2 / 0 | **HOLDS** |
| B-2 procedure-level leakage (KAP23, VAR06, AMB02) | 12 | 7 | 8 | 0.36 / 0.43 | 10 / 2 / 0 | **FAILS** |
| B-3 coupling by construction (CUR13, PEA97, ARC81, KRO93) | 10 | 8 | 8 | 0.54 / 0.54 | 10 / 0 / 0 | **FAILS** |
| B-6 inflated-size decision rules (LAZ18, NIE11, HUR84, LAZ10, MAK19) | 12 | 10 | 12 | 0.60 / 0.82 | 12 / 0 / 0 | **HOLDS** |
| Out of scope | 6 | 2 | 6 | – | 5 / 1 / 0 | no threshold |

Of the 37 in-scope detections, 18 carry a flag of the gate's own noise probe and 19 only flags of the declared streams;
every B-6 detection came from declarations. B-6 holds at the edge: 10 of 12 is the fewest detections that pass with 12
pairs.

**What 0.5.0 changed (primary comparison).** Eight files, the twins of four B-1 pairs, had a component that 0.4.1 made
UNDEFINED, every one through abstentions only (an allowed "empty selection" guard). Under 0.5.0 the four faulty twins
are detected and the four fixed twins pass. Nothing was lost, and the other classes are identical. Under 0.4.1, B-1
fails on the same files (8 of 12 detected, 7 of 12 clean; awareness P 10, C 2, N 0 of 12). The B-1 verdict therefore
depends on 0.5.0's abstention rule.

**Why two classes failed (interpretation, after the run).**

* **B-2:** five of the seven KAP23 pairs (oversampling before the split, random folds on time series, records of one
  person on both sides) were misses labelled "error too small in the declared worlds at this size"; in three of them
  the low-capacity model of both twins also lets little leak. The four VAR06
  pairs (tuning without nested cross-validation) were all detected. Their fixed criteria failed, because the claims'
  thresholds are reached by chance with 40 samples: the corrected criteria hold on pure noise in 25 to 65 of 200
  samples.
* **B-3:** two misses were too small in the declared worlds. Two fixed criteria failed at this size: B3-04's threshold
  has a large sampling spread, and B3-12's test ignores autocorrelation in the months. The B3-12 detection rests on a
  flag that its fixed twin carries at the same rate.

A blind post-run audit by a fresh agent found one detection that does not follow from the planted error (B3-12). In
five more (B2-08 to B2-11, B3-04) the fixed twin carries the same expected flags at lower or similar rates; none of
these six is in B-1 or B-6. It found brief steering in one in-scope pair (B3-09, whose detection stands without it) and
two out-of-scope pairs. Its objections to the first version of the report were checked and the report corrected; the
pre-registered table is unchanged.

**What Phase C does and does not show.** Phase C repeats Phase B's pattern with a world author from a different Claude
model line: the gate flagged documented errors when the declared worlds contained what the error exploits. 47 of the 52
declared worlds may contain it (15 of these count as P because their batch stopped before writing a log). Fable is not
a different vendor or family. Brief and criterion authors, auditors and designer are of the line that wrote the gate,
and no human domain reader took part. With 10 to 12 pairs per class the intervals are wide, and 19 of the 46 in-scope
pairs overlap Phase B. Every fixed file is at best WEAK, because the allowed zero-variance guard abstains on the
all-zeros probe.

## Limitations of the evaluation

* **Not independent of the specification.** All case sets were written by AI sessions that had read the spec, and from
  the same model family as the drafting and coding sessions. Independence means "did not see the implementation", not
  "different kind of author".
* **No human-authored external benchmark.**
* **Synthetic cases.** Faulty twins carry one planted flaw. Real flaws are messier.
* **Small denominators.** Several criteria rest on a handful of cases.
* **The retrospective pilot used conversions made by the same project**, and the review that explains most of its
  failures was also made by the project.

## Bottom line

Kapı reliably checks the logic of criteria against synthetic worlds. It does not detect flaws in model
interpretation or in the real run's controls. In the prospective study, pre-registration, negative controls, a blind
audit and independent recomputation found the major defects. On errors documented in the literature it met the
pre-registered bar for one class of four in Phase B (0.4.0: B-6, awareness P 11, C 0, N 1 of 12). In Phase C (0.5.0,
worlds by a different Claude model line) it met the bar for two of four: B-1 (P 10, C 2, N 0 of 12) and B-6 (P 12 of
12). In both phases its detections depended on declared worlds that may contain what the error exploits. The gate was one part of that process, which is why the
methods protocol in [`../protocol/`](../protocol/PROTOCOL.md) is published with it.
