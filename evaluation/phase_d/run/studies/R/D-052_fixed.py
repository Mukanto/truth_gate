"""D-052: Forty participants, 20 young and 20 old, completed a training programme, and a performance score was recorded before and after it. Claim: the mean improvement (after minus before) is larger in young than in old participants, judged by a one-sided test of the difference between the two groups' mean improvements at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PER_GROUP = 20
N_PARTICIPANTS = 40
PRE_MEAN_YOUNG = 55.0
PRE_MEAN_OLD = 48.0
PRE_SD = 10.0
SD_IMP_YOUNG = 6.0
SD_IMP_OLD = 12.0
MEAN_IMP_YOUNG_PLUS = 8.0
MEAN_IMP_OLD_PLUS = 1.0
MEAN_IMP_NULL = 4.5


def _world(rng, mean_young, mean_old):
    young = np.zeros(N_PARTICIPANTS, dtype=bool)
    young[rng.permutation(N_PARTICIPANTS)[:N_PER_GROUP]] = True
    pre = np.where(young, PRE_MEAN_YOUNG, PRE_MEAN_OLD) + PRE_SD * rng.standard_normal(N_PARTICIPANTS)
    imp = (np.where(young, mean_young, mean_old)
           + np.where(young, SD_IMP_YOUNG, SD_IMP_OLD) * rng.standard_normal(N_PARTICIPANTS))
    post = pre + imp
    return {"pre": pre.astype(float), "post": post.astype(float), "young": young}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, MEAN_IMP_YOUNG_PLUS, MEAN_IMP_OLD_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, MEAN_IMP_NULL, MEAN_IMP_NULL)


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


def _welch(a, b):
    na = a.size
    nb = b.size
    va = a.var(ddof=1) / na
    vb = b.var(ddof=1) / nb
    se2 = va + vb
    if se2 <= 0.0:
        return None
    diff = a.mean() - b.mean()
    t = diff / np.sqrt(se2)
    df = se2 * se2 / (va * va / (na - 1) + vb * vb / (nb - 1))
    return float(diff), _t_sf(t, df)


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
    res = _welch(a, b)
    if res is None:
        return None
    return bool(res[1] < 0.05)
# <<< PHASE D INSERTED CRITERION BODY (end) <<<


def _break(d, rng):
    lab = np.asarray(d["young"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"pre": np.array(d["pre"], dtype=float), "post": np.array(d["post"], dtype=float), "young": new}


STUDY = Study(
    name="D-052",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the age-group difference in mean improvement is set to 0 (8.0 vs 1.0 in plus; both groups at the pooled mean 4.5); improvement sd (6 young, 12 old), baseline scores and group sizes unchanged"),
    },
    controls=[Control("D-052", ["C"], transform=lambda d, rng: _break(d, rng))],
)
