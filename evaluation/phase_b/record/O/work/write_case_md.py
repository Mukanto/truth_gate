"""Writes CASE.md for each case (last step). Text only; executes no criterion."""
import json, os

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")

# pre-check numbers copied from work/precheck_fixed_run1.txt (seed 777; 300 plus/minus/control samples, 100 per probe)
PRE = {
    "O1a": dict(plus="280/300 (0.933)", minus="23/300 (0.077)", ctrl="16/300 (0.053)", noise="0/100", zeros="0/100 (100 UNDEFINED by the guard)", t="0.052 ms", g="0.042 ms", est="0.2 s"),
    "O1b": dict(plus="261/300 (0.870)", minus="2/300 (0.007)", ctrl="1/300 (0.003)", noise="0/100", zeros="0/100 (100 UNDEFINED by the guard)", t="1.164 ms", g="0.088 ms", est="3.0 s"),
    "O2a": dict(plus="256/300 (0.853)", minus="20/300 (0.067)", ctrl="10/300 (0.033)", noise="5/100", zeros="0/100 (100 UNDEFINED by the guard)", t="0.063 ms", g="0.014 ms", est="0.2 s"),
    "O2b": dict(plus="273/300 (0.910)", minus="19/300 (0.063)", ctrl="20/300 (0.067)", noise="3/100", zeros="0/100 (100 UNDEFINED by the guard)", t="0.045 ms", g="0.007 ms", est="0.1 s"),
    "O3a": dict(plus="284/300 (0.947)", minus="0/300 (0.000)", ctrl="0/300 (0.000)", noise="0/100", zeros="0/100 (100 UNDEFINED by the guard)", t="0.041 ms", g="0.023 ms", est="0.2 s"),
    "O3b": dict(plus="300/300 (1.000)", minus="46/300 (0.153)", ctrl="12/300 (0.040)", noise="0/100 (100 UNDEFINED by the guard: no value above 90)", zeros="0/100 (100 UNDEFINED by the guard)", t="0.015 ms", g="0.109 ms", est="0.3 s"),
}

