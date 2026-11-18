"""D-047: 600 patients with menopausal hot flushes received a treatment. Symptom severity (scale 0 to 100, higher is worse) was scored at a screening visit, again at entry on the day treatment began, and again 12 weeks later. Claim: among patients whose screening score was at least 60, at least half have a week-12 score that is 10 or more points below their entry score (proportion of at least 0.5)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


N_PATIENTS = 600
TRUE_MEAN, TRUE_SD = 55.0, 15.0     # each patient's usual symptom severity
VISIT_SD = 11.0                     # visit-to-visit fluctuation plus scoring error at each visit
CHANGE_MEAN, CHANGE_SD = -15.0, 8.0  # true change in severity from entry to week 12 under treatment


def _score(x):
    """Severity scale: integer points between 0 and 100."""
    return np.clip(np.round(x), 0.0, 100.0)


def _draw(rng, effect):
    """One trial cohort. Returns (data, truth); truth holds usual severity and true change."""
    n = N_PATIENTS
    usual = TRUE_MEAN + TRUE_SD * rng.standard_normal(n)
    visit = VISIT_SD * rng.standard_normal((3, n))
    change = effect * (CHANGE_MEAN + CHANGE_SD * rng.standard_normal(n))
    data = {
        "screening": _score(usual + visit[0]),
        "entry": _score(usual + visit[1]),
        "week12": _score(usual + change + visit[2]),
    }
    return data, {"usual": usual, "change": change}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _draw(rng, 1.0)[0]


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _draw(rng, 0.0)[0]


def criterion(d):
    """Data keys (one value per patient, 600 patients, aligned; symptom severity 0 to 100, higher is worse,
    integer points stored as float64): screening (600,) float64, score at the screening visit; entry (600,)
    float64, score at entry, on the day treatment began; week12 (600,) float64, score 12 weeks after treatment
    began.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _entry_week12_swapped(d, rng):
    entry, week12 = d["entry"], d["week12"]
    if np.array_equal(entry, week12):
        return {**d, "entry": np.roll(entry, 1)}
    return {**d, "entry": week12, "week12": entry}


STUDY = Study(
    name="D-047",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="true change in severity from entry to week 12 set to 0 for every patient (usual "
                              "severity, visit-to-visit fluctuation, screening selection and scale unchanged)"),
    },
    controls=[Control("entry_week12_swapped", ["C"], transform=_entry_week12_swapped)],
)
