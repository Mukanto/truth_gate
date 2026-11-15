"""Writes cases/<id>/CASE.md from ASSIGNMENT.json plus the texts below (text generation only)."""
import json
import pathlib

ROOT = pathlib.Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\cases")

KAP = ("KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of "
       "https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). "
       "I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.")
VAR = ("VAR06 (Varma and Simon 2006, addendum source). Read by the part-1 brief author (full text of "
       "https://pmc.ncbi.nlm.nih.gov/articles/PMC1397873/ through the fetch tool's summary). I (part 2) tried the same URL "
       "through ctx_fetch_and_index; it returned a reCAPTCHA page, nothing was read, no workaround was tried. The parameters "
       "below are the ones in the part-1 private note.")
AMB = ("AMB02 (Ambroise and McLachlan 2002). Read by the part-1 brief author as the Europe PMC abstract record "
       "(https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1073/pnas.102102699&format=json&resultType=core) "
       "and search snippets only; the full text was blocked. I (part 2) read nothing of it.")

CASES = {
"B2-01": dict(
    passage="KAP23 Section 2.4, L1.1 'No test set': training and testing on the same data (a 'text-book example of overfitting'); "
            "setting: civil war onset case study (Section 4, Appendix B), test set of 896 rows with 19 positives.",
    reading=KAP,
    mapping="Faulty: a logistic regression on the 30 indicators (standardised inside the fit, L2 penalty lambda = 1 on the slopes) is "
            "fitted on all rows and the AUC is computed on the same rows (no data are held out). Fixed: stratified 5-fold "
            "cross-validation of the same fit (random assignment, seed 20260201); held-out scores are pooled and the AUC is computed "
            "once. Same classifier, same AUC function, same threshold (AUC >= 0.75), same guard family.",
    estimand="Faulty: apparent (in-sample) AUC of the fitted model on the rows it was fitted to. Fixed: AUC of the model on rows not used to fit it (new country-years).",
    guard="Faulty: at least 2 rows of each class (fit and scoring defined). Fixed: at least 2 rows of each class in every training fold of the 5-fold structure (that is, at least 3 per class in the data); non-finite indicators give None.",
    deviations="Classifier fixed to a ridge-penalised logistic regression (the note allowed 'logistic regression with all 30 indicators, or another flexible model'). Stratified 5-fold assignment is random over rows; the skeleton's docstring says rows are laid out in country blocks, which the criterion does not use, so the fixed cross-validation is not grouped by country (the brief says 'new country-years'). The fixed criterion held in minus at 3.5% (7/200) and in the second control at 1.5%, so this did not show up as a problem in the pre-check. None else.",
    revs=0),
"B2-02": dict(
    passage="KAP23 Section 2.4, L1.2 text on over-sampling before the split, which leaves copies of training rows in the test set "
            "(paraphrase returned by the fetch tool in part 1; wording not verified). PB section 1 tie rule: oversampling by copying rows is L1.4.",
    reading=KAP,
    mapping="Faulty: the smaller class is oversampled by copying randomly drawn rows (with replacement) until the two classes are balanced, "
            "on the whole data, and only then is a stratified 5-fold cross-validation run (copies of one row fall in training and held-out folds); "
            "sensitivity is pooled over the held-out rows, copies included. Fixed: the same 5-fold structure on the original rows, "
            "the same oversampling function applied to each training fold only, sensitivity pooled over the untouched held-out original rows. "
            "Classifier: ridge-penalised logistic regression (lambda = 1), threshold 0.60.",
    estimand="Faulty: sensitivity on held-out rows that include copies of rows used for training. Fixed: sensitivity on original rows not seen in training (new patients).",
    guard="Both: at least 2 rows of each class in every training fold of the 5-fold structure on the original rows (at least 3 per class); non-finite measurements give None.",
    deviations="The note suggested a classifier able to use exact copies (1-nearest-neighbour or an unregularised flexible fit). First draft used 5-nearest-neighbour; its pre-check gave plus 0.49 and noise 0.10, so it was replaced by the logistic regression (revision 1). A second pre-check (logistic, oversampling of the positive class only) gave noise 0.23 because with balanced random labels the training set was majority-positive half of the time and the fit then predicted positive too often; oversampling was changed to copy the smaller class whichever it is, as a standard random oversampler does (revision 2). With a logistic regression, exact copies leak little, so the faulty criterion may differ little from the fixed one in these worlds (not tested: the faulty criterion was not run); if so this is 'error too small in the declared worlds at this size'.",
    revs=2),
"B2-03": dict(
    passage="KAP23 Section 2.4, over-sampling before the split leaves copies of training rows in the test set "
            "(paraphrase returned by the fetch tool in part 1). PB section 1 tie rule: copying rows is L1.4.",
    reading=KAP,
    mapping="Faulty: the smaller class is balanced by copying rows on the whole data, then a stratified 5-fold cross-validation, balanced accuracy "
            "(mean of sensitivity and specificity, pooled over the held-out rows, copies included). Fixed: the same oversampling inside each training fold only; "
            "balanced accuracy on the untouched held-out original rows. Classifier: ridge-penalised logistic regression (lambda = 1), threshold 0.65.",
    estimand="Faulty: balanced accuracy on held-out rows that include copies of training rows. Fixed: balanced accuracy on original rows not seen in training (new units).",
    guard="Both: at least 2 rows of each class in every training fold of the 5-fold structure on the original rows (at least 3 per class); non-finite features give None.",
    deviations="Same two revisions as B2-02. First draft used 5-nearest-neighbour on 50 standardised features; pre-check plus 0.033 (6/100 on a second run), so replaced by the logistic regression (revision 1). Revision 2 (oversample the smaller class whichever it is) was made for parity with B2-02 and changed nothing visible here (noise 0 before and after). As in B2-02 the copies may leak little through a logistic regression.",
    revs=2),
"B2-04": dict(
    passage="KAP23 Section 2.4, L3.1 'Temporal leakage': the model uses 'data from the future' during training; Appendix C: 'the training dataset could contain data from a later date than the test dataset because of being shuffled' under k-fold cross-validation (quotes as returned by the fetch tool in part 1).",
    reading=KAP,
    mapping="Faulty: ordinary 5-fold cross-validation with rows assigned to folds at random irrespective of time; 15-nearest-neighbour classifier on the standardised indicators; accuracy pooled over the held-out days. "
            "Fixed: forward evaluation with the same classifier, the same 5 test blocks and the same accuracy: the series is cut into 6 contiguous blocks, block j (j = 1..5) is scored by a classifier fitted on the blocks before it only; accuracy pooled over the 5 scored blocks. Threshold 0.58.",
    estimand="Faulty: accuracy on days interleaved with the days used to fit (later days included in the fitting data). Fixed: accuracy on days later than all days used to fit (forecasting later days).",
    guard="Both: at least 2 rows of each class in every fitting set; fixed: a non-empty scored block (None otherwise); non-finite indicators give None.",
    deviations="The k-nearest-neighbour classifier (k = 15) was chosen, among the classifiers the note names (logistic regression or k-NN), because a flexible classifier on autocorrelated indicators is the case in which shuffled folds matter; it was fixed before the first pre-check and not compared with the logistic regression. The fixed criterion's plus rate is 0.785 on 200 samples (0.81 on the first 100), close to the declared power 0.8. The first scored block of the fixed criterion is trained on one sixth of the series (83 days).",
    revs=0),
"B2-05": dict(
    passage="KAP23 Section 2.4, L3.1 'Temporal leakage' ('data from the future'); Appendix C: shuffled k-fold cross-validation lets the training data contain data from a later date than the test data (quotes as returned by the fetch tool in part 1).",
    reading=KAP,
    mapping="Faulty: shuffled 5-fold cross-validation (random fold assignment irrespective of time) of an ordinary least-squares regression of demand on the 8 drivers; R-squared (1 - SSE/SST about the mean of the scored weeks) pooled over the held-out weeks. "
            "Fixed: the same regression and statistic with chronological evaluation: 6 contiguous blocks, block j (j = 1..5) predicted from a fit on the preceding blocks only; R-squared over the 5 scored blocks. Threshold 0.30.",
    estimand="Faulty: R-squared on weeks surrounded in time by weeks used to fit. Fixed: R-squared on weeks later than all weeks used to fit.",
    guard="Both: fitting set larger than the number of drivers plus 1; non-finite values give None; zero variance of the scored demand gives None (and fixed: fewer than 2 scored weeks gives None).",
    deviations="With a linear regression and drivers that do not carry demand information in minus, shuffled folds can hardly leak, so the faulty criterion may behave like the fixed one in the declared worlds (not tested). Linear regression is what the note names.",
    revs=0),
"B2-06": dict(
    passage="KAP23 Section 2.4, L3.2 'Nonindependence between train and test': Oner et al. 2020 (histopathology) 'uses different observations of the same patient in the training and test sets'; suggested fix block cross-validation (quote as returned by the fetch tool in part 1).",
    reading=KAP,
    mapping="Faulty: all patches are pooled into rows (patients x patches, 20 features) with the patient's label and a stratified 5-fold cross-validation is run over patch rows (patches of one patient fall in training and held-out folds); ridge-penalised logistic regression (lambda = 1); AUC over the pooled held-out patches. "
            "Fixed: the same pipeline with the folds assigned by patient (stratified by the patient's label), so that all patches of a patient stay in one fold. Threshold AUC >= 0.75.",
    estimand="Faulty: AUC on patches whose patients also contribute patches to the fitting data. Fixed: AUC on patches of patients absent from the fitting data (new patients).",
    guard="Both: at least 2 patients of each class in every training fold of the patient-level 5-fold structure (at least 3 per class, counted over patients); non-finite features give None.",
    deviations="None. (The faulty guard is stated on patients, as the fixed one, so that both twins use the same class counts.)",
    revs=0),
"B2-07": dict(
    passage="KAP23 Section 2.4, L3.2 'Nonindependence between train and test': the same people or units appear in both sets; suggested fix block cross-validation (Roberts et al. 2017; Valavi et al. 2021) (as returned by the fetch tool in part 1; wording not verified).",
    reading=KAP,
    mapping="Faulty: sessions are pooled into rows (participants x sessions, 10 measurements), 5-fold cross-validation with random assignment of rows, ordinary least squares (standardised inputs); Pearson correlation between predicted and observed scores over the pooled held-out rows. "
            "Fixed: the same pipeline with participants assigned to folds, so that all sessions of a participant stay in one fold. Threshold r >= 0.30.",
    estimand="Faulty: correlation of predicted and observed scores on sessions of participants who also have sessions in the fitting data. Fixed: correlation on sessions of participants absent from the fitting data.",
    guard="Both: at least 2 participants, at least 3 pooled scored rows, non-zero variance of predictions and of scores, finite values (None otherwise).",
    deviations="Ordinary least squares is a low-capacity model, so leakage through the participant's stable measurements is limited; the faulty criterion may be close to the fixed one in the declared worlds (not tested). The fixed criterion held in minus at 1.0 to 4.0% over two pre-checks.",
    revs=0),
"B2-08": dict(
    passage="VAR06 Abstract/Results: 'The CV error estimate for the classifier with the optimal parameters was found to be a substantially biased estimate of the true error that the classifier would incur on independent data'; the correction is nested cross-validation. Results: shrunken centroid, null data, mean CV error 37.8% against a true error of 50.0%.",
    reading=VAR,
    mapping="Faulty: nearest shrunken centroid (Tibshirani et al. form: standardised centroid differences, s0 = median of the gene-wise pooled SD, class priors, soft threshold delta) with delta on a grid of 20 values from 1 down to 0.01; for each delta the stratified 10-fold CV accuracy on all 40 samples; the criterion reports the best CV accuracy over delta (the source's 'CV error of the classifier with the optimal parameter'). "
            "Fixed: nested cross-validation: outer stratified 10-fold; in each outer training set an inner stratified 10-fold CV picks delta (ties go to the larger delta); the classifier with that delta predicts the outer held-out samples; accuracy pooled over the outer folds. Threshold 0.60.",
    estimand="Faulty: the maximum CV accuracy over the tuning grid. Fixed: accuracy of the whole tuned procedure on samples not used for tuning or fitting.",
    guard="Faulty: at least 2 samples of each class in every training fold of the 10-fold structure. Fixed: at least 2 of each class in every training set of the nested 10 x 10 structure (inner training sets included); non-finite expression gives None.",
    deviations="Grid, folds and tie rule are my choices within the note ('about 0.01 to 1', for example 20 values; outer 10-fold or LOOCV). Gene count 1000 (the skeleton), not the source's 6000. The fixed criterion holds in minus at 17 to 24% and on the noise probe at 26 to 35%: the claim's threshold 0.60 on 40 samples is loose (chance 13% for a binomial) and nested CV at n = 40 has a larger variance than a binomial (checked on 300 minus samples with a copy of the fixed source that returns the accuracy: mean 0.496, sd 0.114, P(>= 0.6) = 0.24). Recorded, not corrected; the criterion was not bent.",
    revs=0),
"B2-09": dict(
    passage="VAR06 Abstract/Results: 'The CV error estimate for the classifier with the optimal parameters was found to be a substantially biased estimate of the true error that the classifier would incur on independent data'; the correction is nested cross-validation.",
    reading=VAR,
    mapping="Faulty: the shrunken-centroid classifier of B2-08 (same code); for each delta the AUC of the pooled held-out discriminant scores of a stratified 10-fold CV on all 40 patients; the best AUC over delta is reported. "
            "Fixed: nested CV: delta chosen by the inner 10-fold pooled AUC in each outer training set (ties go to the larger delta); the outer held-out scores are pooled and the AUC computed once. Threshold 0.65.",
    estimand="Faulty: the maximum, over the tuning grid, of the CV AUC. Fixed: AUC of the whole tuned procedure on patients not used for tuning or fitting.",
    guard="Faulty: at least 2 patients of each class in every training fold of the 10-fold structure. Fixed: at least 2 of each class in every training set of the nested 10 x 10 structure; non-finite expression gives None.",
    deviations="Same grid and tie rule as B2-08. The AUC variant is an extension of the source's error-rate estimate (as the part-1 note says). The fixed criterion holds in minus at 8 to 8.5% (above the nominal 5% for a threshold of 0.65 on 40 samples); recorded, not corrected.",
    revs=0),
"B2-10": dict(
    passage="VAR06 Methods/Results: SVM with Gaussian kernel, trade-off C and kernel parameter gamma tuned by leave-one-out CV over a grid (2^-5 to 2^15, 2^-15 to 2^3); the procedure 'requires that all steps of the algorithm, including classifier parameter tuning, be repeated in each CV loop' (part-1 note, from PMC1397873).",
    reading=VAR,
    mapping="SUBSTITUTION as the note instructs: a Gaussian-kernel ridge classifier (closed form through an eigendecomposition of the kernel matrix; regularisation 1/C) replaces the SVM, with a 5 x 5 grid on the source's ranges (C = 2^-5, 2^0, 2^5, 2^10, 2^15; gamma = 2^-15, 2^-10.5, 2^-6, 2^-1.5, 2^3) and the 3 genes with the largest |t| (pooled-variance two-sample t on the fitting set, standardised on it) chosen again inside every fit. "
            "Faulty: leave-one-out accuracy on all 40 samples for every (C, gamma); the best accuracy over the grid is reported. Fixed: nested CV: outer stratified 10-fold; in each outer training set leave-one-out over the grid (genes reselected in every leave-one-out fit) picks (C, gamma) (ties: first in the order C ascending, gamma ascending); the whole fit (genes, kernel, parameters) predicts the outer held-out samples; accuracy pooled. Threshold 0.60.",
    estimand="Faulty: the maximum leave-one-out accuracy over the (C, gamma) grid. Fixed: accuracy of the whole tuned procedure on samples not used for tuning or fitting.",
    guard="Faulty: at least 3 samples of each class (every leave-one-out fitting set keeps 2 and the t statistic is defined). Fixed: at least 3 of each class in every outer training set; non-finite expression gives None.",
    deviations="Kernel ridge replaces the SVM and the grid is 5 x 5 (the note allows both; the substitution is stated here as the note asks). Outer folds 10 (not leave-one-out) to meet the timing estimate. The fixed criterion holds in minus at 25 to 30% (small samples, 40 per pre-check) and on the noise probe at 20%; as in B2-08 the threshold 0.60 on 40 samples is loose. Recorded, not corrected.",
    revs=0),
"B2-11": dict(
    passage="VAR06 Abstract: the CV error estimate for the classifier with the optimal parameters is a substantially biased estimate of the true error on independent data; 'model selection' in the title, correction nested cross-validation. Reading fixed in SOURCES_ADDENDUM: selection on the data of the error estimate, of features or classifier parameters.",
    reading=VAR,
    mapping="Faulty: within each training set the genes are ranked by the two-sample t statistic and the top k kept, k on the grid 1, 2, 3, 5, 10, 30, 100; nearest-centroid classifier on the standardised panel; for each k the stratified 10-fold CV balanced accuracy on all 40 subjects (gene ranking repeated in every fold); the best balanced accuracy over k is reported. "
            "Fixed: nested CV: outer stratified 10-fold; inner stratified 10-fold CV picks k in each outer training set (ties: smaller k); balanced accuracy of the whole procedure pooled over the outer held-out subjects. Threshold 0.60.",
    estimand="Faulty: the maximum, over the grid of k, of the CV balanced accuracy. Fixed: balanced accuracy of the whole procedure (gene ranking and k chosen inside the fitting data) on subjects not used for it.",
    guard="Faulty: at least 2 subjects of each class in every training fold of the 10-fold structure. Fixed: at least 2 of each class in every training set of the nested 10 x 10 structure; non-finite expression gives None.",
    deviations="Grid and tie rule are mine within the note's example. The fixed criterion holds in minus at 22 to 23% (statistic mean 0.506, sd 0.106 on 300 minus samples from a modified copy of the fixed source; P(>= 0.6) = 0.21); same reading as B2-08. Recorded, not corrected.",
    revs=0),
"B2-12": dict(
    passage="AMB02 abstract (Europe PMC record): earlier error estimates did not account for selection bias, because the same samples were used for gene selection and testing, or because gene selection was not repeated within each cross-validation step (as read by the part-1 author).",
    reading=AMB,
    mapping="Faulty: the genes are ranked by the pooled-variance two-sample t statistic on all 62 tissues, the top 3 kept, and the accuracy of a nearest-centroid classifier on those 3 genes is estimated by stratified 10-fold CV (the gene choice made before the CV, on all tissues). "
            "Fixed: external CV: the ranking and the choice of the top 3 genes are repeated inside every training fold; accuracy pooled over the held-out tissues. Same classifier, folds and threshold (accuracy >= 0.70).",
    estimand="Faulty: CV accuracy of a 3-gene classifier whose genes were chosen with all tissues, including the held-out ones. Fixed: accuracy on tissues not used to choose the genes or fit the classifier (the whole procedure).",
    guard="Both: at least 2 tissues of each class in every training fold of the 10-fold structure (at least 3 per class in the data; also what the t statistic needs); non-finite expression gives None.",
    deviations="The classifier (nearest centroid on the standardised 3 genes) is my choice (the note says 'a classifier'). Gene axis 1000 (skeleton) instead of the source's 2000. The source was read only as an abstract by the part-1 author, which the note flags.",
    revs=0),
}

