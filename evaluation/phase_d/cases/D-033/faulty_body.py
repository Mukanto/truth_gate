import numpy as np


def _corr_cols(x, y):
    xc = x - x.mean(axis=0)
    yc = y - y.mean()
    sxx = (xc ** 2).sum(axis=0)
    syy = float((yc ** 2).sum())
    with np.errstate(divide='ignore', invalid='ignore'):
        return (yc @ xc) / np.sqrt(sxx * syy)


def criterion(d):
    """Claim: in the population, the 25 voxels whose trial-by-trial response is
    most strongly correlated with stimulus intensity have a mean correlation
    with intensity of at least 0.25.

    d['betas']: float array (voxels, trials) = (1000, 60); estimated response
        amplitude of each voxel on each trial.
    d['intensity']: float array (trials,) = (60,); stimulus intensity
        presented on each trial.

    Returns True when the mean correlation is >= 0.25, False otherwise; None
    when a value is non-finite, a correlation has zero variance, or no voxel
    is selected.
    """
    x = np.asarray(d['betas'], dtype=float).T
    y = np.asarray(d['intensity'], dtype=float)
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(y))):
        return None
    if x.shape[0] < 2:
        return None
    r = _corr_cols(x, y)
    if not np.all(np.isfinite(r)):
        return None
    top = np.argsort(-r, kind='stable')[:25]
    if top.size < 1:
        return None
    return bool(r[top].mean() >= 0.25)
