# Fidelity audit, class O (O-1, O-2, O-3)

Read: AUDIT_PHASE.md, PREREG_PHASE_B.md, REVISIONS-post-freeze.md, SOURCES.md, the class BRIEFS.json, PRIVATE.json, LOG.md, cases O1a to O3b (ASSIGNMENT.json, skeleton.py, faulty.py, fixed.py) and the O* entries of STEP5_MECH_CHECK.json. No criterion was called on any data and no gate was run. The only computation was an isolated check of the Welch p-value helper (O2a, O2b): text-extracted nested functions, run on fixed and random vectors, agree with scipy to 4e-14. No source extracts or src folder exist in the class folder; sources were not re-fetched.

All six pairs: (a) to (g) yes, overall pass, no repair request.

## O1a (KAP23 L2)
- (a) Faulty scores a linear classifier on held-out rows using all 12 columns, including column 11 (therapy doses recorded during the stay), a proxy of the outcome. Split is clean.
- (b)/(c) Fixed uses columns 0 to 10 only; the diff is two lines.
- (d) MECH lists nothing; only allowed guards.
- (e) No banned terms; no negation.
- (f) KAP23 gives no sizes; within caps (P-2 item 1).
- (g) Same split, fit, statistic, threshold.

## O1b (KAP23 L1.2, label-free)
- (a) Faulty fits standardisation and PCA on all 120 rows, then centroids on the first 72 and scores the rest. (b)/(c) Fixed fits them on the first 72 only; two-line diff.
- (d) Only the zero-variance guard sd.min() <= 1e-12. (e) clean.
- (f) No sizes in KAP23; 60 genes equals the cap (P-2 item 1). (g) same structure.

## O2a (SIM11 situation A)
- (a) Min of three one-sided Welch p (measure 1, measure 2, mean), n=20, r about 0.5, as in SIM11. Helper verified. Remark: SIM11 may use two-sided tests; the brief fixes one-sided.
- (b)/(c) Fixed tests measure 1 only; diff is the ps statement.
- (d) MECH lists the p < 0.05 threshold and a 1e-14 loop tolerance, both benign. (e) clean; "primary" states the planned analysis. (f) 20 per group matches SIM11. (g) same, three tests vs one is the error.

## O2b (SIM11 optional stopping)
- (a) Looks at 20 then 30 per arm, either p < 0.05. (b)/(c) Fixed tests once at 30; diff is the tuple of sizes.
- (d) Same benign MECH entries. (e) clean. (f) 20 then 30 per cell matches SIM11. (g) same.

## O3a (BAG09 offset)
- (a) Faulty uses columns 6 to 10 instead of 5 to 9 (gene-list offset by one), the documented direction. (b)/(c) Fixed uses columns 5 to 9; one-line diff.
- (d) Only the zero-variance guard. (e) clean. (f) Sizes reduced from a genome-scale panel; 60 lines (from recollection, NCI-60) (P-2). (g) same.
- Skeleton remark (not an audit item): the faulty window overlaps four of the five true signature columns, so it may still hold in plus.

## O3b (HER14 exclusions and averaging)
- (a) Faulty drops the first five countries, the first four years of one more country, and weights countries equally, then high-minus-low <= -1.5. A three-part bundle, all from the cited passage. (b)/(c) Fixed uses all data and pools country-years; yes, noting the bundle.
- (d) MECH lists nothing; guards are finiteness, shape, at least 14 countries, empty bin. (e) clean. (f) 20 countries match; 15 of 64 years, reduced to the cap (P-2 item 2). The brief uses 2 debt bins instead of 4. (g) same.

## Class and subtype remarks
All six assignments follow section 1 (O1a L2, O1b L1.2 label-free, O2a and O2b SIM11, O3a and O3b real-data errors); no disagreement. Each criterion returns True exactly when its claimed statistic meets its threshold.

## P-2 list for the report
- Sizes not documented by the source: O1a (250 patients; 12 variables), O1b (120 tumours; 60 genes), O3a (60 cell lines; 20 genes).
- Reduced to the cap or simplified: O1b (60 genes = cap), O3b (15 of 64 years; 2 bins instead of 4), O3a (genes reduced).
- Matched to the source: O2a (20 per cell), O2b (20 then 30 per cell).

## Result
6 of 6 pairs pass.
