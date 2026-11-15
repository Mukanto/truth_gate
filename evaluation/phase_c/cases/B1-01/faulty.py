"""C33: Among women whose menopausal symptom index at the start of the trial was at least 20 points, active hormone therapy lowers the index more than placebo does: the mean fall in the index (start minus week 12) is at least 3 points greater on active therapy than on placebo, and a one-sided Welch t test of that difference between the two arms is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_WOMEN = 300
N_ACTIVE = 150
SEVERITY_MEAN = 21.0
SEVERITY_SD = 5.5
MEASUREMENT_SD = 3.0     # occasion-to-occasion error of the index
PLACEBO_FALL = 4.0       # fall in both arms (placebo response, natural course)
COURSE_SD = 3.5          # individual variation of the 12-week course
ACTIVE_FRACTION = 0.22   # extra fall on active therapy, as a fraction of the woman's underlying severity


def _trial(rng, active_fraction):
    active = np.zeros(N_WOMEN, dtype=bool)
    active[rng.choice(N_WOMEN, N_ACTIVE, replace=False)] = True
    severity = np.clip(rng.normal(SEVERITY_MEAN, SEVERITY_SD, N_WOMEN), 2.0, None)
    start = severity + rng.normal(0.0, MEASUREMENT_SD, N_WOMEN)
    course = rng.normal(0.0, COURSE_SD, N_WOMEN)
    severity12 = severity - PLACEBO_FALL - active_fraction * severity * active + course
    week12 = severity12 + rng.normal(0.0, MEASUREMENT_SD, N_WOMEN)
    return {
        "index_start": np.clip(start, 0.0, None).astype(np.float64),
        "index_week12": np.clip(week12, 0.0, None).astype(np.float64),
        "active": active,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _trial(rng, ACTIVE_FRACTION)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _trial(rng, 0.0)


def _permute_active(d, rng):
    return {**d, "active": rng.permutation(d["active"])}


def criterion(d):
    """Data keys: index_start, float (300,), menopausal symptom index of each woman at the start of the trial
    (higher is worse); index_week12, float (300,), symptom index of each woman at week 12; active, bool (300,),
    True if the woman was randomised to active hormone therapy, False if to placebo.
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
    def _ttest1(x):
        # one-sample (or paired-difference) t test of mean(x) > 0: (mean, one-sided p); None when the variance is zero
        sd = x.std(ddof=1)
        if not sd > 0.0:
            return None
        return x.mean(), float(_sf(x.mean() / (sd / np.sqrt(x.size)), x.size - 1.0))
    start = np.asarray(d["index_start"], dtype=float)
    week12 = np.asarray(d["index_week12"], dtype=float)
    active = np.asarray(d["active"], dtype=bool)
    if not (np.all(np.isfinite(start)) and np.all(np.isfinite(week12))):
        return None
    fall = start - week12
    x = fall[(start >= 20.0) & active]
    if x.size < 2:
        return None
    r = _ttest1(x)
    if r is None:
        return None
    return bool(r[0] >= 3.0 and r[1] < 0.05)


STUDY = Study(
    name="C33",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the extra fall of the index on active therapy is set to 0 (both arms follow the placebo course)"),
    },
    controls=[Control("permute_active", ["C"], transform=_permute_active)],
)
