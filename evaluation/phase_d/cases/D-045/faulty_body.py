import numpy as np


def corr(x, y):
    xc = x - np.mean(x)
    yc = y - np.mean(y)
    return float(np.sum(xc * yc) / np.sqrt(np.sum(xc * xc) * np.sum(yc * yc)))


def criterion(d):
    """Claim: In 300 patients with a continuous disease severity score measured before and after treatment, improvement is larger in patients with a higher severity level: the Pearson correlation between each patient's change in score (follow-up minus baseline) and the mean of that patient's baseline and follow-up scores is at most -0.30.

    d: dict of numpy arrays, with the keys
      baseline_score  (patients,)  float: severity score of each patient at the baseline visit, higher is more severe
      baseline_score_retest  (patients,)  float: a second, independent reading of the severity score of each patient taken at the baseline visit
      followup_score  (patients,)  float: severity score of each patient at the follow-up visit after treatment

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    b = np.asarray(d['baseline_score'], dtype=float)
    rt = np.asarray(d['baseline_score_retest'], dtype=float)
    f = np.asarray(d['followup_score'], dtype=float)
    n = b.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(rt)) and np.all(np.isfinite(f))):
        return None
    chg = f - b
    x = b
    if np.ptp(chg) == 0 or np.ptp(x) == 0:
        return None
    return bool(corr(chg, x) <= -0.30)