FINAL = {}
for line in pathlib.Path(r"E:\Claude Projects\Kapi\phase_c_private\authors\B2\work\precheck_final.txt").read_text(encoding="utf-8").splitlines():
    pass

PRE = {
"B2-01": "n = 100 (seed 777000): plus 88/100, minus 3/100, control permute_onset_across_country_years 0/100, control permute_onset_histories_across_countries 1/100, noise 0/100, zeros 100 None. Final, n = 200 (seed 888000): plus 179/200 (0.895), minus 7/200 (0.035), controls 0/200 and 3/200, noise 0/200, zeros 200 None.",
"B2-02": "Draft 5-NN, n = 100: plus 49, minus 1, control 0, noise 10, zeros None 100. Revision 1 (logistic, positive class oversampled), n = 100: plus 100, minus 0, control 1, noise 23. Revision 2 (smaller class oversampled), n = 100: plus 100, minus 0, control 1, noise 0. Final, n = 200 (seed 888000): plus 199/200, minus 0/200, control 0/200, noise 1/200, zeros 200 None.",
"B2-03": "Draft 5-NN, n = 60: plus 2/60, minus 0, control 0, noise 0 (and 6/100 plus on a repeat). Revision 1 (logistic), n = 100: plus 100, minus 0, control 0, noise 0. Revision 2 (smaller class oversampled), n = 100: plus 100, minus 0, control 0, noise 0. Final, n = 200 (seed 888000): plus 200/200, minus 0/200, control 0/200, noise 0/200, zeros 200 None.",
"B2-04": "n = 100 (seed 777000): plus 81, minus 1, control shift_rises_in_time 0, noise 0, zeros None 100. Final, n = 200 (seed 888000): plus 157/200 (0.785), minus 0/200, control 0/200, noise 0/200, zeros 200 None.",
"B2-05": "n = 100: plus 99, minus 0, control 0, noise 0, zeros None 100. Final, n = 200: plus 195/200 (0.975), minus 0/200, control 0/200, noise 0/200, zeros 200 None.",
"B2-06": "n = 100: plus 100, minus 0, control 0, noise 0, zeros None 100. Final, n = 200: plus 197/200 (0.985), minus 0/200, control 0/200, noise 0/200, zeros 200 None.",
"B2-07": "n = 100: plus 98, minus 4, control 0, noise 0, zeros None 100. Final, n = 200: plus 200/200, minus 2/200 (0.010), control 2/200, noise 0/200, zeros 200 None.",
"B2-08": "n = 100: plus 100, minus 17, control 28, noise 26, zeros None 100. Final, n = 200: plus 200/200, minus 47/200 (0.235), control 39/200, noise 69/200 (0.345; labels are Bernoulli(0.5), so the classes are often unbalanced and the priors favour the majority), zeros 200 None. Statistic check on 300 minus samples (modified copy of fixed.py returning the accuracy; work\\null_stat_check.py): mean 0.496, sd 0.114, P(>= 0.6) = 0.237.",
"B2-09": "n = 100: plus 100, minus 8, control 11, noise 9, zeros None 100. Final, n = 200: plus 200/200, minus 17/200 (0.085), control 15/200, noise 26/200 (0.13), zeros 200 None.",
"B2-10": "n = 20 (seed 777000): plus 18, minus 5, control 4, noise 4, zeros None 20. Final, n = 40 (seed 888000, 0.23 s per call): plus 33/40 (0.825), minus 12/40 (0.30), control 4/40, noise 8/40, zeros 40 None.",
"B2-11": "n = 100: plus 100, minus 23, control 28, noise 9, zeros None 100. Final, n = 200: plus 200/200, minus 45/200 (0.225), control 42/200, noise 39/200, zeros 200 None. Statistic check on 300 minus samples (modified copy of fixed.py returning the balanced accuracy): mean 0.506, sd 0.106, P(>= 0.6) = 0.207.",
"B2-12": "n = 100: plus 100, minus 2, control 1, noise 1, zeros None 100. Final, n = 200: plus 200/200, minus 0/200, control 8/200 (0.04), noise 2/200, zeros 200 None.",
}

