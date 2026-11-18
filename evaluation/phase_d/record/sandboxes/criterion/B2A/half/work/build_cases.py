"""Builder for the B2A criterion bodies (faulty and fixed).

It only assembles text files: shared helpers + a shared criterion frame, and the
error block (faulty) or the correction block (fixed).  It never imports or runs the
bodies it writes.
"""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cases")

H = {}

H["ridge_fit"] = '''def ridge_fit(X, y, lam):
    """Ridge regression on columns standardised with the mean and sd of the rows given, with an
    unpenalised intercept (y centred).  Closed form; dual form when columns outnumber rows."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    ym = y.mean()
    n, p = Z.shape
    if p > n:
        beta = Z.T @ np.linalg.solve(Z @ Z.T + lam * np.eye(n), y - ym)
    else:
        beta = np.linalg.solve(Z.T @ Z + lam * np.eye(p), Z.T @ (y - ym))
    return mu, sd, beta, ym
'''

H["ridge_predict"] = '''def ridge_predict(model, X):
    """Predictions of a model returned by ridge_fit."""
    mu, sd, beta, ym = model
    return ((X - mu) / sd) @ beta + ym
'''

H["pearson"] = '''def pearson(a, b):
    """Pearson correlation; None when it is undefined (fewer than 2 values, zero variance, non-finite)."""
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if not den > 0:
        return None
    return float(np.sum(a * b) / den)
'''

H["average_ranks"] = '''def average_ranks(v):
    """Ranks 1..n of v, ties receiving the average rank."""
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    starts = np.flatnonzero(np.concatenate([[True], sv[1:] != sv[:-1]]))
    ends = np.concatenate([starts[1:], [v.shape[0]]])
    r = np.empty(v.shape[0])
    r[order] = np.repeat((starts + ends + 1) / 2.0, ends - starts)
    return r
'''

H["auc"] = '''def auc(score, label):
    """Area under the ROC curve (Mann-Whitney form, ties count one half); label is boolean."""
    npos = int(label.sum())
    nneg = label.shape[0] - npos
    r = average_ranks(score)
    return float((r[label].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))
'''

H["strat_folds"] = '''def strat_folds(y):
    """Fold of each row: its rank within its own class (in row order) modulo 5."""
    fold = np.empty(y.shape[0], dtype=int)
    fold[y] = np.arange(int(y.sum())) % 5
    fold[~y] = np.arange(int((~y).sum())) % 5
    return fold
'''

H["nn_predict"] = '''def nn_predict(Xtr, ytr, Xte):
    """One-nearest-neighbour prediction: the y of the nearest training row (Euclidean distance on
    columns standardised with the training mean and sd; the first of tied rows wins)."""
    mu = Xtr.mean(axis=0)
    sd = Xtr.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    A = (Xtr - mu) / sd
    B = (Xte - mu) / sd
    D2 = (B ** 2).sum(axis=1)[:, None] + (A ** 2).sum(axis=1)[None, :] - 2.0 * (B @ A.T)
    return ytr[np.argmin(D2, axis=1)]
'''

H["cv_nn"] = '''def cv_nn(X, y, fold):
    """Pooled held-out one-nearest-neighbour predictions over the 5 folds given by fold."""
    pred = np.empty(y.shape[0], dtype=y.dtype)
    for k in range(5):
        te = fold == k
        pred[te] = nn_predict(X[~te], y[~te], X[te])
    return pred
'''

H["fold_mean_baseline"] = '''def fold_mean_baseline(y, fold):
    """For each row, the mean of y over the rows outside its fold (the training-fold mean predictor)."""
    base = np.empty(y.shape[0])
    for k in range(5):
        te = fold == k
        base[te] = y[~te].mean()
    return base
'''

H["poly"] = '''def poly_features(Z):
    """Intercept, linear terms, squares and all pairwise products of the columns of Z."""
    n, p = Z.shape
    iu, ju = np.triu_indices(p)
    return np.column_stack([np.ones(n), Z, Z[:, iu] * Z[:, ju]])


def poly_fit(X, y):
    """Second-order polynomial regression by ordinary least squares on standardised columns."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    coef = np.linalg.lstsq(poly_features((X - mu) / sd), y, rcond=None)[0]
    return mu, sd, coef


def poly_predict(model, X):
    """Predictions of a model returned by poly_fit."""
    mu, sd, coef = model
    return poly_features((X - mu) / sd) @ coef
'''

