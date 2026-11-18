import numpy as np


def _cell(r, g, c, cv, gv):
    m = (c == cv) & (g == gv)
    return int(r[m].sum()), int(m.sum())


def criterion(d):
    """Claim: the drug raises the proportion of responders more in carriers than
    in non-carriers, that is, the difference between the two drug-minus-vehicle
    differences in responder proportion (carriers minus non-carriers) is
    positive, judged by a one-sided test at the 0.05 level.

    d['responder']: bool array (participants,) = (240,); True if the
        participant met the response criterion.
    d['drug']: bool array (participants,) = (240,); True if the participant
        received the drug, False if the vehicle.
    d['carrier']: bool array (participants,) = (240,); True if the participant
        carries the gene variant.

    Returns True when the claim is supported at the 0.05 level, False
    otherwise; None when a (carrier, drug) cell is empty or the variance
    needed for the test is zero.
    """
    r = np.asarray(d['responder'], dtype=bool)
    g = np.asarray(d['drug'], dtype=bool)
    c = np.asarray(d['carrier'], dtype=bool)
    k11, n11 = _cell(r, g, c, True, True)
    k10, n10 = _cell(r, g, c, True, False)
    k01, n01 = _cell(r, g, c, False, True)
    k00, n00 = _cell(r, g, c, False, False)
    if min(n11, n10, n01, n00) < 1:
        return None
    p11 = k11 / n11
    p10 = k10 / n10
    p01 = k01 / n01
    p00 = k00 / n00
    var = (p11 * (1.0 - p11) / n11 + p10 * (1.0 - p10) / n10
           + p01 * (1.0 - p01) / n01 + p00 * (1.0 - p00) / n00)
    if var <= 0.0:
        return None
    z = ((p11 - p10) - (p01 - p00)) / np.sqrt(var)
    return bool(z > 1.6448536269514722)
