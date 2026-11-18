"""Writes cases/<id>/CASE.md from BRIEFS.json, PRIVATE.json, CASE_IDS.json and the hand-written mapping below."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HALF = os.path.join(HERE, "..")
briefs = {b["local_id"]: b for b in json.load(open(os.path.join(HALF, "BRIEFS.json"), encoding="utf-8"))}
priv = {p["local_id"]: p for p in json.load(open(os.path.join(HALF, "PRIVATE.json"), encoding="utf-8"))}
ids = json.load(open(os.path.join(HALF, "CASE_IDS.json"), encoding="utf-8"))

COMMON_RUNS = ("`work\\check_fixed.py`: form check of `fixed_body.py` (passes), then 2 self-generated noise arrays with the "
               "brief's keys, shapes and dtypes, 2 calls each (4 calls): every call returned a bool, the two calls on "
               "the same array agreed, time per call {t} s. `work\\sanity_fixed.py`: 1 call on an array with a strong "
               "planted signal ({sig}), and guard checks ({guards}). `work\\test_helpers.py`: unit checks of the "
               "helpers that this file shares with the other cases (see LOG.md). No rate was estimated and nothing was "
               "tuned. `faulty_body.py`: syntax check only (`ast.parse`), passed; it was never run or analysed.")

M = {}

M["B2A-01"] = dict(
    sub="L1.1 (no test set)",
    faulty_lines="L44: `pred = ridge_predict(ridge_fit(X, y, 1.0), X)` - the model is fitted on all 100 rows and scored on the same rows "
                 "(R-squared of the fitted values). Parameters: ridge penalty 1.0, standardised measurements, intercept (all in the claim); "
                 "100 x 150 from the brief; the source states no sample size or feature count (private note: `sizes_note`).",
    fixed_lines="L44-48: 5-fold cross-validation, fold of row i = i mod 5, one ridge fit per fold (standardisation fitted inside `ridge_fit` on the "
                "training rows), pooled held-out predictions; the R-squared lines after it (SST around the mean of y over all rows) are identical in both files.",
    estimand="expected out-of-sample R-squared of the ridge model fitted on 80 samples and applied to new samples (the private note's fixed estimand).",
    guard="2 rows; zero variance of y; non-finite values in X or y.",
    t="0.001", sig="150 features, 10 informative", guards="NaN in X, constant y",
    dev="none")

M["B2A-02"] = dict(
    sub="L1.1 (no test set)",
    faulty_lines="L55: `pred = poly_predict(poly_fit(X, y), X)` - second-order polynomial OLS (66 coefficients: intercept, 10 linear, 10 squares, 45 products; "
                 "helper `poly_features` returns 66 columns for 10 readings, checked) fitted on all 300 rows, correlation of its fitted values with y on the same rows. "
                 "Model and size from the claim and the brief; the source states none.",
    fixed_lines="L55-59: 5-fold cross-validation (fold = i mod 5) with the same polynomial fit per fold; the Pearson correlation of the pooled held-out predictions with y "
                "over all 300 rows (the post-lines are identical in both files).",
    estimand="the correlation between out-of-sample predictions and observed outcomes for new runs.",
    guard="2 rows; zero variance of the predictions or of y; non-finite values.",
    t="0.012", sig="quadratic term in two readings", guards="constant y",
    dev="none")

M["B2A-03"] = dict(
    sub="L1.2 (pre-processing on training and test set)",
    faulty_lines="L71: `Xc = impute(X, np.ones(n, dtype=bool), y[:, None])` - the iterative ridge imputation (helper `impute`, 5 sweeps = default `sweeps=5`, ridge penalty 1.0, "
                 "start from column means) is run once on all 250 rows with y as an extra regressor, before the 5-fold loop (L72-74) that runs ridge on the completed X. "
                 "Parameters (5 sweeps, penalty 1.0, y used) from the private note; the proposed 25% missing rate is the note's, not a source value.",
    fixed_lines="L73: `Xc = impute(X, ~te, np.empty((n, 0)))` inside the fold loop - regressions fitted on the training rows only, no y (empty auxiliary block), applied to training and held-out rows; "
                "column means from the training rows.",
    estimand="the out-of-sample R-squared for new patients whose outcome is unknown when their missing values are filled.",
    guard="2 rows; zero variance of y; infinite values in X or non-finite y; a column with no observed value in the fitting rows gives non-finite predictions, so R-squared is non-finite and None is returned. NaN in X is data (missing values), not a guard.",
    t="0.034", sig="5 informative columns, 25% NaN", guards="a fully missing column (returns None, with numpy RuntimeWarnings from empty means)",
    dev="Columns are updated in ascending order within a sweep, each regression seeing the current filled values (Gauss-Seidel); the private note does not fix the order. In the faulty body the held-out rows are the same rows as the fitting rows, as the note says (imputation once on all rows).")

M["B2A-04"] = dict(
    sub="L1.2 (pre-processing on training and test set; target encoding, from the task's subtype list)",
    faulty_lines="L54-55: `enc = Cf @ district_means(C, y, all rows)` and the design matrix are built once from the district means of all 1200 rows, before the 5-fold loop; "
                 "a held-out row's encoding therefore contains its own outcome. Parameters (about 8 rows per district, 150 districts) from the brief's sizes; the source states none.",
    fixed_lines="L56-57 inside the loop: `enc = Cf @ district_means(C, y, ~te)` and the design matrix from the training rows only (training rows use their own training mean, held-out rows the training mean of their district, the training grand mean if the district is absent).",
    estimand="the out-of-sample correlation for new patients, whose outcome is unknown when the district is encoded.",
    guard="2 rows; zero variance of predictions or y; non-finite covariates or y.",
    t="0.002", sig="district effect + one covariate", guards="no guard run",
    dev="Source-basis caveat as in the private note: KAP23's quoted sentence names imputation and over/under sampling; target encoding comes from the subtype definition. A row with no True in `category` would get encoding 0 (not expected under the brief's meaning).")

M["B2A-05"] = dict(
    sub="L1.3 (feature selection on training and test set)",
    faulty_lines="L88: `sel = top_t(X, y, 20)` - the 20 features with the largest absolute Welch t statistic are chosen on all 80 rows, before the 5-fold loop (L89-91) that fits the ridge classifier on them. "
                 "Parameters: 20 features, penalty 10, +/-1 coding from the claim; stratified folds from the private note.",
    fixed_lines="L90: `sel = top_t(X[~te], y[~te], 20)` inside the fold loop - the choice uses the training rows only.",
    estimand="the out-of-sample AUC of the whole pipeline (feature choice plus classifier) for new subjects.",
    guard="1 case and 1 control; constant scores (zero variance); non-finite X.",
    t="0.002", sig="20 shifted features", guards="a single class",
    dev="The private note says 'two-sample t statistic'; the Welch form is used (pooled-variance form would pick nearly the same features). Ties in the t ranking are broken by column index (stable sort).")

M["B2A-06"] = dict(
    sub="L1.4 (duplicates)",
    faulty_lines="L54-63 (the common post block, identical in the fixed file apart from the reduction inserted before it): `fold = np.arange(n) % 5`, `cv_nn` and the skill on all 600 rows as given, repeated records kept. "
                 "The error is the absence of any reduction of repeated records before the cut. Parameters: one neighbour, standardised distance, 10% MAE skill from the claim; the share of exact repeats is the world author's (the note's 0.3 is proposed; the source states none).",
    fixed_lines="L54-62: rows with an identical X vector (squared standardised distance < 1e-16, i.e. distance < 1e-8, computed by direct differences so identical rows give exactly 0) are reduced to the first of each group; "
                "then n is recomputed and the same cross-validation runs on the remaining rows.",
    estimand="skill for new distinct entries.",
    guard="2 rows (before and after the reduction; one-nearest-neighbour cross-validation needs a held-out and a fitting row, so 2 rather than the note's 1 held-out row); zero MAE of the mean predictor; non-finite values.",
    t="0.014", sig="X1 squared plus X2 (array also contains 180 exact repeats)", guards="constant y",
    dev="Guard minimum 2 rows instead of 1 (see item 5); the guard_minimum 1 of the note counts held-out rows.")

M["B2A-07"] = dict(
    sub="L1.4 (duplicates)",
    faulty_lines="L74: `fold = np.arange(n) % 5` - records are assigned to folds without regard to near copies, so a held-out record can have a near copy among the fitting records. "
                 "Parameters: one neighbour, correlation 0.30 from the claim; near-copy share proposed by the note (0.3), source states none.",
    fixed_lines="L74: `fold = link_components(X, 0.1) % 5` - single-linkage components of records closer than 0.1 times the median pairwise standardised distance are placed whole into one fold "
                "(component number by first member, mod 5); helper `link_components`, checked against an independent union-find on a random array and on a planted chain of near copies.",
    estimand="the correlation for new compounds that have no near-identical record among those used to fit.",
    guard="2 records; zero variance of predictions or y; non-finite values.",
    t="0.042", sig="y = X1 + noise", guards="no guard run",
    dev="none")

M["B2A-08"] = dict(
    sub="L3.1 (temporal leakage)",
    faulty_lines="L56-62: days assigned to 5 folds by a fixed pseudo-random permutation (`default_rng(0)`), ridge fitted on days around the held-out ones, correlation over all 1000 days (`ev` all True). "
                 "Parameters from the claim and the private note; the autocorrelation (0.8) is the note's proposal, the source states none.",
    fixed_lines="L56-60: forward chaining - `np.array_split(np.arange(n), 6)[1:]` gives the blocks 2 to 6; the model is fitted on all days before the block except the last 5 (`blk[0] - 5`), predicts the block; correlation over blocks 2 to 6 only (`ev`).",
    estimand="the correlation between forecasts and outcomes on days after all fitting days.",
    guard="2 days; zero variance of the forecasts or y; non-finite values.",
    t="0.001", sig="slowly varying predictor", guards="no guard run",
    dev="Block sizes from `np.array_split` of 1000 into 6 are 167, 167, 167, 167, 166, 166, so the first forecast day is index 167 (the 168th day) and the last is index 999; the note's 'days 168 to 999' is read this way. Only the faulty body uses randomness (`default_rng(0)`); the fixed body has none.")

M["B2A-09"] = dict(
    sub="L3.1 (temporal leakage)",
    faulty_lines="L48-54 and L56: the 10,000 station-days are pooled, assigned to 5 folds by a fixed permutation (`default_rng(0)`), ridge cross-validation; skill over days 2 to T (`ev[:, 1:]`). "
                 "Parameters: penalty 1.0, 5% skill, persistence baseline from the claim; the source states no autocorrelation.",
    fixed_lines="L48-51 and L53: ridge fitted on all stations for the first `(7 * T) // 10` = 175 days, forecasts the remaining 75 days (`ev[:, cut:]`); persistence = y of the previous day (for the first forecast day the last fitting day's y).",
    estimand="skill on days after every fitting day.",
    guard="a forecast day must exist (`ev.any()`); zero MSE of the persistence forecast; non-finite values.",
    t="0.001", sig="y driven by X1", guards="constant y",
    dev="The 70% split is computed as `(7 * T) // 10` = 175 days for T = 250 (integer arithmetic). Only the faulty body uses randomness.")

M["B2A-10"] = dict(
    sub="L3.2 (non-independence between training and test samples)",
    faulty_lines="L58-60: the 1800 subject-trial rows are pooled and assigned to 5 folds by a fixed permutation (`default_rng(0)`), so trials of one subject appear on both sides. "
                 "Parameters: penalty 1.0, 5% MAE skill from the claim; the source states no subject or trial counts.",
    fixed_lines="L58: `fold = np.repeat(np.arange(S) % 5, T)` - all trials of a subject in the same fold (subject index mod 5); the rest (ridge, mean predictor of the training folds, MAE skill) is the same code.",
    estimand="skill for trials of new subjects.",
    guard="at least 2 rows in all, i.e. 1 held-out trial (S*T >= 2); zero MAE of the mean predictor; non-finite values.",
    t="0.003", sig="y driven by one feature", guards="constant y",
    dev="none")

M["B2A-R1"] = dict(
    sub="L1.1 (no test set), reserve",
    faulty_lines="L39-41: OLS (intercept + 25 features, numpy lstsq) fitted on all 60 rows and evaluated on the same rows; baseline = mean of y over the same rows. Parameters: 25 features, 60 samples from the brief; 10% skill from the claim.",
    fixed_lines="L39-44: 5-fold cross-validation (fold = i mod 5), OLS fitted on 48 rows predicts 12; pooled MAE against the training-fold mean predictor (`fold_mean_baseline`).",
    estimand="expected out-of-sample MAE skill.",
    guard="zero MAE of the mean predictor; at least 2 samples; non-finite values.",
    t="0.001", sig="3 informative features", guards="no guard run",
    dev="none")

M["B2A-R2"] = dict(
    sub="L1.2 (pre-processing on training and test set), reserve",
    faulty_lines="L93-96: missing entries replaced by the column mean within the same outcome class (y True or False), computed over all 1400 rows, before the stratified 5-fold loop (L97-99). Parameters: ridge penalty 1.0, 25 Newton iterations (helper `logit_fit`), AUC 0.75; the 30% missing rate is the note's proposal.",
    fixed_lines="L95: `Xc = fill(X, col_means(X, ~te))` inside the loop - missing entries of training and held-out rows are replaced by the column mean of the training rows; no label used.",
    estimand="the out-of-sample AUC for new country-years with the label unknown.",
    guard="1 onset and 1 non-onset; constant scores; non-finite scores (a column with no value in the class or fold); infinite values in X. NaN in X is data.",
    t="0.012", sig="two informative indicators, 30% NaN, 61 events", guards="no guard run",
    dev="Penalised logistic regression is written as: Newton iterations from zero, intercept unpenalised, penalty (lambda/2) times the sum of squared coefficients (gradient `+ lambda * w`) on columns standardised with the fitting rows; the note says only 'lambda 1.0, 25 iterations'. The score is the linear predictor (monotone in the probability).")

M["B2A-R3"] = dict(
    sub="L1.3 (feature selection on training and test set), reserve",
    faulty_lines="L57: `sel = top_corr(X, y, 20)` - the 20 features with the largest absolute Pearson correlation with y chosen on all 100 rows, before the fold loop; ridge penalty 10 on them. Parameters from the claim.",
    fixed_lines="L59: `sel = top_corr(X[~te], y[~te], 20)` inside the fold loop (training rows only).",
    estimand="the out-of-sample R-squared of the whole pipeline (choice plus ridge) for new samples.",
    guard="2 rows; zero variance of y; non-finite values.",
    t="0.002", sig="20 informative features of 500", guards="no guard run",
    dev="none")

M["B2A-R4"] = dict(
    sub="L1.4 (duplicates; oversampling by copying, under the task's tie-break), reserve",
    faulty_lines="L50-55 and L58-59: the True rows are copied (`rng.choice(..., replace=True)` with `default_rng(0)`) until the classes are equal, on all 1000 rows, before the cut; folds = i mod 5 over the enlarged table; balanced accuracy over its held-out rows (`ya`, `pred`). Parameters: one neighbour, 0.65 from the claim; the 8% minority share is the note's proposal.",
    fixed_lines="L50-51 and L54-59: stratified folds on the original rows, copies made inside each fold among the training rows only, held-out rows untouched; balanced accuracy over the original rows.",
    estimand="balanced accuracy for new patients drawn with the original class balance.",
    guard="at least 2 rows in each class (covers 'a class absent in a held-out pool'); non-finite X.",
    t="0.010", sig="2 informative columns of 15, 69 positives; it returned False", guards="a single positive; the separate script `work\sanity_d066.py` then ran a clustered rare class (103 positives; True) and noise (False)")
M["B2A-R4"]["dev"] = ("The note says rows with y True are copied; if True were the majority the copy count is 0 (`max(..., 0)`) and nothing is copied. "
                      "On the planted-signal array of `sanity_fixed.py` (signal in 2 of 15 columns) the fixed body returned False; this is a property of one-nearest-neighbour in 15 dimensions with noise columns, not an error in the code; a clustered rare class returned True in `sanity_d066.py`.")

M["B2A-R5"] = dict(
    sub="L3.1 (temporal leakage), reserve",
    faulty_lines="L56-62: months assigned to 5 folds by a fixed permutation (`default_rng(0)`), ridge cross-validation, slope of observed y on the pooled held-out forecasts over all 400 months (`ev` all True). Parameters from the claim; the 0.9 lag-1 autocorrelation is the note's proposal.",
    fixed_lines="L56-63: forward chaining in 5 blocks of 40 months starting at month 201 (`first = n // 2`, `size = n // 10`); the first block is fitted on months 1 to 200, each later block on all earlier months except the last 3 (`s - 3`); slope over months 201 to 400.",
    estimand="the calibration slope of forecasts for months after all fitting months.",
    guard="2 forecast months; zero variance of the forecasts (helper `slope` returns None); non-finite values.",
    t="0.000", sig="slowly varying predictor", guards="constant X (the forecasts still differ between blocks through the training mean, so the result is a bool, not None)",
    dev="The note reads 'fitted on months 1 to 200 ... then on months 1 to 240 (less a 3-month gap)'. The 3-month gap is applied from the second block on, as written; the first block has no gap. Applying the gap to the first block too would change only 3 of 200 fitting months. Only the faulty body uses randomness.")


def fence(s):
    return "```\n" + s + "\n```"


for local, cid in ids.items():
    b, p, m = briefs[local], priv[local], M[local]
    key_lines = "\n".join(
        "- `%s` %s, %s: %s" % (k["key"], k["dtype"], k["shape"], k["meaning"]) for k in b["data_keys"])
    runs = COMMON_RUNS.format(t=m["t"], sig=m["sig"], guards=m["guards"])
    text = f"""# CASE {cid} ({local})