H["impute"] = '''def impute(X, fit, aux, sweeps=5):
    """Iterative regression imputation.  Start from the column means over the rows in fit; in each sweep
    every incomplete column is regressed (ridge, penalty 1.0) on the other columns of X and on the columns
    of aux, fitted on the rows in fit where the column was observed, and applied to the rows where it is
    missing (all rows, whether in fit or not)."""
    n, p = X.shape
    miss = np.isnan(X)
    cnt = (~miss[fit]).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mu = np.where(miss[fit], 0.0, X[fit]).sum(axis=0) / cnt
    Xc = np.where(miss, mu, X)
    for _ in range(sweeps):
        for j in range(p):
            mj = miss[:, j]
            if not mj.any():
                continue
            Z = np.column_stack([np.delete(Xc, j, axis=1), aux])
            obs = fit & ~mj
            m = ridge_fit(Z[obs], Xc[obs, j], 1.0)
            Xc[mj, j] = ridge_predict(m, Z[mj])
    return Xc
'''

H["district_means"] = '''def district_means(C, y, rows):
    """Mean of y per category (column of C) over the rows selected; the grand mean of those rows for a
    category with no selected row."""
    Cr = C[rows].astype(float)
    cnt = Cr.sum(axis=0)
    grand = y[rows].mean()
    return np.where(cnt > 0, (Cr.T @ y[rows]) / np.maximum(cnt, 1.0), grand)
'''

H["ols_predict"] = '''def ols_predict(A, y, tr, te):
    """Ordinary least squares (numpy lstsq) of y on the columns of A over the rows tr; predictions for rows te."""
    coef = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    return A[te] @ coef
'''

H["top_t"] = '''def top_t(X, y, m):
    """Indices of the m columns with the largest absolute Welch two-sample t statistic between the rows
    with y True and the rows with y False (a column with no spread scores 0)."""
    A = X[y]
    B = X[~y]
    with np.errstate(invalid="ignore", divide="ignore"):
        se = np.sqrt(A.var(axis=0, ddof=1) / A.shape[0] + B.var(axis=0, ddof=1) / B.shape[0])
        t = (A.mean(axis=0) - B.mean(axis=0)) / se
    t = np.where(np.isfinite(t), np.abs(t), 0.0)
    return np.argsort(-t, kind="stable")[:m]
'''

H["top_corr"] = '''def top_corr(X, y, m):
    """Indices of the m columns with the largest absolute Pearson correlation with y (a column with no
    spread scores 0)."""
    A = X - X.mean(axis=0)
    b = y - y.mean()
    den = np.sqrt((A ** 2).sum(axis=0) * (b ** 2).sum())
    r = (A * b[:, None]).sum(axis=0) / np.where(den > 0, den, 1.0)
    return np.argsort(-np.abs(r), kind="stable")[:m]
'''

H["link_components"] = '''def link_components(X, frac):
    """Single-linkage components of the rows of X: two rows are linked when their distance (Euclidean, on
    columns standardised with all rows) is below frac times the median pairwise distance.  Returns the
    component number of each row, numbered in order of the first member of each component."""
    sd = X.std(axis=0)
    Z = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)
    sq = (Z ** 2).sum(axis=1)
    D = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2.0 * (Z @ Z.T), 0.0))
    n = D.shape[0]
    med = np.median(D[np.triu_indices(n, k=1)])
    A = D < frac * med
    lab = np.arange(n)
    while True:
        new = np.minimum(lab, np.where(A, lab[None, :], n).min(axis=1))
        if np.array_equal(new, lab):
            break
        lab = new
    return np.searchsorted(np.unique(lab), lab)
'''

H["col_means"] = '''def col_means(X, rows):
    """Mean of each column of X over the rows selected, ignoring NaN (NaN for a column with no value)."""
    miss = np.isnan(X[rows])
    cnt = (~miss).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(miss, 0.0, X[rows]).sum(axis=0) / cnt
'''

H["fill"] = '''def fill(X, mu):
    """Replace the NaN entries of X by the value of the same column in mu."""
    return np.where(np.isnan(X), mu, X)
'''