TEXT = {
    "O1a": dict(
        quote_loc="KAP23 (Kapoor and Narayanan 2023), section 2.4, type L2: \"If the model has access to features that should not be legitimately available for use in the modeling exercise, this could result in leakage. One instance when this can happen is if a feature is a proxy for the outcome variable.\" (the paper's example: anti-hypertensive drug use as a predictor of hypertension).",
        read="Read by the earlier author (phase 1), ar5iv full text of section 2.4 (see LOG.md, 'Revision after coordinator message'). Not re-read by the phase 2 author.",
        mapping="Faulty: a least-squares linear classifier (0/1 labels, intercept, threshold 0.5) is fitted on the first 150 patients and its accuracy is measured on the remaining 100, using all 12 variables, including column 11, the number of targeted-therapy doses recorded during the stay, which is a proxy for the diagnosis (the L2 error: a feature that should not be legitimately available). The split and the fit are clean, so the leakage is at the data level. Parameters: the accuracy threshold 0.75 is the claim's; the split 150/100 and the least-squares classifier are my choice (the brief says 'a linear classifier' on 'new patients'; the source documents no values). Fixed: the same pipeline with column 11 dropped (11 variables available at admission); same statistic (test accuracy), same threshold, same decision rule.",
        dev="Private note said 'fixed block of rows'; I chose 150 train / 100 test and a least-squares classifier before looking at any rate. The fixed criterion holds in 0.933 of plus and 0.077 of minus (chance accuracy near the 0.70 base rate with 100 test rows; a feature of the skeleton's 30% prevalence, not changed). No skeleton request.",
    ),
    "O1b": dict(
        quote_loc="KAP23, section 2.4, type L1.2: \"Using the entire dataset for any pre-processing steps such as imputation or over/under sampling.\" The paper's example is label-dependent; the label-free variant (standardisation and PCA on all rows) is the one used here, per the O-1 class definition in PREREG section 1 (\"scaling, unsupervised imputation, PCA on all data\").",
        read="Read by the earlier author (phase 1), ar5iv full text of section 2.4. Not re-read by the phase 2 author.",
        mapping="Faulty: every gene is standardised and a PCA (top 5 components, SVD) is fitted on all 120 tumours, train and test rows together; a nearest-centroid classifier (Euclidean, in the 5-component space) is fitted on the first 72 tumours and scored on the remaining 48; the claim holds when accuracy >= 0.70. This is the label-free pre-processing leak: the test rows influence the means, scales and axes. Parameters: 5 components is the private note's value (the brief says 'leading principal components' and does not give a number; the source documents no values); 72/48 split is my choice. Fixed: the standardisation and the PCA are fitted on the 72 training rows only and applied to the test rows; everything else is identical.",
        dev="Private note gave no split; I chose 72/48 (60/40, as in O1a) before looking at any rate. Expected invisible effect as the note says. No skeleton request.",
    ),
    "O2a": dict(
        quote_loc="SIM11 (Simmons, Nelson and Simonsohn 2011), Table 1 and the text on the first rows: Situation A, \"two dependent variables (r = .50)\", with three tests: one on each dependent variable and one on their average, 20 observations per cell, 15,000 simulated samples.",
        read="Read by the earlier author (phase 1), full text PDF (UBC course copy), Table 1 and the text of the first two rows. Not re-read by the phase 2 author.",
        mapping="Faulty: one-sided Welch t tests on measure 1, on measure 2 and on the average of the two measures; the claim holds if the smallest of the three p values is below 0.05 (the analysis that is reported is chosen after seeing all three). Parameters are those of SIM11 Situation A (two correlated DVs, r about 0.5, 20 per cell, threshold 0.05) and are fixed by the skeleton. Fixed: the planned primary analysis only, a one-sided Welch test on measure 1 at 0.05. Both use the same hand-written numpy Welch/t-tail code (the exact tail via the regularised incomplete beta function; no scipy).",
        dev="The t tail is computed with an incomplete-beta routine written inside the criterion; it was checked against the tabulated one-sided 5% critical values for df 1, 2, 10, 20, 38, 58, 1000 (agreement to 1e-7) in work/helper_test.py. None otherwise; no skeleton request.",
    ),
    "O2b": dict(
        quote_loc="SIM11, text on optional stopping: the researcher \"collects 20 observations per condition and then tests for significance\"; \"if the result is nonsignificant, the researcher collects 10 additional observations per condition, and then again tests for significance.\"",
        read="Read by the earlier author (phase 1), full text PDF. Not re-read by the phase 2 author.",
        mapping="Faulty: one-sided Welch tests at the first 20 per group (first 20 rows of each array, rows are in recruitment order) and again at 30 per group; the claim holds if either p is below 0.05 (the stopping point is chosen after seeing both). Parameters: 20 then 30 per cell (SIM11; the private note corrected an earlier 20/25/30 draft to the two looks of the source), threshold 0.05. Fixed: a single test at the planned 30 per group, same test and threshold. Both use the same numpy Welch/t-tail code as O2a.",
        dev="None. Same incomplete-beta helper as O2a (checked in work/helper_test.py). No skeleton request.",
    ),
    "O3a": dict(
        quote_loc="BAG09 (Baggerly and Coombes 2009), abstract: \"the most common errors are simple (e.g., row or column offsets)\"; Fig. 2 caption: expression values obtained by \"offsetting\" by one row (e.g., replacing 200075_s_at with 200076_at).",
        read="Read by the earlier author (phase 1), arXiv full text PDF (abstract, Fig. 2 caption, sections 2 and 3). Not re-read by the phase 2 author.",
        mapping="Faulty: the signature score is the mean of the gene columns offset by one position in the gene list, columns 6 to 10 counting from 1 (index 5:10) instead of the named columns 5 to 9; the claim holds if the Pearson correlation of that score with the sensitivity is >= 0.5 (the threshold of the claim). The one-position offset along the gene axis is the error BAG09 documents. Fixed: the score from the named columns 5 to 9 (index 4:9), same Pearson r and threshold.",
        dev="The private note expects the faulty criterion to usually fail in plus because the offset genes 'carry no signal'. Reading the skeleton generator (not running any faulty code) the signature genes are columns 5 to 9 and the offset window 6 to 10 shares four of the five, so the note's expectation may not hold; this is a property of the skeleton, the faulty criterion was written as documented and not changed. No skeleton request.",
    ),
    "O3b": dict(
        quote_loc="HER14 (Herndon, Ash and Pollin; PERI working paper 322), 'Spreadsheet coding error': \"A coding error in the RR working spreadsheet entirely excludes five countries, Australia, Austria, Belgium, Canada, and Denmark, from the analysis.\" Also in the paper: countries \"equally weighted by country\"; early years of Australia, Canada and New Zealand excluded.",
        read="Read by the earlier author (phase 1), the PERI WP322 PDF via pdftotext (sections on the spreadsheet coding error, exclusions and weighting). Not re-read by the phase 2 author. The critique is disputed by the original authors (SOURCES.md).",
        mapping="Faulty: the first five country rows (alphabetical, the five of the spreadsheet error) are left out entirely, the first four years of one further country row (row 13, the position of New Zealand in an alphabetical list of the 20 countries) are left out, each remaining country's mean growth is computed within the high-debt (> 90%) and the low-debt (<= 90%) bin, the country means are averaged with equal weight (countries empty in a bin are dropped), and the claim holds if high minus low <= -1.5 (the claim's threshold). These are the three documented choices: spreadsheet exclusion, selective exclusion of early years, equal weighting by country. Fixed: all 20 countries and all years, pooled country-year means per bin, same difference and threshold.",
        dev="Guard: the criterion returns None when a bin is empty (no country-year above 90, as in the noise and zero probes). The faulty and fixed statistics differ in two documented respects (exclusions and weighting); the weighting is part of the documented error, and both are mirrored in the structure (a mask plus a per-bin mean). The fixed criterion holds in 0.153 of minus because the skeleton's minus world keeps the correlation between country growth and country debt level and the reverse causation; recorded, not changed. No skeleton request.",
    ),
}

