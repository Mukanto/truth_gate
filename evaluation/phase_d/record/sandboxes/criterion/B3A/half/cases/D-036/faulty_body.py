import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _resid(y, X):
    """Residuals of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    A = np.column_stack([np.ones(len(y)), X])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    return y - A @ coef


def _r2(y, X):
    """R-squared of the least-squares regression of y (n,) on an intercept and the columns of X (n, k)."""
    res = _resid(y, X)
    sst = np.sum((y - np.mean(y)) ** 2)
    return float(1.0 - np.sum(res * res) / sst)


def criterion(d):
    """Claim: across patients, cardiac output explains at least 25% of the variance in systemic vascular
    resistance (R-squared of at least 0.25).

    d['mean_arterial_pressure']   : (patients,) float, mean arterial pressure of each patient, in mmHg
    d['central_venous_pressure']  : (patients,) float, central venous pressure of each patient, in mmHg
    d['co_thermodilution']        : (patients,) float, cardiac output of each patient measured by
                                    thermodilution, in L/min
    d['co_fick']                  : (patients,) float, cardiac output of each patient measured by the Fick
                                    method from expired-gas oxygen uptake, in L/min

    Systemic vascular resistance is 80 * (mean_arterial_pressure - central_venous_pressure) /
    co_thermodilution (dyn s / cm5).
    Returns True / False; None when a value is not finite, fewer than 2 patients, or a variance is zero.
    """
    mapp = np.asarray(d['mean_arterial_pressure'], dtype=float)
    cvp = np.asarray(d['central_venous_pressure'], dtype=float)
    cot = np.asarray(d['co_thermodilution'], dtype=float)
    cof = np.asarray(d['co_fick'], dtype=float)
    if not (np.all(np.isfinite(mapp)) and np.all(np.isfinite(cvp)) and np.all(np.isfinite(cot))
            and np.all(np.isfinite(cof))):
        return None
    if mapp.size < 2:
        return None
    with np.errstate(divide='ignore', invalid='ignore'):
        svr = 80.0 * (mapp - cvp) / cot
    if not np.all(np.isfinite(svr)):
        return None
    x = cot
    if _flat(svr) or _flat(x):
        return None
    stat = _r2(svr, x.reshape(-1, 1))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.25)