H["logit"] = '''def logit_fit(X, y, lam):
    """Ridge-penalised logistic regression (penalty lam on the coefficients of columns standardised with
    the mean and sd of the rows given, intercept unpenalised), 25 Newton iterations from zero."""
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    n, p = Z.shape
    A = np.column_stack([np.ones(n), Z])
    pen = lam * np.eye(p + 1)
    pen[0, 0] = 0.0
    t = y.astype(float)
    w = np.zeros(p + 1)
    for _ in range(25):
        q = 0.5 * (1.0 + np.tanh(0.5 * (A @ w)))
        g = A.T @ (q - t) + pen @ w
        Hm = (A.T * (q * (1.0 - q))) @ A + pen
        w = w - np.linalg.solve(Hm, g)
    return mu, sd, w


def logit_predict(model, X):
    """Linear predictor (log odds) of a model returned by logit_fit."""
    mu, sd, w = model
    return w[0] + ((X - mu) / sd) @ w[1:]
'''

H["balanced_accuracy"] = '''def balanced_accuracy(y, pred):
    """Mean of sensitivity and specificity; y and pred are boolean."""
    return 0.5 * (np.mean(pred[y]) + np.mean(~pred[~y]))
'''

H["slope"] = '''def slope(x, y):
    """Slope of the ordinary least squares regression of y on x (with intercept); None when x has no spread."""
    a = x - x.mean()
    den = np.sum(a * a)
    if not den > 0:
        return None
    return float(np.sum(a * (y - y.mean())) / den)
'''

CASES = []


def case(**kw):
    CASES.append(kw)


# ---------------------------------------------------------------- B2A-01 (D-005)
PRE_REG = '''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
'''
POST_R2 = '''    sst = np.sum((y - y.mean()) ** 2)
    if not sst > 0:
        return None
    r2 = 1.0 - np.sum((y - pred) ** 2) / sst
    if not np.isfinite(r2):
        return None
    return bool(r2 >= 0.10)
'''
CV_RIDGE = '''    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te], y[~te], 1.0), X[te])
'''

case(
    id="D-005",
    helpers=["ridge_fit", "ridge_predict"],
    doc='''Claim: the R-squared of a ridge regression (penalty 1.0, standardised measurements, intercept) of y on X,
    evaluated on new samples, is at least 0.10.

    Data keys:
      "X": float array (samples, features) = (100, 150); the 150 continuous biomarker measurements of each sample.
      "y": float array (samples,) = (100,); the continuous clinical score of each sample.

    Returns True when R-squared >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero variance of y).''',
    pre=PRE_REG,
    faulty='''    pred = ridge_predict(ridge_fit(X, y, 1.0), X)
''',
    fixed=CV_RIDGE,
    post=POST_R2,
)

# ---------------------------------------------------------------- B2A-02 (D-022)
case(
    id="D-022",
    helpers=["pearson", "poly"],
    doc='''Claim: a second-order polynomial regression of y on X (intercept, the 10 readings, their squares and all
    pairwise products, ordinary least squares) predicts y for new runs with a Pearson correlation between
    predicted and observed y of at least 0.30.

    Data keys:
      "X": float array (samples, features) = (300, 10); the 10 continuous process readings of each production run.
      "y": float array (samples,) = (300,); the continuous quality score of each production run.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 runs, zero variance of the predictions or of y).''',
    pre=PRE_REG,
    faulty='''    pred = poly_predict(poly_fit(X, y), X)
''',
    fixed='''    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = poly_predict(poly_fit(X[~te], y[~te]), X[te])
''',
    post='''    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
''',
)

# ---------------------------------------------------------------- B2A-03 (D-014)
case(
    id="D-014",
    helpers=["ridge_fit", "ridge_predict", "impute"],
    doc='''Claim: the R-squared of a ridge regression (penalty 1.0, standardised values, intercept) of y on the 20
    laboratory values in X, for new patients, is at least 0.10.  Values not measured are NaN and are filled
    by iterative ridge regression imputation (5 sweeps) before the regression.

    Data keys:
      "X": float array (samples, features) = (250, 20); the 20 laboratory values of each patient, NaN where
           a value was not measured.
      "y": float array (samples,) = (250,); the continuous clinical outcome of each patient.

    Returns True when R-squared >= 0.10, False otherwise, None at an allowed guard (infinite values in X or
    non-finite y, fewer than 2 patients, a column with no observed value, zero variance of y).''',
    pre='''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if np.any(np.isinf(X)) or not np.all(np.isfinite(y)):
        return None
    fold = np.arange(n) % 5
    pred = np.empty(n)
''',
    faulty='''    Xc = impute(X, np.ones(n, dtype=bool), y[:, None])
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(Xc[~te], y[~te], 1.0), Xc[te])
''',
    fixed='''    for k in range(5):
        te = fold == k
        Xc = impute(X, ~te, np.empty((n, 0)))
        pred[te] = ridge_predict(ridge_fit(Xc[~te], y[~te], 1.0), Xc[te])
''',
    post=POST_R2,
)

