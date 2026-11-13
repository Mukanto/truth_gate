# Fidelity audit, class B-3 (coupling by construction)

Auditor: blind, fresh agent. Read: PREREG_PHASE_B.md, REVISIONS-post-freeze.md (P-2), SOURCES.md, the class folder (ASSIGNMENT.json, faulty.py, fixed.py, PRIVATE.json, src/pea.txt) and STEP5_MECH_CHECK.json (B3 entries). No criterion was called on any data, no gate was run, no helper computation was run. I only ran text checks (twins equal outside the criterion bodies, banned-term grep on the briefs).

## B3-01 (ARC81 type 2): pass (a-g all yes)
- a: Yes. Fick VO2 = O2content*(SaO2-SvO2) correlated (Pearson, r>=0.5) with DO2 = O2content*SaO2; both contain CO, Hb, SaO2 and their measurement errors (the common-component coupling of the abstract). (source: ARC81 type 2).
- b: Yes. VO2 replaced by vo2_expired (independent measurement); same Pearson r, same threshold; only the now-unused svo2 read is dropped.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=40 patients; ARC81 abstract gives no sizes; ICU series of tens of patients (private note), under caps. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-02 (ARC81 type 3): pass (a-g all yes)
- a: Yes. SVR = 80(MAP-CVP)/CO_th is Spearman-correlated with the same CO_th (derived variable against its own denominator); threshold -0.4. (source: ARC81 type 3).
- b: Yes. Spearman of the same SVR with co_doppler (separate operator, independent error); single line changed.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=100 patients; no size in the abstract; larger ICU series, under caps. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-03 (ARC81 type 3): pass (a-g all yes)
- a: Yes. EDV = SVI/EF, then z-scored slope on EF (<= -0.4); EF is inside EDV so the slope is negative by construction. (source: ARC81 type 3).
- b: Yes. EDV taken from the radionuclide key (independent), same z-scored slope and threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=30 patients; no size in the abstract; small cardiology series, under caps. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-04 (ARC81 type 1 (+2)): pass (a-g all yes)
- a: Yes. Per-patient changes in Fick VO2 and in DO2 share the changes in CO, Hb, SaO2; R2 = r^2 of the regression, threshold 0.25. (source: ARC81 type 1 (+2)).
- b: Yes. Change in vo2_expired against change in DO2; same R2 and threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=24 patients x 2 time points; no size in the abstract; small dobutamine series, under caps. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-05 (PEA97 Prop. III / p.490-491): pass (a-g all yes)
- a: Yes. Pearson r between femur/vcl and tibia/vcl, threshold 0.4 (the text itself gives about 0.45 for independent bones with a shared denominator). (source: PEA97 Prop. III / p.490-491).
- b: Yes. Partial correlation of femur and tibia controlling for vcl (raw, not logs), same threshold; collinearity guard returns None.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=120; Pearson's illustration is 1000 skeletons (hypothetical) and his data are not summarised in the extract; 120 is below the 300 cap. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-06 (PEA97 Prop. III (application)): pass (a-g all yes)
- a: Yes. Spearman of co2/pop with gdp/pop (shared denominator), threshold 0.5. (source: PEA97 Prop. III (application)).
- b: Yes. Spearman partial correlation (ranks) of co2 and gdp controlling for pop, same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=150 countries; the source has no economic data (application of the proposition); below the cap, real set ~190. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-07 (PEA97 Prop. III (application)): pass (a-g all yes)
- a: Yes. Standardised slope of yield/area on fertilizer/area, threshold 0.3 (shared area denominator). (source: PEA97 Prop. III (application)).
- b: Yes. Standardised coefficient of fertilizer_total in yield_total ~ fertilizer_total + farm_area (z-scored), same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=90 farms; setting not in the source. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-08 (PEA97 Prop. III (application)): pass (a-g all yes)
- a: Yes. R2 of peak_power/mass on vo2max/mass (r^2 of the ratios), threshold 0.25. (source: PEA97 Prop. III (application)).
- b: Yes. Squared partial correlation of peak_power and vo2max controlling for mass, same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=30 athletes; setting not in the source. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-09 (KRO93 ratio as dependent): pass (a-g all yes)
- a: Yes. Standardised slope of infections/admissions on beds, threshold <= -0.3. (source: KRO93 ratio as dependent).
- b: Yes. Standardised coefficient of beds in infections ~ beds + admissions (ratio-free form), same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=100 hospitals; abstract only, no sizes. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-10 (KRO93 ratio as independent): pass (a-g all yes)
- a: Yes. Standardised slope of systolic pressure on heart_weight/body_weight, threshold >= 0.3. (source: KRO93 ratio as independent).
- b: Yes. Standardised coefficient of heart_weight in pressure ~ heart_weight + body_weight, same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=60 rats; abstract only, no sizes. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-11 (KRO93 ratio as dependent): pass (a-g all yes)
- a: Yes. Spearman of occupants with energy/area, threshold <= -0.3. (source: KRO93 ratio as dependent).
- b: Yes. Spearman partial correlation (ranks) of energy and occupants controlling for area, same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=150 buildings; abstract only, no sizes. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## B3-12 (KRO93 ratio as dependent): pass (a-g all yes)
- a: Yes. R2 (r^2) of leavers/headcount on payroll, threshold 0.1. (source: KRO93 ratio as dependent).
- b: Yes. Squared partial correlation of leavers and payroll controlling for headcount, same threshold.
- c: Yes. Text outside the criterion body is identical in the twins (checked by script); inside it the only change is the replaced statistic input.
- d: Yes. Every comparison listed by the designer is a zero-variance guard (np.std(...)==0) returning None, plus finite checks and, in the partial-correlation twins, a degenerate-denominator guard (den > 1e-12) returning None. No noise/zero/shuffle test, no probe-specific branch.
- e: Yes. Banned-term grep over claim, keys and sizes: no hits; the brief does not say what 'claim false' means.
- f: Yes. n=250 firms; abstract only, no sizes; below cap 300. Read as P-2.
- g: Yes. Same statistic family, same threshold and decision rule; cost comparable (a few vector operations on at most 250 values).

