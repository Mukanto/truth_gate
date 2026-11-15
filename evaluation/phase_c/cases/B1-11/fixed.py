"""C31: Patients show a larger evoked response than controls in the time window in which the two groups' responses differ: the mean amplitude over a window of 10 consecutive samples is at least 0.5 microvolts greater for patients than for controls, and a one-sided Welch t test of that difference is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUBJ = 60
N_TIME = 200
N_PATIENTS = 30
GROUP_GAIN = 2.2     # extra amplitude (microvolts) of the late component in patients, at its peak
NOISE_RHO = 0.9      # sample-to-sample autocorrelation of the residual EEG
NOISE_SD = 1.2       # microvolts, per sample


def _recording(rng, group_gain):
    t = np.arange(N_TIME, dtype=float)[None, :]
    patient = np.zeros(N_SUBJ, dtype=bool)
    patient[rng.choice(N_SUBJ, N_PATIENTS, replace=False)] = True
    # early negative deflection and late positive component, both present in every participant
    lat_early = 40.0 + rng.normal(0.0, 3.0, (N_SUBJ, 1))
    amp_early = -3.0 + rng.normal(0.0, 1.0, (N_SUBJ, 1))
    lat_late = 120.0 + rng.normal(0.0, 6.0, (N_SUBJ, 1))
    amp_late = 5.0 + rng.normal(0.0, 1.3, (N_SUBJ, 1))
    amp_late = amp_late + group_gain * patient[:, None]
    signal = amp_early * np.exp(-0.5 * ((t - lat_early) / 8.0) ** 2)
    signal = signal + amp_late * np.exp(-0.5 * ((t - lat_late) / 18.0) ** 2)
    # residual EEG: autocorrelated in time, independent between participants
    white = rng.normal(0.0, 1.0, (N_SUBJ, N_TIME))
    noise = np.empty((N_SUBJ, N_TIME))
    noise[:, 0] = white[:, 0]
    innov = np.sqrt(1.0 - NOISE_RHO ** 2)
    for k in range(1, N_TIME):
        noise[:, k] = NOISE_RHO * noise[:, k - 1] + innov * white[:, k]
    offset = rng.normal(0.0, 0.5, (N_SUBJ, 1))
    erp = signal + NOISE_SD * noise + offset
    return {"erp": erp.astype(np.float64), "patient": patient}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _recording(rng, GROUP_GAIN)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _recording(rng, 0.0)


def _permute_patient(d, rng):
    return {**d, "patient": rng.permutation(d["patient"])}


def criterion(d):
    """Data keys: erp, float (60, 200) = (participants, time), evoked-response amplitude (microvolts) of each
    participant at each time sample after stimulus onset, time samples in order; patient, bool (60,), True for a
    patient, False for a control participant.
    Holds when the claim is supported by the data. Written by someone else."""
    def _sf(t, df):
        # upper-tail probability of Student's t: integral of cos(x)**(df-1) over [arctan(t/sqrt(df)), pi/2], trapezoid rule
        t = np.asarray(t, dtype=float)
        df = np.broadcast_to(np.asarray(df, dtype=float), t.shape)
        u = np.linspace(0.0, 1.0, 1001)

        def tail(lo):
            x = lo[..., None] + (np.pi / 2.0 - lo[..., None]) * u
            f = np.cos(x) ** (df[..., None] - 1.0)
            return (f.sum(-1) - 0.5 * (f[..., 0] + f[..., -1])) * (np.pi / 2.0 - lo) / (len(u) - 1)

        ang = np.arctan(np.abs(t) / np.sqrt(df))
        upper = tail(ang) / (2.0 * tail(np.zeros_like(ang)))
        return np.where(t >= 0.0, upper, 1.0 - upper)
    def _welch(a, b):
        # Welch t test of mean(a) > mean(b): (difference of means, one-sided p); None when both variances are zero
        va = a.var(ddof=1) / a.size
        vb = b.var(ddof=1) / b.size
        se2 = va + vb
        if not se2 > 0.0:
            return None
        df = se2 ** 2 / (va ** 2 / (a.size - 1.0) + vb ** 2 / (b.size - 1.0))
        diff = a.mean() - b.mean()
        return diff, float(_sf(diff / np.sqrt(se2), df))
    erp = np.asarray(d["erp"], dtype=float)
    pat = np.asarray(d["patient"], dtype=bool)
    if not np.all(np.isfinite(erp)):
        return None
    n, n_time = erp.shape
    width = 10
    if n_time < width:
        return None
    sel = np.arange(0, n, 2)
    est = np.arange(1, n, 2)
    if pat[sel].sum() < 1 or (~pat[sel]).sum() < 1:
        return None
    csum = np.concatenate([np.zeros((n, 1)), np.cumsum(erp, axis=1)], axis=1)
    win = (csum[:, width:] - csum[:, :-width]) / width
    gap = win[sel][pat[sel]].mean(axis=0) - win[sel][~pat[sel]].mean(axis=0)
    best = int(np.argmax(gap))
    a = win[est][pat[est], best]
    b = win[est][~pat[est], best]
    if a.size < 2 or b.size < 2:
        return None
    r = _welch(a, b)
    if r is None:
        return None
    return bool(r[0] >= 0.5 and r[1] < 0.05)


STUDY = Study(
    name="C31",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the patient-control amplitude difference of the late component is set to 0 (patients have the control response)"),
    },
    controls=[Control("permute_patient", ["C"], transform=_permute_patient)],
)
