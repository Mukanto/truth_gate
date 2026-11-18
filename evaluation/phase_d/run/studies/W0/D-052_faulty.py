"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_YOUNG = 20
N_OLD = 20
BASE_YOUNG = 60.0       # mean baseline performance score, young
BASE_OLD = 52.0         # mean baseline performance score, old
SD_ABILITY = 10.0       # between-subject SD of true ability
SD_GAIN = 4.0           # between-subject SD of the true training gain
SD_MEAS = 3.0           # test-retest measurement error SD per session
GAIN_OLD = 4.5          # mean true gain, old
GAIN_YOUNG_PLUS = 10.0  # mean true gain, young (plus); minus sets it to GAIN_OLD


def _generate(rng, gain_young):
    n = N_YOUNG + N_OLD
    young = np.zeros(n, dtype=bool)
    young[rng.permutation(n)[:N_YOUNG]] = True
    ability = np.where(young, BASE_YOUNG, BASE_OLD) + SD_ABILITY * rng.standard_normal(n)
    gain = np.where(young, gain_young, GAIN_OLD) + SD_GAIN * rng.standard_normal(n)
    pre = ability + SD_MEAS * rng.standard_normal(n)
    post = ability + gain + SD_MEAS * rng.standard_normal(n)
    return {
        "pre": np.asarray(pre, dtype=np.float64),
        "post": np.asarray(post, dtype=np.float64),
        "young": young,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, GAIN_YOUNG_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, GAIN_OLD)


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
    return {**d, "young": rng.permutation(d["young"])}


def _swap_sessions(d, rng):
    return {**d, "pre": d["post"].copy(), "post": d["pre"].copy()}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="mean true training gain of young set equal to that of old (10.0 -> 4.5); all else unchanged"),
    },
    controls=[
        Control("age_labels_permuted", ["C"], transform=_permute_age_labels),
        Control("pre_post_swapped", ["C"], transform=_swap_sessions),
    ],
)
