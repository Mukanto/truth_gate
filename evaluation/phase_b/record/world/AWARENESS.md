# World-author awareness of the error (designer's classification, before any criterion exists)

Written by the designer (Claude, under the author's delegation) on 2026-11-13, after the world author finished and the
mechanical check passed (54/54), **before** any criterion body was written and before any gate run. It is frozen with
the skeletons in `FREEZE_SKELETONS.json`. It changes no rule of the pre-registration: no threshold, no expected flag,
no drop rule. It adds one **descriptive** breakdown to the report, motivated by limit I-4.

## Why

`WORLD_LOG.md` shows that the world author inferred the error mechanism for most briefs and modelled it in the worlds
(for example W01 "the vertebral column length is a shared denominator with its own error", W19 "the classic selection
bias", W31 "200 cells per arm would be pseudoreplication", W54 "a leak: the therapy follows the diagnosis"). The fixed
`minus` rule ("every other quantity keeps its `plus` value") required these structures to stay in `minus`; the world
author also chose their size in `plus` (W01: "I let the artefact stay close to the threshold on purpose"). This is the
contamination that I-4 names, and it is stronger than the pre-registration expected. Declared detections on these cases
show what the gate does when the declared worlds contain the artefact that the error exploits, i.e. when the person who
declares the worlds anticipates it.

## Rule (applied to the text of `WORLD_LOG.md` only)

* **P (planted):** the entry states a mechanism by which an analysis of the `minus` data could still appear to support
  the claim, or reports a non-null value of a naive statistic in `minus`, or names the error.
* **C (considered):** the entry mentions the mechanism or a related analysis pitfall but reports that no such artefact
  is left in `minus` (or that it cannot be represented).
* **N (none):** neither.

Generous reading: when in doubt between N and C, or C and P, the higher level is chosen, so that the N group is as
free of awareness as the log allows.

## Classification

| Level | Ids | Count |
|---|---|---|
| P | W01 W02 W04 W05 W06 W07 W08 W09 W10 W12 W13 W14 W15 W16 W17 W19 W20 W21 W22 W24 W25 W26 W27 W28 W29 W31 W32 W34 W35 W36 W39 W40 W41 W43 W44 W45 W46 W47 W48 W49 W50 W51 W52 W53 W54 | 45 |
| C | W03 (stopping rule not representable), W11 (ratio artefact considered, none added beyond the shared headcount), W23 (no natural ratio artefact found), W33 (scale differences that hurt unstandardised PCA), W37 (an equally persistent unmeasured driver) | 5 |
| N | W18 W30 W38 W42 | 4 |

## Reporting

The report gives, per level and per class, the number of pairs, detections (generic / declared / K2-only) and clean
passes. No interval or verdict is computed per level (the N and C groups are far too small); the breakdown is
descriptive and labelled as such. The headline and the class verdicts are unchanged and are stated together with this
table.

## Process notes on the world author (from its final message)

* It read `WORLD_INSTRUCTIONS.md`, `BRIEFS_SHUFFLED.json`, `docs\GATE.md` and `docs\SPEC.md` (not `README.md`, not
  `docs\MANIFEST.md`), and imported `kapi` only to build each `Study`.
* It wrote throw-away helper scripts to the system temporary folder (outside this folder) and deleted them; they
  computed shapes, timings and descriptive quantities only. No classifier, cross-validation or test statistic was run.
* This was the second world-author agent: the first stopped at a rate limit having written no skeleton, and could not be
  resumed after a session change; the second started from the same files and instructions.
