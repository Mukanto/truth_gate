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
    raise NotImplementedError


STUDY = Study(
    name="C08",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="difference between the task effects of region A and region B set to zero (both 0.30, their plus average)"),
    },
    controls=[Control("swap_region_labels_in_half_the_subjects", ["C"], transform=_swap_regions)],
)
