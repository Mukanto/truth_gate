import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def _change_stats(u1, u2, k):
    """Regression of the change u2 - u1 on the baseline u1, adjusted for the error-variance share k.

    Returns (b, r): the slope (b_crude + k) / (1 - k) and the correlation implied by it, with the SDs of the
    baseline and of the change reduced to their true parts (baseline variance times (1 - k); change variance
    minus 2 * k * baseline variance, equal error variance at both visits). With k = 0 these are the crude
    slope and the crude correlation. None when the baseline or the change has zero variance; b or r may be
    non-finite (k = 1, or a true-part variance that is not positive) and the caller checks the one it uses.
    """
    ch = u2 - u1
    v1 = np.var(u1, ddof=1)
    vc = np.var(ch, ddof=1)
    if _flat(u1) or _flat(ch):
        return None
    b_crude = np.sum((u1 - np.mean(u1)) * (ch - np.mean(ch))) / ((len(u1) - 1) * v1)
    with np.errstate(divide='ignore', invalid='ignore'):
        b = (b_crude + k) / (1.0 - k)
        sd_x = np.sqrt(v1 * (1.0 - k))
        var_c = vc - 2.0 * k * v1
        sd_c = np.sqrt(var_c) if var_c > 0.0 else np.nan
        r = b * sd_x / sd_c
    return float(b), float(r)


def criterion(d):
    """Claim: the expected change in BMI between baseline and follow-up is smaller for children with a higher
    baseline BMI; each additional 1 kg/m2 of baseline BMI goes with a change in BMI that is at least
    0.2 kg/m2 smaller (slope of at most -0.2).

    d['bmi_baseline'] : (children,) float, BMI of each child at the baseline visit, in kg/m2
    d['bmi_followup'] : (children,) float, BMI of each child at the follow-up visit five years after
                        baseline, in kg/m2
    d['bmi_retest']   : (retest_children, retest_sessions) float, BMI of each child of a test-retest sample
                        at two sessions a few days apart, in kg/m2

    Returns True / False; None when a value is not finite, fewer than 2 children in the main sample or in
    the retest sample, fewer than 2 sessions, a zero variance, or a non-finite result.
    """
    u1 = np.asarray(d['bmi_baseline'], dtype=float)
    u2 = np.asarray(d['bmi_followup'], dtype=float)
    rt = np.asarray(d['bmi_retest'], dtype=float)
    if not (np.all(np.isfinite(u1)) and np.all(np.isfinite(u2)) and np.all(np.isfinite(rt))):
        return None
    if u1.size < 2 or rt.shape[0] < 2 or rt.shape[1] < 2:
        return None
    if _flat(u1):
        return None
    k = 0.0
    res = _change_stats(u1, u2, k)
    if res is None or not np.isfinite(res[0]):
        return None
    return bool(res[0] <= -0.2)
