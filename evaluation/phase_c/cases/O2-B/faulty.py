"""C20: The mean score of the treatment condition exceeds that of the control condition: the difference in means is positive and a two-sided two-sample t test (equal variances assumed) on all participants gives p < .05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _group(rng, n, shift):
    attentive = rng.normal(70.0, 10.0, n)
    careless = rng.normal(45.0, 10.0, n)
    is_careless = rng.random(n) < 0.04      # a few low-effort participants in either condition
    score = np.where(is_careless, careless, attentive) + shift
    return np.clip(score, 0.0, 100.0).astype(np.float64)


def _world(rng, effect):
    n = 50
    return {"score_control": _group(rng, n, 0.0), "score_treatment": _group(rng, n, effect)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 7.5)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def _reassign_conditions(d, rng):
    # participants are re-dealt at random to the two conditions
    n = d["score_control"].shape[0]
    pooled = np.concatenate([d["score_control"], d["score_treatment"]])
    shuffled = rng.permutation(pooled)
    while np.array_equal(shuffled, pooled):
        shuffled = rng.permutation(pooled)
    return {**d, "score_control": shuffled[:n], "score_treatment": shuffled[n:]}


def criterion(d):
    """Data keys: score_control (50,) float, task score (0-100) of each participant in the control condition;
    score_treatment (50,) float, task score of each participant in the treatment condition. The two conditions are
    different participants.
    Holds when the claim is supported by the data. Written by someone else."""
    alpha = 0.05
    ctrl = np.asarray(d["score_control"], dtype=float)
    trt = np.asarray(d["score_treatment"], dtype=float)
    if not (np.all(np.isfinite(ctrl)) and np.all(np.isfinite(trt))):
        return None
    n_max = min(ctrl.size, trt.size)
    if n_max < 2:
        return None
    # first look after 10 observations per condition, then after every additional observation, up to the maximum
    sizes = list(range(min(10, n_max), n_max + 1))

    def p_two_sided(t, df):
        # exact two-sided p value of Student's t for integer df (Abramowitz and Stegun 26.7.3 and 26.7.4)
        theta = np.arctan(abs(t) / np.sqrt(df))
        c, s = np.cos(theta), np.sin(theta)
        if df % 2 == 0:
            term, tot = 1.0, 1.0
            for k in range(2, df - 1, 2):
                term *= c * c * (k - 1) / k
                tot += term
            inside = s * tot
        elif df == 1:
            inside = 2.0 * theta / np.pi
        else:
            term, tot = c, c
            for k in range(3, df - 1, 2):
                term *= c * c * (k - 1) / k
                tot += term
            inside = (2.0 / np.pi) * (theta + s * tot)
        return 1.0 - inside

    def pooled_t_test(a, b):
        n1, n2 = a.size, b.size
        pooled = ((n1 - 1) * np.var(a, ddof=1) + (n2 - 1) * np.var(b, ddof=1)) / (n1 + n2 - 2)
        if pooled == 0.0:
            return None
        diff = np.mean(b) - np.mean(a)
        t = diff / np.sqrt(pooled * (1.0 / n1 + 1.0 / n2))
        return diff, p_two_sided(t, n1 + n2 - 2)

    holds = False
    for n in sizes:
        result = pooled_t_test(ctrl[:n], trt[:n])
        if result is None:
            return None
        diff, p = result
        if diff > 0.0 and p < alpha:
            holds = True
    return holds


STUDY = Study(
    name="C20",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect on the score set to 0 (was +7.5 points); score distribution, including the 4% low-effort participants, kept"),
    },
    controls=[
        Control("reassign_conditions", ["C"], transform=_reassign_conditions),
    ],
)
