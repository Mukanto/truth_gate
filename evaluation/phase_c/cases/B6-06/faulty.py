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
    def lgam(x):
        g = (676.5203681218851, -1259.1392167224028, 771.3234287776531, -176.6150291621406,
             12.507343278686905, -0.13857109526572012, 9.984369578019572e-6, 1.5056327351493116e-7)
        x = x - 1.0
        a = 0.99999999999980993
        for i, gi in enumerate(g):
            a += gi / (x + i + 1.0)
        t = x + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a)

    def betacf(a, b, x):
        tiny = 1e-300
        c = 1.0
        dd = 1.0 - (a + b) * x / (a + 1.0)
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 500):
            m2 = 2 * m
            aa = m * (b - m) * x / ((a - 1.0 + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + 1.0 + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-14:
                break
        return h

    def p2t(t, df):
        # two-sided p value of Student's t statistic with df degrees of freedom
        x = df / (df + t * t)
        if x >= 1.0:
            return 1.0
        if x <= 0.0:
            return 0.0
        a, b = 0.5 * df, 0.5
        lb = lgam(a + b) - lgam(a) - lgam(b) + a * np.log(x) + b * np.log1p(-x)
        if x < (a + 1.0) / (a + b + 2.0):
            return float(np.exp(lb) * betacf(a, b, x) / a)
        return float(1.0 - np.exp(lb) * betacf(b, a, 1.0 - x) / b)

    rt = np.asarray(d["rt"], dtype=float)
    g = np.asarray(d["patient"], dtype=bool)
    if not np.all(np.isfinite(rt)):
        return None
    if g.sum() < 2 or (~g).sum() < 2 or rt.shape[1] < 2:
        return None
    sess = np.arange(rt.shape[1], dtype=float)
    sc = sess - sess.mean()
    slope = ((rt - rt.mean(axis=1, keepdims=True)) * sc).sum(axis=1) / (sc ** 2).sum()
    x = slope[~g]
    y = slope[g]
    def one(v):
        # one-sample t test of the within-group mean slope against zero
        se2 = v.var(ddof=1) / v.size
        if not se2 > 0.0:
            return None
        return v.mean(), p2t(v.mean() / np.sqrt(se2), v.size - 1.0)

    r1 = one(x)
    r0 = one(y)
    if r1 is None or r0 is None:
        return None
    return bool(r1[0] < 0.0 and r1[1] < 0.05 and r0[1] >= 0.05)


STUDY = Study(
    name="C52",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the mean practice slope is the same in both groups (both set to the pooled mean, -12 ms per session); the group difference in overall reaction time, the between-subject slope variability and the session noise are unchanged"),
    },
    controls=[Control("permute_group_membership_across_subjects", ["C"], transform=permute_groups)],
)
