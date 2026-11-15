"""C11: Among patients whose symptom score at the screening visit was at least 60, at least 40% improve by 10 points or more between the start of the programme and the 6-month follow-up (score at the start minus score at 6 months of at least 10); the claim is that the proportion of such patients is at least 0.40."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, mean_improvement):
    n = 500
    severity = rng.normal(55.0, 10.0, n)                         # stable severity of each patient
    screen = severity + rng.normal(0.0, 10.0, n)                 # visit-to-visit fluctuation and measurement error
    start = severity + rng.normal(0.0, 10.0, n)
    change = rng.normal(mean_improvement, 8.0, n)                # true change over the six months
    follow = severity - change + rng.normal(0.0, 10.0, n)
    return {
        "score_screen": np.clip(screen, 0.0, 100.0),
        "score_start": np.clip(start, 0.0, 100.0),
        "score_6m": np.clip(follow, 0.0, 100.0),
    }


def plus(rng):
    """The claim is true: mean true improvement 13 points, so about 57% improve by 10 or more from the start."""
    return _gen(rng, 13.0)


def minus(rng):
    """The claim is false: mean true improvement 0 (about 27% reach 10 points by fluctuation alone)."""
    return _gen(rng, 0.0)


def _reverse_time(d, rng):
    return {**d, "score_start": d["score_6m"], "score_6m": d["score_start"]}


def criterion(d):
    """Data keys: score_screen, float (500 patients,), symptom score of each patient at the screening visit
    (higher is worse); score_start, float (500,), symptom score at the start of the programme; score_6m,
    float (500,), symptom score at the 6-month follow-up.
    Holds when the claim is supported by the data. Written by someone else."""
    screen = np.asarray(d["score_screen"], dtype=float)
    start = np.asarray(d["score_start"], dtype=float)
    six = np.asarray(d["score_6m"], dtype=float)
    if not all(np.all(np.isfinite(x)) for x in (screen, start, six)):
        return None
    keep = start >= 60.0
    if keep.sum() < 1:
        return None
    share = np.mean((start[keep] - six[keep]) >= 10.0)
    return bool(share >= 0.40)


STUDY = Study(
    name="C11",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="mean true improvement between the start and 6 months set to zero"),
    },
    controls=[Control("exchange_start_and_6_month_scores", ["C"], transform=_reverse_time)],
)
