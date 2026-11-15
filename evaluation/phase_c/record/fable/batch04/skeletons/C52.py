"""C52: Reaction times fall more steeply over practice sessions in healthy subjects than in patients: the mean per-subject linear slope of reaction time on session number is more negative in the healthy group, and a two-sample t test of the difference between the two groups' mean slopes gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUBJECTS = 30
N_SESSIONS = 8
N_PATIENT_GROUP = 15
HEALTHY_SLOPE = -16.0    # mean change of reaction time per session, ms, healthy group
PATIENT_SLOPE = -8.0     # the same in the patient group
SLOPE_SD = 5.5           # between-subject SD of the true slope
HEALTHY_START = 520.0    # mean first-session reaction time, ms
PATIENT_START = 610.0
HEALTHY_START_SD = 50.0
PATIENT_START_SD = 70.0
SESSION_SD = 18.0        # session-to-session noise of a subject's median reaction time


def _generate(rng, healthy_slope, patient_slope):
    patient = np.zeros(N_SUBJECTS, dtype=bool)
    patient[rng.permutation(N_SUBJECTS)[:N_PATIENT_GROUP]] = True
    start_z = rng.normal(size=N_SUBJECTS)
    slope_z = rng.normal(size=N_SUBJECTS)
    noise = rng.normal(0.0, SESSION_SD, size=(N_SUBJECTS, N_SESSIONS))
    start = np.where(patient, PATIENT_START + PATIENT_START_SD * start_z, HEALTHY_START + HEALTHY_START_SD * start_z)
    slope = np.where(patient, patient_slope, healthy_slope) + SLOPE_SD * slope_z
    rt = start[:, None] + slope[:, None] * np.arange(N_SESSIONS) + noise
    return {"rt": rt, "patient": patient}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, HEALTHY_SLOPE, PATIENT_SLOPE)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    pooled = 0.5 * (HEALTHY_SLOPE + PATIENT_SLOPE)
    return _generate(rng, pooled, pooled)


def permute_groups(d, rng):
    return {**d, "patient": d["patient"][rng.permutation(d["patient"].shape[0])]}


def criterion(d):
    """Data keys: rt, float array of shape (30, 8) = (subjects, sessions): median reaction time in milliseconds of
    each subject in each practice session, sessions in order; patient, bool array of shape (30,) = (subjects,):
    whether the subject belongs to the patient group (True) or the healthy group (False).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C52",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the mean practice slope is the same in both groups (both set to the pooled mean, -12 ms per session); the group difference in overall reaction time, the between-subject slope variability and the session noise are unchanged"),
    },
    controls=[Control("permute_group_membership_across_subjects", ["C"], transform=permute_groups)],
)
