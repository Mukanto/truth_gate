"""C37: A classifier built from the 12 clinical measurements detects at least 60% of the patients who have the less frequent outcome among new patients (sensitivity of at least 0.60)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 400
N_MEAS = 12
PREVALENCE = 0.22
COMMON = 0.4                                         # loading of every measurement on a shared factor (general health)
SHIFTS = np.array([0.85, 0.75, 0.65, 0.45])          # outcome-related shift of 4 measurements, in SD units
CENTRE = np.array([62.0, 27.5, 135.0, 82.0, 74.0, 5.6, 1.0, 13.8, 4.1, 140.0, 5.2, 38.0])
SPREAD = np.array([11.0, 4.5, 18.0, 11.0, 12.0, 0.9, 0.25, 1.5, 0.4, 3.0, 1.1, 9.0])


def _clinic(rng, strength):
    n_pos = int(np.clip(rng.binomial(N_PATIENTS, PREVALENCE), 50, 150))
    outcome = np.zeros(N_PATIENTS, dtype=bool)
    outcome[rng.choice(N_PATIENTS, n_pos, replace=False)] = True
    shared = rng.normal(0.0, 1.0, (N_PATIENTS, 1))
    z = COMMON * shared + np.sqrt(1.0 - COMMON ** 2) * rng.normal(0.0, 1.0, (N_PATIENTS, N_MEAS))
    informative = rng.choice(N_MEAS, SHIFTS.size, replace=False)
    sign = rng.choice(np.array([-1.0, 1.0]), SHIFTS.size)
    delta = np.zeros(N_MEAS)
    delta[informative] = sign * SHIFTS * strength
    z = z + outcome[:, None] * delta[None, :]
    measurements = CENTRE[None, :] + SPREAD[None, :] * z
    return {"measurements": measurements.astype(np.float64), "outcome": outcome}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _clinic(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _clinic(rng, 0.0)


def _permute_outcome(d, rng):
    return {**d, "outcome": rng.permutation(d["outcome"])}


def criterion(d):
    """Data keys: measurements, float (400, 12) = (patients, measurements), 12 clinical measurements of each
    patient; outcome, bool (400,), True when the patient has the less frequent of the two outcomes.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C37",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the measurements carry no information about the outcome (all outcome-related shifts set to 0; prevalence unchanged)"),
    },
    controls=[Control("permute_outcome", ["C"], transform=_permute_outcome)],
)
