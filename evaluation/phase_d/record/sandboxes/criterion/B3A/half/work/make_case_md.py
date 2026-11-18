"""Writes cases/<id>/CASE.md for every case (text assembled from BRIEFS.json, PRIVATE.json and the body files).

It reads the body files as text only (never imports or runs them). Run: py -I make_case_md.py
"""
import json
import os

BASE = r"E:\Claude Projects\Kapi\phase_d_work\criterion\B3A\half"
CASES = os.path.join(BASE, "cases")
briefs = {b["local_id"]: b for b in json.load(open(os.path.join(BASE, "BRIEFS.json"), encoding="utf-8"))}
private = {p["local_id"]: p for p in json.load(open(os.path.join(BASE, "PRIVATE.json"), encoding="utf-8"))}
ids = json.load(open(os.path.join(BASE, "CASE_IDS.json"), encoding="utf-8"))
rev = {v: k for k, v in ids.items()}

READER_CHI = ("The brief author read it in the Europe PMC full-text XML (saved in `fetched/chi13.txt`); I re-read the "
              "'Analyses' passage on the five methods there (random-effects, crude, Oldham, repeated measurement, Blomqvist).")
READER = {
    "PEA97": "Read by the brief author in the abstract (OpenAlex OCR text, `fetched/pea97.json`); the abstract is the whole readable text. I fetched nothing online.",
    "KRO93": "Read by the brief author in the abstract (RePEc/IDEAS page, WebFetch excerpt). I fetched nothing online.",
    "CHI13": READER_CHI + " I fetched nothing online.",
    "ARC81": "Read by the brief author in the abstract (PubMed efetch text, `fetched/arc81_pubmed.txt`); the abstract documents the coupling, not a correction (the correction used is the generic remedy of an independent measurement of the shared term; not verified in the source text). I fetched nothing online.",
}


def lines_of(path):
    return open(path, encoding="utf-8").read().split("\n")


def find(lines, first, last=None):
    """Line number range (1-based) of the line equal (after strip) to `first`, to `last` if given."""
    for i, l in enumerate(lines):
        if l.strip() == first.strip():
            if last is None:
                return (i + 1, i + 1)
            for j in range(i, len(lines)):
                if lines[j].strip() == last.strip():
                    return (i + 1, j + 1)
    raise SystemExit("marker not found: %r" % first)


def fmt(rng):
    return "line %d" % rng[0] if rng[0] == rng[1] else "lines %d-%d" % rng


