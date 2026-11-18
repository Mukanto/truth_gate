import numpy as np


def criterion(d):
    """Claim: Among 40 anaesthetised dogs, whole-body oxygen consumption and oxygen delivery, each computed from the measured cardiac output and the arterial and mixed-venous blood oxygen contents by the standard Fick definitions, are positively related: their Pearson correlation is at least 0.40.

    d: dict of numpy arrays, with the keys
      cardiac_output  (subjects,)  float: cardiac output of each dog, in L per min
      cardiac_output_2  (subjects,)  float: a second, independent determination of the cardiac output of each dog, in L per min
      arterial_o2_content  (subjects,)  float: arterial blood oxygen content of each dog, in mL O2 per dL
      venous_o2_content  (subjects,)  float: mixed-venous blood oxygen content of each dog, in mL O2 per dL

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    co = np.asarray(d['cardiac_output'], dtype=float)
    co2 = np.asarray(d['cardiac_output_2'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    n = co.shape[0]
    if n < 2:
        return None
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(co2)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))):
        return None
    k = 10.0
    dd = ca - cv
    vo2 = k * co * dd
    do2 = k * co * ca
    c = np.cov(vo2, do2)
    v = c[0, 0]
    w = c[1, 1]
    cc = c[0, 1]
    s2 = float(np.var(co - co2, ddof=1)) / 2.0
    v = v - k * k * s2 * np.mean(dd * dd)
    w = w - k * k * s2 * np.mean(ca * ca)
    cc = cc - k * k * s2 * np.mean(dd * ca)
    if not (v > 0.0 and w > 0.0):
        return None
    r = cc / np.sqrt(v * w)
    return bool(r >= 0.40)