# ---------------------------------------------------------------- B2A-04 (D-010)
case(
    id="D-010",
    helpers=["pearson", "district_means", "ols_predict"],
    doc='''Claim: the postal district and the three covariates together predict y for new patients: the Pearson
    correlation between predicted and observed y is at least 0.25.  The district enters as its mean-outcome
    encoding; the model is ordinary least squares of y on an intercept, the encoding and the 3 covariates.

    Data keys:
      "category":   bool array (samples, categories) = (1200, 150); True where the patient's home postal
                    district is the district of that column (one True per row).
      "covariates": float array (samples, features) = (1200, 3); age, body-mass index and systolic pressure.
      "y":          float array (samples,) = (1200,); the continuous health outcome of each patient.

    Returns True when the correlation >= 0.25, False otherwise, None at an allowed guard (non-finite
    covariates or y, fewer than 2 patients, zero variance of the predictions or of y).''',
    pre='''    C = np.asarray(d["category"], dtype=bool)
    V = np.asarray(d["covariates"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    n = y.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(V)) and np.all(np.isfinite(y))):
        return None
    Cf = C.astype(float)
    fold = np.arange(n) % 5
    pred = np.empty(n)
''',
    faulty='''    enc = Cf @ district_means(C, y, np.ones(n, dtype=bool))
    A = np.column_stack([np.ones(n), enc, V])
    for k in range(5):
        te = fold == k
        pred[te] = ols_predict(A, y, ~te, te)
''',
    fixed='''    for k in range(5):
        te = fold == k
        enc = Cf @ district_means(C, y, ~te)
        A = np.column_stack([np.ones(n), enc, V])
        pred[te] = ols_predict(A, y, ~te, te)
''',
    post='''    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.25)
''',
)

# ---------------------------------------------------------------- B2A-05 (D-054)
case(
    id="D-054",
    helpers=["ridge_fit", "ridge_predict", "average_ranks", "auc", "strat_folds", "top_t"],
    doc='''Claim: the area under the ROC curve of a linear classifier (ridge regression, penalty 10, standardised
    features, on the diagnosis coded +1/-1) that uses 20 of the 1000 expression features, for new subjects,
    is at least 0.65.  The 20 features are the ones with the largest absolute two-sample (Welch) t statistic
    between cases and controls.

    Data keys:
      "X": float array (samples, features) = (80, 1000); expression level of each gene for each subject.
      "y": bool array (samples,) = (80,); True where the subject has the diagnosis, False for a control.

    Returns True when the AUC >= 0.65, False otherwise, None at an allowed guard (non-finite X, fewer than
    one case or one control, constant scores).''',
    pre='''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 1 or int((~y).sum()) < 1:
        return None
    if not np.all(np.isfinite(X)):
        return None
    fold = strat_folds(y)
    t = np.where(y, 1.0, -1.0)
    score = np.empty(n)
''',
    faulty='''    sel = top_t(X, y, 20)
    for k in range(5):
        te = fold == k
        score[te] = ridge_predict(ridge_fit(X[~te][:, sel], t[~te], 10.0), X[te][:, sel])
''',
    fixed='''    for k in range(5):
        te = fold == k
        sel = top_t(X[~te], y[~te], 20)
        score[te] = ridge_predict(ridge_fit(X[~te][:, sel], t[~te], 10.0), X[te][:, sel])
''',
    post='''    if not np.std(score) > 0:
        return None
    a = auc(score, y)
    if not np.isfinite(a):
        return None
    return bool(a >= 0.65)
''',
)

