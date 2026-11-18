import numpy as np


def criterion(d):
    """Claim: Across 120 anaesthetised animals, tissues extract more oxygen when more is supplied: the Pearson correlation between the arterial-minus-mixed-venous oxygen content difference and the arterial oxygen content is at least 0.30.

    d: dict of numpy arrays, with the keys
      arterial_o2_content  (subjects,)  float: arterial blood oxygen content of each animal, in mL O2 per dL
      arterial_o2_content_2  (subjects,)  float: a second, independent determination of the arterial blood oxygen content of each animal, in mL O2 per dL
      venous_o2_content  (subjects,)  float: mixed-venous blood oxygen content of each animal, in mL O2 per dL
      venous_o2_content_2  (subjects,)  float: a second, independent determination of the mixed-venous blood oxygen content of each animal, in mL O2 per dL

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    ca2 = np.asarray(d['arterial_o2_content_2'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    cv2 = np.asarray(d['venous_o2_content_2'], dtype=float)
    n = ca.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(ca)) and np.all(np.isfinite(ca2)) and np.all(np.isfinite(cv)) and np.all(np.isfinite(cv2))):
        return None
    dif = ca - cv
    c = np.cov(dif, ca)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
    if not (v > 0.0 and w > 0.0):
        return None
    r = cc / np.sqrt(v * w)
    return bool(r >= 0.30)
