"""W28: In a study of 60 participants, those who perform worst at the start of a perceptual-learning task benefit most from training: the improvement (late-block score minus early-block score) of the lower-scoring half exceeds that of the higher-scoring half by at least 4 points, with an independent-samples t-test p < 0.05 (one-sided)."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N, B = 60, 4
CURVE = np.array([0.0, 0.45, 0.75, 1.0])                    # share of the total learning reached at each block


def _gen(rng, eff):
    skill = 60.0 + 8.0 * rng.standard_normal(N)             # true starting skill
    e = rng.standard_normal((N, B))
    gain = 6.0 - eff * 0.6 * (skill - 60.0)                 # total learning: weaker participants learn more in plus
    score = skill[:, None] + gain[:, None] * CURVE[None, :] + 6.0 * e
    return {"score": np.clip(score, 0.0, 100.0)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: score (60, 4) percent correct (0 to 100) in each of 4 consecutive blocks of the task, axes (participants,
    blocks), block 0 first and block 3 last.
    Holds when the claim is supported by the data. Written by someone else."""
    def _lg(z):
        c = (0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
             -176.61502916214059, 12.507343278686905, -0.13857109526572012,
             9.9843695780195716e-6, 1.5056327351493116e-7)
        z = z - 1.0
        x = c[0]
        for i in range(1, 9):
            x += c[i] / (z + i)
        t = z + 7.5
        return 0.5 * np.log(2.0 * np.pi) + (z + 0.5) * np.log(t) - t + np.log(x)

    def _cf(a, b, x):
        tiny = 1e-300
        qab, qap, qam = a + b, a + 1.0, a - 1.0
        c = 1.0
        dd = 1.0 - qab * x / qap
        dd = 1.0 / (dd if abs(dd) > tiny else tiny)
        h = dd
        for m in range(1, 400):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= dd * c
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            dd = 1.0 + aa * dd
            dd = 1.0 / (dd if abs(dd) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            de = dd * c
            h *= de
            if abs(de - 1.0) < 1e-13:
                break
        return h

    def _ib(x, a, b):
        # regularized incomplete beta function I_x(a, b)
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        bt = np.exp(_lg(a + b) - _lg(a) - _lg(b) + a * np.log(x) + b * np.log(1.0 - x))
        if x < (a + 1.0) / (a + b + 2.0):
            return float(bt * _cf(a, b, x) / a)
        return float(1.0 - bt * _cf(b, a, 1.0 - x) / b)

    def _tsf(t, df):
        # one-sided upper-tail probability of Student's t
        t = float(t)
        if t == 0.0:
            return 0.5
        p = 0.5 * _ib(df / (df + t * t), 0.5 * df, 0.5)
        return p if t > 0 else 1.0 - p

    s = np.asarray(d["score"], dtype=float)
    if not np.all(np.isfinite(s)):
        return None
    n = s.shape[0]
    split = s[:, 0]
    order = np.argsort(split, kind="stable")
    low, up = order[: n // 2], order[n // 2:]                  # lower-scoring and higher-scoring half
    imp = s[:, -1] - s[:, 0]                                   # late block minus early block
    a, b = imp[low], imp[up]
    if len(a) < 3 or len(b) < 3:
        return None
    sp2 = ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)
    if not sp2 > 0:
        return None
    diff = a.mean() - b.mean()
    t = diff / np.sqrt(sp2 * (1.0 / len(a) + 1.0 / len(b)))
    return bool(diff >= 4.0 and _tsf(t, len(a) + len(b) - 2) < 0.05)


def decouple_gain_from_start(d, rng):
    s = d["score"]
    p = rng.permutation(N)
    gain_other = s[p] - s[p][:, :1]                          # change from the first block of another participant
    return {**d, "score": np.clip(s[:, :1] + gain_other, 0.0, 100.0)}


STUDY = Study(
    name="W28",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true learning depends on starting skill (-0.6 points of learning per point of skill, about 7 points more for the weaker half) -> every participant learns the same 6 points in total; skill spread (sd 8), block noise (sd 6) and the learning curve unchanged"),
    },
    controls=[Control("decouple_gain_from_start", ["C"], transform=decouple_gain_from_start)],
)
