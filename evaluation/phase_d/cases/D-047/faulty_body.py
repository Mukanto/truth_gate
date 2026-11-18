import numpy as np


def criterion(d):
    """Claim: among patients whose screening score was at least 60, at least half
    have a week-12 score that is 10 or more points below their entry score
    (proportion of at least 0.5).

    d['screening']: float array (patients,) = (600,); symptom severity score
        (0 to 100, higher is worse) at the screening visit.
    d['entry']: float array (patients,) = (600,); symptom severity score at
        entry, on the day treatment began.
    d['week12']: float array (patients,) = (600,); symptom severity score 12
        weeks after treatment began.

    Returns True when the proportion is >= 0.5, False otherwise; None when a
    value is non-finite or no patient has a screening score of at least 60.
    """
    s = np.asarray(d['screening'], dtype=float)
    e = np.asarray(d['entry'], dtype=float)
    w = np.asarray(d['week12'], dtype=float)
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(e))
            and np.all(np.isfinite(w))):
        return None
    flag = s >= 60.0
    if not np.any(flag):
        return None
    change = s[flag] - w[flag]
    return bool(np.mean(change >= 10.0) >= 0.5)
