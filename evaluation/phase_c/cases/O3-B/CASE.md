# CASE O3-B

1. **Case id** O3-B; **world id** C14; **class** O; **subtype** O-3 (spreadsheet range error in the real data).
2. **Source** HER14, section 2 "Spreadsheet coding error": "A coding error in the RR working spreadsheet entirely excludes five countries, Australia, Austria, Belgium, Canada, and Denmark, from the analysis." Footnote: "RR averaged cells in lines 30 to 44 instead of lines 30 to 49." Read by the brief author in the PERI working paper WP322 (same authors and title, April 2013 version) http://peri.umass.edu/wp-content/uploads/joomla/images/WP322.pdf (LOG.md part 1); the part-2 author did not re-read it.
3. **Brief**: claim "Across the advanced economies in the post-war period, average real GDP growth in country-years with a public debt ratio above 90 percent of GDP is at least 2 percentage points lower than average real GDP growth in country-years with a debt ratio of 90 percent or below." Keys: `growth` float (countries, years), `debt_ratio` float (countries, years). Sizes: 20 countries, 64 years.
4. **Mapping.** Faulty: both group means are taken over the country-years of the first 15 country rows only (the averaging range stops five rows short, as in lines 30 to 44 of 30 to 49); the claim holds when mean growth above 90 minus mean growth at or below 90 is <= -2. Fixed: the same over all 20 countries (pooled country-years, as in the corrected analysis); same threshold and code (only the row selection differs).
   **Estimand line.** Faulty: difference in mean real GDP growth between high-debt and other country-years for 15 of the 20 countries. Fixed: the same difference over all 20 countries' country-years.
5. **Pre-checks of the fixed criterion**: 400 `plus` samples: 400 hold; 400 `minus`: 0 hold; control `reassign_debt_histories_between_countries` (400): 0 hold; shuffle probe on the declared relational pair (400, rows of debt_ratio permuted against growth; `work\precheck_o3b_shuffle.py`): 2 hold, 398 fail; noise probe (400): all None (no country-year above 90, an allowed empty-selection guard); zeros probe (20): all None. Revisions: 0.
6. **Timing**: t = 0.000022 s, g = 0.000272 s, S = 2 worlds + 1 control + 0 premises + 1 relational pair + 2 = 6; estimate 2 x 200 x 7 x 0.000294 = 0.8 s.
7. **Deviations, problems, skeleton requests.** The note's faulty text is ambiguous: "the first 15 of the 20 countries only (drop the first five country rows, i.e. the averaging range stops five lines short)". Read as the range stopping five rows short: rows 0 to 14 are kept and the last five dropped (the footnote's lines 30 to 44 of 30 to 49; the same "first 15 of 20"). The other reading (drop rows 0 to 4) changes nothing statistically, because the skeleton's country rows are exchangeable draws. Guards: non-finite values; no country-year above 90 or none at or below 90 in the selected rows (empty selection). No skeleton request.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case O3b.
- Mechanism tag / statistic family (private note): O-3 / mean.
- Allowed-guard minimum (private note): 1 country-year in each debt group (difference of two means is defined from one value each); non-finite values return None
- Size ratio (brief size to source size): countries 20/20 = 1.0; years 64/64 = 1.0.
- The estimand line is in item 4 (criterion author).
