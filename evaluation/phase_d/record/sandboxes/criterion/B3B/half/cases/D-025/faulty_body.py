import numpy as np


def criterion(d):
    """Claim: Across 12 trials of guided tissue regeneration with 20 defects each, deeper disease means larger gain: the mean over trials of the within-trial regression slope of the change in attachment loss (follow-up minus baseline) on the mean of the baseline and follow-up attachment loss is at most -0.20 (mm per mm).

    d: dict of numpy arrays, with the keys
      baseline_attachment_loss  (trials, defects)  float: clinical attachment loss of each defect in each trial at the baseline examination, in mm
      baseline_attachment_loss_retest  (trials, defects)  float: a second, independent measurement of the attachment loss of each defect at the baseline examination, in mm
      followup_attachment_loss  (trials, defects)  float: clinical attachment loss of each defect at the follow-up examination after treatment, in mm

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    b = np.asarray(d['baseline_attachment_loss'], dtype=float)
    rt = np.asarray(d['baseline_attachment_loss_retest'], dtype=float)
    f = np.asarray(d['followup_attachment_loss'], dtype=float)
    nt = b.shape[0]
    nd = b.shape[1]
    if nt < 1 or nd < 2:
        return None
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(rt)) and np.all(np.isfinite(f))):
        return None
    chg = f - b
    x = b
    if np.any(np.ptp(x, axis=1) == 0):
        return None
    xc = x - np.mean(x, axis=1, keepdims=True)
    yc = chg - np.mean(chg, axis=1, keepdims=True)
    slope = np.sum(xc * yc, axis=1) / np.sum(xc * xc, axis=1)
    return bool(np.mean(slope) <= -0.20)