for case in ["O1a", "O1b", "O2a", "O2b", "O3a", "O3b"]:
    p = os.path.join(root, case, "CASE.md")
    if os.path.exists(p):
        print("skip", case)
        continue
    a = json.load(open(os.path.join(root, case, "ASSIGNMENT.json"), encoding="utf-8"))
    T, P = TEXT[case], PRE[case]
    brief = json.dumps(a["brief"], indent=2, ensure_ascii=False)
    md = f"""# CASE {a['local_id']}

## 1. Identification
- Case id: {a['local_id']}
- World id: {a['world_id']}
- Class: {a['class']} (out of scope); subtype assigned by the designer: {a['subtype']}

## 2. Source and documented error
- Source key: {a['source']}
- Passage: {T['quote_loc']}
- Reading: {T['read']}

## 3. Brief (exactly as in ASSIGNMENT.json)
```json
{brief}
```

## 4. Mapping of the criteria to the documented error and its correction
{T['mapping']}

## 5. Pre-checks of the fixed criterion (plain Python, work/precheck_fixed.py, seed 777)
- plus: holds in {P['plus']}
- minus: holds in {P['minus']}
- declared control (applied to plus samples): holds in {P['ctrl']}
- my approximation of the noise probe (float arrays N(0,1), bool arrays fair coin), 100 samples: holds in {P['noise']}
- zero probe (all-zero arrays, bool False), 100 samples: holds in {P['zeros']}
- Same input evaluated twice gave the same answer (repeatable).
- Revisions of the fixed criterion: 0 (the faulty criterion was never run).

## 6. Timing
- t (mean of 50 calls of the fixed criterion on plus samples) = {P['t']}; g (mean of 50 plus generations) = {P['g']}
- S = 5 (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes)
- Estimate 2 x 200 x (S + 1) x (t + g) = {P['est']} (limit 900 s)

## 7. Deviations, problems, skeleton requests
{T['dev']}
"""
    open(p, "w", encoding="utf-8", newline="\n").write(md)
    print("wrote", case)
