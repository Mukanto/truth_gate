"""D-047: 600 patients with menopausal hot flushes received a treatment. Symptom severity (scale 0 to 100, higher is worse) was scored at a screening visit, again at entry on the day treatment began, and again 12 weeks later. Claim: among patients whose screening score was at least 60, at least half have a week-12 score that is 10 or more points below their entry score (proportion of at least 0.5)."""
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


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
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
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


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
