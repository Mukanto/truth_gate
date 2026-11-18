import numpy as np


def criterion(d):
    """Claim: mean occupancy is higher in fenced plots than in open plots by at
    least 0.15, where the occupancy of a plot is the fraction of dates on which
    it is occupied, and a one-sided test of the difference between the mean
    occupancy of fenced plots and that of open plots is significant at the
    0.05 level.

    d['present']: bool array (plots, dates) = (8, 12); True if the species was
        present in that plot on that date; dates are in time order.
    d['fenced']: bool array (plots,) = (8,); True if the plot was fenced
        against grazers.

    Returns True when the difference is >= 0.15 and the test is significant at
    the 0.05 level, False otherwise; None when a group has too few units for
    the test or the variance needed for the test is zero.
    """
    y = np.asarray(d['present'], dtype=float)
    g = np.asarray(d['fenced'], dtype=bool)
    a = y[g]
    b = y[~g]
    n1 = a.size
    n0 = b.size
    if n1 < 1 or n0 < 1:
        return None
    k1 = a.sum()
    k0 = b.sum()
    p = (k1 + k0) / (n1 + n0)
    se2 = p * (1.0 - p) * (1.0 / n1 + 1.0 / n0)
    if se2 <= 0.0:
        return None
    diff = k1 / n1 - k0 / n0
    return bool(diff >= 0.15 and diff / np.sqrt(se2) > 1.6448536269514722)