# ---------------------------------------------------------------- B2A-06 (D-029)
POST_SKILL_MAE = '''    mae0 = np.mean(np.abs(y - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(y - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= {thr})
'''
case(
    id="D-029",
    helpers=["nn_predict", "cv_nn", "fold_mean_baseline"],
    doc='''Claim: a one-nearest-neighbour regression (Euclidean distance on standardised measurements) of y on X
    predicts y for new entries with a mean absolute error at least 10% below that of predicting the mean
    of y: 1 - MAE(model) / MAE(mean predictor) >= 0.10.  Evaluated by 5-fold cross-validation (fold of
    row i = i mod 5); the mean predictor of a held-out row is the mean of y over its training folds.

    Data keys:
      "X": float array (rows, features) = (600, 8); the 8 continuous property measurements of each registry entry.
      "y": float array (rows,) = (600,); the continuous target value of each registry entry.

    Returns True when the skill >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 rows, zero MAE of the mean predictor).''',
    pre=PRE_REG,
    faulty='',
    fixed='''    sd = X.std(axis=0)
    Z = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)
    D2 = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(axis=2)
    dup = np.tril(D2 < 1e-16, k=-1).any(axis=1)
    X = X[~dup]
    y = y[~dup]
    n = y.shape[0]
    if n < 2:
        return None
''',
    post='''    fold = np.arange(n) % 5
    pred = cv_nn(X, y, fold)
    base = fold_mean_baseline(y, fold)
''' + POST_SKILL_MAE.format(thr="0.10"),
)

# ---------------------------------------------------------------- B2A-07 (D-042)
case(
    id="D-042",
    helpers=["pearson", "nn_predict", "cv_nn", "link_components"],
    doc='''Claim: a one-nearest-neighbour regression (Euclidean distance on standardised descriptors) of y on X
    predicts y for new compounds with a Pearson correlation between predicted and observed y of at least
    0.30.  Evaluated by 5-fold cross-validation over the records.

    Data keys:
      "X": float array (records, features) = (1200, 20); the 20 continuous molecular descriptors of each compound record.
      "y": float array (records,) = (1200,); the continuous activity response measured for each compound record.

    Returns True when the correlation >= 0.30, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 records, zero variance of the predictions or of y).''',
    pre=PRE_REG,
    faulty='''    fold = np.arange(n) % 5
''',
    fixed='''    fold = link_components(X, 0.1) % 5
''',
    post='''    pred = cv_nn(X, y, fold)
    r = pearson(pred, y)
    if r is None:
        return None
    return bool(r >= 0.30)
''',
)

# ---------------------------------------------------------------- B2A-08 (D-055)
case(
    id="D-055",
    helpers=["ridge_fit", "ridge_predict", "pearson"],
    doc='''Claim: on future days, the Pearson correlation between y and the prediction of a ridge regression of y on
    X (penalty 1.0, standardised predictors, intercept) is at least 0.20.

    Data keys:
      "X": float array (days_in_order, features) = (1000, 6); the 6 continuous daily predictor series, rows in
           time order.
      "y": float array (days_in_order,) = (1000,); the continuous daily outcome, in time order.

    Returns True when the correlation >= 0.20, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 days, zero variance of the predictions or of y).''',
    pre=PRE_REG + '''    pred = np.empty(n)
''',
    faulty='''    rng = np.random.default_rng(0)
    fold = np.empty(n, dtype=int)
    fold[rng.permutation(n)] = np.arange(n) % 5
    ev = np.ones(n, dtype=bool)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te], y[~te], 1.0), X[te])
''',
    fixed='''    ev = np.zeros(n, dtype=bool)
    for blk in np.array_split(np.arange(n), 6)[1:]:
        tr = np.arange(n) < blk[0] - 5
        pred[blk] = ridge_predict(ridge_fit(X[tr], y[tr], 1.0), X[blk])
        ev[blk] = True
''',
    post='''    r = pearson(pred[ev], y[ev])
    if r is None:
        return None
    return bool(r >= 0.20)
''',
)

