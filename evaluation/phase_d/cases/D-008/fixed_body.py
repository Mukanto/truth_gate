import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def criterion(d):
    """Claim: within patients, oxygen consumption rises with oxygen delivery; the mean over patients of the
    within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min.

    d['cardiac_output']      : (patients, occasions) float, cardiac output of each patient at each
                               measurement occasion, in L/min
    d['arterial_o2_content'] : (patients, occasions) float, oxygen content of arterial blood of each
                               patient at each occasion, in mL O2 per dL
    d['venous_o2_content']   : (patients, occasions) float, oxygen content of mixed venous blood of each
                               patient at each occasion, in mL O2 per dL
    d['vo2_expired_gas']     : (patients, occasions) float, oxygen consumption of each patient at each
                               occasion measured from expired-gas analysis, in mL/min

    Oxygen delivery is cardiac_output * arterial_o2_content * 10 (mL/min). Patients whose delivery has no
    variance across occasions are not counted.
    Returns True / False; None when a value is not finite, fewer than 2 occasions, or no patient can be
    counted.
    """
    co = np.asarray(d['cardiac_output'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    vo = np.asarray(d['vo2_expired_gas'], dtype=float)
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))
            and np.all(np.isfinite(vo))):
        return None
    n, m = co.shape
    if n < 1 or m < 2:
        return None
    do2 = co * ca * 10.0
    vo2 = vo
    ok = np.max(do2, axis=1) > np.min(do2, axis=1)
    if not np.any(ok):
        return None
    xc = do2 - np.mean(do2, axis=1, keepdims=True)
    yc = vo2 - np.mean(vo2, axis=1, keepdims=True)
    slopes = np.sum(xc * yc, axis=1)[ok] / np.sum(xc * xc, axis=1)[ok]
    stat = float(np.mean(slopes))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.1)
