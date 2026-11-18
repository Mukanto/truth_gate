import numpy as np


def _corr_cols(x, y):
    xc = x - x.mean(axis=0)
    yc = y - y.mean()
    sxx = (xc ** 2).sum(axis=0)
    syy = float((yc ** 2).sum())
    with np.errstate(divide='ignore', invalid='ignore'):
        return (yc @ xc) / np.sqrt(sxx * syy)


def criterion(d):
    """Claim: in the population, the 20 voxels whose activation is most strongly
    correlated with the questionnaire score have a mean correlation with that
    score of at least 0.5.

    d['activation']: float array (subjects, voxels) = (20, 1000); task-related
        activation of each voxel in each subject.
    d['trait']: float array (subjects,) = (20,); personality questionnaire
        score of each subject.

    Returns True when the mean correlation is >= 0.5, False otherwise; None
    when a value is non-finite, a correlation has zero variance, or no voxel
    is selected.
    """
    x = np.asarray(d['activation'], dtype=float)
    y = np.asarray(d['trait'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    if x.shape[0] < 2:
        return None
    r = _corr_cols(x, y)
    if not np.all(np.isfinite(r)):
        return None
    top = np.argsort(-r, kind='stable')[:20]
    if top.size < 1:
        return None
    return bool(r[top].mean() >= 0.5)
