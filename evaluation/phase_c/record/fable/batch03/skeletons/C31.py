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
    raise NotImplementedError


STUDY = Study(
    name="C31",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the patient-control amplitude difference of the late component is set to 0 (patients have the control response)"),
    },
    controls=[Control("permute_patient", ["C"], transform=_permute_patient)],
)
