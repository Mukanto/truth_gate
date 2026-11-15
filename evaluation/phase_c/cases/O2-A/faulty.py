"""C18: Participants in the treatment condition report higher liking of the product than participants in the control condition: the difference in mean liking is positive and a two-sided two-sample t test (equal variances assumed) gives p < .05."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _group(rng, n, liking_shift, wtp_log_shift):
    positivity = rng.normal(0.0, 1.0, n)   # participant trait shared by both ratings
    e_like = rng.normal(0.0, 1.0, n)
    e_wtp = rng.normal(0.0, 1.0, n)
    # liking on a 0-100 slider
    liking = 50.0 + liking_shift + 15.0 * (0.6 * positivity + 0.8 * e_like)
    liking = np.round(np.clip(liking, 0.0, 100.0))
    # willingness to pay in currency units, right-skewed
    wtp = np.exp(np.log(8.0) + wtp_log_shift + 0.5 * (0.5 * positivity + np.sqrt(0.75) * e_wtp))
    wtp = np.round(wtp, 2)
    return liking.astype(np.float64), wtp.astype(np.float64)


def _world(rng, liking_effect):
    n = 20
    liking_c, wtp_c = _group(rng, n, 0.0, 0.0)
    # the treatment's own effect on willingness to pay (0.25 log units) is not what the claim is about and is
    # the same in both worlds
    liking_t, wtp_t = _group(rng, n, liking_effect, 0.25)
    return {
        "liking_control": liking_c,
        "liking_treatment": liking_t,
        "willingness_to_pay_control": wtp_c,
        "willingness_to_pay_treatment": wtp_t,
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 16.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def _reassign_conditions(d, rng):
    # participants (each with both of their ratings) are re-dealt at random to the two conditions
    n = d["liking_control"].shape[0]
    liking = np.concatenate([d["liking_control"], d["liking_treatment"]])
    wtp = np.concatenate([d["willingness_to_pay_control"], d["willingness_to_pay_treatment"]])
    idx = rng.permutation(2 * n)
    while np.array_equal(liking[idx], liking) and np.array_equal(wtp[idx], wtp):
        idx = rng.permutation(2 * n)
    return {
        **d,
        "liking_control": liking[idx[:n]],
        "liking_treatment": liking[idx[n:]],
        "willingness_to_pay_control": wtp[idx[:n]],
        "willingness_to_pay_treatment": wtp[idx[n:]],
    }


def criterion(d):
    """Data keys: liking_control (20,) float, liking of the product (0-100) reported by each control participant;
    liking_treatment (20,) float, the same for each treatment participant; willingness_to_pay_control (20,) float,
    willingness to pay reported by each control participant; willingness_to_pay_treatment (20,) float, the same
    for each treatment participant. The two conditions are different participants.
    Holds when the claim is supported by the data. Written by someone else."""
    alpha = 0.05
    like_c = np.asarray(d["liking_control"], dtype=float)
    like_t = np.asarray(d["liking_treatment"], dtype=float)
    wtp_c = np.asarray(d["willingness_to_pay_control"], dtype=float)
    wtp_t = np.asarray(d["willingness_to_pay_treatment"], dtype=float)
    # three tests: liking, willingness to pay, and the raw average of the two measures
    comparisons = [(like_c, like_t), (wtp_c, wtp_t), ((like_c + wtp_c) / 2.0, (like_t + wtp_t) / 2.0)]
    for a, b in comparisons:
        if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
            return None
        if a.size < 2 or b.size < 2:
            return None

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
    for a, b in comparisons:
        result = pooled_t_test(a, b)
        if result is None:
            return None
        diff, p = result
        if diff > 0.0 and p < alpha:
            holds = True
    return holds


STUDY = Study(
    name="C18",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="treatment effect on liking set to 0 (was +16 points on the 0-100 scale); willingness to pay, including its own treatment effect, kept"),
    },
    controls=[
        Control("reassign_conditions", ["C"], transform=_reassign_conditions),
    ],
)
