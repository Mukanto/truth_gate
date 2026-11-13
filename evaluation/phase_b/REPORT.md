# Phase B report: external evidence

Pre-registration: `PREREG_PHASE_B.md` v3 (`FREEZE_PREREG.json`, core `31F2415AB2990D37`). Cases and expected flags:
`FREEZE_CASES.json` (core `0811095AA6F7E824`); record: `FREEZE_RECORD.json` (core `21E1520ADD1F0C18`). The frozen
state was pushed to the public repository as commit `fe86e96` before the gate ran (`REVISIONS-post-freeze.md`, P-6).
Run on 2026-11-13: Truth_Gate at tag `v0.4.0` (commit `62fd9e3`) and the comparator at tag `v0.3.0` (`627e34c`), full
mode, every file, one check at a time, by `run_phase_b.py`. Every number below comes from `run/RESULTS.json`; the
designer recomputed them from the certificates with a separate script written without reading the runner
(`run/recompute_designer.py`), with **0 differences** over the 54 pairs.

Sections 1 to 4 are the pre-registered results. Section 5 is interpretation, written after the run and labelled as
such. Section 6 lists the limits.

## 1. Result

| Class | Pairs | Detections (generic / declared / K2-only) | Clean passes | Wilson lower bound, detection | Wilson lower bound, clean pass | Verdict |
|---|---|---|---|---|---|---|
| B-1 circular analysis | 12 | 7 (3 / 4 / 0) | 7 | 0.356 | 0.356 | **FAILS** |
| B-2 procedure-level leakage | 12 | 7 (5 / 2 / 0) | 11 | 0.356 | 0.699 | **FAILS** |
| B-3 coupling by construction | 12 | 8 (5 / 3 / 0) | 8 | 0.432 | 0.432 | **FAILS** |
| B-6 inflated-size decision rules | 12 | 11 (0 / 11 / 0) | 11 | 0.699 | 0.699 | **HOLDS** |
| Out of scope (O-1 to O-3) | 6 | 2 (1 / 1 / 0) | 5 | – | – | no threshold |

One-sided 95% Wilson bounds; a class holds when both lower bounds are at least 0.6 (with 12 pairs: at least 11 of 12
on both). B-2 per subtype (2 pairs each, no verdict): L1.1 2 detected / 2 clean, L1.2 1 / 2, L1.3 1 / 2, L1.4 2 / 2,
L3.1 0 / 1, L3.2 1 / 2. B-4 and B-5: no documented cases; no evidence either way.

**Answer to the pre-registered question (§0).** Truth_Gate 0.4.0, with worlds and controls declared by someone who
did not know the error, met the pre-registered bar for one of the four in-scope classes: B-6 (a difference claimed from
"significant here, not there"; non-independent units counted as independent). It did not meet it for B-1, B-2 or B-3.
Over the 48 in-scope pairs it detected 33 faulty criteria (13 through its own noise probe, 20 through the declared
streams) and passed 37 fixed ones.

## 2. Baselines (same files)

| Baseline | B-1 det / clean | B-2 | B-3 | B-6 | Verdicts |
|---|---|---|---|---|---|
| Truth_Gate 0.3.0 | 7 / 7 | 7 / 11 | 8 / 8 | 11 / 11 | identical to 0.4.0 on all 108 files (as expected) |
| Flag everything | 12 / 0 | 12 / 0 | 12 / 0 | 12 / 0 | FAILS everywhere (clean pass) |
| Noise probe only (detection) | 3 | 5 | 5 | 0 | FAILS everywhere |
| Declared streams only (detection) | 7 | 6 | 7 | 11 | B-6 would hold on detection |

The noise probe, which needs no declaration, found 13 of the 33 in-scope detections, none in B-6. Every B-6 detection
came from the declared `minus` world or control (`K2_HIGH_SIZE`, `HIGH_RATE:control:<id>`). No detection was K2-only.

## 3. Awareness of the world author (descriptive, P-1)

| Level (from the world log, frozen before any criterion) | In-scope pairs | Detected | Clean passes |
|---|---|---|---|
| P: the log names how `minus` could still support the claim | 41 | 30 (generic 11, declared 19) | 31 |
| C: considered, nothing left in `minus` | 3 | 0 | 2 |
| N: no sign | 4 | 3 (generic 2, declared 1) | 4 |

Per class: P — B-1 12 pairs / 7 detected, B-2 8 / 5, B-3 10 / 8, B-6 11 / 10; C — B-2 1 / 0, B-3 2 / 0; N — B-2 3 / 2
(both by the noise probe), B-6 1 / 1 (declared). Out of scope: P 4 / 2, C 2 / 0. No pair whose world author
considered the artefact but left none in `minus` was detected. This is what limit I-4 predicts: declared detections depend on the declared worlds
containing what the error exploits.

