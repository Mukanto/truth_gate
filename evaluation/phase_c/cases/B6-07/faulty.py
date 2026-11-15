"""C08: The task engages region A more than region B: the task-evoked signal change (task minus rest) is larger in region A than in region B, with the mean across subjects of the within-subject difference of the two signal changes positive, and a paired t test of that difference gives two-sided p < 0.05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, eff_a, eff_b):
    n = 24
    g = rng.normal(0.0, 1.0, n)                                  # subject-wide signal offset
    base_a = 0.3 * g + 0.2 * rng.normal(0.0, 1.0, n)
    base_b = 0.3 * g + 0.2 * rng.normal(0.0, 1.0, n)
    u1 = rng.normal(0.0, 1.0, n)
    u2 = rng.normal(0.0, 1.0, n)
    resp_a = eff_a + 0.26 * u1                                   # subject's task effect in region A
    resp_b = eff_b + 0.58 * (0.4 * u1 + np.sqrt(0.84) * u2)      # region B is more variable across subjects
    e = 0.1 * rng.normal(0.0, 1.0, (4, n))                       # block-average measurement noise
    return {
        "task_a": base_a + resp_a + e[0],
        "rest_a": base_a + e[1],
        "task_b": base_b + resp_b + e[2],
        "rest_b": base_b + e[3],
    }


def plus(rng):
    """The claim is true: task effect 0.50 in region A and 0.10 in region B (difference 0.40)."""
    return _gen(rng, 0.50, 0.10)


def minus(rng):
    """The claim is false: the task effect is the same in both regions (0.30, the plus average)."""
    return _gen(rng, 0.30, 0.30)


def _swap_regions(d, rng):
    n = d["task_a"].shape[0]
    swap = rng.permutation(n) < n // 2                           # exchange the region labels in half the subjects
    return {
        **d,
        "task_a": np.where(swap, d["task_b"], d["task_a"]),
        "rest_a": np.where(swap, d["rest_b"], d["rest_a"]),
        "task_b": np.where(swap, d["task_a"], d["task_b"]),
        "rest_b": np.where(swap, d["rest_a"], d["rest_b"]),
    }


def criterion(d):
    """Data keys: task_a, float (24 subjects,), mean signal in region A of each subject during task blocks
    (percent signal change units); rest_a, float (24,), mean signal in region A during rest blocks; task_b,
    float (24,), mean signal in region B during task blocks; rest_b, float (24,), mean signal in region B
    during rest blocks.
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

    ta = np.asarray(d["task_a"], dtype=float)
    ra = np.asarray(d["rest_a"], dtype=float)
    tb = np.asarray(d["task_b"], dtype=float)
    rb = np.asarray(d["rest_b"], dtype=float)
    if not (np.all(np.isfinite(ta)) and np.all(np.isfinite(ra)) and np.all(np.isfinite(tb)) and np.all(np.isfinite(rb))):
        return None
    if ta.size < 2:
        return None
    ea = ta - ra
    eb = tb - rb
    def one(v):
        # one-sample t test of the region's mean signal change against zero
        se2 = v.var(ddof=1) / v.size
        if not se2 > 0.0:
            return None
        return v.mean(), p2t(v.mean() / np.sqrt(se2), v.size - 1.0)

    r1 = one(ea)
    r0 = one(eb)
    if r1 is None or r0 is None:
        return None
    return bool(r1[0] > 0.0 and r1[1] < 0.05 and r0[1] >= 0.05)


STUDY = Study(
    name="C08",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="difference between the task effects of region A and region B set to zero (both 0.30, their plus average)"),
    },
    controls=[Control("swap_region_labels_in_half_the_subjects", ["C"], transform=_swap_regions)],
)
