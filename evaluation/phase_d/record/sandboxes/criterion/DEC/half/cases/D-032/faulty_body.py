import numpy as np


def _cell(r, g, c, cv, gv):
    m = (c == cv) & (g == gv)
    return int(r[m].sum()), int(m.sum())


def _z_pooled(k1, n1, k0, n0):
    p = (k1 + k0) / (n1 + n0)
    se2 = p * (1.0 - p) * (1.0 / n1 + 1.0 / n0)
    if se2 <= 0.0:
        return None
    return (k1 / n1 - k0 / n0) / np.sqrt(se2)


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
    z_carrier = _z_pooled(k11, n11, k10, n10)
    z_non = _z_pooled(k01, n01, k00, n00)
    if z_carrier is None or z_non is None:
        return None
    return bool(z_carrier > 1.6448536269514722 and not z_non > 1.6448536269514722)
