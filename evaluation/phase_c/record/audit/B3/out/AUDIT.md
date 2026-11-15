# Fidelity audit, Phase C, class B-3 (blind auditor)

Date 2026-11-15. Instruction file `AUDIT_PHASE_C.md`. Twelve pairs (B3-01 to B3-12). **Result: 10 pass, 2 fail**
(B3-07 item (f), B3-10 item (h)). In both failed pairs the defect is in the brief or its sizes, not in the criterion
bodies. The criterion author cannot repair it, so under PB §5.3 both pairs are dropped after the repair round.

No criterion was called on any data, no case file was imported or run, and Truth_Gate was not run. One helper computation
was run in isolation (`scratch\audit_checks.py`, `py -I`). It contained:
(1) a banned-term scan of the 12 briefs;
(2) a text comparison of each twin with its skeleton outside the criterion body;
(3) a list of the import lines and of any file, network, process or randomness tokens in the bodies;
(4) a copy of the Student-t tail routine used in B3-01 and B3-12, checked on known one-sided 5% critical values
(df 1, 2, 5, 10, 30, 45, 46, 60, 117, 120: each gives p = 0.05000) and against scipy (largest absolute error 3.2e-7).

## Mechanical facts confirmed

* All 24 twins equal their skeleton outside the criterion body (prefix and suffix identical).
* The only imports are `numpy` and `truth_gate`.
* No body contains `open(`, `os.`, `sys.`, subprocess, socket, urllib, eval/exec, `np.random` or a reference to `STUDY`.
  No criterion uses randomness.
* Every comparison listed in `MECH_CHECK.json` was judged:
  * B3-03 line 63 and B3-11 line 49 (`flat()`: sum of squares > 0) are zero-variance guards and are identical in both twins.
  * B3-06 lines 82/78 and B3-07 lines 71/66 compare the summary statistic with the threshold of the claim, so they are
    the decision rule.
  * B3-10 line 68 is the label definition taken from the claim (total ≥ 12).
  * None of them is a check for noise, zeros or a shuffle.

## Per pair

**B3-01 (CUR13), pass.**
* The faulty criterion divides heart weight by body mass and compares the quotient between the groups: a one-sided
  pooled two-sample t test, written as OLS on the treatment dummy.
* The fixed criterion is ANCOVA, the correction named in CUR13's abstract: heart weight on treatment and body mass, with a
  one-sided t test of the treatment coefficient.
* The note named a Welch test. The pooled t is a typical form, and with 24 + 24 animals its t value equals Welch's (only
  the degrees of freedom differ). This deviation is disclosed and accepted.
* Guards: non-finite values; residual df < 1; a constant or collinear treatment column; zero variance of y or of the
  residuals.
* Size: 48, not documented by the source.

**B3-02 (CUR13), pass.**
* Faulty: correlation of age with the albumin/creatinine quotient (r ≥ 0.15).
* Fixed: partial correlation of albumin and age given creatinine.
* Both versions share one routine. Size: 800, not documented by the source.

**B3-03 (CUR13), pass.**
* Faulty: R² of systolic pressure on LV mass / BSA.
* Fixed: R² gain of LV mass over BSA.
* The guards differ only in which variables enter each version's statistic. Size: 300, not documented by the source.

**B3-04 (CUR13), pass.**
* Faulty: slope of liver/body mass on kidney/body mass.
* Fixed: kidney coefficient with body mass as a covariate.
* Size: 150, not documented by the source.

**B3-05 (PEA97), pass.**
* This is Pearson's own femur/tibia/humerus example (located in the OCR text).
* Fixed: partial correlation given humerus length.
* Size: 1000 skeletons, which is the source's "1000 skeletons" (size ratio 1) and equals the axis cap.

**B3-06 (PEA97), pass.**
* Pearson's personal-equation example with three observers: relative errors versus partial correlations of the estimates
  given the true value.
* Observers = 3, as in the source. The number of trials is not stated in the source ("a considerable series"), so 200 is
  read under P-2 reading 1.

**B3-07 (PEA97), fail on (f).**
* Items (a)–(e) and (g)–(i) are yes: per-species slopes of the length indices versus per-species coefficients with body
  length as a covariate.
* (f): The note says PEA97 states no sizes for the crustacean setting. That is inaccurate:
  * The sentence right after the passage the note quotes sets up a table of "some thousand individuals".
  * Weldon's note appended to the paper reports 420 constructed shrimps.
* The brief has 40 individuals per species (15 species). The caps and the timing would allow the source's size (for
  example 15 × 1000 = 15 000 values), so the §2 rule "source sizes where the timing rule allows" is not met.
* Neither P-2 reading applies: the source does state sizes, and those sizes are not above the cap.
* The defect is in the sizes, so the pair is dropped after the repair round.

**B3-08 (ARC81), pass.**
* Faulty: the fall is correlated with the first baseline reading, from which the fall is computed.
* Fixed: the same correlation with the second baseline reading.
* Only one key differs. Using a separate baseline measurement is a standard remedy. Size: 120, not documented by the
  source.

