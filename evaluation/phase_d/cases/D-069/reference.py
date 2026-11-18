"""D-069: In a trial of a blood-pressure drug, 900 patients had systolic pressure measured at baseline and again after 6 months, and the array treated marks which patients received the drug. The reduction of a patient is the baseline pressure minus the 6-month pressure. Claim: the reduction attributable to the drug (mean reduction in treated patients minus mean reduction in untreated patients) is larger in patients in the top third of baseline pressures than in patients in the bottom third of baseline pressures, by at least 3 mmHg."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 900
N_TREATED = 450
SBP_MEAN = 150.0
SD_TRUE = 15.06
SD_VISIT = 9.86
PLACEBO_FALL = 2.0
DRUG_FALL = 10.0
SLOPE_PLUS = 0.20
SD_RESPONSE = 4.0


def _world(rng, slope):
    true = SBP_MEAN + SD_TRUE * rng.standard_normal(N_PATIENTS)
    baseline = true + SD_VISIT * rng.standard_normal(N_PATIENTS)
    treated = np.zeros(N_PATIENTS, dtype=bool)
    treated[rng.permutation(N_PATIENTS)[:N_TREATED]] = True
    drug_effect = DRUG_FALL + slope * (true - SBP_MEAN) + SD_RESPONSE * rng.standard_normal(N_PATIENTS)
    followup = true - PLACEBO_FALL - np.where(treated, drug_effect, 0.0) + SD_VISIT * rng.standard_normal(N_PATIENTS)
    return {"baseline_sbp": baseline.astype(float), "followup_sbp": followup.astype(float), "treated": treated}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, SLOPE_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: baseline_sbp (900,) float, systolic blood pressure in mmHg at baseline;
    followup_sbp (900,) float, systolic blood pressure in mmHg after 6 months;
    treated (900,) bool, True if the patient received the drug.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    lab = np.asarray(d["treated"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"baseline_sbp": np.array(d["baseline_sbp"], dtype=float), "followup_sbp": np.array(d["followup_sbp"], dtype=float), "treated": new}


STUDY = Study(
    name="D-069",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the dependence of the drug-attributable fall on true baseline pressure is set to 0 (slope 0.20 in plus; mean drug fall 10 mmHg kept); visit error, placebo fall, response spread and allocation unchanged"),
    },
    controls=[Control("D-069", ["C"], transform=lambda d, rng: _break(d, rng))],
)
