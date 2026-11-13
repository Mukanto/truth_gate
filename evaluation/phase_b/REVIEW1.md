# Blind review 1 of the Phase B pre-registration draft v1 (fresh agent, 2026-11-12)

The reviewer read the draft, `SOURCES.md`, the public documentation and the gate's code. Condensed findings; the
designer's responses are in `REVISIONS.md`.

1. **Critical (§6, §4).** Almost all expected flags read streams the author declares (`minus`, controls, `null`,
   relational pairs); only `K5_HOLDS_ON_NOISE` and `HIGH_RATE:probe:noise` are generic. The noise probe cannot reach
   B-3 (zero-mean noise has no coupling), L1.4, L3.1, L3.2 (i.i.d. noise has no duplicates, time order or clusters) or
   B-6 (no dependence structure). An author who knows the error can build the `minus` world that exposes it, and the
   report would credit the gate. Report the split between generic and declared detections, add ablations, rename the
   headline.
2. **Critical (§4).** Authors know the planted error and `GATE.md` and can pre-check with plain Python what K2
   measures; failed attempts can be discarded silently; the same author writes worlds and criteria. Use two-phase
   authoring (worlds committed and hashed before criteria), log every attempt and pre-check, add a held-out control or
   separate authors.
3. **Major (§2, §5).** The 30-minute limit cannot be checked before the freeze (no gate runs), and slower corrected
   twins are penalised. Replace with a plain-Python timing estimate and state how timeouts count.
4. **Major (§6).** n = 10 means 9 of 10 on both rates; a class with true detection 0.85 passes about half the time.
   State this, say that all non-dropped pairs count, report intervals without over-reading.
5. **Major (§6, §1).** Fixed twins can fail for reasons the author cannot see: `K2_HOLDS_UNREACHABLE`,
   `K2_NO_SEPARATION` from low power, `K5_HOLDS_ON_DEGENERATE` for "fails to reject" criteria, and the noise probe
   turning integer labels or group ids into continuous values. Require structure in array shapes, positive claims, and
   plain-Python simulation of the documented probes; report fixed-twin failures by flag.
6. **Major (§1, §5).** Class boundaries overlap (AMB02 is B-1 and B-2; pseudoreplication overlaps L3.2; BAR05 is a
   selection effect; supervised versus unsupervised pre-processing undefined). Give decision rules; the designer assigns
   the class; report B-2 per subtype.
7. **Major (§1, B-2).** With the source cap, the hard B-2 subtypes (L1.4, L3.1, L3.2, supervised L1.2) can only come from
   KAP23, at most 4 pairs, so the class can pass on the easy subtypes. Require minima per subtype or drop them.
8. **Major (§0, §1 versus spec §14).** Undeclared deviations: one flag set for all classes and a `HIGH_RATE:<stream>`
   template (§14: per class, no wildcards); B-3 redefined from "tautological criteria" to mathematical coupling; B-2
   widened; B-4 "not built" although §14 calls it a known-mechanism class. Record them in a post-freeze revision.
9. **Major (sources).** MAK19 was listed but unread although B-1 needs it for three sources; OLD62 and ARC81 were only
   read through citing works; GEL06 repeats NIE11 and should not count as independent.
10. **Minor (§2).** "No gate-aware code" is not checkable; list the allowed guards and flag suspicious tests by script.
11. **Minor (§6).** 0.3.0 adds no information for Python cases; add K2/K4-only and noise-only baselines.
12. **Minor (§5, §7).** Fidelity terms need yes/no criteria; a disputed pair should count as dropped and be reported.

**Verdict (reviewer):** not ready to freeze; blocking: 1, 2, 3, 5, 6, 7, 8, 9.