SPEC = {
    "D-040": dict(
        faulty=[("a = x / z", "b = y / z"), ("r = _corr(a, b)", None)],
        fixed=[("a = x", None), ("b = y", None), ("r = _partial_corr(a, b, z)", None)],
        error="The two indices breadth/length and height/length (common denominator = length) are formed and their Pearson correlation is compared with 0.2 (`>=`). Parameters: none numeric in the source (the abstract names the case, indices with the same denominator, and states no numbers); the threshold 0.2 is the claim's. Documented in PEA97 (passage above).",
        fix="Partial correlation of breadth and height given length (correlation of the residuals of each on an intercept and length, `_partial_corr`), compared with the same 0.2, same `>=`.",
        estimand="Association between breadth and height net of length (partial correlation given length).",
        guard="3 skulls (below 3 returns None), non-finite values, zero variance of the used breadth/height quantities or of length. The partial correlation is defined from 3 observations (the residual space is one-dimensional); the private note says 4.",
        dev="Minimum 3 skulls instead of the note's 4 (the statistic is defined at 3; the rule caps the guard at the smallest defined size). Zero-variance guard is applied to the quantities that enter the statistic (the two ratios in the faulty body, breadth and height in the fixed one) and to length, plus a numerical-zero residual variance guard inside `_partial_corr` (residual variance <= 1e-24 of the total). `_resid` and `_partial_corr` are present in the faulty file as well (same helper set), unused there.",
    ),
    "D-017": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "ratio = fvc / height"),
                ("stat = abs((np.mean(ratio[smoker]) - np.mean(ratio[~smoker])) * np.mean(height))", None)],
        fixed=[("A = np.column_stack([np.ones(n), smoker.astype(float), height])", None),
               ("coef = np.linalg.lstsq(A, fvc, rcond=None)[0]", None),
               ("stat = abs(float(coef[1]))", None)],
        error="Ratio standard: difference between the group means of fvc/height, rescaled to litres at the overall mean height, in absolute value, compared with 0.2 L (`>=`). Parameters: none numeric in the source (abstract states none); the private note gives the rescaling 'at the mean height', here the mean height of all subjects. Documented in KRO93 (passage above: ratios as dependent variable).",
        fix="Analysis of covariance: least-squares fit of fvc on intercept, smoker (0/1) and height; the smoker coefficient (the mean difference at equal height) in absolute value, compared with the same 0.2 (`>=`). This is the source's correction (deflator as a covariate).",
        estimand="Difference between the group mean fvc at equal height (adjusted mean difference, litres).",
        guard="3 subjects, both groups non-empty, non-finite values, zero variance of height. Same as the private note (a fit with three parameters is defined at 3).",
        dev="none. (The choice of the mean height of all subjects for the rescaling is mine; the note leaves it open: 'rescaled to litres at the mean height, or tested at the claim's 0.2 L size'.)",
    ),
    "D-053": dict(
        faulty=[("x = u1", None)],
        fixed=[("x = u1b", None)],
        error="Crude method: Pearson correlation of the observed baseline BMI with the change (follow-up minus baseline), compared with -0.25 (`<=`). Parameters: none numeric beyond the source's scenario (ICC 95% or 50% as the world's error size); documented in CHI13, Table 1 and Analyses (2) 'Crude method', and the Glossary on mathematical coupling.",
        fix="Repeated measurement method: Pearson correlation of the second baseline reading (U1bis) with the same change, compared with the same -0.25 (`<=`). Documented in CHI13 Table 1 and Analyses (4).",
        estimand="Correlation between the baseline level (measured by the second reading, whose error is not shared with the change) and the change.",
        guard="2 children, non-finite values, zero variance of the used baseline reading or of the change (inside `_corr`). Same as the note.",
        dev="none.",
    ),
    "D-071": dict(
        faulty=[("vo2 = co * (ca - cv) * 10.0", None)],
        fixed=[("vo2 = vo", None)],
        error="Oxygen consumption calculated by the Fick equation VO2 = cardiac_output * (arterial - venous content) * 10 from the same cardiac output that enters delivery DO2 = cardiac_output * arterial content * 10; Pearson correlation of DO2 with it, compared with 0.4 (`>=`). Parameters: the factor 10 (mL/dL to mL/L); no other numeric parameter in the source. Documented in ARC81 (passage above, type 2 coupling).",
        fix="Pearson correlation of the same DO2 with the independently measured expired-gas consumption `vo2_expired_gas`, compared with the same 0.4 (`>=`). The correction is the generic remedy, not stated in the abstract (flagged in the private note).",
        estimand="Correlation between calculated oxygen delivery and consumption measured by a method that does not use cardiac output.",
        guard="2 patients, non-finite values, zero variance of delivery or of the consumption used (inside `_corr`). Same as the note.",
        dev="none. The correction is not verified in the source text (abstract only), as the private note says.",
    ),
    "D-062": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "b = ys / zs"),
                ("r = _corr(a, b)", None)],
        fixed=[("a = xs", None), ("b = ys", None), ("r = _partial_corr(a, b, zs)", None)],
        error="Within each species the Pearson correlation between femur/body_length and humerus/body_length (common denominator); the share of species with correlation >= 0.2 compared with 0.6 (`>=`). Parameters: none numeric in the source; both thresholds are the claim's. Documented in PEA97 (passage above).",
        fix="Within each species the partial correlation of femur and humerus given body_length (`_partial_corr`), same per-species threshold 0.2 and share threshold 0.6.",
        estimand="Share of species in which the association of the two bones, net of body length, reaches 0.2.",
        guard="Per species: fewer than 3 individuals (the array has fewer than 3 columns: None), non-finite value, zero variance: the species is not counted; None when no species can be counted (or there are no species). The share is taken over the counted species. Private note: same, with 4 individuals.",
        dev="Minimum 3 individuals per species instead of 4 (partial correlation is defined at 3). The share's denominator is the number of counted species (as in the note).",
    ),
    "D-038": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "x = sales / pop"),
                ("b = _std_coef(y, x.reshape(-1, 1), 0)", None)],
        fixed=[("x = sales", None), ("b = _std_coef(y, np.column_stack([x, pop]), 0)", None)],
        error="Standardised slope (slope times SD of regressor over SD of deaths) of deaths regressed on per-capita sales (sales / population) alone, absolute value compared with 0.2 (`>=`). Parameters: none numeric in the source. Documented in KRO93 (a single ratio as independent variable).",
        fix="Standardised coefficient of cigarettes_sold in the regression of deaths on cigarettes_sold and population (the denominator as a covariate), same 0.2 in absolute value. The source's correction.",
        estimand="Association of deaths with total sales at a given population (standardised partial coefficient).",
        guard="3 countries, non-finite values (a zero population gives a non-finite ratio in the faulty body), zero variance of deaths, of the regressor or of population. Same as the note.",
        dev="none. 'Zero population' is covered by the non-finite guard of the ratio in the faulty body (the fixed body does not divide).",
    ),
    "D-006": dict(
        faulty=[("r = _corr(bmi[:, 0], bmi[:, -1] - bmi[:, 0])", None)],
        fixed=[("X = np.column_stack([np.ones(m), np.arange(m, dtype=float)])", "r = float(G[0, 1] / np.sqrt(G[0, 0] * G[1, 1]))")],
        error="Crude two-wave analysis: Pearson correlation of the first-visit BMI with the change between the last and first visits, compared with -0.25 (`<=`). Parameters: none numeric beyond the source's scenario. Documented in CHI13 (Analyses (2), and the Glossary on mathematical coupling).",
        fix="Linear random-effects model of BMI on age with all visits, correlation between the random intercept (at the first visit) and the random slope, compared with the same -0.25 (`<=`). Implemented in closed form for the balanced design: per-child least-squares intercept and slope, and the covariance matrix of the random coefficients as the covariance of those estimates minus sigma^2 (X'X)^-1, with sigma^2 the pooled residual variance (the moment/REML solution when it is positive definite). The source's r_random (CHI13 Analyses (1)).",
        estimand="Correlation between a child's true level at the first visit and the true yearly rate of change.",
        guard="2 children, 3 visits (needed for the error variance), non-finite values, zero variance of the first-visit BMI or of the change (faulty, inside `_corr`); fixed: the estimated variance of the random intercept or slope not positive (correlation undefined) returns None.",
        dev="The note calls for the correction 'for the error variance estimated from the residuals'; I used the balanced-data moment solution of the random-effects model rather than an iterative REML routine (numpy only). I treat an estimated variance component <= 0 (boundary solution; the correlation is then undefined, not finite) as the zero-variance guard. On independent random arrays this guard fires in some draws (see runs), so it may return None on data without a trend; I flag this for review under the rule that None comes only from the allowed guards.",
    ),
    "D-008": dict(
        faulty=[("vo2 = co * (ca - cv) * 10.0", None)],
        fixed=[("vo2 = vo", None)],
        error="Within each patient the least-squares slope across occasions of the Fick-calculated VO2 = cardiac_output * (arterial - venous content) * 10 on DO2 = cardiac_output * arterial content * 10 (shared cardiac output); mean of the slopes compared with 0.1 (`>=`). Parameters: factor 10; none else numeric in the source. Documented in ARC81 (type 2 coupling).",
        fix="Same per-patient slope with the independently measured `vo2_expired_gas` as the response, mean over patients compared with the same 0.1 (`>=`). Generic remedy, not stated in the abstract.",
        estimand="Mean within-patient slope of measured consumption on calculated delivery.",
        guard="2 occasions, at least 1 patient with a defined slope (a patient with zero variance of delivery is not counted), non-finite values (all keys).",
        dev="Minimum 1 patient with a defined slope instead of the note's 2: a mean over one patient is defined, and the rule caps the guard at the smallest defined size. Non-finite values anywhere give None (the note allows the same).",
    ),
    "D-067": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "x = heart / body"),
                ("b = _std_coef(y, x.reshape(-1, 1), 0)", None)],
        fixed=[("y = kid", None), ("x = heart", None), ("b = _std_coef(y, np.column_stack([x, body]), 0)", None)],
        error="Standardised slope of the index kidney/body on the index heart/body (simple regression; equals their correlation), compared with 0.25 (`>=`). Parameters: none numeric in the source. Documented in PEA97 (indices with the same denominator).",
        fix="Standardised coefficient of heart weight in the regression of kidney weight on heart weight and body mass (denominator as a covariate), compared with the same 0.25 (`>=`).",
        estimand="Standardised partial slope of kidney weight on heart weight at fixed body mass.",
        guard="3 rats, non-finite values, zero variance of the response, regressor or body mass used. Same as the note.",
        dev="none.",
    ),
    "D-050": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "y = liver / body"),
                ("stat = _r2(y, age.reshape(-1, 1))", None)],
        fixed=[("y = liver", None),
               ("stat = _r2(y, np.column_stack([body, age])) - _r2(y, body.reshape(-1, 1))", None)],
        error="R-squared of the regression of the ratio liver_mass/body_mass on age_days, compared with 0.10 (`>=`). Parameters: none numeric in the source. Documented in KRO93 (a single ratio as dependent variable).",
        fix="Increase in R-squared when age_days is added to the regression of liver_mass on body_mass, compared with the same 0.10 (`>=`). The source's correction (denominator as a covariate).",
        estimand="Variance of liver mass explained by age beyond body mass.",
        guard="3 rats, non-finite values, zero variance of the response, age or body mass used. Same as the note.",
        dev="none.",
    ),
    "D-020": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "x = heart / body"),
                ("stat = _r2(y, x.reshape(-1, 1))", None)],
        fixed=[("y = liver", None), ("x = heart", None),
               ("stat = _r2(y, np.column_stack([body, x])) - _r2(y, body.reshape(-1, 1))", None)],
        error="R-squared of the regression of the index liver_weight/body_mass on the index heart_weight/body_mass (squared correlation of the two indices), compared with 0.10 (`>=`). Parameters: none numeric in the source. Documented in PEA97 (indices with the same denominator).",
        fix="Increase in R-squared when heart_weight is added to the regression of liver_weight on body_mass, compared with the same 0.10 (`>=`).",
        estimand="Variance of liver weight explained by heart weight beyond body mass.",
        guard="3 mice, non-finite values, zero variance of the response, heart quantity or body mass used. Same as the note.",
        dev="none.",
    ),
    "D-031": dict(
        faulty=[("with np.errstate(divide='ignore', invalid='ignore'):", "a = off / pop"),
                ("r = _corr(a, age)", None)],
        fixed=[("a = off", None), ("r = _partial_corr(a, age, pop)", None)],
        error="Pearson correlation between the per-capita rate offences/population and median_age, absolute value compared with 0.25 (`>=`). Parameters: none numeric in the source. Documented in KRO93 (a single ratio as dependent variable).",
        fix="Partial correlation between offences and median_age given population (correlation of the residuals on an intercept and population), same 0.25 in absolute value. The source's correction.",
        estimand="Partial correlation between total offences and median age at a given population.",
        guard="3 cities, non-finite values (a zero population gives a non-finite ratio in the faulty body), zero variance of the used offences quantity, of median age or of population.",
        dev="Minimum 3 cities instead of the note's 4 (partial correlation defined at 3). `_resid` and `_partial_corr` are present in the faulty file as well (same helper set), unused there.",
    ),
    "D-037": dict(
        faulty=[("k = 0.0", None)],
        fixed=[("k = float(np.mean(np.var(rt, axis=1, ddof=1)) / np.var(u1, ddof=1))", None)],
        error="Crude regression of change (follow-up minus baseline) on baseline BMI, slope compared with -0.2 (`<=`); the error-variance share is ignored, which is `k = 0` in the shared helper `_change_stats` (adjusted slope (b_crude + k)/(1 - k) with k = 0 is b_crude). Parameters: none numeric in the source. Documented in CHI13 (Analyses (2) and (5): b_crude).",
        fix="Blomqvist's adjusted slope (b_crude + k)/(1 - k), with k = error variance / total variance; the error variance is the mean within-child variance of the retest sample (half the mean squared difference for two sessions) and the total variance is the variance of bmi_baseline. Same -0.2 (`<=`). Documented in CHI13 Methods and Analyses (5).",
        estimand="Slope of the true change on the true baseline level.",
        guard="2 children in the main sample and in the retest sample, 2 sessions, non-finite values, zero variance of the baseline (or of the change), non-finite adjusted slope (k = 1).",
        dev="none. The faulty body passes the literal `k = 0.0` so that the helper, identical in both files, reduces to the crude slope; the retest array is read and checked for finite values in both files but only used in the fixed one.",
    ),
    "D-015": dict(
        faulty=[("k = 0.0", None)],
        fixed=[("icc = _corr(u1, u1b)", "k = 1.0 - icc")],
        error="R-squared of the crude regression of change on baseline (squared crude correlation, the share of variance of observed change explained by observed baseline) compared with 0.10 (`>=`); the error-variance share is ignored (`k = 0` in the shared helper `_change_stats`). Parameters: none numeric in the source. Documented in CHI13 (Analyses (2)).",
        fix="Squared Blomqvist-adjusted correlation: k = 1 - corr(bmi_baseline, bmi_baseline_retest) (the source's k = 1 - ICC between short-term repeated measurements), adjusted slope (b_crude + k)/(1 - k), converted to a correlation with the SD of the true baseline (SD of baseline times sqrt(1 - k)) and the SD of the true change (variance of the observed change minus 2 k times the baseline variance, equal error variance at both visits); squared and compared with the same 0.10 (`>=`). Documented in CHI13 Analyses (5).",
        estimand="Share of the variance of the true change explained by the true baseline level (r_Blomqvist squared).",
        guard="2 children, non-finite values, zero variance of the baseline, of the change or of the retest reading, adjusted correlation not finite (k = 1, or a true-change variance estimate that is not positive).",
        dev="The source says only 'the corresponding correlation r Blomqvist was estimated'; the conversion to a correlation follows the private note ('with the SDs of the true baseline and change') and the derivation above, which is mine. Verified on my own large array that it recovers the known value (see runs). A non-positive estimated true-change variance (undefined correlation) returns None as a non-finite result.",
    ),
    "D-036": dict(
        faulty=[("x = cot", None)],
        fixed=[("x = cof", None)],
        error="R-squared of the regression of systemic vascular resistance SVR = 80 * (MAP - CVP) / co_thermodilution on the same co_thermodilution, compared with 0.25 (`>=`). Parameters: the factor 80; none else numeric in the source. Documented in ARC81 (a variable that contains the other directly).",
        fix="R-squared of the regression of the same SVR on the independently measured co_fick, compared with the same 0.25 (`>=`). Generic remedy, not stated in the abstract.",
        estimand="Share of variance of calculated resistance explained by an independently measured cardiac output.",
        guard="2 patients, non-finite values (a zero thermodilution output gives a non-finite resistance), zero variance of resistance or of the cardiac output used.",
        dev="none. The correction is not verified in the source text (abstract only), as the private note says.",
    ),
}

