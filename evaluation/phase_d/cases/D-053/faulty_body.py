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
    """Claim: across children, BMI at baseline and the subsequent change in BMI are negatively correlated;
    the correlation between the BMI level at baseline and the change in BMI by follow-up is at most -0.25.

    d['bmi_baseline']        : (children,) float, BMI of each child at the baseline visit, in kg/m2
    d['bmi_baseline_retest'] : (children,) float, a second BMI measurement of each child at the baseline
                               visit, in kg/m2
    d['bmi_followup']        : (children,) float, BMI of each child at the follow-up visit five years
                               after baseline, in kg/m2

    Returns True / False; None when a value is not finite, fewer than 2 children, or a variance is zero.
    """
    u1 = np.asarray(d['bmi_baseline'], dtype=float)
    u1b = np.asarray(d['bmi_baseline_retest'], dtype=float)
    u2 = np.asarray(d['bmi_followup'], dtype=float)
    if not (np.all(np.isfinite(u1)) and np.all(np.isfinite(u1b)) and np.all(np.isfinite(u2))):
        return None
    if u1.size < 2:
        return None
    change = u2 - u1
    x = u1
    r = _corr(x, change)
    if r is None or not np.isfinite(r):
        return None
    return bool(r <= -0.25)