## 1. Case
- Id: {cid} (author-local id {local}); class B-2 (procedure-level leakage), half A.
- Subtype / tag: {m['sub']}; mechanism tag {p['mechanism_tag']}; statistic family: {p['statistic_family']}.

## 2. Source and documenting passage
- Source key: {p['source']} (Kapoor and Narayanan 2023, Patterns 4(9):100804).
- Passage (from the brief author's private note, which gives it as returned by the fetch tool; not re-read online by the criterion author): {p['passage']}
- Read by the brief author through PubMed Central (PMC10499856) full text. I did not fetch any URL.

## 3. Brief
- Claim: {b['claim']}
- Data keys:
{key_lines}
- Sizes: {json.dumps(b['sizes'])}

## 4. Mapping
- Private note, faulty: {p['faulty']}
- Private note, fixed: {p['fixed']}
- Lines of `faulty_body.py` that carry the error: {m['faulty_lines']}
- Lines of `fixed_body.py` that carry the correction: {m['fixed_lines']}
- All other lines (helpers, guards, threshold, decision rule, statistic) are identical in both files; `diff` of the two files shows only the lines named above.
- Estimand line: {m['estimand']} (private note: {p['estimand']})

## 5. Allowed-guard minimum used
{m['guard']} Private-note `guard_minimum`: {p['guard_minimum']}.

## 6. Runs of the fixed body
{runs}

## 7. Deviations from the private note, and problems
{m['dev']}
Problems: none. Fixed-body revisions after the first run: 0.
"""
    with open(os.path.join(HALF, "cases", cid, "CASE.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", cid)