RUNS_COMMON = ("Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. "
               "(2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and "
               "maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly "
               "does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.")

SMOKE = {}
for line in open(os.path.join(BASE, "work", "run_fixed_output.txt"), encoding="utf-8"):
    parts = line.split()
    if parts and parts[0].startswith("D-") and "types" in line:
        SMOKE[parts[0]] = line.strip()

EXTRA_RUNS = {
    "D-006": " Estimator check (`work/check_estimators.py`, n = 200000, known truth): true corr(b0, b1) -0.6270, corrected estimator -0.6289, uncorrected per-child OLS -0.6857. On the independent random smoke arrays the result was None in some draws (estimated slope variance not positive) and bool in others.",
    "D-015": " Estimator check (n = 200000, known truth): true corr(level, change) -0.6270, crude -0.6542, adjusted -0.6287 (k 0.4994). On the independent random smoke arrays the result was None in some draws (k >= 1 or non-positive true-change variance) and bool in others.",
    "D-037": " Estimator check (n = 200000, known truth): true slope -0.5019, crude -0.7521, adjusted -0.5048; k from a retest sample 0.5016 (true 0.4999).",
    "D-040": " Estimator check: partial correlation on a known structure, true 0.5000, estimated 0.5021 (n = 100000).",
    "D-038": " Estimator check: standardised coefficient on a known structure, true 0.1778, estimated 0.1766 (n = 100000).",
}

