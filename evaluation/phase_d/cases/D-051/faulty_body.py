import numpy as np


def criterion(d):
    """Claim: In 12 anaesthetised dogs, each studied at 8 steps, whole-body oxygen consumption rises with oxygen delivery within a dog, both computed from the measured cardiac output and the arterial and mixed-venous blood oxygen contents by the standard Fick definitions: the mean over dogs of the within-dog regression slope of oxygen consumption on oxygen delivery is at least 0.15 (mL O2 per min per mL O2 per min).

    d: dict of numpy arrays, with the keys
      cardiac_output  (animals, steps)  float: cardiac output of each dog at each step, in L per min
      cardiac_output_2  (animals, steps)  float: a second, independent determination of the cardiac output of each dog at each step, in L per min
      arterial_o2_content  (animals, steps)  float: arterial blood oxygen content of each dog at each step, in mL O2 per dL
      venous_o2_content  (animals, steps)  float: mixed-venous blood oxygen content of each dog at each step, in mL O2 per dL

    Returns True when the claim is supported, False when it is not, None when the statistic is not
    defined (non-finite values, too small a sample, zero variance).
    """
    co = np.asarray(d['cardiac_output'], dtype=float)
    co2 = np.asarray(d['cardiac_output_2'], dtype=float)
    ca = np.asarray(d['arterial_o2_content'], dtype=float)
    cv = np.asarray(d['venous_o2_content'], dtype=float)
    na = co.shape[0]
    ns = co.shape[1]
    if na < 1 or ns < 2:
        return None
    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(co2)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv))):
        return None
    k = 10.0
    dd = ca - cv
    vo2 = k * co * dd
    do2 = k * co * ca
    vc = vo2 - np.mean(vo2, axis=1, keepdims=True)
    dc = do2 - np.mean(do2, axis=1, keepdims=True)
    num = np.sum(vc * dc, axis=1) / (ns - 1)
    den = np.sum(dc * dc, axis=1) / (ns - 1)
    if not np.all(den > 0.0):
        return None
    return bool(np.mean(num / den) >= 0.15)
