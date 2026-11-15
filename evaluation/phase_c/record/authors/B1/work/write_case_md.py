"""Scratch: writes CASE.md for each case from ASSIGNMENT.json, PRIVATE.json and the last fixed-criterion pre-check."""
import json
from pathlib import Path

B1 = Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B1")
priv = {p["local_id"]: p for p in json.loads((B1 / "PRIVATE.json").read_text(encoding="utf-8"))}
pre = json.loads((B1 / "work" / "precheck_last.json").read_text(encoding="utf-8"))

MAP = {
    "B1-01": (
        "Faulty: keeps women with index_start >= 20, takes only the active-arm women and tests the within-arm fall (index_start minus index_week12): mean fall >= 3 and one-sided paired t test (df n-1) at 0.05; the fall of selected extreme starters includes the regression of their start values, and no arm contrast absorbs it (MOR03, placebo effect section). Fixed: the same selection in both arms; difference of mean falls (active minus placebo) >= 3 and one-sided Welch t test at 0.05 (the placebo arm, selected the same way, absorbs the regression). The cut 20 is the claim's own.",
        "Faulty: mean fall (start to week 12) among active-arm women with start >= 20. Fixed: difference between arms in mean fall among women with start >= 20.",
        "The statistic differs by design (paired within-arm t versus two-arm Welch), as the private note says; the threshold 3 and the one-sided 0.05 level are the same.",
    ),
    "B1-02": (
        "Faulty: groups the women by the sign of the first-year change (bmd_m12_scan1 vs bmd_start) and measures the second-year percentage change from the same 12-month reading, 100*(bmd_m24 - bmd_m12_scan1)/bmd_m12_scan1; difference of group means (rose minus fell) >= 0.5 and one-sided Welch t test at 0.05. Fixed: the same grouping, second-year change measured from the second 12-month scan, 100*(bmd_m24 - bmd_m12_scan2)/bmd_m12_scan2; same threshold and test (MOR03, Figure 1 legend and text). Women with a first-year change of exactly 0 are in neither group.",
        "Faulty: difference in mean second-year change between first-year gainers and losers where one 12-month reading defines the group and starts the second-year change. Fixed: the same difference with the second-year change started from the second scan.",
        "Direction of the documented error against the claim: the shared reading makes first-year losers show a gain in the second year (the source's own observation), that is a bias of the group difference that is opposite in sign to the direction the claim asserts. The faulty criterion is therefore expected to hold less often than the fixed one in plus and may not hold in minus either; I did not run or simulate it, this is a statement about the documented mechanism only. The note's mechanism was kept unchanged; the designer should read a miss on this pair with this in mind.",
    ),
    "B1-03": (
        "Faulty: keeps patients whose reading 2 (column 1 of sbp) is >= 160 mmHg and tests the fall from reading 2 to reading 3 (mean fall >= 8, one-sided paired t test at 0.05). Fixed: keeps patients whose reading 1 (column 0, the screening reading) is >= 160 and tests the same fall with the same threshold and test (MOR03, diagnostic-tests section: serial measurements).",
        "Faulty: mean fall from reading 2 to reading 3 among patients chosen by reading 2. Fixed: mean fall from reading 2 to reading 3 among patients chosen by reading 1.",
        "none",
    ),
    "B1-04": (
        "Faulty: per participant, voxels with t > 2.0 for faces minus houses over all 8 runs (one-sided, t over runs); faces minus bodies averaged over those voxels and runs (same runs); mean across participants >= 0.3 and one-sided paired t test across participants at 0.05. Fixed: voxels selected from the even-numbered runs (runs 2, 4, 6, 8 = indices 1, 3, 5, 7), faces minus bodies measured in the odd-numbered runs only (indices 0, 2, 4, 6); same t > 2.0 cut, threshold and test (KRI10, Q7 and introduction: independent data from the same subjects).",
        "Faulty: mean faces-minus-bodies response in voxels chosen on the faces-vs-houses contrast of the same runs. Fixed: the same quantity with voxels chosen in other runs.",
        "Numbering convention: runs are numbered from 1, so 'even-numbered' means array indices 1, 3, 5, 7. The cut t > 2.0 is kept as the same constant in both versions, so on 4 selection runs (df 3) it corresponds to a stricter one-sided p than on 8 runs (df 7). A participant with an empty region is left out of the across-participant test, and the criterion returns None when fewer than 2 participants remain (the guard minimum of the note); a voxel with zero variance across the selection runs gives None.",
    ),
    "B1-05": (
        "Faulty: voxels with a one-sided one-sample t test across all 40 participants at p < 0.001; effect averaged over those voxels per participant; mean across participants >= 0.25 and one-sided one-sample t test across participants at 0.05, on the same 40 participants. Fixed: voxels selected with the same test on participants 0-19; mean and t test on participants 20-39 only (KRI10, Q6 and Q7: independent subjects).",
        "Faulty: mean effect in voxels chosen on the group-level test of the same participants. Fixed: mean effect in voxels chosen from other participants.",
        "The empty-selection guard is reached often in this skeleton's minus world and controls (see pre-check counts: abstentions on 91/200 minus samples, 104/200 random-sign samples, 85/200 noise samples); this follows from the 0.001 cut on 1000 voxels and is an allowed guard, not a change. t on one call is 0.03 s because 1000 tail probabilities are integrated.",
    ),
    "B1-06": (
        "Faulty: voxels whose response correlates positively with contrast across all 240 trials (one-sided p < 0.01), average of those voxels regressed on contrast over all 240 trials; slope >= 0.2 and one-sided p < 0.05. Fixed: voxels selected on the even-numbered trials (indices 1, 3, ..., 239), slope estimated on the odd-numbered trials only (indices 0, 2, ..., 238); same p < 0.01 rule, threshold and test (KRI10, introduction: half of the data to select, the other half to estimate).",
        "Faulty: slope of the average of voxels chosen for correlation with contrast, on the same trials. Fixed: the same slope on trials not used to choose the voxels.",
        "Numbering convention as in B1-04 (trials numbered from 1). The correlation p value of each voxel is that of a t statistic with n - 2 degrees of freedom (n = 240 in the faulty, 120 in the fixed); the cut p < 0.01 is the same in both.",
    ),
    "B1-07": (
        "Faulty: neurons with a one-sided Welch t test of rate_vertical over rate_horizontal across the 15 presentations each at p < 0.05; orientation index (V-H)/(V+H) of the trial-averaged rates of those neurons from all 15 presentations; mean index >= 0.1. Fixed: neurons selected by the same test on the odd-numbered presentations (indices 0, 2, ..., 14: 8 trials) and the index computed from the even-numbered presentations (indices 1, 3, ..., 13: 7 trials); same threshold (KRI09, introduction: single-cell selection and an independent data set).",
        "Faulty: mean index of neurons chosen for a vertical-over-horizontal difference on the same trials. Fixed: mean index of the same kind of neurons computed on other trials.",
        "The fixed criterion holds on the N(0,1) noise probe in about half the samples (99/200): on noise the trial-averaged rates have positive and negative sums near zero, so the ratio index is heavy-tailed and its mean exceeds 0.1 about as often as not. The index is the claim's own statistic, the allowed guards do not cover a near-zero or negative denominator (only a non-finite one returns None), and I did not change the statistic. A clean pass of the fixed twin may fail on K5_HOLDS_ON_NOISE for this reason, independent of the correction; the faulty twin has the same ratio.",
    ),
    "B1-08": (
        "Faulty: electrodes whose amplitude is larger on stimulus than on control trials (one-sided Welch t test across all 100 trials, p < 0.05); amplitude averaged over those electrodes; R-squared of its regression on the stimulus condition over all 100 trials >= 0.10. Fixed: electrodes selected by the same test on the odd-numbered trials (indices 0, 2, ..., 98); R-squared computed on the even-numbered trials only (indices 1, 3, ..., 99); same threshold (KRI09, introduction: selection of sensors).",
        "Faulty: R-squared of the condition on the average of electrodes chosen for a condition difference on the same trials. Fixed: R-squared of the condition on the average of electrodes chosen on other trials.",
        "R-squared of the one-predictor regression is computed as the squared correlation of the condition (as 0/1) with the electrode average. Guard minima as in the note: 2 trials per condition in the selection half (Welch), at least 3 trials in the estimation half, a stimulus with both conditions present (zero variance gives None). The fixed criterion holds on 89.5% of plus samples (above the 0.8 power target); the abstention (empty selection) rate in minus is 64/200.",
    ),
    "B1-09": (
        "Faulty: sessions averaged; voxel-wise correlation across the 16 participants with the trait; voxels with one-sided p < 0.005 (cut computed from the t distribution with 14 degrees of freedom) kept; mean of their correlations >= 0.5, computed on the same averaged data. Fixed: voxels selected from the correlations of act_session1 with the trait (same p < 0.005 rule); mean correlation of act_session2 with the trait over those voxels >= 0.5 (VUL09, abstract: reporting means of only the voxels exceeding chosen thresholds).",
        "Faulty: mean per-voxel correlation across voxels chosen for their correlation with the trait in the same data. Fixed: mean per-voxel correlation measured in a second session across voxels chosen in the first.",
        "The fixed criterion holds on 11/200 minus samples (5.5%) because the skeleton's test-retest structure carries the chance correlation of a selected voxel from session 1 into session 2; it is not repaired (PREREG_PHASE_C §2). VUL09 was read from the abstract only.",
    ),
    "B1-10": (
        "Faulty: ranks the 240 neurons by rate_pre (stable argsort, ties kept in order), takes the lowest and highest thirds (80 each), difference of mean change (rate_post minus rate_pre) lowest minus highest >= 1.0 and one-sided Welch t test at 0.05. Fixed: the same with the ranking by rate_rest (MAK19, circular analysis section: binning on the activity observed at baseline).",
        "Faulty: difference in mean change between neurons grouped by the pre-manipulation rate itself. Fixed: the same difference with groups by an independent resting recording.",
        "none",
    ),
    "B1-11": (
        "Faulty: mean amplitude in each window of 10 consecutive samples (191 windows, cumulative sums); the window with the largest patient-minus-control difference of group means over all 60 participants is picked and its mean amplitude difference is tested on the same participants (difference >= 0.5 and one-sided Welch t test at 0.05). Fixed: the window is picked on the even-indexed participants (indices 0, 2, ..., 58), the difference is tested on the odd-indexed participants (indices 1, 3, ..., 59); same width, threshold and test (MAK19, circular analysis section: defining a region of interest).",
        "Faulty: mean difference over a window chosen for the largest group difference in the same participants. Fixed: mean difference over a window chosen on other participants.",
        "Here the note says 'even-indexed', which I read as array indices 0, 2, ...; this differs from the 1-based 'even-numbered' reading used in B1-04, B1-06, B1-07 and B1-08, as the notes word it. Guard: at least 1 participant per group in the selection half (a mean is defined from 1), at least 2 per group in the test half (Welch); the note's parenthetical 'at least 2 per group' for the selection half was read as the test-half minimum only, so that the guard does not exceed the smallest defined size. The fixed criterion holds on 88.5% of plus samples and on 10/200 minus samples.",
    ),
    "B1-12": (
        "Faulty: keeps patients with score_start >= 60 and requires the proportion with score_start minus score_6m >= 10 to be >= 0.40. Fixed: keeps patients with score_screen >= 60 and requires the same proportion >= 0.40 (BAR05, abstract: baseline-selected sub-sample).",
        "Faulty: share improving by 10 points among patients chosen by the very score the improvement is measured from. Fixed: the same share among patients chosen by the independent screening score.",
        "none",
    ),
}


