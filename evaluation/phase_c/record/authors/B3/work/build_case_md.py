# Scratch (Part 2): writes CASE.md for each B-3 case from ASSIGNMENT.json, PRIVATE.json and the logged pre-check numbers.
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
priv = {p["local_id"]: p for p in json.loads((ROOT / "PRIVATE.json").read_text(encoding="utf-8"))}

# pre-check run 1 (work/precheck_fixed_run1.txt), 300 samples per stream, seeds in precheck_fixed.py
PRE = {
 "B3-01": dict(plus=(282, 18, 0), minus=(24, 276, 0), controls={"permute_treated": (15, 285, 0)}, noise=(14, 286, 0)),
 "B3-02": dict(plus=(300, 0, 0), minus=(0, 300, 0), controls={"permute_age_across_participants": (0, 300, 0)}, noise=(0, 300, 0)),
 "B3-03": dict(plus=(298, 2, 0), minus=(0, 300, 0), controls={"permute_lv_mass": (0, 300, 0), "permute_lv_mass_residual": (0, 300, 0)}, noise=(0, 300, 0)),
 "B3-04": dict(plus=(300, 0, 0), minus=(48, 252, 0), controls={"permute_kidney_within_body_mass_blocks": (58, 242, 0)}, noise=(0, 300, 0)),
 "B3-05": dict(plus=(300, 0, 0), minus=(0, 300, 0), controls={"permute_tibia_within_humerus_blocks": (0, 300, 0)}, noise=(0, 300, 0)),
 "B3-06": dict(plus=(300, 0, 0), minus=(0, 300, 0), controls={"decouple_observers_within_true_value_blocks": (0, 300, 0)}, noise=(0, 300, 0)),
 "B3-07": dict(plus=(300, 0, 0), minus=(0, 300, 0), controls={"permute_abdomen_within_species": (0, 300, 0)}, noise=(0, 300, 0)),
 "B3-08": dict(plus=(275, 25, 0), minus=(0, 300, 0), controls={"permute_second_baseline_across_patients": (0, 300, 0)}, noise=(1, 299, 0)),
 "B3-09": dict(plus=(300, 0, 0), minus=(5, 295, 0), controls={"permute_uptake_across_patients": (1, 299, 0)}, noise=(5, 295, 0)),
 "B3-10": dict(plus=(300, 0, 0), minus=(0, 300, 0), controls={"permute_item1_across_patients": (0, 300, 0)}, noise=(0, 0, 300)),
 "B3-11": dict(plus=(280, 20, 0), minus=(0, 300, 0), controls={"permute_gene_a_across_samples": (0, 300, 0)}, noise=(9, 291, 0)),
 "B3-12": dict(plus=(286, 14, 0), minus=(35, 265, 0), controls={"permute_time_across_months": (14, 286, 0), "reverse_time": (0, 300, 0)}, noise=(14, 286, 0)),
}
# (t ms, g ms, S, estimate s)
TIM = {
 "B3-01": (0.181, 0.017, 5, 0.5), "B3-02": (0.059, 0.065, 5, 0.3), "B3-03": (0.081, 0.035, 6, 0.3),
 "B3-04": (0.033, 0.019, 5, 0.1), "B3-05": (0.061, 0.055, 5, 0.3), "B3-06": (0.123, 0.032, 5, 0.4),
 "B3-07": (0.359, 0.047, 5, 1.0), "B3-08": (0.039, 0.028, 5, 0.2), "B3-09": (0.040, 0.042, 5, 0.2),
 "B3-10": (0.020, 0.094, 5, 0.3), "B3-11": (0.061, 0.022, 5, 0.2), "B3-12": (0.237, 0.065, 6, 0.8),
}