## 4. Run

216 checks (108 per version), no timeout; per check 0.38 to 29 s with v0.4.0 (median 0.53 s). Of the 54 faulty files 35
were NOT_FALSIFIABLE (every one with an expected flag), 14 WEAK and 5 UNDEFINED; of the 54 fixed files 1 was
FALSIFIABLE, 41 WEAK, 7 NOT_FALSIFIABLE and 5 UNDEFINED. All 41 WEAK fixed files carry `K5_INCONCLUSIVE:zeros`: the
allowed zero-variance guard makes the criterion UNDEFINED on the all-zeros probe.

## 5. Misses and failed clean passes (interpretation, written after the run)

Rates are HOLDS counts out of 200 samples per stream from the certificates; "u" is the number of UNDEFINED outcomes.

**5.1 K1 turned five flagged B-1 criteria into UNDEFINED.** B1-04, B1-05, B1-06, B1-07 and B1-08: the faulty
criterion holds in a large share of the `minus` samples on which it is defined (B1-04 27 of 27, B1-05 29 of 29, B1-06
86 of 168, B1-07 109 of 196, B1-08 132 of 132) and carries expected flags (`K2_HIGH_SIZE`, `HIGH_RATE` on the control
and on the noise probe; B1-07 also `K5_HOLDS_ON_NOISE`, with 191/200 on noise). But the criteria use the allowed guard
"empty selection returns UNDEFINED", and K1 makes the study UNDEFINED as soon as any outcome on `plus` or `minus` is
UNDEFINED; in B1-07 four UNDEFINED `minus` samples out of 200 were enough. The same rule made the fixed twins of B1-04,
B1-05, B1-06 and B1-08 UNDEFINED, and the fixed twin of B2-09 (a chronological split that leaves one class empty in 17
`plus` samples): five failed clean passes that come from the guard in the fixed criterion meeting K1, not from the
skeleton. B1-04 and B1-05 are the two pairs repaired in the fidelity audit to the source's threshold `p < .01`; the
stricter threshold left the selection empty in 173 and 171 of 200 `minus` samples. *Post hoc, not a pre-registered
number:* these five faulty files carry the flags of a detection, and without K1's rule B-1 could have reached 12 of 12
detections; its clean passes would still have been at most 11.