TIM = {
"B2-01": (0.0040, 0.0010, 6, 14, 200), "B2-02": (0.0017, 0.0001, 5, 4, 200), "B2-03": (0.0091, 0.0008, 5, 24, 200),
"B2-04": (0.0011, 0.0011, 5, 5, 200), "B2-05": (0.0004, 0.0010, 5, 3, 200), "B2-06": (0.0023, 0.0003, 5, 6, 200),
"B2-07": (0.0005, 0.0001, 5, 1, 200), "B2-08": (0.0372, 0.0006, 5, 91, 200), "B2-09": (0.0414, 0.0006, 5, 101, 200),
"B2-10": (0.2340, 0.0007, 5, 563, 40), "B2-11": (0.0195, 0.0006, 6, 56, 200), "B2-12": (0.0022, 0.0009, 6, 9, 200),
}

for cid, c in CASES.items():
    a = json.loads((ROOT / cid / "ASSIGNMENT.json").read_text(encoding="utf-8"))
    t, g, S, est, ncalls = TIM[cid]
    brief = json.dumps(a["brief"], indent=2, ensure_ascii=False)
    text = f"""# CASE {cid}

## 1. Identity
Case id {cid}; world id {a['world_id']}; class {a['class']}; subtype {a['subtype']}; source key {a['source']}.

## 2. Source and documenting passage
{c['passage']}

Who read it and how: {c['reading']}

## 3. The brief (as in ASSIGNMENT.json)
```json
{brief}
```

## 4. Mapping
{c['mapping']}

Estimand line. {c['estimand']}

Allowed-guard minimum used. {c['guard']}

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\\; the faulty criterion was never run, only syntax-checked)
{PRE[cid]}

Number of revisions of the fixed criterion: {c['revs']}.

## 6. Timing (final fixed criterion)
t = {t:.4f} s (mean of {ncalls} calls on plus samples), g = {g:.4f} s (mean plus generation), S = {S} (2 worlds + {S - 4} control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = {est} s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
{c['deviations']}

Skeleton requests: none.
"""
    (ROOT / cid / "CASE.md").write_text(text, encoding="utf-8")
    print("CASE.md", cid)