# what was implemented, in plain words, per case (guard minima as coded)
IMPL = {
 "B3-01": ("Faulty: ordinary least squares of the quotient heart_weight / body_mass on treatment status, one-sided t test of the treatment coefficient (positive and p < 0.05). "
           "Fixed: ordinary least squares of heart_weight on treatment status and body_mass, same one-sided t test of the treatment coefficient. Both use one OLS-t routine and one Student-t tail routine (numerical integration, no scipy).",
           "Faulty guard: residual df >= 1 (n >= 3); fixed guard: residual df >= 1 (n >= 4, as the note says); no animal in one group or zero residual variance -> None; non-finite -> None."),
 "B3-02": ("Faulty: Pearson correlation of age with albumin_excretion / creatinine_excretion, holds when r >= 0.15. Fixed: partial correlation of albumin_excretion and age given creatinine_excretion (residuals on an intercept and creatinine, then Pearson r), holds when >= 0.15. One routine, with an empty covariate list in the faulty version.",
           "Faulty n >= 3 (Pearson), fixed n >= 4 (one covariate), as the note; zero variance of a variable or residual -> None; non-finite -> None."),
 "B3-03": ("Faulty: R-squared of systolic_bp regressed on the quotient lv_mass / body_surface_area, holds when >= 0.05. Fixed: R-squared of systolic_bp on body_surface_area and lv_mass minus R-squared on body_surface_area alone, holds when the gain >= 0.05.",
           "Faulty n >= 3, fixed n >= 4 (2 predictors plus intercept, 1 residual df); zero variance of a variable entering the statistic -> None; non-finite -> None."),
 "B3-04": ("Faulty: slope of the simple regression of liver_weight / body_mass on kidney_weight / body_mass, holds when >= 0.25. Fixed: coefficient of kidney_weight in the OLS regression of liver_weight on kidney_weight and body_mass, holds when >= 0.25.",
           "Faulty n >= 3, fixed n >= 4; zero variance of the predictor (after removing the other columns) -> None; non-finite -> None."),
 "B3-05": ("Faulty: Pearson correlation of femur_length / humerus_length with tibia_length / humerus_length, holds when r >= 0.3. Fixed: partial correlation of femur_length and tibia_length given humerus_length, holds when >= 0.3.",
           "Faulty n >= 3, fixed n >= 4; zero variance -> None; non-finite -> None."),
 "B3-06": ("Faulty: relative error (estimate - true_value) / true_value of each observer; mean over the three observer pairs of the Pearson correlation of the relative errors across trials, holds when the mean >= 0.2. Fixed: for each observer pair the partial correlation of the two estimates given true_value, mean over pairs, holds when >= 0.2. Pairs are formed from the columns of estimates.",
           "Faulty n >= 3, fixed n >= 4 per pair; fewer than 2 observers -> None; zero variance of any residual -> None; non-finite -> None."),
 "B3-07": ("Faulty: per species, the slope of claw_length / body_length on abdomen_length / body_length across individuals; mean of the species slopes, holds when >= 0.15. Fixed: per species, the coefficient of abdomen_length in the OLS regression of claw_length on abdomen_length and body_length; mean over species, holds when >= 0.15.",
           "Faulty n >= 3, fixed n >= 4 individuals per species; a species with an undefined coefficient (zero variance) makes the criterion return None; non-finite -> None."),
 "B3-08": ("Faulty: Pearson correlation across patients between the fall (sbp_baseline_first - sbp_week12) and sbp_baseline_first, holds when r >= 0.3. Fixed: Pearson correlation between the same fall and sbp_baseline_second, holds when >= 0.3.",
           "n >= 3 in both; zero variance -> None; non-finite -> None."),
 "B3-09": ("Faulty: Pearson correlation between oxygen delivery (cardiac_output * arterial_o2_content) and the uptake calculated from the same cardiac output, cardiac_output * (arterial_o2_content - venous_o2_content), holds when r >= 0.3. Fixed: Pearson correlation between the same delivery and o2_uptake_expired, holds when >= 0.3. The constant 10 of the unit conversion does not change a correlation and is left out.",
           "n >= 3 in both; zero variance -> None; non-finite -> None."),
 "B3-10": ("Faulty: label = total over all eight items >= 12; rank-based AUC (ties counted one half) of the item 1 score for that label, holds when AUC >= 0.65. Fixed: label = total over items 2 to 8 >= 12, the same AUC, holds when >= 0.65.",
           "Either label class empty -> None (smallest size at which an AUC is defined: one patient per class); non-finite -> None."),
 "B3-11": ("Faulty: R-squared of the regression of gene_b_expression / gene_c_expression on gene_a_expression / gene_c_expression, holds when >= 0.05. Fixed: gain in R-squared when gene_a_expression is added to the regression of gene_b_expression on gene_c_expression, holds when the gain >= 0.05.",
           "Faulty n >= 3, fixed n >= 4; zero variance of a variable entering the statistic -> None; non-finite -> None."),
 "B3-12": ("Faulty: OLS of admissions / population on time_years, one-sided t test of the time coefficient (positive and p < 0.05). Fixed: OLS of admissions on time_years and population, same one-sided t test of the time coefficient.",
           "Faulty residual df >= 1 (n >= 3), fixed n >= 4; zero variance of time_years (after removing population) or perfect fit -> None; non-finite -> None."),
}

