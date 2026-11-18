import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _std_coef(y, X, j):
    """Standardised coefficient of column j of X (n, k) in the regression of y (n,) on an intercept and X."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(coef[1 + j] * np.std(X[:, j], ddof=1) / np.std(y, ddof=1))


def criterion(d):
    """Claim: across countries, annual lung-cancer deaths and annual cigarette sales are associated after
    accounting for population; the standardised slope of deaths on cigarette sales, with population
    accounted for, is at least 0.2 in absolute value.

    d['lung_cancer_deaths'] : (countries,) float, total lung-cancer deaths in each country in one year,
                              in thousands
    d['cigarettes_sold']    : (countries,) float, total cigarettes sold in each country in the same year,
                              in millions
    d['population']         : (countries,) float, population of each country, in millions

    Returns True / False; None when a value is not finite, fewer than 3 countries, or a variance is zero.
    """
    y = np.asarray(d['lung_cancer_deaths'], dtype=float)
    sales = np.asarray(d['cigarettes_sold'], dtype=float)
    pop = np.asarray(d['population'], dtype=float)
    if not (np.all(np.isfinite(y)) and np.all(np.isfinite(sales)) and np.all(np.isfinite(pop))):
        return None
    if y.size < 3:
        return None
    x = sales
    if not np.all(np.isfinite(x)):
        return None
    if _flat(y) or _flat(x) or _flat(pop):
        return None
    b = _std_coef(y, np.column_stack([x, pop]), 0)
    if not np.isfinite(b):
        return None
    return bool(abs(b) >= 0.2)