REVISIONS = {
    "D-015": "1 revision of the fixed body after its first run (the shared helper `_change_stats` returned None whenever the correlation was not finite; it now returns both numbers and each caller checks the one it uses; the criterion's docstring was extended). Both files changed alike.",
    "D-037": "1 revision of the fixed body after its first run (same helper change as D-015: the first version returned None when the correlation was not finite although this claim uses only the slope; D-037 returned None on some independent random arrays for this reason). Both files changed alike.",
    "D-006": "1 revision after its first run, docstring only (the None condition of the fitted model was added to the docstring). Both files changed alike.",
}


def main():
    for local, cid in sorted(ids.items(), key=lambda kv: kv[1]):
        b = briefs[local]
        p = private[local]
        sp = SPEC[cid]
        fl = lines_of(os.path.join(CASES, cid, "faulty_body.py"))
        xl = lines_of(os.path.join(CASES, cid, "fixed_body.py"))
        fparts = []
        for first, last in sp["faulty"]:
            rng = find(fl, first, last)
            fparts.append("%s: `%s`%s" % (fmt(rng), first, (" ... `%s`" % last) if last else ""))
        xparts = []
        for first, last in sp["fixed"]:
            rng = find(xl, first, last)
            xparts.append("%s: `%s`%s" % (fmt(rng), first, (" ... `%s`" % last) if last else ""))
        keys = "\n".join("  - `%s` %s %s: %s" % (k["key"], k["shape"], k["dtype"], k["meaning"]) for k in b["data_keys"])
        out = []
        out.append("# CASE %s (author-local id %s)\n" % (cid, local))
        out.append("## 1. Case\n- Case id: %s (brief author's local id %s)\n- Class: B-3, coupling by construction (half A)\n- Tag: %s; statistic family: %s; role %s\n" % (
            cid, local, p["mechanism_tag"], p["statistic_family"], p["notes"].split(".")[0].replace("Role: ", "")))
        out.append("## 2. Source and documenting passage\n- Source key: %s\n- Passage: %s\n- Read: %s\n" % (p["source"], p["passage"], READER[p["source"]]))
        out.append("## 3. Brief\n- Claim: %s\n- Data keys:\n%s\n- Sizes: %s\n" % (b["claim"], keys, json.dumps(b["sizes"])))
        out.append("## 4. Mapping\n- **Faulty body, the error** (`faulty_body.py`): %s\n  - %s\n- **Fixed body, the correction** (`fixed_body.py`): %s\n  - %s\n- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).\n- **Estimand:** %s\n" % (
            "; ".join(fparts), sp["error"], "; ".join(xparts), sp["fix"], sp["estimand"]))
        out.append("## 5. Allowed-guard minimum\n%s\n" % sp["guard"])
        out.append("## 6. Runs of the fixed body\n%s\n- Smoke result (3 arrays): `%s`\n- Fixed-body revisions: %s\n" % (
            RUNS_COMMON + EXTRA_RUNS.get(cid, ""), SMOKE[cid], REVISIONS.get(cid, "0")))
        out.append("## 7. Deviations from the private note, and problems\n%s\n" % sp["dev"])
        with open(os.path.join(CASES, cid, "CASE.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out))
        print("wrote CASE.md", cid)


if __name__ == "__main__":
    main()
