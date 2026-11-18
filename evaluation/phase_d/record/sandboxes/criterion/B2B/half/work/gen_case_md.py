"""Writes CASE.md of every case (after the body files exist and run_fixed.py has produced run_results.json).
Line numbers are looked up in the written body files; the texts come from PRIVATE.json, BRIEFS.json and the notes below."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
HALF = os.path.dirname(HERE)
IDS = json.load(open(os.path.join(HALF, "CASE_IDS.json"), encoding="utf-8"))
BR = {b["local_id"]: b for b in json.load(open(os.path.join(HALF, "BRIEFS.json"), encoding="utf-8"))}
PV = {b["local_id"]: b for b in json.load(open(os.path.join(HALF, "PRIVATE.json"), encoding="utf-8"))}
RUNS = json.load(open(os.path.join(HERE, "run_results.json"), encoding="utf-8"))

# (description, marker); marker ending in "$" must equal the stripped line, otherwise the stripped line must start with it
M = {
 "B2B-01": dict(
  F=[("model fitted on all patients and applied to the same patients (resubstitution)", "pred = _ridge_predict(x, y, x, lam)"),
     ("ridge penalty = number of genes (chosen by the brief author; no source value)", "lam = float(x.shape[1])")],
  X=[("5-fold partition of the patients", "folds = _random_folds(rng, n, 5)"),
     ("each held-out fold predicted by a model fitted (and standardised) on the other folds only", "pred[te] = _ridge_predict(x[~te]")]),
 "B2B-02": dict(
  F=[("fitted on all patients, predictions for the same patients (resubstitution)", "pred = _ridge_predict(x, y, x, lam)"),
     ("ridge penalty = number of columns (brief author's choice)", "lam = float(x.shape[1])")],
  X=[("10-fold partition of the patients", "folds = _random_folds(rng, n, 10)"),
     ("held-out predictions from models fitted on the other folds", "pred[te] = _ridge_predict(x[~te]")]),
 "B2B-03": dict(
  F=[("SMOTE (k = 5) applied to all records before any fold is formed", "xs, ys = _smote(x, y, rng, 5)"),
     ("folds drawn on the enlarged data, so synthetic rows are test rows", "folds = _stratified_folds(rng, ys, 5)"),
     ("F1 is scored on the enlarged labels", "ye = ys$"),
     ("CART depth 6 trained and tested on enlarged folds", "pred[te] = _tree_scores(xs[~te]")],
  X=[("folds drawn on the original records", "folds = _stratified_folds(rng, y, 5)"),
     ("SMOTE (k = 5) on the training part of each fold only", "xs, ys = _smote(x[~te], y[~te], rng, 5)"),
     ("scored on the original test-fold records", "ye = y$")]),
 "B2B-04": dict(
  F=[("SMOTE (k = 5) applied to all records before any fold is formed", "xs, ys = _smote(x, y, rng, 5)"),
     ("folds drawn on the enlarged data", "folds = _stratified_folds(rng, ys, 10)"),
     ("balanced accuracy scored on the enlarged labels", "ye = ys$")],
  X=[("folds drawn on the original records", "folds = _stratified_folds(rng, y, 10)"),
     ("SMOTE (k = 5) on the training part of each fold only", "xs, ys = _smote(x[~te], y[~te], rng, 5)"),
     ("scored on the original test-fold records", "ye = y$")]),
 "B2B-05": dict(
  F=[("random oversampling of all records before any fold is formed", "xs, ys = _oversample(x, y, rng)"),
     ("folds drawn on the enlarged data, so copies are test rows", "folds = _stratified_folds(rng, ys, 5)"),
     ("sensitivity scored on the enlarged labels", "ye = ys$")],
  X=[("folds drawn on the original records", "folds = _stratified_folds(rng, y, 5)"),
     ("oversampling of the training part of each fold only", "xs, ys = _oversample(x[~te], y[~te], rng)"),
     ("scored on the original test-fold records", "ye = y$")]),
 "B2B-06": dict(
  F=[("top 3 genes by |t| chosen once on all tissues, before the cross-validation", "sel = _top_genes(x, y, 3)"),
     ("the cross-validation then runs on those pre-selected genes", "pred[te] = _lda_predict(xs[~te]")],
  X=[("top 3 genes chosen inside each fold, on the training tissues only", "sel = _top_genes(x[~te], y[~te], 3)"),
     ("discriminant fitted and applied on those genes", "pred[te] = _lda_predict(x[~te][:, sel]")]),
 "B2B-07": dict(
  F=[("10-fold CV error for each of the 20 thresholds, all 40 samples", "err = _cv_errors_nsc(x, y, folds, 10, deltas)"),
     ("the smallest of these errors (ties: larger threshold) is the statistic", "stat = err[_pick_delta(err)] / n"),
     ("threshold grid: 20 values in [0.01, 1]", "deltas = np.linspace(0.01, 1.0, 20)")],
  X=[("outer leave-one-out loop", "for i in range(n):"),
     ("threshold chosen by 10-fold CV on the remaining 39 samples (ties: larger threshold)", "best = _pick_delta(_cv_errors_nsc(xi, yi, inner, 10, deltas))"),
     ("classifier refitted on the 39 with that threshold, held-out sample classified", "errors += int(_nsc_errors("),
     ("outer error rate", "stat = errors / n")]),
 "B2B-08": dict(
  F=[("months assigned to 10 folds uniformly at random", "folds = _random_folds(rng, n, 10)"),
     ("R-squared over all months", "ye = y$")],
  X=[("10 consecutive blocks", "edges = (np.arange(11) * n) // 10"),
     ("blocks 3 to 10 predicted from all earlier blocks only", "te = np.arange(edges[b], edges[b + 1])"),
     ("baseline = mean of the predicted blocks", "ye = y[edges[2]:]")]),
 "B2B-09": dict(
  F=[("plot rows assigned to 10 folds uniformly at random (sites shared across folds)", "folds = _random_folds(rng, n, 10)")],
  X=[("sites assigned to 10 folds (4 sites per fold); every plot takes its site's fold", "folds = np.repeat(_random_folds(rng, s, 10), m)")]),
 "B2B-10": dict(
  F=[("windows assigned to 10 folds uniformly at random (record-wise)", "folds = _random_folds(rng, n, 10)")],
  X=[("subjects assigned to 10 folds (3 per fold); every window takes its subject's fold (subject-wise)", "folds = np.repeat(_random_folds(rng, s, 10), m)")]),
 "B2B-11": dict(
  F=[("fitted on all patients and scored on the same patients (resubstitution)", "scores = _logit_scores(x, y, x, lam)"),
     ("penalty = number of genes (brief author's choice)", "lam = float(x.shape[1])")],
  X=[("10-fold partition of the patients", "folds = _stratified_folds(rng, y, 10)"),
     ("held-out scores from models fitted (and standardised) on the other folds", "scores[te] = _logit_scores(x[~te]")]),
 "B2B-12": dict(
  F=[("random oversampling of all records before any fold is formed", "xs, ys = _oversample(x, y, rng)"),
     ("folds drawn on the enlarged data, so copies are test rows", "folds = _stratified_folds(rng, ys, 10)"),
     ("AUC scored on the enlarged labels", "ye = ys$")],
  X=[("folds drawn on the original records", "folds = _stratified_folds(rng, y, 10)"),
     ("oversampling of the training part of each fold only", "xs, ys = _oversample(x[~te], y[~te], rng)"),
     ("AUC scored on the original test-fold records", "ye = y$")]),
 "B2B-13": dict(
  F=[("top 20 genes by |t| chosen once on all samples, before the cross-validation", "sel = _top_genes(x, y, 20)"),
     ("the cross-validation then runs on those pre-selected genes", "scores[te] = _centroid_scores(xs[~te]")],
  X=[("top 20 genes chosen inside each fold, on the training samples only", "sel = _top_genes(x[~te], y[~te], 20)"),
     ("centroids from those genes, held-out scores", "scores[te] = _centroid_scores(x[~te][:, sel]")]),
 "B2B-14": dict(
  F=[("days assigned to 10 folds uniformly at random", "folds = _random_folds(rng, n, 10)"),
     ("scaled by the SD of the level over all days", "ye = y$")],
  X=[("10 consecutive blocks", "edges = (np.arange(11) * n) // 10"),
     ("blocks 3 to 10 predicted from all earlier days only", "te = np.arange(edges[b], edges[b + 1])"),
     ("scaled by the SD of the level in the predicted blocks", "ye = y[edges[2]:]")]),
 "B2B-15": dict(
  F=[("10 folds", "nf = 10"),
     ("recordings assigned to folds uniformly at random (record-wise)", "folds = _random_folds(rng, n, nf)")],
  X=[("8 folds of 2 subjects each (s // 2 folds)", "nf = s // 2"),
     ("subjects assigned to folds; every recording takes its subject's fold (subject-wise)", "folds = np.repeat(_random_folds(rng, s, nf), m)")]),
}

GUARD = {
 "B2B-01": "2 (fewer than 2 patients -> None; constant survival_months -> None). Non-finite expression or survival_months -> None.",
 "B2B-02": "2 (fewer than 2 patients -> None; constant response, or constant held-out/fitted predictions -> None). Non-finite values -> None.",
 "B2B-03": "1 (no positive record -> None). Non-finite features -> None.",
 "B2B-04": "2 (a class with no record, i.e. fewer than one record of each class -> None). Non-finite features -> None.",
 "B2B-05": "1 (no positive record -> None). Non-finite measurements -> None.",
 "B2B-06": "1 (no tissue -> None). In addition a label with zero variance (all tumour or all normal) -> None, because a t-statistic and a discriminant are undefined with one class. Non-finite expression -> None.",
 "B2B-07": "1 stated in the private note. The code returns None for fewer than 3 samples (the pooled within-class standard deviation divides by n - 2, so 3 is the smallest size at which the classifier, hence the statistic, is defined), for a label with zero variance, and for non-finite expression. This is slightly above the stated 1; see section 7.",
 "B2B-08": "2 (fewer than 2 evaluated months -> None; constant evaluated abundance -> None). Non-finite values -> None.",
 "B2B-09": "2 (fewer than 2 plots -> None; constant cover or constant predictions -> None). Non-finite values -> None.",
 "B2B-10": "1 (no window -> None). Non-finite features -> None.",
 "B2B-11": "2 (fewer than 2 patients -> None; no relapse or no non-relapse patient -> None). Non-finite expression -> None.",
 "B2B-12": "2 (a class with no record -> None). Non-finite features -> None.",
 "B2B-13": "1 stated in the private note; read as one sample in each class, the smallest size at which an AUC is defined (no sample, or a class with no sample -> None). Non-finite expression -> None.",
 "B2B-14": "1 (no evaluated day -> None; constant evaluated level, i.e. zero SD -> None). Non-finite values -> None.",
 "B2B-15": "2 (fewer than 2 subjects -> None; no diseased or no healthy subject -> None). Non-finite measurements -> None.",
}

CHOICES = {
 "B2B-01": "Ridge in dual form on columns standardised with the training part (a constant column is left at zero). Folds are uniformly random, 5 folds. SST is about the mean of all patients' y.",
 "B2B-02": "Expression and clinical blocks are concatenated and standardised together column by column with the training part; penalty = number of columns (1508). 10 uniformly random folds.",
 "B2B-03": "Stratified folds (by label). SMOTE: minority = smaller class, nearest neighbours by Euclidean distance on the raw variables, synthetic count = difference of class sizes, base row, neighbour and gap drawn uniformly at random; a class with fewer than 2 records cannot be interpolated and is left unchanged. CART: Gini (variance reduction on a 0/1 target), depth <= 6, minimum leaf 1, midpoint thresholds, positive when leaf share > 0.5.",
 "B2B-04": "Stratified folds. SMOTE as in B2B-03. 5-NN on columns standardised with the training part (including synthetic rows in the faulty file), vote share > 0.5 = positive. Balanced accuracy is pooled over all evaluated rows.",
 "B2B-05": "Stratified folds. Oversampling: original rows plus rows of the smaller class drawn with replacement until equal counts. Unpruned CART (no depth limit, minimum leaf 1).",
 "B2B-06": "Stratified folds. t-statistic with pooled variance; top 3 by absolute value (stable ties). Fisher discriminant with the pooled within-class covariance (pseudo-inverse) and the midpoint threshold (equal priors).",
 "B2B-07": "Stratified inner folds. Nearest shrunken centroids as in Tibshirani et al.: d = (class mean - overall mean) / (m_k (s_j + s0)), m_k = sqrt(1/n_k - 1/n), s0 = median s_j, soft threshold, class-share priors, discriminant with the shrunken centroids. Threshold grid np.linspace(0.01, 1, 20).",
 "B2B-08": "Random forest: 50 trees on bootstrap resamples, minimum leaf 5, a third of the variables searched per node (3 of 10), variance reduction. 10 uniformly random folds. Blocks of n/10 months (60).",
 "B2B-09": "Random forest: 40 trees, minimum leaf 5 (not stated in the brief), a third of the variables per node (2 of 6). Sites are assigned to folds at random.",
 "B2B-10": "Random forest: 50 trees, fully grown (minimum leaf 1), floor(sqrt(variables)) = 6 variables per node, Gini; window is walking when the mean leaf share > 0.5. Windows (faulty) or subjects (fixed) assigned to folds at random.",
 "B2B-11": "L2-penalised logistic regression, penalty = number of genes (the brief says only 'fixed'), unpenalised intercept, columns standardised with the training part, Newton steps in dual form (agrees with an L-BFGS fit of the primal objective to 2e-9). Stratified folds.",
 "B2B-12": "Stratified folds. Oversampling as in B2B-05. 5-NN on standardised columns (the brief does not say standardised); probability = share of positive neighbours; AUC with average ranks for ties.",
 "B2B-13": "Stratified folds. t-statistic with pooled variance, top 20; nearest centroid on the raw expression of the selected genes, score = distance to the False-class centroid minus distance to the True-class centroid.",
 "B2B-14": "5-NN regression on drivers standardised with the fitted part; RMSE over the evaluated days divided by their population SD (ddof 0). 10 uniformly random folds in the faulty file.",
 "B2B-15": "Random forest: 50 trees, fully grown, floor(sqrt(10)) = 3 variables per node. Recordings (faulty) or subjects (fixed, 2 per fold) assigned to folds at random; the AUC pools all recording scores.",
}


def lines_of(path, markers):
    src = open(path, encoding="utf-8").read().split("\n")
    start = next(i for i, l in enumerate(src) if l.startswith("def criterion"))
    out = []
    for desc, mk in markers:
        exact = mk.endswith("$")
        mk2 = mk[:-1] if exact else mk
        hit = None
        for i in range(start, len(src)):
            s = src[i].strip()
            if (s == mk2) if exact else s.startswith(mk2):
                hit = i + 1
                break
        if hit is None:
            raise SystemExit("marker not found %s %s" % (path, mk))
        out.append((desc, hit, src[hit - 1].strip()))
    return out


for local, cid in IDS.items():
    folder = os.path.join(HALF, "cases", cid)
    b, p, r = BR[local], PV[local], RUNS[local]
    fl = lines_of(os.path.join(folder, "faulty_body.py"), M[local]["F"])
    xl = lines_of(os.path.join(folder, "fixed_body.py"), M[local]["X"])
    keys = "\n".join("   - `%s` %s, %s: %s" % (k["key"], k["dtype"], k["shape"], k["meaning"]) for k in b["data_keys"])
    sizes = ", ".join("%s %d" % (k, v) for k, v in b["sizes"].items())
    cr = open(os.path.join(folder, "fixed_body.py"), encoding="utf-8").read().split("\n")
    crit_line = next(i for i, l in enumerate(cr) if l.startswith("def criterion")) + 1
    crit_end = len(cr) - 1
    fl_txt = "\n".join("   - faulty_body.py line %d, `%s`: %s." % (n, t, dsc) for dsc, n, t in fl)
    xl_txt = "\n".join("   - fixed_body.py line %d, `%s`: %s." % (n, t, dsc) for dsc, n, t in xl)
    vals = ", ".join(str(v) for v in r["values"])
    secs = ", ".join("%.2f s" % s for s in r["seconds"])
    md = f"""# CASE {cid} ({local})