def pc(cid):
    r = pre[cid]
    lines = []
    for k, v in r.items():
        if k == "timing":
            continue
        lines.append(f"  * {k}: holds {v['holds']}, fails {v['fails']}, None {v['none']}, exceptions {v['errors']} (n = {v['n']})")
    return "\n".join(lines)


for cid, p in priv.items():
    a = json.loads((B1 / "cases" / cid / "ASSIGNMENT.json").read_text(encoding="utf-8"))
    b = a["brief"]
    tm = pre[cid]["timing"]
    faulty, estimand, dev = MAP[cid]
    keys = "\n".join(f"  * `{k['key']}`, {k['dtype']}, {k['shape']}: {k['meaning']}" for k in b["data_keys"])
    text = f"""# CASE {cid} (world {a['world_id']})

## 1. Identification
Case id {cid}; world id {a['world_id']}; class {a['class']}; subtype {a['subtype']}.
Mechanism tag: {p['mechanism_tag']}. Statistic family: {p['statistic_family']}.
Allowed-guard minimum (private note): {p['guard_minimum']}.
Size ratio (brief size to source size): source states none (see the sizes note of the private note: {p['sizes_note'].split('. ')[0]}).

## 2. Source and documenting passage
Source key: {p['source']}.
Passage (from the private note of the brief author): {p['passage']}
Read by the brief author (Part 1) from the URLs in `LOG.md`; I (Part 2 author) did not re-read the source and used the note's quotation.

## 3. The brief (as in `ASSIGNMENT.json`)
Claim: {b['claim']}

Data keys:
{keys}

Sizes: {json.dumps(b['sizes'])}

## 4. Mapping
{faulty}

Estimand line. {p['estimand']}
(Estimand of the two statistics as in the private note; faulty estimates it in the documented wrong way, fixed estimates the claim's quantity.)
{estimand}

Both twins are generated from the same helper text (a quadrature Student-t upper tail written with numpy only, checked against scipy in `work/test_sf.py`, absolute error below 3e-5 for 1 to 600 degrees of freedom), and the twin bodies differ only in the lines that carry the error and its correction. No randomness is used in either criterion. Returns: True or False; None only for a non-finite input, an empty selection or one below the stated minimum, or a zero variance.

## 5. Pre-checks of the fixed criterion (plain Python, 200 samples per stream, my own seeds; the faulty criterion was never run)
{pc(cid)}
  * Cross-check: the decision of the fixed criterion was compared with an independent scipy re-implementation of the same rule on 60 plus and 60 minus samples (`work/crosscheck_fixed.py`): 0 disagreements of 120.
Number of revisions of the fixed criterion: 0 (the first version was kept after the pre-check). Pre-check script: `work/precheck_fixed.py`; the probes follow `agent_docs/GATE.md` (noise: N(0,1), bool as coin flips; zeros).

## 6. Timing (final fixed criterion)
t = {tm['t']:.6f} s (mean of {tm['calls']} calls on plus samples), g = {tm['g']:.6f} s (mean plus generation, {tm['calls']} samples), S = {tm['S']} (worlds + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = {tm['estimate_s']:.1f} s (limit 900 s).

## 7. Deviations, problems, skeleton requests
{dev}
Skeleton requests: none. Size requests: none.

(The designer adds the overlap line and the size ratio.)
"""
    (B1 / "cases" / cid / "CASE.md").write_text(text, encoding="utf-8")
    print("CASE.md written", cid)
