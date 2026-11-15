"""C50: Among patients whose first systolic blood-pressure reading was at least 160 mmHg, antihypertensive treatment lowers systolic pressure: the mean fall from the second reading (taken before treatment began) to the third reading (taken after 8 weeks of treatment) is at least 8 mmHg, and a one-sided paired t test of the fall is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 250
N_READINGS = 3
USUAL_MEAN = 152.0       # mean of the patients' usual systolic pressure, mmHg
USUAL_SD = 14.0          # between-patient SD of usual pressure
VISIT_SD = 11.0          # within-patient visit-to-visit variability and measurement error
TREATMENT_CUT = 160.0    # treatment is started when the screening reading is at least this
MEAN_RESPONSE = 12.0     # mean fall caused by 8 weeks of treatment, mmHg
RESPONSE_SD = 6.0        # between-patient SD of the treatment response


def _generate(rng, mean_response, response_sd):
    usual = rng.normal(USUAL_MEAN, USUAL_SD, size=N_PATIENTS)
    visit = rng.normal(0.0, VISIT_SD, size=(N_PATIENTS, N_READINGS))
    response_z = rng.normal(size=N_PATIENTS)
    sbp = usual[:, None] + visit
    treated = sbp[:, 0] >= TREATMENT_CUT
    sbp[:, 2] -= treated * (mean_response + response_sd * response_z)
    return {"sbp": sbp}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, MEAN_RESPONSE, RESPONSE_SD)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, 0.0, 0.0)


def swap_pre_post(d, rng):
    sbp = d["sbp"].copy()
    swap = rng.random(sbp.shape[0]) < 0.5
    swap[rng.integers(sbp.shape[0])] = True
    sbp[swap, 1], sbp[swap, 2] = d["sbp"][swap, 2], d["sbp"][swap, 1]
    return {**d, "sbp": sbp}


def criterion(d):
    """Data keys: sbp, float array of shape (250, 3) = (patients, readings): systolic blood pressure in mmHg; readings
    in time order: column 0 = reading 1 at the screening visit, column 1 = reading 2 at the pre-treatment visit,
    column 2 = reading 3 after 8 weeks of treatment.
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
    sbp = np.asarray(d["sbp"], dtype=float)
    if not np.all(np.isfinite(sbp)):
        return None
    keep = sbp[:, 0] >= 160.0
    fall = sbp[keep, 1] - sbp[keep, 2]
    if fall.size < 2:
        return None
    r = _ttest1(fall)
    if r is None:
        return None
    return bool(r[0] >= 8.0 and r[1] < 0.05)


STUDY = Study(
    name="C50",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the treatment response is set to zero: reading 3 is another untreated reading of the same patient (usual pressures, visit-to-visit variability and the selection on reading 1 unchanged)"),
    },
    controls=[Control("swap_readings_2_and_3_at_random_within_patient", ["C"], transform=swap_pre_post)],
)