DEV = {
 "B3-01": ("The note names a Welch test for the faulty version. I implemented the faulty comparison as the pooled-variance two-sample t test (OLS of the quotient on treatment status) so that both versions share one OLS-t routine and the same one-sided 5% rule (audit items (b), (g)); with 24 + 24 animals the two tests differ negligibly. "
           "The note's guard on zero variance of body_mass is replaced by the guard on the treatment coefficient (constant body mass does not make that coefficient undefined). The p value comes from a numerical integral (max abs. error against scipy 2e-6 over df 1 to 797, scratch check work/check_tsf.py), because only numpy may be used."),
 "B3-02": "none",
 "B3-03": "none",
 "B3-04": "The fixed criterion holds in 16% of minus samples and 19% of the control samples (see the pre-check). The claim's threshold (coefficient >= 0.25) has a sampling standard deviation of about 0.3 at 150 mice in these worlds, so the criterion is a weak test at this size. Not repaired, per AUTHOR_PHASE2_C.md; it stays in the table.",
 "B3-05": "none",
 "B3-06": "none",
 "B3-07": "The note says a species with too few individuals is skipped; I return None when any species has an undefined coefficient (all species have the same number of individuals in the array, so the skip rule would only matter for a zero-variance species; one undefined species is read as 'the statistic is not defined' rather than silently dropped).",
 "B3-08": "The brief's claim names sbp_baseline_second; the faulty criterion deliberately uses sbp_baseline_first (the documented error), as the private note planned. No other deviation.",
 "B3-09": "The faulty criterion does not read o2_uptake_expired and the fixed criterion does not read venous_o2_content (as planned in the note).",
 "B3-10": "On i.i.d. N(0,1) noise the fixed criterion returns None in all 300 samples because no row reaches a total of 12 over items 2 to 8 and one label class is empty (the 'empty selection' guard); this is an abstention, not a claim.",
 "B3-11": "none",
 "B3-12": "The fixed criterion holds in 11.7% of minus samples (nominal 5%): the skeleton's months carry autocorrelated variation, which the ordinary one-sided t test of the fixed criterion (the rule in the claim) does not model. Not bent; it stays in the table.",
}


def line(name, trip):
    h, f, u = trip
    n = h + f + u
    return f"{name}: holds {h}/{n}, fails {f}/{n}, None {u}/{n} (rate {h / n:.3f})"


for cid, p in priv.items():
    a = json.loads((ROOT / "cases" / cid / "ASSIGNMENT.json").read_text(encoding="utf-8"))
    b = a["brief"]
    keys = "\n".join(f"  * `{k['key']}` {k['shape']} {k['dtype']}: {k['meaning']}" for k in b["data_keys"])
    pre = PRE[cid]
    pre_lines = [line("plus", pre["plus"]), line("minus", pre["minus"])]
    pre_lines += [line("control " + k, v) for k, v in pre["controls"].items()]
    pre_lines += [line("noise probe (i.i.d. N(0,1) / Bernoulli(0.5) per array, as GATE.md describes)", pre["noise"]), "zeros probe: 1 sample, None (zero variance guard)"]
    t, g, S, est = TIM[cid]
    impl, guard = IMPL[cid]
    text = f"""# CASE {cid}

## 1. Identity
Case id {cid}; world id {a['world_id']}; class {a['class']}; subtype {a['subtype'] if a['subtype'] else 'none (n/a)'}.

## 2. Source and documenting passage
Source key {p['source']}. Passage (as recorded in the part-1 private note): {p['passage']}
Read by the part-1 author of this class (the earlier agent in the same role), as the note and `LOG.md` part 1 state (Europe PMC / EconPapers / archive.org OCR records). In part 2 I did not fetch any source or URL; I relied on the note.

## 3. Brief (as in ASSIGNMENT.json)
Claim: {b['claim']}
Data keys:
{keys}
Sizes: {b['sizes']}

## 4. Mapping
Documented error (note): {p['faulty']}
Documented correction (note): {p['fixed']}
As implemented. {impl}
Guards as coded: {guard}
No randomness is used by either criterion (no `rng` is created); the answer is a function of the data only.
Estimand line (from the note): {p['estimand']}
Mechanism tag {p['mechanism_tag']}, statistic family {p['statistic_family']} (note).

## 5. Pre-checks of the fixed criterion (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_run1.txt`)
Run 1, 300 samples per stream, seeds fixed in the script; fixed criterion only, the faulty file was never imported or run.
""" + "\n".join("* " + x for x in pre_lines) + f"""
Number of revisions of the fixed criterion: 0.

## 6. Timing (fixed criterion, mean of 40 calls on plus samples; plus generation mean of 40 calls)
t = {t:.3f} ms, g = {g:.3f} ms, S = {S} (worlds 2 + controls + premises + relational pairs, plus 2), estimate 2 x 200 x (S + 1) x (t + g) = {est:.1f} s (limit 900 s). No speed change was needed.

## 7. Deviations, problems, skeleton requests
{DEV[cid]}
Skeleton requests: none. Size requests: none.
"""
    (ROOT / "cases" / cid / "CASE.md").write_text(text, encoding="utf-8", newline="\n")
    print("wrote", cid)