**B3-09 (ARC81), pass.**
* Faulty: delivery is correlated with the Fick uptake. Both are calculated from the same cardiac output (Type 2 coupling).
* Fixed: delivery is correlated with the expired-gas uptake, a standard remedy.
* Size: 60, not documented by the source.

**B3-10 (ARC81), fail on (h).**
* All other items are yes: a label from the total including item 1, versus a corrected item-total label.
* (h): The meaning of `item_scores` states "columns are in checklist order, item 1 first". That is a fact about how the
  variables on the `items` axis are ordered, beyond the axis name.
* The quoted text allows such a fact only as an axis name (like "time in order") or as part of what the claim states.
* The fact is needed to locate item 1 and is unrelated to the error. Item (h) is answered by the text, however, and the
  text makes no exception.
* The defect is in the brief, so the pair is dropped after the repair round.

**B3-11 (KRO93), pass.**
* Faulty: R² of B/C on A/C.
* Fixed: R² gain of gene A over gene C.
* Size: 96, not documented by the source.

**B3-12 (KRO93), pass.**
* Faulty: the rate admissions/population regressed on time, with a one-sided t test.
* Fixed: admissions on time and population, with the same test.
* The brief states no ordering of the months. Size: 120 months, not documented by the source.

## Reading of guard minima (item (d))

All minima equal one residual degree of freedom for each version's own statistic:
* 3 for a correlation or a simple regression;
* 4 for a model with one covariate;
* one per class for an AUC.

This is the reading in PREREG_PHASE_C §2's example, where a correlation needs 3 pairs. In B3-04 and B3-07 the
coefficient alone is computable at one observation fewer. With the declared sizes (150 rows; 40 per species) these
guards can never fire, on the worlds or on the probes.

## Criterion returns `True` exactly when the claim, with its statistic and threshold, is supported

Every fixed criterion computes the statistic named in the claim and applies its threshold. The t-tail routine is
accurate, and the AUC counts ties as one half. One remark:
* **B3-11**: the claim says "positively related", but its stated statistic (R² gain ≥ 0.05) ignores the sign, so the
  fixed criterion would also hold for a negative partial relation with that gain. This matches the stated statistic and
  threshold; it is a remark only.

Information only, not an audit item: the author recorded weak fixed criteria in the pre-checks, with minus hold rates
0.16 (B3-04), 0.12 (B3-12) and 0.08 (B3-01). They are kept as PREREG_PHASE_C §2 requires. The fixed criterion of B3-10
abstains on the noise probe (empty class).

## Class and subtype (PB §1)

The class is B-3 for all pairs and no subtype applies. No higher-precedence class (B-2, B-6, B-1) fits any pair.

| Pairs | Fit with PB §1 |
|---|---|
| B3-04, B3-05, B3-06, B3-07, B3-11 | Clear B-3: shared denominator |
| B3-08 | Clear B-3: change score against its own baseline |
| B3-09 | Clear B-3: shared measured component |
| B3-10 | Clear B-3: target computed from what it is compared with |
| B3-01, B3-02, B3-03, B3-12 (tag `ratio-vs-denominator-proxy`) | Mild disagreement, see below |

For the four pairs in the last row, a single ratio is related to a variable that is linked to the ratio's own
denominator. There is no shared denominator or shared component between the two quantities that are related. These
pairs therefore fit the PB §1 rule ("coupled to its target by construction or by shared measurement error") only
loosely; they are closer to a failure of ratio adjustment. B-3 is still the nearest in-scope class, and
PREREG_PHASE_C §2's estimand example and the addendum place CUR13 there. Reported as instructed; it changes nothing.

## Sizes

* **Not documented by the source** (P-2 reading 1): B3-01, B3-02, B3-03, B3-04 (CUR13, abstract only), B3-06 (trials
  axis; observers = 3 is documented), B3-08, B3-09, B3-10 (ARC81, abstract only), B3-11, B3-12 (KRO93, abstract only).
* **Reduced for timing:** none. **Reduced to the cap:** none (B3-05 equals both the source size and the cap).
* **Outside both readings:** B3-07 (see above).

## Sources read online (all URLs logged)

* CUR13 abstract: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1152/advan.00053.2013&resultType=core&format=json
* ARC81 abstract: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:7212790%20AND%20SRC:MED&resultType=core&format=json
* KRO93 abstract: https://econpapers.repec.org/RePEc:bla:jorssa:v:156:y:1993:i:3:p:379-392
* PEA97 OCR full text: https://archive.org/download/philtrans00847732/00847732_djvu.txt

Each URL was fetched twice: once with `ctx_fetch_and_index`, under labels `B3audC-*`, and once from a `ctx_execute`
Python script. `ctx_search` was called only with a `source` filter on those labels. `ctx_batch_execute` and `ctx_index`
were not called.