# ---------------------------------------------------------------- B2A-09 (D-004)
case(
    id="D-004",
    helpers=["ridge_fit", "ridge_predict"],
    doc='''Claim: on future days, a ridge regression forecast of y from the day's 5 predictors X (penalty 1.0,
    standardised predictors, intercept, one model for all stations) has a squared error at least 5% below
    that of the persistence forecast (the previous day's y at the same station), squared errors pooled over
    stations: 1 - MSE(model) / MSE(persistence) >= 0.05.

    Data keys:
      "X": float array (stations, days_in_order, features) = (40, 250, 5); the 5 continuous daily predictors
           at each station on each day, days in time order.
      "y": float array (stations, days_in_order) = (40, 250); the continuous daily outcome at each station,
           days in time order.

    Returns True when the skill >= 0.05, False otherwise, None at an allowed guard (non-finite values, no
    forecast day, zero MSE of the persistence forecast).''',
    pre='''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    S, T, F = X.shape
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    Xf = X.reshape(S * T, F)
    yf = y.reshape(S * T)
''',
    faulty='''    rng = np.random.default_rng(0)
    fold = np.empty(S * T, dtype=int)
    fold[rng.permutation(S * T)] = np.arange(S * T) % 5
    pred = np.empty(S * T)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(Xf[~te], yf[~te], 1.0), Xf[te])
    ev = np.zeros((S, T), dtype=bool)
    ev[:, 1:] = True
''',
    fixed='''    cut = (7 * T) // 10
    tr = np.zeros((S, T), dtype=bool)
    tr[:, :cut] = True
    pred = ridge_predict(ridge_fit(X[tr], y[tr], 1.0), Xf)
    ev = np.zeros((S, T), dtype=bool)
    ev[:, cut:] = True
''',
    post='''    pred = pred.reshape(S, T)
    prev = np.zeros((S, T))
    prev[:, 1:] = y[:, :-1]
    if not ev.any():
        return None
    mse0 = np.mean((y[ev] - prev[ev]) ** 2)
    if not mse0 > 0:
        return None
    skill = 1.0 - np.mean((y[ev] - pred[ev]) ** 2) / mse0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.05)
''',
)

# ---------------------------------------------------------------- B2A-10 (D-044)
case(
    id="D-044",
    helpers=["ridge_fit", "ridge_predict", "fold_mean_baseline"],
    doc='''Claim: for new subjects, a ridge regression of the trial-level outcome y on the features X (penalty 1.0,
    standardised features, intercept) has a mean absolute error at least 5% below that of predicting the
    mean outcome: 1 - MAE(model) / MAE(mean predictor) >= 0.05.  Evaluated by 5-fold cross-validation over
    the pooled subject-trial rows; the mean predictor of a held-out row is the mean of y over its training folds.

    Data keys:
      "X": float array (subjects, trials, features) = (60, 30, 25); the 25 continuous features computed for
           each trial of each subject.
      "y": float array (subjects, trials) = (60, 30); the continuous outcome of each trial of each subject.

    Returns True when the skill >= 0.05, False otherwise, None at an allowed guard (non-finite values, no
    held-out trial, zero MAE of the mean predictor).''',
    pre='''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    S, T, F = X.shape
    if S * T < 2:
        return None
    if not (np.all(np.isfinite(X)) and np.all(np.isfinite(y))):
        return None
    Xf = X.reshape(S * T, F)
    yf = y.reshape(S * T)
''',
    faulty='''    rng = np.random.default_rng(0)
    fold = np.empty(S * T, dtype=int)
    fold[rng.permutation(S * T)] = np.arange(S * T) % 5
''',
    fixed='''    fold = np.repeat(np.arange(S) % 5, T)
''',
    post='''    pred = np.empty(S * T)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(Xf[~te], yf[~te], 1.0), Xf[te])
    base = fold_mean_baseline(yf, fold)
    mae0 = np.mean(np.abs(yf - base))
    if not mae0 > 0:
        return None
    skill = 1.0 - np.mean(np.abs(yf - pred)) / mae0
    if not np.isfinite(skill):
        return None
    return bool(skill >= 0.05)
''',
)

