# CASE O3-A

1. **Case id** O3-A; **world id** C29; **class** O; **subtype** O-3 (row offset in the real data).
2. **Source** BAG09, section 3.2: gene lists "were off-by-one due to an indexing error"; "quantifications from row 98 (probeset 200076_at) of the Gyorffy et al. 2006 table were used instead of those from row 97" (a single-row shift). Section 3.9: "Poor documentation hid an off-by-one indexing error affecting all genes reported". Read by the brief author in the ar5iv full text https://ar5iv.labs.arxiv.org/html/1010.1092 (LOG.md part 1); the part-2 author did not re-read it.
3. **Brief**: claim "Across the cell lines, the average expression of the probe sets on the published drug-response signature is higher in the cell lines sensitive to the drug than in the resistant cell lines, by at least 0.5 log2 units (Welch two-sample t test on the per-cell-line signature averages, p < .01)." Keys: `expression` float (probe_sets, cell_lines), `on_signature` bool (probe_sets,), `sensitive` bool (cell_lines,). Sizes: 1000 probe sets, 60 cell lines.
4. **Mapping.** Faulty: the membership mask is shifted by one row (`np.roll(mask, 1)` along the probe-set axis, shift of one row as documented), so each listed probe set is replaced by the one in the adjacent row; then per-cell-line average over the selected rows, sensitive-minus-resistant difference of the per-line averages, Welch two-sample t test, claim holds if difference >= 0.5 and two-sided p < .01. Fixed: the mask as given; everything else identical (the single `np.roll` line is the only difference). The Welch p value uses the Welch-Satterthwaite degrees of freedom and the regularised incomplete beta (Lanczos log-gamma, continued fraction), written in the body because only numpy is allowed.
   **Estimand line.** Faulty: sensitive-minus-resistant difference in the mean expression of the probe sets one row away from the signature's. Fixed: sensitive-minus-resistant difference in the mean expression of the signature's own probe sets.
5. **Pre-checks of the fixed criterion** (300 samples each): `plus` 299 hold, 1 fail, 0 None; `minus` 0 hold; control `permute_sensitive_across_cell_lines` 0; control `random_signature_same_size` 0; noise probe 0; zeros probe (20) all None. Helper validation (scratch `work\validate_welch_helper.py`, fixed file only): over 3000 random two-sample cases the Welch p value differs from `scipy.stats.ttest_ind(equal_var=False)` by at most 2.5e-13 (relative 3.7e-13); log-gamma within 1.7e-13 of scipy. Revisions: 0.
6. **Timing**: t = 0.000094 s, g = 0.001087 s, S = 2 + 2 + 0 + 0 + 2 = 6; estimate 2 x 200 x 7 x 0.001181 = 3.3 s.
7. **Deviations, problems, skeleton requests.** None. Guards: non-finite expression values; fewer than 1 probe set on the signature; fewer than 2 sensitive or fewer than 2 resistant cell lines; zero variance in both groups (zero standard error of the difference).

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: no.
- Mechanism tag / statistic family (private note): O-3 / mean.
- Allowed-guard minimum (private note): 2 sensitive and 2 resistant cell lines, and at least 1 probe set on the signature; non-finite values and zero variance return None
- Size ratio (brief size to source size): cell lines 60/60 = 1.0; probe sets 1000/12 558-22 283 = 0.045-0.080 (reduced to the cap).
- The estimand line is in item 4 (criterion author).