## Remarks (no effect on answers)
- Held/True rule: in all 12 files the criterion returns True exactly when the stated statistic passes the brief's threshold. B3-04, B3-08, B3-12 use R squared (unsigned), as the brief's statistic is R squared; direction is not tested in either twin.
- Class and subtype: B-3, no subtype, for all 12; no disagreement with the section 1 rules. Borderline note: the literal rule says "ratios with a shared denominator". B3-01 to B3-08 satisfy it directly (shared components or denominator). B3-09, B3-11 and B3-12 (ratio as dependent variable against a predictor correlated with the denominator) and B3-10 (ratio as independent variable) follow KRO93 (listed as a B-3 source) but have no denominator shared with the other variable; I accept B-3 because KRO93 is the cited source and no more specific class applies.
- The partial-correlation fixed twins use raw (not log) values in B3-05, B3-08, B3-12; a standard form of the correction, accepted.

## Pairs whose sizes are "not documented by the source" or "reduced to the cap" (P-2)
- Not documented (source abstract states no sizes): B3-01, B3-02, B3-03, B3-04 (ARC81); B3-09, B3-10, B3-11, B3-12 (KRO93).
- Setting not in the source (application of the proposition; sizes of the order of the setting, under the caps): B3-06, B3-07, B3-08 (PEA97).
- Source illustration larger than the cap (1000 hypothetical skeletons; brief uses 120, under the 300 cap): B3-05 (PEA97).
- Reduced to the cap: none (no brief is at 300; B3-12 at 250 is the largest).

## Result
12 of 12 pairs pass; no repair requests.