# ---------------------------------------------------------------- B2A-R1 (D-027)
case(
    id="D-027",
    helpers=["ols_predict", "fold_mean_baseline"],
    doc='''Claim: the mean absolute error of an ordinary least squares regression of y on the 25 measurements X
    (with an intercept), for new samples, is at least 10% below that of predicting the mean of y:
    1 - MAE(model) / MAE(mean predictor) >= 0.10.

    Data keys:
      "X": float array (samples, features) = (60, 25); the 25 continuous measurements of each sample.
      "y": float array (samples,) = (60,); the continuous outcome of each sample.

    Returns True when the skill >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero MAE of the mean predictor).''',
    pre=PRE_REG + '''    A = np.column_stack([np.ones(n), X])
''',
    faulty='''    every = np.ones(n, dtype=bool)
    pred = ols_predict(A, y, every, every)
    base = np.full(n, y.mean())
''',
    fixed='''    fold = np.arange(n) % 5
    pred = np.empty(n)
    for k in range(5):
        te = fold == k
        pred[te] = ols_predict(A, y, ~te, te)
    base = fold_mean_baseline(y, fold)
''',
    post=POST_SKILL_MAE.format(thr="0.10"),
)

# ---------------------------------------------------------------- B2A-R2 (D-041)
case(
    id="D-041",
    helpers=["col_means", "fill", "logit", "average_ranks", "auc", "strat_folds"],
    doc='''Claim: the area under the ROC curve of a ridge-penalised logistic regression (penalty 1.0,
    standardised indicators) of the civil-war onset y on X, for new country-years, is at least 0.75.
    Missing indicators are filled with a column mean before the regression.

    Data keys:
      "X": float array (samples, features) = (1400, 25); the 25 continuous country-year indicators, NaN where
           an indicator was not recorded.
      "y": bool array (samples,) = (1400,); True where a civil war onset occurred in the country-year.

    Returns True when the AUC >= 0.75, False otherwise, None at an allowed guard (infinite values in X,
    fewer than one onset or one non-onset, a column with no recorded value, constant scores).''',
    pre='''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 1 or int((~y).sum()) < 1:
        return None
    if np.any(np.isinf(X)):
        return None
    fold = strat_folds(y)
    score = np.empty(n)
''',
    faulty='''    Xc = np.empty_like(X)
    for c in (True, False):
        s = y == c
        Xc[s] = fill(X[s], col_means(X, s))
    for k in range(5):
        te = fold == k
        score[te] = logit_predict(logit_fit(Xc[~te], y[~te], 1.0), Xc[te])
''',
    fixed='''    for k in range(5):
        te = fold == k
        Xc = fill(X, col_means(X, ~te))
        score[te] = logit_predict(logit_fit(Xc[~te], y[~te], 1.0), Xc[te])
''',
    post='''    if not np.all(np.isfinite(score)):
        return None
    if not np.std(score) > 0:
        return None
    a = auc(score, y)
    return bool(a >= 0.75)
''',
)

# ---------------------------------------------------------------- B2A-R3 (D-060)
case(
    id="D-060",
    helpers=["ridge_fit", "ridge_predict", "top_corr"],
    doc='''Claim: the R-squared of a ridge-penalised linear regression of y (penalty 10, standardised features,
    intercept) that uses 20 of the 500 features, for new samples, is at least 0.10.  The 20 features are
    the ones with the largest absolute Pearson correlation with y.

    Data keys:
      "X": float array (samples, features) = (100, 500); the 500 continuous imaging-derived features of each sample.
      "y": float array (samples,) = (100,); the continuous symptom score of each sample.

    Returns True when R-squared >= 0.10, False otherwise, None at an allowed guard (non-finite values,
    fewer than 2 samples, zero variance of y).''',
    pre=PRE_REG + '''    fold = np.arange(n) % 5
    pred = np.empty(n)
''',
    faulty='''    sel = top_corr(X, y, 20)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te][:, sel], y[~te], 10.0), X[te][:, sel])
''',
    fixed='''    for k in range(5):
        te = fold == k
        sel = top_corr(X[~te], y[~te], 20)
        pred[te] = ridge_predict(ridge_fit(X[~te][:, sel], y[~te], 10.0), X[te][:, sel])
''',
    post=POST_R2,
)

