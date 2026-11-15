"""C15: Scores on the task and on the symptom scale are more strongly related in group A than in group B: the Pearson correlation between task score and symptom score is higher in group A than in group B, and a Fisher z test of the difference between the two correlations gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, r_a, r_b):
    n = 40
    group_a = np.zeros(n, dtype=bool)
    group_a[rng.permutation(n)[:20]] = True                      # 20 participants per group
    r = np.where(group_a, r_a, r_b)
    z1 = rng.normal(0.0, 1.0, n)
    z2 = rng.normal(0.0, 1.0, n)
    task = np.where(group_a, 56.0, 50.0) + 9.0 * z1
    symptom = np.where(group_a, 24.0, 14.0) + 7.0 * (r * z1 + np.sqrt(1.0 - r * r) * z2)
    return {"task_score": task, "symptom_score": symptom, "group_a": group_a}


def plus(rng):
    """The claim is true: the correlation is 0.8 in group A and 0.0 in group B."""
    return _gen(rng, 0.8, 0.0)


def minus(rng):
    """The claim is false: the correlation is the same in both groups (0.4, the plus average)."""
    return _gen(rng, 0.4, 0.4)


def _permute_groups(d, rng):
    return {**d, "group_a": d["group_a"][rng.permutation(d["group_a"].shape[0])]}


def criterion(d):
    """Data keys: task_score, float (40 participants,), score of each participant on the experimental task;
    symptom_score, float (40,), score of each participant on the symptom questionnaire; group_a, bool (40,),
    whether the participant belongs to group A (True) or group B (False).
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

    a = np.asarray(d["task_score"], dtype=float)
    b = np.asarray(d["symptom_score"], dtype=float)
    g = np.asarray(d["group_a"], dtype=bool)
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return None
    if g.sum() < 4 or (~g).sum() < 4:
        return None

    def corr(u, w):
        uc = u - u.mean()
        wc = w - w.mean()
        suu = (uc ** 2).sum()
        sww = (wc ** 2).sum()
        if not (suu > 0.0 and sww > 0.0):
            return None
        return (uc * wc).sum() / np.sqrt(suu * sww)

    r_a = corr(a[g], b[g])
    r_b = corr(a[~g], b[~g])
    if r_a is None or r_b is None:
        return None
    n_a = float(g.sum())
    n_b = float((~g).sum())
    p_a = p2t(r_a * np.sqrt((n_a - 2.0) / (1.0 - r_a * r_a)), n_a - 2.0)
    p_b = p2t(r_b * np.sqrt((n_b - 2.0) / (1.0 - r_b * r_b)), n_b - 2.0)
    return bool(r_a > 0.0 and p_a < 0.05 and p_b >= 0.05)


STUDY = Study(
    name="C15",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="difference between the two groups' task-symptom correlations set to zero (both 0.4, their plus average)"),
    },
    controls=[Control("permute_group_labels", ["C"], transform=_permute_groups)],
)
