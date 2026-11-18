import numpy as np


def criterion(d):
    """Claim: the reduction attributable to the drug (mean reduction in treated
    patients minus mean reduction in untreated patients) is larger in patients
    in the top third of baseline pressures than in patients in the bottom third
    of baseline pressures, by at least 3 mmHg. The reduction of a patient is the
    baseline pressure minus the 6-month pressure.

    d['baseline_sbp']: float array (patients,) = (900,); systolic blood
        pressure in mmHg at baseline.
    d['followup_sbp']: float array (patients,) = (900,); systolic blood
        pressure in mmHg after 6 months.
    d['treated']: bool array (patients,) = (900,); True if the patient
        received the drug.

    Returns True when the difference is >= 3 mmHg, False otherwise; None when
    a value is non-finite or a group needed for the difference is empty.
    """
    b = np.asarray(d['baseline_sbp'], dtype=float)
    f = np.asarray(d['followup_sbp'], dtype=float)
    tr = np.asarray(d['treated'], dtype=bool)
    if not (np.all(np.isfinite(b)) and np.all(np.isfinite(f))):
        return None
    red = b - f
    if b.size < 1:
        return None
    q1, q2 = np.percentile(b, [100.0 / 3.0, 200.0 / 3.0])
    lo = b <= q1
    hi = b >= q2
    cells = (hi & tr, hi & ~tr, lo & tr, lo & ~tr)
    if not all(np.any(c) for c in cells):
        return None
    eff_hi = red[cells[0]].mean() - red[cells[1]].mean()
    eff_lo = red[cells[2]].mean() - red[cells[3]].mean()
    return bool(eff_hi - eff_lo >= 3.0)
