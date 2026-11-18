"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_YOUNG = 20
N_OLD = 20
BASE_GAIN = 10.0            # mean true improvement, averaged over the two age groups (points)
GAIN_DIFF = 7.0             # young minus old mean true improvement (points); about d = 0.85 on improvement scores
ABILITY_MEAN_YOUNG = 104.0
ABILITY_MEAN_OLD = 96.0
ABILITY_SD_YOUNG = 11.0
ABILITY_SD_OLD = 13.0
GAIN_SD = 4.0               # between-person SD of the true improvement within an age group
GAIN_ON_BASELINE = -0.1     # within-group dependence of the true improvement on true baseline ability
MEAS_SD = 5.0               # measurement error SD of one score (test-retest reliability about 0.85)


def _generate(rng, gain_diff):
    n = N_YOUNG + N_OLD
    labels = np.concatenate([np.ones(N_YOUNG, dtype=bool), np.zeros(N_OLD, dtype=bool)])
    young = rng.permutation(labels)
    mu = np.where(young, ABILITY_MEAN_YOUNG, ABILITY_MEAN_OLD)
    sd = np.where(young, ABILITY_SD_YOUNG, ABILITY_SD_OLD)
    ability = mu + sd * rng.standard_normal(n)
    group_gain = np.where(young, BASE_GAIN + 0.5 * gain_diff, BASE_GAIN - 0.5 * gain_diff)
    gain = group_gain + GAIN_ON_BASELINE * (ability - mu) + GAIN_SD * rng.standard_normal(n)
    pre = ability + MEAS_SD * rng.standard_normal(n)
    post = ability + gain + MEAS_SD * rng.standard_normal(n)
    return {
        "pre": np.asarray(pre, dtype=np.float64),
        "post": np.asarray(post, dtype=np.float64),
        "young": np.asarray(young, dtype=bool),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Young participants improve on average 7 points more than old participants (10 + 3.5 vs 10 - 3.5), about
    d = 0.85 on improvement scores. Stable person ability is shared by pre and post; old participants start lower
    and vary more."""
    return _generate(rng, GAIN_DIFF)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    Both age groups have the same mean true improvement (10 points); everything else as in plus."""
    return _generate(rng, 0.0)


# >>> PHASE D INSERTED CRITERION BODY (begin) >>>
def _lgamma(x):
    c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028,
         771.32342877765313, -176.61502916214059, 12.507343278686905,
         -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7)
    x = x - 1.0
    a = c[0]
    t = x + 7.5
    for i in range(1, 9):
        a = a + c[i] / (x + i)
    return 0.5 * np.log(2.0 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a)


def _betacf(a, b, x):
    tiny = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 2000):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h = h * d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        de = d * c
        h = h * de
        if abs(de - 1.0) < 1e-15:
            break
    return h


def _betainc(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = (_lgamma(a + b) - _lgamma(a) - _lgamma(b)
           + a * np.log(x) + b * np.log(1.0 - x))
    bt = np.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return float(bt * _betacf(a, b, x) / a)
    return float(1.0 - bt * _betacf(b, a, 1.0 - x) / b)


def _t_sf(t, df):
    t = float(t)
    df = float(df)
    if t == 0.0:
        return 0.5
    x = df / (df + t * t)
    p = 0.5 * _betainc(0.5 * df, 0.5, x)
    if t > 0.0:
        return p
    return 1.0 - p


def _t1_p(x):
    n = x.size
    if n < 2:
        return None
    s = x.std(ddof=1)
    if s <= 0.0:
        return None
    t = x.mean() / (s / np.sqrt(n))
    return _t_sf(t, n - 1)


def criterion(d):
    """Claim: the mean improvement (after minus before) is larger in young than
    in old participants, judged by a one-sided test of the difference between
    the two groups' mean improvements at the 0.05 level.

    d['pre']: float array (participants,) = (40,); performance score before
        the programme.
    d['post']: float array (participants,) = (40,); performance score after
        the programme.
    d['young']: bool array (participants,) = (40,); True for young
        participants, False for old participants.

    Returns True when the claim is supported at the 0.05 level, False
    otherwise; None when a value is non-finite, a group has fewer than 2
    participants, or the variance needed for the test is zero.
    """
    pre = np.asarray(d['pre'], dtype=float)
    post = np.asarray(d['post'], dtype=float)
    g = np.asarray(d['young'], dtype=bool)
    if not (np.all(np.isfinite(pre)) and np.all(np.isfinite(post))):
        return None
    imp = post - pre
    a = imp[g]
    b = imp[~g]
    if a.size < 2 or b.size < 2:
        return None
    pa = _t1_p(a)
    pb = _t1_p(b)
    if pa is None or pb is None:
        return None
    return bool(pa < 0.05 and not pb < 0.05)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _permute_age_labels(d, rng):
    young = d["young"]
    shuffled = young[rng.permutation(young.shape[0])]
    if np.array_equal(shuffled, young):
        shuffled = np.roll(young, 1)
    return {**d, "young": shuffled}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="young-old difference in mean true improvement set to 0 (7 -> 0 points; mean improvement kept at 10)"),
    },
    controls=[Control("age_labels_permuted", ["C"], transform=_permute_age_labels)],
    relational=[("post", "young")],
)
