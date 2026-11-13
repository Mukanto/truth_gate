# Targeted review 2 of the Phase B pre-registration draft v2 (fresh agent, 2026-11-12)

The reviewer read draft v2, `SOURCES.md`, `REVIEW1.md`, spec §14 and R-35/R-36, not the revision log. Condensed.

**Review 1 items:** resolved 4, 7 (feasible, KAP23-dominated), 8, 10, 11, 12; partly 1, 2, 3, 5, 6, 9.

**New findings:**

* **B1 (high).** Steering survives through the brief: the claim's wording fixes what "claim false" means and so the
  natural `minus` (for "significant in A, not in B" the negation could be "equal effects" or "no effect in either"); the
  author picks numbers of features, n and thresholds; the author sees the frozen worlds and could tune the faulty
  variant by reasoning or by simulating it on its own noise. Fix: a fixed `minus` template not chosen by the author;
  faulty parameters fixed at documented values; no pre-simulation of the faulty criterion in any form.
* **B2 (high).** Hierarchical or structural briefs reveal the class, and the claim's form points to it; audit item (e)
  is subjective. Fix: a mechanical term test; state the class-inference limitation under I-4.
* **B3 (high).** The precedence order sends every BAR05 case to B-1, leaving B-3 with two sources capped at 8 pairs, so
  B-3 is "insufficient" by construction; the B-2 rule ("held-out score") excludes its own subtype L1.1; oversampling is
  both L1.2 and L1.4 and no subtype tie rule exists.
* **B4 (medium).** B-1 feasibility (three capped sources) and MAK19 counted in two classes.
* **B5 (medium).** The timing formula's factors are unexplained, and it requires timing the faulty criterion, which §4.5
  forbids; numpy-only and 15 minutes push B-2 toward tiny models.
* **B6 (medium).** The shuffle flag's exact string must match the gate; label shuffle is "declared" (conservative); a
  world author unaware of the class may not declare a label-shuffle control — state as a limit.
* **B7 (medium).** `K2_NO_SEPARATION` and `K2_FAILS_UNREACHABLE` can fire on a weak skeleton for reasons unrelated to the
  error; report K2-only detections separately.
* **B8 (low).** Log fixed-criterion revisions per pair.
* **B9 (low).** The post-run audit has no checklist.

**Verdict (reviewer):** not ready; blocking B1, B2, B3, B5.
