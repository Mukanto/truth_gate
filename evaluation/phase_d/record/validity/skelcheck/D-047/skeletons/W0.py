"""D-047: 600 patients with menopausal hot flushes received a treatment. Symptom severity (scale 0 to 100, higher is worse) was scored at a screening visit, again at entry on the day treatment began, and again 12 weeks later. Claim: among patients whose screening score was at least 60, at least half have a week-12 score that is 10 or more points below their entry score (proportion of at least 0.5)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 600
TRUE_MEAN = 52.0          # mean of each patient's stable true severity
TRUE_SD = 13.0            # between-patient SD of true severity
VISIT_SD = 9.0            # visit-to-visit fluctuation and scoring error of one score
PLUS_MEAN_CHANGE = 15.0   # mean true improvement from entry to week 12 in plus
CHANGE_SD = 9.0           # between-patient SD of the true improvement


def _simulate(rng, mean_change):
    n = N_PATIENTS
    severity = TRUE_MEAN + TRUE_SD * rng.standard_normal(n)
    screening = severity + VISIT_SD * rng.standard_normal(n)
    entry = severity + VISIT_SD * rng.standard_normal(n)
    improvement = mean_change + CHANGE_SD * rng.standard_normal(n)
    week12 = severity - improvement + VISIT_SD * rng.standard_normal(n)
    return {
        "screening": np.asarray(np.clip(screening, 0.0, 100.0), dtype=np.float64),
        "entry": np.asarray(np.clip(entry, 0.0, 100.0), dtype=np.float64),
        "week12": np.asarray(np.clip(week12, 0.0, 100.0), dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _simulate(rng, PLUS_MEAN_CHANGE)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _simulate(rng, 0.0)


def criterion(d):
    """Data keys: screening (600,) float, symptom severity score (0-100, higher is worse) of each patient at the
    screening visit; entry (600,) float, symptom severity score at entry, on the day treatment began; week12 (600,)
    float, symptom severity score 12 weeks after treatment began.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _reverse_time(d, rng):
    return {**d, "entry": d["week12"].copy(), "week12": d["entry"].copy()}


STUDY = Study(
    name="D-047",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean true improvement from entry to week 12 set from 15 to 0 points; between-patient SD of change, true-severity distribution, visit fluctuation (hence regression to the mean after screening selection) unchanged"),
    },
    controls=[Control("entry_and_week12_swapped", ["C"], transform=_reverse_time)],
)
