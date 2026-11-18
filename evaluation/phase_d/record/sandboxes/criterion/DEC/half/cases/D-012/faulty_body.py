import numpy as np


def criterion(d):
    """Claim: mean occupancy is higher in fenced plots than in open plots by at
    least 0.10, where the occupancy of a plot is the fraction of its quadrats
    that are occupied, and a one-sided test of the difference between the mean
    occupancy of fenced plots and that of open plots is significant at the
    0.05 level.

    d['occupied']: bool array (plots, quadrats) = (10, 30); True if the species
        was present in that quadrat of that plot.
    d['exclosure']: bool array (plots,) = (10,); True if the plot was fenced
        against grazers.

    Returns True when the difference is >= 0.10 and the test is significant at
    the 0.05 level, False otherwise; None when a group has too few units for
    the test or the variance needed for the test is zero.
    """
    y = np.asarray(d['occupied'], dtype=float)
    g = np.asarray(d['exclosure'], dtype=bool)
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
    return bool(diff >= 0.10 and diff / np.sqrt(se2) > 1.6448536269514722)
