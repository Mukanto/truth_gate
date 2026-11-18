import numpy as np


def corr(x, y):
    xc = x - np.mean(x)
    yc = y - np.mean(y)
    return float(np.sum(xc * yc) / np.sqrt(np.sum(xc * xc) * np.sum(yc * yc)))


def criterion(d):
    """Claim: In 24 intrabony periodontal defects treated by guided tissue regeneration, the level of disease explains the amount of change: the mean of the baseline and follow-up pocket probing depth explains at least 15% of the variance in the change in pocket probing depth (follow-up minus baseline), that is, the R-squared of the linear regression of the change on that mean is at least 0.15.

    d: dict of numpy arrays, with the keys
      baseline_depth  (defects,)  float: pocket probing depth of each defect at the baseline examination, in mm
      baseline_depth_retest  (defects,)  float: a second, independent probing of the depth of each defect at the baseline examination, in mm
      followup_depth  (defects,)  float: pocket probing depth of each defect at the follow-up examination after treatment, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    b = np.asarray(d['baseline_depth'], dtype=float)
    rt = np.asarray(d['baseline_depth_retest'], dtype=float)
    f = np.asarray(d['followup_depth'], dtype=float)
    n = b.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(rt)) and np.all(np.isfinite(f))):
        return None
    chg = f - b
    x = b
    if np.ptp(chg) == 0 or np.ptp(x) == 0:
        return None
    r = corr(chg, x)
    return bool(r * r >= 0.15)