# ---------------------------------------------------------------- B2A-R4 (D-066)
case(
    id="D-066",
    helpers=["nn_predict", "strat_folds", "balanced_accuracy"],
    doc='''Claim: a one-nearest-neighbour classifier (Euclidean distance on standardised measurements) recovers the
    rare outcome y from X for new patients with a balanced accuracy (mean of sensitivity and specificity)
    of at least 0.65.  The rare class (y True) is balanced by copying its rows (sampling with replacement)
    until the two classes have equal size.

    Data keys:
      "X": float array (samples, features) = (1000, 15); the 15 continuous clinical measurements of each patient.
      "y": bool array (samples,) = (1000,); True where the patient has the rare outcome.

    Returns True when the balanced accuracy >= 0.65, False otherwise, None at an allowed guard (non-finite X,
    fewer than 2 patients in either class).''',
    pre='''    X = np.asarray(d["X"], dtype=float)
    y = np.asarray(d["y"], dtype=bool)
    n = y.shape[0]
    if int(y.sum()) < 2 or int((~y).sum()) < 2:
        return None
    if not np.all(np.isfinite(X)):
        return None
    rng = np.random.default_rng(0)
''',
    faulty='''    pos = np.flatnonzero(y)
    extra = rng.choice(pos, size=max(n - 2 * pos.shape[0], 0), replace=True)
    Xa = np.concatenate([X, X[extra]])
    ya = np.concatenate([y, y[extra]])
    fold = np.arange(ya.shape[0]) % 5
    pred = np.empty(ya.shape[0], dtype=bool)
    for k in range(5):
        te = fold == k
        pred[te] = nn_predict(Xa[~te], ya[~te], Xa[te])
    bal = balanced_accuracy(ya, pred)
''',
    fixed='''    fold = strat_folds(y)
    pred = np.empty(n, dtype=bool)
    for k in range(5):
        te = fold == k
        Xtr = X[~te]
        ytr = y[~te]
        pos = np.flatnonzero(ytr)
        extra = rng.choice(pos, size=max(ytr.shape[0] - 2 * pos.shape[0], 0), replace=True)
        pred[te] = nn_predict(np.concatenate([Xtr, Xtr[extra]]), np.concatenate([ytr, ytr[extra]]), X[te])
    bal = balanced_accuracy(y, pred)
''',
    post='''    if not np.isfinite(bal):
        return None
    return bool(bal >= 0.65)
''',
)

# ---------------------------------------------------------------- B2A-R5 (D-039)
case(
    id="D-039",
    helpers=["ridge_fit", "ridge_predict", "slope"],
    doc='''Claim: on future months, the slope of the ordinary least squares regression of observed y on the
    forecasts of a ridge regression of y on the 3 predictors X (penalty 1.0, standardised predictors,
    intercept) is at least 0.5.

    Data keys:
      "X": float array (months_in_order, features) = (400, 3); the 3 continuous monthly predictor series, rows
           in time order.
      "y": float array (months_in_order,) = (400,); the continuous monthly outcome, in time order.

    Returns True when the slope >= 0.5, False otherwise, None at an allowed guard (non-finite values, fewer
    than 2 forecast months, zero variance of the forecasts).''',
    pre=PRE_REG + '''    pred = np.empty(n)
''',
    faulty='''    rng = np.random.default_rng(0)
    fold = np.empty(n, dtype=int)
    fold[rng.permutation(n)] = np.arange(n) % 5
    ev = np.ones(n, dtype=bool)
    for k in range(5):
        te = fold == k
        pred[te] = ridge_predict(ridge_fit(X[~te], y[~te], 1.0), X[te])
''',
    fixed='''    ev = np.zeros(n, dtype=bool)
    first = n // 2
    size = n // 10
    for s in range(first, n, size):
        blk = np.arange(s, min(s + size, n))
        tr = np.arange(n) < (s if s == first else s - 3)
        pred[blk] = ridge_predict(ridge_fit(X[tr], y[tr], 1.0), X[blk])
        ev[blk] = True
''',
    post='''    b = slope(pred[ev], y[ev])
    if b is None:
        return None
    return bool(b >= 0.5)
''',
)


def assemble(spec, which):
    parts = ["import numpy as np\n\n\n"]
    parts.append("\n\n".join(H[h] for h in spec["helpers"]))
    parts.append("\n\ndef criterion(d):\n")
    parts.append('    """' + spec["doc"] + '\n    """\n')
    parts.append(spec["pre"])
    parts.append(spec[which])
    parts.append(spec["post"])
    return "".join(parts)


def main():
    for spec in CASES:
        folder = os.path.join(ROOT, spec["id"])
        for which in ("faulty", "fixed"):
            with open(os.path.join(folder, which + "_body.py"), "w", encoding="utf-8", newline="\n") as f:
                f.write(assemble(spec, which))
        print("wrote", spec["id"])


if __name__ == "__main__":
    main()