## 1. Id, class, subtype
- Case id {cid}; local id {local}; class B-2 (procedure-level leakage), half B.
- Subtype / mechanism tag: {p["subtype"]} ({p["mechanism_tag"]}); statistic family: {p["statistic_family"]}.

## 2. Source and documenting passage
- Source key: {p["source"]}.
- Passage (as recorded in the private note): {p["passage"]}
- Who read it and how: the brief author, as recorded in LOG.md (tool summaries of the online text or abstract; see the
  private note's `sizes_note`). I, the criterion author, fetched no source and visited no URL; I relied on the brief
  author's passage and on SOURCES_D.md.

## 3. Brief
- Claim: {b["claim"]}
- Data keys:
{keys}
- Sizes: {sizes}.

## 4. Mapping
Error as documented in the private note: {p["faulty"]}

Correction as documented: {p["fixed"]}

Model-family choice in the private note: {p["model_family"]}

Lines of `faulty_body.py` that carry the error (parameters are those of the private note, where the source gives none the brief author's choice; the source's own sizes and bias figures are in the private note's `sizes_note`):
{fl_txt}

Lines of `fixed_body.py` that carry the correction:
{xl_txt}

The remaining lines (helpers, guards, statistic and threshold line) are identical in the two files. `criterion` occupies
lines {crit_line} to {crit_end} of fixed_body.py.

Implementation choices the private note leaves open (identical in both files): {CHOICES[local]}

**Estimand.** {p["estimand"]}

## 5. Allowed-guard minimum used
Private note: {p["guard_minimum"]}. Code: {GUARD[local]}

## 6. Runs of the fixed body (own arrays, no world)
- Arrays generated by `work/run_fixed.py` from the brief's keys, shapes and dtypes (standard-normal floats; booleans
  with probability 0.2): 3 arrays (seeds 101-103) plus one repeat of the first array to check determinism.
- Returned values: {vals} (bool each time; the same answer on the repeat: {r["deterministic"]}). The values are not
  read as rates; the arrays are pure noise.
- Time per call: {secs}.
- The faulty body was never run; its syntax was checked with `ast.parse` only. Helper functions (the text shared by
  both files) were checked against brute-force, scipy and scikit-learn references in `work/test_helpers.py`.
- Number of revisions of the fixed body after the first version: 0.

## 7. Deviations from the private note, and problems
{{DEV}}
"""
    dev = {
        "B2B-07": "- Guard: the private note gives 1; the code returns None below 3 samples because the pooled standard deviation divides by n - 2 (the statistic is undefined below 3). Otherwise none.",
        "B2B-13": "- Guard: the private note's minimum 1 is read as one sample in each class (smallest size at which an AUC is defined). Otherwise none.",
        "B2B-06": "- Guard: a one-class label also returns None (zero variance of the label). Otherwise none.",
        "B2B-03": "- SMOTE leaves a class with fewer than 2 records unchanged (no neighbour to interpolate towards); this is an edge of the algorithm, not a test of the data. Otherwise none.",
        "B2B-04": "- SMOTE leaves a class with fewer than 2 records unchanged (no neighbour to interpolate towards); this is an edge of the algorithm. Otherwise none.",
    }.get(local, "- none")
    if local in ("B2B-05", "B2B-12"):
        dev = "- none (oversampling leaves a class with no record unchanged; the guard excludes that for the positive class)."
    md = md.replace("{DEV}", dev)
    with open(os.path.join(folder, "CASE.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
print("CASE.md written for", len(IDS), "cases")
