import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _corr(a, b):
    """Pearson correlation of two 1-D arrays; None when either has zero variance."""
    if _flat(a) or _flat(b):
        return None
    a = a - np.mean(a)
    b = b - np.mean(b)
    sa = np.sqrt(np.sum(a * a))
    sb = np.sqrt(np.sum(b * b))
    if sa == 0.0 or sb == 0.0:
        return None
    return float(np.sum(a * b) / (sa * sb))


def criterion(d):
    """Claim: across patients, oxygen delivery and oxygen consumption are positively correlated; the Pearson
    correlation coefficient between them is at least 0.4.

    d['cardiac_output']       : (patients,) float, cardiac output of each patient, in L/min
    d['arterial_o2_content']  : (patients,) float, oxygen content of arterial blood of each patient,
                                in mL O2 per dL
    d['venous_o2_content']    : (patients,) float, oxygen content of mixed venous blood of each patient,
                                in mL O2 per dL
    d['vo2_expired_gas']      : (patients,) float, oxygen consumption of each patient measured from
                                expired-gas analysis, in mL/min

    Oxygen delivery is cardiac_output * arterial_o2_content * 10 (mL/min).
    Returns True / False; None when a value is not finite, fewer than 2 patients, or a variance is zero.
    """
    co = np.asarray(d['cardiac_output'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    vo = np.asarray(d['vo2_expired_gas'], dtype=float)
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))
            and np.all(np.isfinite(vo))):
        return None
    if co.size < 2:
        return None
    do2 = co * ca * 10.0
    vo2 = co * (ca - cv) * 10.0
    r = _corr(do2, vo2)
    if r is None or not np.isfinite(r):
        return None
    return bool(r >= 0.4)