**5.2 The error was too small in the declared worlds (faulty WEAK, no expected flag).** B2-03 (selection before
cross-validation on 60 genes: the bias that AMB02 documents with thousands of genes is small at the 60-feature cap;
faulty holds in `minus` 9/200), B2-06 (oversampling before the split: 0/200), B2-09 and B2-10 (shuffled folds on time
series: 3/200 and 2/200), B2-12 (patients of the same hospital on both sides of the split: 0/200), B3-06 and B3-10 (the
faulty statistic is the claim's own ratio statistic, and the worlds generate the per-capita and per-weight values
directly, so the ratios recomputed from the totals carry no shared error: 0/200 and 2/200), B3-09 and B3-12 (the world
author considered a ratio artefact and left none: 0/200 and 0/200), B6-10 (the pattern "significant in one condition,
not in the other" occurred in 10/200 `minus` samples, near the nominal level). In these pairs the faulty criterion fails in
`minus` at or below the nominal rate, and the gate's verdict describes the criterion as it behaves on the declared
worlds. The miss shows that the declared world did not contain enough of what the error exploits; it is not a criterion
that held in `minus` unnoticed.

**5.3 Fixed criteria that the skeleton defeats** (all reported by the criterion authors from their pre-checks before
the audit, P-3): B3-05 (fixed holds in `minus` 34/200: shared body size and a noisy common denominator remain after
partialling), B3-07 (23/200), B6-08 (51/200: a linear drift shared by both measurements in both worlds), B3-11 and
B3-12 (fixed holds in `plus` 4/200 and 1/200). In B3-11 and B3-12 the correction tests a different quantity (the
association after the denominator is held fixed) from the one the world author made true (the raw ratio); the claim as
the world author read it is true in `plus`, the corrected claim is not. This is a general difficulty of B-3 cases: the
documented correction changes the estimand, so a clean pass depends on the world modelling the effect at the corrected
level.

**5.4 A fixed criterion that holds on noise.** B1-02: the fixed orientation-selectivity criterion holds on the noise
probe in 21/200 samples, above the declared size, so the gate calls it NOT_FALSIFIABLE (`HIGH_RATE:probe:noise`).

**5.5 Out of scope.** Detected: O1a (an illegitimate feature recorded after the diagnosis; the world kept that
dependence in `minus`, so the faulty criterion holds there: `K2_HIGH_SIZE`) and O2a (the best of three analyses: its
false-positive rate shows on the control and on the noise probe). Missed, as expected: O1b, O2b, O3a, O3b. O3b's fixed
twin fails (`K2_HIGH_SIZE`, 34/200 in `minus`: confounding and reverse causation kept in both worlds); its faulty twin
holds in `minus` less often (9/200) than the fixed one, so no stream could have separated them.

Section 5 was corrected after the post-run audit (section 7): the first version said the five B-1 faulty criteria hold
in `minus` "whenever defined", left the B3-12 miss unexplained, counted B2-09's failed clean pass as a skeleton effect,
and called the B6-10 slopes "borderline".

## 6. Limits

* **Who wrote the cases.** Every role (criterion authors, world author, auditors, designer) is a model of the same
  family that wrote the gate and read its documentation. No human domain reader was available. The criterion bodies were
  written by fresh agents from the notes of the agents that wrote the briefs (P-1).
* **Awareness (I-4, P-1).** The world author inferred the error for 45 of 54 briefs. Declared detections show what the
  gate does when whoever declares the worlds anticipates the artefact, not that it finds errors nobody anticipated.
* **Sizes and sources.** Data were capped at 300 rows and 60 features; several sources describe much larger studies
  (P-2 lists the pairs). Some settings are applications of the sources rather than the sources' own studies; ARC81,
  KRO93 and BAR05 were read as abstracts only. MAK19 counts in two classes; the structured B-2 subtypes rest mostly on
  KAP23 (I-5).
* **12 pairs per class.** A class with a true detection rate near 0.85 passes the bar about half the time; the
  intervals in section 1 are the result, the verdicts a summary.
* **Allowed guards and K1.** The pre-registration allowed guards that return UNDEFINED; the gate's K1 rule makes any
  UNDEFINED outcome on `plus` or `minus` decisive. This interaction caused nine of the ten B-1 misses and failed clean
  passes, and one B-2 failed clean pass (5.1). It is a property of the gate as released, reported as found; any change belongs to a later version and its own
  pre-registration.

## 7. Post-run blind audit (PREREG §7)

A fresh agent that wrote nothing in this evaluation read the frozen cases, the certificates and this report, and
answered three questions per pair (`run/POSTRUN_AUDIT.json`, `run/POSTRUN_AUDIT.md`; instructions in
`POSTRUN_AUDIT_INSTRUCTIONS.md`). It ran no gate.

| Class | (i) detection follows from the error: yes / n/a | (ii) failed clean pass comes from the skeleton: yes / no | (iii) sign that a brief steered the worlds: yes |
|---|---|---|---|
| B-1 | 7 / 5 | 0 / 5 | 0 |
| B-2 | 7 / 5 | 0 / 1 | 1 (B2-07) |
| B-3 | 8 / 4 | 4 / 0 | 1 (B3-05) |
| B-6 | 11 / 1 | 1 / 0 | 0 |
| Out of scope | 2 / 4 | 1 / 0 | 2 (O1a, O2a) |

* **(i)** No detection was answered "no": every one of the 33 in-scope detections follows from the planted error. The
  auditor marks some as narrow: B2-05 rests only on the noise probe (22/200); B2-07 and B6-09 only on the control flag;
  in B1-02, B3-05, B3-07 and B6-08 the fixed twin carries a flag of the same name at a much lower rate or for another
  reason.
* **(ii)** Of the eleven in-scope failed clean passes, six come from the fixed criterion (B1-04, B1-05, B1-06, B1-08 and
  B2-09: the allowed UNDEFINED guard meeting K1; B1-02: an index that is unstable on negative-valued noise) and five
  from the skeleton (B3-05, B3-07, B3-11, B3-12, B6-08). O3b's failure also comes from the skeleton.
* **(iii)** Beyond the awareness already recorded (P-1), four briefs or world logs show steering: the B2-07 brief says
  that about a quarter of the rows repeat an earlier entry with its diagnosis (the structure the error exploits); in
  B3-05 the world author kept the artefact near the threshold "on purpose"; the O1a data keys name the variable that
  leaks; the O2a brief names the secondary outcome and its correlation with the primary one. These pairs stay in the
  table; their detections are the weakest evidence in the set.
* The auditor's objections to the first version of section 5 were checked against the certificates by the designer
  and section 5 was corrected (see its last paragraph). The pre-registered table in section 1 is unchanged.
