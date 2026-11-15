"""C45: The training programme improves task accuracy more than the control activity: the mean change in accuracy (post minus pre) is larger in the trained group than in the control group, and a two-sample t test of the difference between the two groups' mean changes gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_SUBJ = 40
N_TRAINED = 20
N_TRIALS = 120          # trials behind each accuracy value
ABILITY_MEAN = 0.70
ABILITY_SD = 0.07
GAIN_CONTROL = 0.035    # practice effect of taking the task twice
GAIN_TRAINED = 0.105    # practice effect plus training effect
GAIN_SD = 0.03          # individual variation of the true gain


def _experiment(rng, gain_trained):
    trained = np.zeros(N_SUBJ, dtype=bool)
    trained[rng.choice(N_SUBJ, N_TRAINED, replace=False)] = True
    ability = np.clip(rng.normal(ABILITY_MEAN, ABILITY_SD, N_SUBJ), 0.40, 0.90)
    gain = np.where(trained, gain_trained, GAIN_CONTROL) + rng.normal(0.0, GAIN_SD, N_SUBJ)
    after = np.clip(ability + gain, 0.02, 0.98)
    pre = rng.binomial(N_TRIALS, ability) / N_TRIALS
    post = rng.binomial(N_TRIALS, after) / N_TRIALS
    return {"pre": pre.astype(np.float64), "post": post.astype(np.float64), "trained": trained}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _experiment(rng, GAIN_TRAINED)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _experiment(rng, GAIN_CONTROL)


def _permute_trained(d, rng):
    return {**d, "trained": rng.permutation(d["trained"])}


def criterion(d):
    """Data keys: pre, float (40,), task accuracy (proportion correct) of each subject before the programme; post,
    float (40,), task accuracy (proportion correct) of each subject after the programme; trained, bool (40,),
    whether the subject took part in the training programme (true) or in the control activity (false).
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

    pre = np.asarray(d["pre"], dtype=float)
    post = np.asarray(d["post"], dtype=float)
    g = np.asarray(d["trained"], dtype=bool)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    if g.sum() < 2 or (~g).sum() < 2:
        return None
    change = post - pre
    x = change[g]
    y = change[~g]
    nx, ny = x.size, y.size
    df = nx + ny - 2.0
    s2 = ((nx - 1.0) * x.var(ddof=1) + (ny - 1.0) * y.var(ddof=1)) / df
    se2 = s2 * (1.0 / nx + 1.0 / ny)
    if not se2 > 0.0:
        return None
    t = (x.mean() - y.mean()) / np.sqrt(se2)
    return bool(x.mean() > y.mean() and p2t(t, df) < 0.05)


STUDY = Study(
    name="C45",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the training effect is set to 0: the trained group's expected gain equals the control group's (0.105 -> 0.035)"),
    },
    controls=[Control("permute_trained", ["C"], transform=_permute_trained)],
)
