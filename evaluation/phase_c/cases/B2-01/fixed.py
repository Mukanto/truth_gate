"""C44: A statistical classifier built from the 30 annual indicators of a country distinguishes the country-years in which a civil war begins from the country-years in which none begins, with an area under the ROC curve of at least 0.75 on new country-years."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_COUNTRIES = 56
N_YEARS = 16           # 56 countries x 16 consecutive years = 896 country-years, rows in country blocks
N_IND = 30
COUNTRY_SD = 0.8       # stable country-specific level of each indicator
YEAR_SD = 0.6          # within-country year-to-year variation, autocorrelated
YEAR_RHO = 0.7
N_INFORMATIVE = 6
BASE_LOG_ODDS = -4.0   # onsets in about 5% of country-years
SLOPE = 1.7            # log-odds of an onset per SD of the risk score
CENTRE = np.linspace(-2.0, 40.0, N_IND)
SPREAD = np.linspace(0.5, 15.0, N_IND)


def _panel(rng):
    level = rng.normal(0.0, COUNTRY_SD, (N_COUNTRIES, 1, N_IND))
    white = rng.normal(0.0, YEAR_SD, (N_COUNTRIES, N_YEARS, N_IND))
    within = np.empty((N_COUNTRIES, N_YEARS, N_IND))
    within[:, 0] = white[:, 0]
    for k in range(1, N_YEARS):
        within[:, k] = YEAR_RHO * within[:, k - 1] + np.sqrt(1.0 - YEAR_RHO ** 2) * white[:, k]
    return level + within


def _world(rng, linked):
    observed = _panel(rng)
    unrelated = _panel(rng)
    informative = rng.choice(N_IND, N_INFORMATIVE, replace=False)
    weights = np.zeros(N_IND)
    weights[informative] = rng.choice(np.array([-1.0, 1.0]), N_INFORMATIVE) * rng.uniform(0.6, 1.0, N_INFORMATIVE)
    risk = (observed if linked else unrelated) @ weights
    risk = (risk - risk.mean()) / risk.std()
    p_onset = 1.0 / (1.0 + np.exp(-(BASE_LOG_ODDS + SLOPE * risk)))
    onset = rng.random((N_COUNTRIES, N_YEARS)) < p_onset
    indicators = CENTRE + SPREAD * observed
    return {
        "indicators": indicators.reshape(N_COUNTRIES * N_YEARS, N_IND).astype(np.float64),
        "onset": onset.reshape(N_COUNTRIES * N_YEARS),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def _permute_onset(d, rng):
    return {**d, "onset": rng.permutation(d["onset"])}


def _permute_countries(d, rng):
    # each country's 16-year onset history, kept together, is given to another country's indicators
    blocks = d["onset"].reshape(N_COUNTRIES, N_YEARS)
    return {**d, "onset": blocks[rng.permutation(N_COUNTRIES)].reshape(N_COUNTRIES * N_YEARS)}


def criterion(d):
    """Data keys: indicators, float (896, 30) = (country_years, indicators), 30 annual political, economic and
    demographic indicators of the country in that year; onset, bool (896,), True when a civil war begins in that
    country-year. Row layout in these worlds: 56 countries x 16 consecutive years, rows in country blocks (rows
    0-15 are the first country in year order, rows 16-31 the second, and so on).
    Holds when the claim is supported by the data. Written by someone else."""
    X = np.asarray(d["indicators"], dtype=float)
    y = np.asarray(d["onset"], dtype=bool)
    if not np.all(np.isfinite(X)):
        return None
    n_pos = int(y.sum())
    n_neg = y.size - n_pos
    rng = np.random.default_rng(20260201)
    THRESHOLD = 0.75
    LAM = 1.0
    if min((n_pos - (-(-(n_pos) // 5))), (n_neg - (-(-(n_neg) // 5)))) < 2:
        return None
    def strat_folds(yy, k):
        f = np.empty(yy.size, dtype=int)
        off = 0
        for c in (False, True):
            idx = np.flatnonzero(yy == c)
            idx = idx[rng.permutation(idx.size)]
            f[idx] = (np.arange(idx.size) + off) % k
            off += idx.size
        return f

    def auc(s, yy):
        o = np.argsort(s, kind="mergesort")
        ss = s[o]
        first = np.r_[True, ss[1:] != ss[:-1]]
        grp = np.cumsum(first) - 1
        starts = np.flatnonzero(first)
        ends = np.r_[starts[1:], ss.size]
        avg = (starts + ends + 1) / 2.0
        r = np.empty(ss.size)
        r[o] = avg[grp]
        n1 = int(yy.sum())
        n0 = yy.size - n1
        return (r[yy].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)

    def fit_predict(Xtr, ytr, Xte):
        mu = Xtr.mean(0)
        sd = Xtr.std(0)
        sd = np.where(sd > 0, sd, 1.0)
        A = np.c_[np.ones(len(Xtr)), (Xtr - mu) / sd]
        B = np.c_[np.ones(len(Xte)), (Xte - mu) / sd]
        t = ytr.astype(float)
        pen = np.ones(A.shape[1])
        pen[0] = 0.0
        w = np.zeros(A.shape[1])
        for _ in range(30):
            p = 1.0 / (1.0 + np.exp(-np.clip(A @ w, -30.0, 30.0)))
            g = A.T @ (p - t) + LAM * pen * w
            H = (A * (p * (1.0 - p))[:, None]).T @ A + LAM * np.diag(pen)
            step = np.linalg.solve(H, g)
            w = w - step
            if np.max(np.abs(step)) < 1e-8:
                break
        return B @ w

    fold = strat_folds(y, 5)
    score = np.empty(y.size)
    for j in range(5):
        te = fold == j
        score[te] = fit_predict(X[~te], y[~te], X[te])
    return bool(auc(score, y) >= THRESHOLD)


STUDY = Study(
    name="C44",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the indicators carry no information about onset: onset risk is driven by an unrelated indicator panel with the same country/year structure (same onset rate, same clustering of onsets within countries)"),
    },
    controls=[
        Control("permute_onset_across_country_years", ["C"], transform=_permute_onset),
        Control("permute_onset_histories_across_countries", ["C"], transform=_permute_countries),
    ],
)
