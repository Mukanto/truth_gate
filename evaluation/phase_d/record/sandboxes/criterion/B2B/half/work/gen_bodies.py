"""Writes faulty_body.py and fixed_body.py of every case of the B2B half from the helper texts in gen_helpers.py and
the per-case criterion texts below. This script only writes text; it neither imports nor runs a body."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_helpers import HELPERS  # noqa: E402

HALF = os.path.dirname(HERE)
IDS = json.load(open(os.path.join(HALF, "CASE_IDS.json"), encoding="utf-8"))

CASES = {}


def case(local, seed, helpers, doc, head, mid_faulty, mid_fixed, tail):
    CASES[local] = dict(seed=seed, helpers=helpers, doc=doc, head=head, mid_faulty=mid_faulty, mid_fixed=mid_fixed,
                        tail=tail)


# ---------------------------------------------------------------- B2B-01 (D-007) ridge, R-squared, resubstitution
case("B2B-01", 2001, ["_standardise", "_ridge_predict", "_r2", "_random_folds"],
     '''Claim: the out-of-sample R-squared for predicting survival_months from the expression profile is at least 0.10.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["survival_months"]: float array (patients,); months from diagnosis to death, observed for every patient.
    Returns True when the statistic is at least 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 patients, constant survival_months).''',
     '''    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["survival_months"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = x.shape[0]
    if n < 2 or y.max() == y.min():
        return None
    rng = np.random.default_rng(2001)
    lam = float(x.shape[1])''',
     '''    pred = _ridge_predict(x, y, x, lam)''',
     '''    folds = _random_folds(rng, n, 5)
    pred = np.zeros(n)
    for f in range(5):
        te = folds == f
        pred[te] = _ridge_predict(x[~te], y[~te], x[te], lam)''',
     '''    return bool(_r2(y, pred) >= 0.10)''')

# ---------------------------------------------------------------- B2B-02 (D-064) ridge, correlation, resubstitution
case("B2B-02", 2002, ["_standardise", "_ridge_predict", "_corr", "_random_folds"],
     '''Claim: the Pearson correlation between predicted and observed response (expression plus clinical covariates) in
    new patients is at least 0.30.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["clinical"]: float array (patients, covariates); standardised clinical covariates of each patient.
    d["response"]: float array (patients,); percentage tumour shrinkage measured after treatment.
    Returns True when the statistic is at least 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 patients, constant response or constant predictions).''',
     '''    xe = np.asarray(d["expression"], dtype=float)
    xc = np.asarray(d["clinical"], dtype=float)
    y = np.asarray(d["response"], dtype=float)
    if not (np.all(np.isfinite(xe)) and np.all(np.isfinite(xc)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    if n < 2 or y.max() == y.min():
        return None
    x = np.hstack([xe, xc])
    rng = np.random.default_rng(2002)
    lam = float(x.shape[1])''',
     '''    pred = _ridge_predict(x, y, x, lam)''',
     '''    folds = _random_folds(rng, n, 10)
    pred = np.zeros(n)
    for f in range(10):
        te = folds == f
        pred[te] = _ridge_predict(x[~te], y[~te], x[te], lam)''',
     '''    if pred.max() == pred.min():
        return None
    return bool(_corr(y, pred) >= 0.30)''')

# ---------------------------------------------------------------- B2B-03 (D-049) SMOTE, CART depth 6, F1
case("B2B-03", 2003, ["_stratified_folds", "_grow", "_tree_predict", "_tree_scores", "_smote", "_f1"],
     '''Claim: a classifier built from the 12 measured variables recognises the positive class in new records with an F1
    score for the positive class of at least 0.50.
    d["features"]: float array (records, variables); measured variables of each record.
    d["positive"]: bool array (records,); True if the condition is present in the record.
    Returns True when the F1 score is at least 0.50, False otherwise, None at an allowed guard (non-finite values, no
    positive record).''',
     '''    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["positive"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if not np.any(y):
        return None
    rng = np.random.default_rng(2003)''',
     '''    xs, ys = _smote(x, y, rng, 5)
    folds = _stratified_folds(rng, ys, 5)
    ye = ys
    pred = np.zeros(ys.size, dtype=bool)
    for f in range(5):
        te = folds == f
        pred[te] = _tree_scores(xs[~te], ys[~te].astype(float), xs[te], rng, 6, 1) > 0.5''',
     '''    folds = _stratified_folds(rng, y, 5)
    ye = y
    pred = np.zeros(y.size, dtype=bool)
    for f in range(5):
        te = folds == f
        xs, ys = _smote(x[~te], y[~te], rng, 5)
        pred[te] = _tree_scores(xs, ys.astype(float), x[te], rng, 6, 1) > 0.5''',
     '''    return bool(_f1(ye, pred) >= 0.50)''')

# ---------------------------------------------------------------- B2B-04 (D-035) SMOTE, 5-NN, balanced accuracy
case("B2B-04", 2004, ["_standardise", "_stratified_folds", "_smote", "_knn_scores", "_balanced_accuracy"],
     '''Claim: a classifier built from the measured variables recognises both classes in new records: the balanced
    accuracy (mean of sensitivity and specificity for the positive class) is at least 0.65.
    d["features"]: float array (records, variables); measured variables of each record.
    d["positive"]: bool array (records,); True if the condition is present in the record.
    Returns True when the balanced accuracy is at least 0.65, False otherwise, None at an allowed guard (non-finite
    values, a class with no record).''',
     '''    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["positive"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.all() or not y.any():
        return None
    rng = np.random.default_rng(2004)''',
     '''    xs, ys = _smote(x, y, rng, 5)
    folds = _stratified_folds(rng, ys, 10)
    ye = ys
    pred = np.zeros(ys.size, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _knn_scores(xs[~te], ys[~te].astype(float), xs[te], 5) > 0.5''',
     '''    folds = _stratified_folds(rng, y, 10)
    ye = y
    pred = np.zeros(y.size, dtype=bool)
    for f in range(10):
        te = folds == f
        xs, ys = _smote(x[~te], y[~te], rng, 5)
        pred[te] = _knn_scores(xs, ys.astype(float), x[te], 5) > 0.5''',
     '''    return bool(_balanced_accuracy(ye, pred) >= 0.65)''')

# ---------------------------------------------------------------- B2B-05 (D-043) random oversampling, CART, sensitivity
case("B2B-05", 2005, ["_stratified_folds", "_grow", "_tree_predict", "_tree_scores", "_oversample"],
     '''Claim: a classifier built from the measurements detects the condition in new records: its sensitivity for the
    positive class is at least 0.60.
    d["measurements"]: float array (records, variables); measured variables of each record.
    d["positive"]: bool array (records,); True if the condition is present in the record.
    Returns True when the sensitivity is at least 0.60, False otherwise, None at an allowed guard (non-finite values,
    no positive record).''',
     '''    x = np.asarray(d["measurements"], dtype=float)
    y = np.asarray(d["positive"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if not np.any(y):
        return None
    rng = np.random.default_rng(2005)''',
     '''    xs, ys = _oversample(x, y, rng)
    folds = _stratified_folds(rng, ys, 5)
    ye = ys
    pred = np.zeros(ys.size, dtype=bool)
    for f in range(5):
        te = folds == f
        pred[te] = _tree_scores(xs[~te], ys[~te].astype(float), xs[te], rng, 1000, 1) > 0.5''',
     '''    folds = _stratified_folds(rng, y, 5)
    ye = y
    pred = np.zeros(y.size, dtype=bool)
    for f in range(5):
        te = folds == f
        xs, ys = _oversample(x[~te], y[~te], rng)
        pred[te] = _tree_scores(xs, ys.astype(float), x[te], rng, 1000, 1) > 0.5''',
     '''    return bool(np.sum(pred & ye) / float(np.sum(ye)) >= 0.60)''')

# ---------------------------------------------------------------- B2B-06 (D-024) top-3 genes, Fisher LDA, error
case("B2B-06", 2006, ["_stratified_folds", "_top_genes", "_lda_predict"],
     '''Claim: gene-expression profiles allow tumour tissue to be distinguished from normal tissue in new samples: the
    classification error rate is at most 0.20.
    d["expression"]: float array (tissues, genes); log expression level of each gene in each tissue sample.
    d["tumour"]: bool array (tissues,); True for a tumour tissue sample, False for a normal tissue sample.
    Returns True when the error rate is at most 0.20, False otherwise, None at an allowed guard (non-finite values,
    no tissue, a class with no tissue).''',
     '''    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["tumour"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 1 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2006)''',
     '''    sel = _top_genes(x, y, 3)
    xs = x[:, sel]
    folds = _stratified_folds(rng, y, 10)
    pred = np.zeros(n, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _lda_predict(xs[~te], y[~te], xs[te])''',
     '''    folds = _stratified_folds(rng, y, 10)
    pred = np.zeros(n, dtype=bool)
    for f in range(10):
        te = folds == f
        sel = _top_genes(x[~te], y[~te], 3)
        pred[te] = _lda_predict(x[~te][:, sel], y[~te], x[te][:, sel])''',
     '''    return bool(np.mean(pred != y) <= 0.20)''')

# ---------------------------------------------------------------- B2B-07 (D-013) nearest shrunken centroids, tuned threshold
case("B2B-07", 2007, ["_stratified_folds", "_nsc_errors", "_cv_errors_nsc", "_pick_delta"],
     '''Claim: gene-expression profiles allow the two classes to be told apart in new samples: the classification error
    rate is at most 0.40.
    d["expression"]: float array (samples, genes); expression level of each gene in each sample.
    d["class_b"]: bool array (samples,); True for a sample of class B, False for a sample of class A.
    Returns True when the error rate is at most 0.40, False otherwise, None at an allowed guard (non-finite values,
    fewer than 3 samples, a class with no sample).''',
     '''    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["class_b"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 3 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2007)
    deltas = np.linspace(0.01, 1.0, 20)''',
     '''    folds = _stratified_folds(rng, y, 10)
    err = _cv_errors_nsc(x, y, folds, 10, deltas)
    stat = err[_pick_delta(err)] / n''',
     '''    errors = 0
    for i in range(n):
        keep = np.arange(n) != i
        xi = x[keep]
        yi = y[keep]
        inner = _stratified_folds(rng, yi, 10)
        best = _pick_delta(_cv_errors_nsc(xi, yi, inner, 10, deltas))
        errors += int(_nsc_errors(xi, yi, x[i:i + 1], y[i:i + 1], deltas[best:best + 1])[0])
    stat = errors / n''',
     '''    return bool(stat <= 0.40)''')

# ---------------------------------------------------------------- B2B-08 (D-059) random forest, random-fold CV, R-squared
case("B2B-08", 2008, ["_random_folds", "_grow", "_tree_predict", "_forest_scores", "_r2"],
     '''Claim: the monthly environmental measurements predict the abundance in later months of the series: the
    out-of-sample R-squared is at least 0.30.
    d["abundance"]: float array (months,); monthly abundance index of the species, on a log scale, in time order.
    d["environment"]: float array (months, variables); monthly environmental measurements, in time order.
    Returns True when the R-squared is at least 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 evaluated months, constant evaluated abundance).''',
     '''    y = np.asarray(d["abundance"], dtype=float)
    x = np.asarray(d["environment"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    rng = np.random.default_rng(2008)
    mtry = max(1, x.shape[1] // 3)''',
     '''    folds = _random_folds(rng, n, 10)
    pred = np.zeros(n)
    for f in range(10):
        te = folds == f
        pred[te] = _forest_scores(x[~te], y[~te], x[te], rng, 50, 5, mtry)
    ye = y''',
     '''    edges = (np.arange(11) * n) // 10
    parts = []
    for b in range(2, 10):
        tr = np.arange(edges[b])
        te = np.arange(edges[b], edges[b + 1])
        parts.append(_forest_scores(x[tr], y[tr], x[te], rng, 50, 5, mtry))
    pred = np.concatenate(parts)
    ye = y[edges[2]:]''',
     '''    if ye.size < 2 or ye.max() == ye.min():
        return None
    return bool(_r2(ye, pred) >= 0.30)''')

# ---------------------------------------------------------------- B2B-09 (D-065) random forest, site grouping, correlation
case("B2B-09", 2009, ["_random_folds", "_grow", "_tree_predict", "_forest_scores", "_corr"],
     '''Claim: habitat measurements predict vegetation cover at new sites: the Pearson correlation between predicted and
    observed cover is at least 0.40.
    d["habitat"]: float array (sites, plots, variables); habitat measurements of each plot at each site.
    d["cover"]: float array (sites, plots); vegetation cover measured in each plot.
    Returns True when the correlation is at least 0.40, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 plots, constant cover or constant predictions).''',
     '''    h = np.asarray(d["habitat"], dtype=float)
    c = np.asarray(d["cover"], dtype=float)
    if not (np.all(np.isfinite(h)) and np.all(np.isfinite(c))):
        return None
    s, m, v = h.shape
    x = h.reshape(s * m, v)
    y = c.reshape(s * m)
    n = y.size
    if n < 2 or y.max() == y.min():
        return None
    rng = np.random.default_rng(2009)
    mtry = max(1, v // 3)''',
     '''    folds = _random_folds(rng, n, 10)
    pred = np.zeros(n)
    for f in range(10):
        te = folds == f
        pred[te] = _forest_scores(x[~te], y[~te], x[te], rng, 40, 5, mtry)''',
     '''    folds = np.repeat(_random_folds(rng, s, 10), m)
    pred = np.zeros(n)
    for f in range(10):
        te = folds == f
        pred[te] = _forest_scores(x[~te], y[~te], x[te], rng, 40, 5, mtry)''',
     '''    if pred.max() == pred.min():
        return None
    return bool(_corr(y, pred) >= 0.40)''')

# ---------------------------------------------------------------- B2B-10 (D-058) random forest, record-wise vs subject-wise, error
case("B2B-10", 2010, ["_random_folds", "_grow", "_tree_predict", "_forest_scores"],
     '''Claim: features computed from wearable-sensor signals recognise walking in newly recruited subjects: the
    classification error rate for walking versus other activities is at most 0.10.
    d["signal_features"]: float array (subjects, windows, features); features computed from the sensor signal in each
    time window of each subject.
    d["walking"]: bool array (subjects, windows); True if the subject was walking during the window.
    Returns True when the error rate is at most 0.10, False otherwise, None at an allowed guard (non-finite values,
    no window).''',
     '''    x3 = np.asarray(d["signal_features"], dtype=float)
    y2 = np.asarray(d["walking"], dtype=bool)
    if not np.all(np.isfinite(x3)):
        return None
    s, m, v = x3.shape
    x = x3.reshape(s * m, v)
    y = y2.reshape(s * m)
    n = y.size
    if n < 1:
        return None
    rng = np.random.default_rng(2010)
    mtry = max(1, int(np.sqrt(v)))''',
     '''    folds = _random_folds(rng, n, 10)
    pred = np.zeros(n, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _forest_scores(x[~te], y[~te].astype(float), x[te], rng, 50, 1, mtry) > 0.5''',
     '''    folds = np.repeat(_random_folds(rng, s, 10), m)
    pred = np.zeros(n, dtype=bool)
    for f in range(10):
        te = folds == f
        pred[te] = _forest_scores(x[~te], y[~te].astype(float), x[te], rng, 50, 1, mtry) > 0.5''',
     '''    return bool(np.mean(pred != y) <= 0.10)''')

# ---------------------------------------------------------------- B2B-11 (D-070) logistic regression, AUC
case("B2B-11", 2011, ["_standardise", "_logit_scores", "_stratified_folds", "_auc"],
     '''Claim: gene-expression profiles predict five-year relapse in new patients: the area under the ROC curve is at
    least 0.70.
    d["expression"]: float array (patients, genes); log2 expression level of each gene in each patient's tumour sample.
    d["relapse_5y"]: bool array (patients,); True if the patient relapsed within five years of diagnosis.
    Returns True when the AUC is at least 0.70, False otherwise, None at an allowed guard (non-finite values, fewer
    than 2 patients, a class with no patient).''',
     '''    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["relapse_5y"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 2 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2011)
    lam = float(x.shape[1])''',
     '''    scores = _logit_scores(x, y, x, lam)''',
     '''    folds = _stratified_folds(rng, y, 10)
    scores = np.zeros(n)
    for f in range(10):
        te = folds == f
        scores[te] = _logit_scores(x[~te], y[~te], x[te], lam)''',
     '''    return bool(_auc(scores, y) >= 0.70)''')

# ---------------------------------------------------------------- B2B-12 (D-003) random oversampling, 5-NN, AUC
case("B2B-12", 2012, ["_standardise", "_stratified_folds", "_oversample", "_knn_scores", "_auc"],
     '''Claim: a classifier built from the measured variables ranks new records correctly: the area under the ROC curve
    for the event is at least 0.75.
    d["features"]: float array (records, variables); measured variables of each record.
    d["event"]: bool array (records,); True if the event occurred for the record.
    Returns True when the AUC is at least 0.75, False otherwise, None at an allowed guard (non-finite values, a class
    with no record).''',
     '''    x = np.asarray(d["features"], dtype=float)
    y = np.asarray(d["event"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    if y.all() or not y.any():
        return None
    rng = np.random.default_rng(2012)''',
     '''    xs, ys = _oversample(x, y, rng)
    folds = _stratified_folds(rng, ys, 10)
    ye = ys
    scores = np.zeros(ys.size)
    for f in range(10):
        te = folds == f
        scores[te] = _knn_scores(xs[~te], ys[~te].astype(float), xs[te], 5)''',
     '''    folds = _stratified_folds(rng, y, 10)
    ye = y
    scores = np.zeros(y.size)
    for f in range(10):
        te = folds == f
        xs, ys = _oversample(x[~te], y[~te], rng)
        scores[te] = _knn_scores(xs, ys.astype(float), x[te], 5)''',
     '''    return bool(_auc(scores, ye) >= 0.75)''')

# ---------------------------------------------------------------- B2B-13 (D-011) top-20 genes, nearest centroid, AUC
case("B2B-13", 2013, ["_stratified_folds", "_top_genes", "_centroid_scores", "_auc"],
     '''Claim: gene-expression profiles distinguish the two leukaemia types in new samples: the area under the ROC curve
    is at least 0.90.
    d["expression"]: float array (samples, genes); expression level of each gene in each bone-marrow sample.
    d["myeloid"]: bool array (samples,); True for acute myeloid leukaemia, False for acute lymphoblastic leukaemia.
    Returns True when the AUC is at least 0.90, False otherwise, None at an allowed guard (non-finite values, no
    sample, a class with no sample).''',
     '''    x = np.asarray(d["expression"], dtype=float)
    y = np.asarray(d["myeloid"], dtype=bool)
    if not np.all(np.isfinite(x)):
        return None
    n = y.size
    if n < 1 or y.all() or not y.any():
        return None
    rng = np.random.default_rng(2013)''',
     '''    sel = _top_genes(x, y, 20)
    xs = x[:, sel]
    folds = _stratified_folds(rng, y, 10)
    scores = np.zeros(n)
    for f in range(10):
        te = folds == f
        scores[te] = _centroid_scores(xs[~te], y[~te], xs[te])''',
     '''    folds = _stratified_folds(rng, y, 10)
    scores = np.zeros(n)
    for f in range(10):
        te = folds == f
        sel = _top_genes(x[~te], y[~te], 20)
        scores[te] = _centroid_scores(x[~te][:, sel], y[~te], x[te][:, sel])''',
     '''    return bool(_auc(scores, y) >= 0.90)''')

# ---------------------------------------------------------------- B2B-14 (D-034) 5-NN regression, random folds, scaled RMSE
case("B2B-14", 2014, ["_standardise", "_random_folds", "_knn_scores"],
     '''Claim: the daily driver measurements predict the daily river level in later days of the record: the root-mean-
    square error of the prediction is at most 0.70 standard deviations of the level.
    d["level"]: float array (days,); daily river level, in time order.
    d["drivers"]: float array (days, variables); daily measurements of the variables that may influence the river
    level, in time order.
    Returns True when RMSE / SD(level) is at most 0.70, False otherwise, None at an allowed guard (non-finite values,
    no evaluated day, constant evaluated level).''',
     '''    y = np.asarray(d["level"], dtype=float)
    x = np.asarray(d["drivers"], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    n = y.size
    rng = np.random.default_rng(2014)''',
     '''    folds = _random_folds(rng, n, 10)
    pred = np.zeros(n)
    for f in range(10):
        te = folds == f
        pred[te] = _knn_scores(x[~te], y[~te], x[te], 5)
    ye = y''',
     '''    edges = (np.arange(11) * n) // 10
    parts = []
    for b in range(2, 10):
        tr = np.arange(edges[b])
        te = np.arange(edges[b], edges[b + 1])
        parts.append(_knn_scores(x[tr], y[tr], x[te], 5))
    pred = np.concatenate(parts)
    ye = y[edges[2]:]''',
     '''    if ye.size < 1 or ye.max() == ye.min():
        return None
    return bool(np.sqrt(np.mean((ye - pred) ** 2)) / ye.std() <= 0.70)''')

# ---------------------------------------------------------------- B2B-15 (D-018) random forest, record-wise vs subject-wise, AUC
case("B2B-15", 2015, ["_random_folds", "_grow", "_tree_predict", "_forest_scores", "_auc"],
     '''Claim: sensor measurements classify the disease status of newly recruited subjects: the area under the ROC curve
    of the classification is at least 0.70.
    d["measurements"]: float array (subjects, records, variables); sensor measurements of each recording of each
    subject.
    d["diseased"]: bool array (subjects,); True if the subject has the disease.
    Returns True when the AUC is at least 0.70, False otherwise, None at an allowed guard (non-finite values, fewer
    than 2 subjects, no diseased or no healthy subject).''',
     '''    x3 = np.asarray(d["measurements"], dtype=float)
    dis = np.asarray(d["diseased"], dtype=bool)
    if not np.all(np.isfinite(x3)):
        return None
    s, m, v = x3.shape
    x = x3.reshape(s * m, v)
    y = np.repeat(dis, m)
    n = y.size
    if s < 2 or dis.all() or not dis.any():
        return None
    rng = np.random.default_rng(2015)
    mtry = max(1, int(np.sqrt(v)))''',
     '''    nf = 10
    folds = _random_folds(rng, n, nf)
    scores = np.zeros(n)
    for f in range(nf):
        te = folds == f
        scores[te] = _forest_scores(x[~te], y[~te].astype(float), x[te], rng, 50, 1, mtry)''',
     '''    nf = s // 2
    folds = np.repeat(_random_folds(rng, s, nf), m)
    scores = np.zeros(n)
    for f in range(nf):
        te = folds == f
        scores[te] = _forest_scores(x[~te], y[~te].astype(float), x[te], rng, 50, 1, mtry)''',
     '''    return bool(_auc(scores, y) >= 0.70)''')


def build(local, which):
    c = CASES[local]
    parts = ["import numpy as np", ""]
    for h in c["helpers"]:
        parts.append("")
        parts.append(HELPERS[h].rstrip("\n"))
        parts.append("")
    parts.append("")
    mid = c["mid_faulty"] if which == "faulty" else c["mid_fixed"]
    parts.append("def criterion(d):")
    parts.append('    """' + c["doc"] + '"""')
    parts.append(c["head"])
    parts.append(mid)
    parts.append(c["tail"])
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    for local, cid in IDS.items():
        for which in ("faulty", "fixed"):
            path = os.path.join(HALF, "cases", cid, which + "_body.py")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(build(local, which))
    print("written", len(IDS) * 2, "files")
