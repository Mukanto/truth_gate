# Phase D post-run audit, part 2

I opened `part2\` after writing `out\POSTRUN_AUDIT.json` and `out\POSTRUN_AUDIT.md`, and I have not changed those files
since.

## A. Numbers in the report's tables

**Result: every number in the tables of REPORT.md sections 1 to 10 equals RESULTS_D.md / RESULTS_D.json, and every
certificate-based number also equals my own recount from the 120 certificates.** The recount is `scratch\summ.py`; the
comparison scripts are run inline from `scratch\`.

What I compared:
- **All 60 pair-arms in RESULTS_D.json against the certificates.** For each I compared the faulty and fixed verdicts,
  the full flag lists, the set of qualifying streams with their faulty and fixed counts, and the attributable,
  generic, declared, PB-detected and clean outcomes: 0 differences.
  - The number of distinct qualifying streams is 143, which matches section 9's "143 stream counts".
- **The per-arm, per-class cells:**
  - n, attributable, generic, declared, both, generic-only and declared-only;
  - PB-style, PB generic and PB declared;
  - draft-1, noise-only, declared-only and flag-everything;
  - clean;
  - the three Wilson lower bounds (z = 1.6449).
  - Result: 0 differences.
- **Report tables:**
  - §3.1 H-D1/H-D2: n, k, bounds 0.6523, 0.7871, 0.5477, 0.7212.
  - §3.2 H-D3: 17 pairs, 14/14 declared, b = c = 0, p = 1; the comparable list.
  - §3.3 guard: 16/17 vs 17/17, 0/1 discordant, p = 1, +1; decoys 3/3.
  - §4.1 counts table.
  - §4.2 decoys.
  - §4.3 W-0 columns.
  - §4.4 miss labels, clean-pass class and structure shares (0.015, 0.155, 0.000).
  - §5 drop table and label counts (they match RESULTS; the source file `FREEZE_VALIDITY.json` is not in my folder).
  - §6 awareness table, recomputed from the four READING.json files and both maps.
- **Run facts:**
  - 120 checks, attempt 1, no timeout or infrastructure failure.
  - The sum of check durations is 1303.2 s (wall time 1311 s); the longest check took 114.24 s.
  - Gate commit `0aed4249f902`.
  - All certificate hashes match the run log.
- **§4.3 PB and PC columns:** these equal RESULTS_D and, for B-2 and B-3, PREREG_PHASE_D §0.1.

## B. Statements contradicted or not supported (10 findings)

1. **§1 (outcome table bullet) and §4.4: "The miss labels say where the misses lie: label (b) ... for D-055 (B-2) and
   D-062 (B-3) in both arms. No miss has label (a), structure missing."**
   - The labels are what the frozen tool gives, but the reading they suggest (structure present, rate below the
     threshold) is not supported.
   - **D-062.** The structure statistic is Pearson's approximation from the three CVs, and it assumes numerators
     uncorrelated with the denominator.
     - In W0 the bones are proportional to body length (`femur = rf*body + resid`). In W1 they follow log body length
       with slopes 0.95 and 0.90.
     - Under such scaling the index correlation the error needs is nearly absent: faulty minus 0/200 and 1/200. Yet
       the statistic reads "present" (share 1.000 in both arms).
     - The reference world draws the bones independent of body length and gets 149/200.
   - **D-055.** The statistic measures only the predictors' autocorrelation.
     - The error also needs a persistent outcome: outcome noise is AR 0.3 in W0 and AR 0.6 in W1, against 0.92 in R.
     - Faulty minus is 0/200 and 1/200.
   - In both pairs the declared worlds lack part of what the error exploits, and the statistic does not measure that
     part.
   - The same weakness shows the other way in D-068 W1: share 0.000, yet attributable (minus 125 vs 1).
2. **§1 (B-2 W-1 "9 of 10"), §3.1, §3.2 (14 declared in each arm), §4.1.** These counts include D-042's declared
   detections in W-0 and W-1. Part 1 found a sign of brief steering there, (iii) = yes:
   - the key meanings "for each compound record" and the axis "records", set against the claim's "new compounds", led
     both world authors to build duplicate records with identical descriptors;
   - both world logs cite this wording;
   - the detection rests entirely on those duplicates.
   - Under PREREG §7 the numbers stand, but the report gives them with no note. As written, the statements are not
     supported without that qualification.
3. **§1 and §3.1, the class verdicts.** The report gives "insufficient cases" but not the pre-registered "minimum not
   met" (PREREG §1: "A class below a minimum is reported as 'minimum not met'").
   - **B-2:** the final set has L3.1 = 1 and L3.2 = 0, against minima of 2 and 2.
   - **B-3:** shared-measured-component = 1, ratio-vs-denominator-proxy = 1 and change-vs-baseline = 0, against at
     least 3 per tag. 5 of the 7 B-3 pairs are ratio-shared-denominator.
   - Neither REPORT.md nor RESULTS_D.md uses the word "minimum".
4. **§1: "This sample carries no information on a checklist effect"; §10: "At this n the test cannot show a checklist
   effect of any size."**
   - The limit comes from W-0's ceiling, not from n.
   - W-0 already had 14 of 17 declared detections, so at most 3 W-1-only discordant pairs were possible. The smallest
     attainable one-sided exact p was therefore 0.125.
   - With 17 pairs and a lower W-0 rate, 5 one-way discordant pairs would give p = 0.031.
5. **§4.3: "V1 and V2 remove pairs whose error does not bite in a reference world and pairs whose fixed twin fails the
   noise probe"; §5: "V2 removes pairs whose fixed criterion fails the noise probe, or the plus-power part of V2".**
   - Both are incomplete. PREREG §2.3's V2 also requires the fixed twin to hold in at most 0.065 of reference `minus`
     samples.
   - §4.3 also omits the plus-power part (at least 0.70 of reference `plus`).
6. **§6: "One reader (r1) did not count an entry's general notes, against its prompt. Before any tally, it was replaced
   once by a fresh reader (r1b) ... r1's reading is kept and excluded."**
   - This process event is not in `REVISIONS-post-freeze.md`. P-6 names two fresh first readers and says nothing about
     a replacement, and r1's reading is not among the files.
   - RESULTS_D.json `rules.resolution` cites "r1 excluded (P-6)", but P-6 contains no such rule.
   - The statement is not supported by the record given to me.
7. **§8: "batch 2 W-1's first agent was invalid: a forbidden `TaskStop` call ...".** WORLD_RUN.md (order 6) records 2
   forbidden tool calls: "ToolSearch select:TaskStop; TaskStop on its own background command". This is minor.
8. **§3.1: "Awareness shares ... (as section 6 asks next to any class statement)".**
   - PREREG_PHASE_D §6 contains no such rule. The rule is PC §6: "Every statement of a class verdict in the report
     carries that class's P/C/N shares from the resolved reading and the wording 'declared worlds that may contain what
     the error exploits'".
   - If that rule applies through "as PC", the §1 class verdict statements lack the shares, and neither §1 nor §3.1
     carries the wording.
9. **§1 Limitation paragraph and §10 first bullet ("see the fixed sentence in section 1").**
   - P-1 amendment 3 says the limitation sentence "is printed in the limitations section and next to every class verdict
     sentence".
   - §10 does not print it; it only refers to §1. The §3.1 verdict table (H-D1/H-D2 "insufficient cases") has no such
     sentence next to it.
10. **§1 outcome reading: "The reading is the last row: neither class meets the bar, and no checklist effect is
    demonstrated."** P-1 amendment 4 says "Every I-D3 reading is read with 'with Claude Opus 5.5 as world author'". The
    sentence lacks that qualifier.

**One omission that no single statement carries.** PREREG §1 (overlap) says: "If strictly more than half of a class's
pairs overlap, the report says that the class result 'largely repeats Phase B and C settings'. Every table is also
given without the overlapping pairs."
- Neither REPORT.md nor RESULTS_D.md has an overlap marking or tables without the overlapping pairs.
- I cannot compute the overlap: the Phase B/C pair descriptors are not in my folder.

## C. Statements I could not check from the files given (no finding)

- **§2:** the runner and its SHA-256, the pre-flight checks, the freeze commits `77e5c1d` and `25bdbb2`, and the file
  counts 546 and 1805. Transcripts are private.
- **§5:** the drop table itself (it matches RESULTS, but `FREEZE_VALIDITY.json` is not here); the unused reserves
  D-026 and D-070 and the reason given for them; the author's decision of 2026-11-18; and the designer's reading of the
  change-vs-baseline noise-probe failures.
- **§7:** model ids of every role except the world authors (WORLD_RUN.md confirms `claude-opus-5-5`, `xhigh`, 2.1.326).
- **§9:** "1158 items, 0 disagreements" and the round-4 agreement. My own recount agrees with every pair-arm and table
  cell I compared (part A).

## D. Effect of part 2 on my part-1 answers

None of my part-1 answers changes. RESULTS confirms several part-1 points:
- D-052 W0/W1 is PB-detected but not attributable, label (c). This matches my (i) "yes", reached by the weakness
  route.
- D-035 W0 is clean-pass class 3, fixed weak in `plus`. This matches my (ii) "yes" (skeleton, low power in plus).
- D-062 has structure share 1.000 in both W arms. This matches my remark that the frozen statistic does not register
  the near-isometric scaling.
- The awareness tallies match my combined readings.
