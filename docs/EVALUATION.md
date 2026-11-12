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
audit and independent recomputation found the major defects. The gate was one part of that process, which is why the
methods protocol in [`../protocol/`](../protocol/PROTOCOL.md) is published with it.
