import numpy as np

def _flat(a):
    """True when all entries of the array are equal (zero variance)."""
    return bool(np.max(a) == np.min(a))


def criterion(d):
    """Claim: at a given height, the mean forced vital capacity of smokers and of non-smokers differs by at
    least 0.2 L; the difference between the two group means, after accounting for height, is at least
    0.2 L in absolute value.

    d['fvc']    : (subjects,) float, forced vital capacity of each subject, in litres
    d['height'] : (subjects,) float, standing height of each subject, in cm
    d['smoker'] : (subjects,) bool, True if the subject is a current smoker

    Returns True / False; None when a value is not finite, fewer than 3 subjects, a group is empty, or
    height has zero variance.
    """
    fvc = np.asarray(d['fvc'], dtype=float)
    height = np.asarray(d['height'], dtype=float)
    smoker = np.asarray(d['smoker'], dtype=bool)
    if not (np.all(np.isfinite(fvc)) and np.all(np.isfinite(height))):
        return None
    n = fvc.size
    ns = int(np.sum(smoker))
    if n < 3 or ns < 1 or ns == n:
        return None
    if _flat(height):
        return None
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = fvc / height
    if not np.all(np.isfinite(ratio)):
        return None
    stat = abs((np.mean(ratio[smoker]) - np.mean(ratio[~smoker])) * np.mean(height))
    if not np.isfinite(stat):
        return None
    return bool(stat >= 0.2)
