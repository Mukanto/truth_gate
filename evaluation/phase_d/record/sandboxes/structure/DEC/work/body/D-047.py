import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 600
SCORE_MEAN = 44.0
SD_TRUE = 16.27
SD_ERROR = 13.28
IMPROVE_PLUS = 0.30


def _world(rng, improve):
    true = SCORE_MEAN + SD_TRUE * rng.standard_normal(N_PATIENTS)
    screening = true + SD_ERROR * rng.standard_normal(N_PATIENTS)
    entry = true + SD_ERROR * rng.standard_normal(N_PATIENTS)
    week12 = (1.0 - improve) * true + SD_ERROR * rng.standard_normal(N_PATIENTS)
    return {
        "screening": np.clip(screening, 0.0, 100.0).astype(float),
        "entry": np.clip(entry, 0.0, 100.0).astype(float),
        "week12": np.clip(week12, 0.0, 100.0).astype(float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, IMPROVE_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: screening (600,) float, symptom severity score (0 to 100) at the screening visit;
    entry (600,) float, symptom severity score at entry on the day treatment began;
    week12 (600,) float, symptom severity score 12 weeks after treatment began.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    screening = np.array(d["screening"], dtype=float)
    entry = np.array(d["entry"], dtype=float)
    week12 = np.array(d["week12"], dtype=float)
    change = week12 - entry
    p = rng.permutation(change.size)
    if np.array_equal(p, np.arange(change.size)):
        p = np.roll(p, 1)
    new_change = change[p] - change.mean()
    return {"screening": screening, "entry": entry, "week12": entry + new_change}


STUDY = Study(
    name="D-047",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the treatment-related fall in severity from entry to week 12 is set to 0 (30 percent of the true severity in plus); true-severity spread, visit-to-visit error and screening/entry measurement unchanged"),
    },
    controls=[Control("D-047", ["C"], transform=lambda d, rng: _break(d, rng))],
)
