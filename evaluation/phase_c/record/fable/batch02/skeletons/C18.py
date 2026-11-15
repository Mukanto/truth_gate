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
    raise NotImplementedError


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
