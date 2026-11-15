"""C30: In adults with hypertension, the fall in systolic pressure over a 12-week programme is larger in patients with a higher starting pressure: the correlation, across patients, between the fall (first baseline reading minus week-12 reading) and the second baseline reading is at least 0.3."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, fall_depends_on_start):
    n = 120
    usual = rng.normal(0.0, 12.0, n)            # usual systolic pressure of the patient, around 155 mmHg
    unrelated = rng.normal(0.0, 12.0, n)        # a patient variable with the same spread, unrelated to pressure
    visit0 = rng.normal(0.0, 3.0, n)            # day-level deviation shared by the two baseline readings
    read1 = rng.normal(0.0, 6.0, n)             # reading-to-reading variability and measurement error
    read2 = rng.normal(0.0, 6.0, n)
    visit12 = rng.normal(0.0, 3.0, n)
    read12 = rng.normal(0.0, 6.0, n)
    response = rng.normal(0.0, 6.0, n)          # individual response to the programme
    source = usual if fall_depends_on_start else unrelated
    true_fall = 10.0 + 0.45 * source + response
    first = 155.0 + usual + visit0 + read1
    second = 155.0 + usual + visit0 + read2
    week12 = 155.0 + usual - true_fall + visit12 + read12
    return {
        "sbp_baseline_first": first.astype(np.float64),
        "sbp_baseline_second": second.astype(np.float64),
        "sbp_week12": week12.astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, False)


def criterion(d):
    """Data keys: sbp_baseline_first (120,) float, systolic blood pressure, first reading at the baseline visit,
    mmHg; sbp_baseline_second (120,) float, second reading at the baseline visit, mmHg; sbp_week12 (120,) float,
    systolic blood pressure at the week-12 visit, mmHg. The three arrays are aligned by patient.
    Holds when the claim is supported by the data. Written by someone else."""
    first = np.asarray(d["sbp_baseline_first"], dtype=float)
    second = np.asarray(d["sbp_baseline_second"], dtype=float)
    week12 = np.asarray(d["sbp_week12"], dtype=float)

    def partial_r(x, y, covs):
        n = x.shape[0]
        Z = np.column_stack([np.ones(n)] + list(covs))
        if n < Z.shape[1] + 2:
            return None
        rx = x - Z @ np.linalg.lstsq(Z, x, rcond=None)[0]
        ry = y - Z @ np.linalg.lstsq(Z, y, rcond=None)[0]
        sx = float(rx @ rx)
        sy = float(ry @ ry)
        cx = float(np.sum((x - x.mean()) ** 2))
        cy = float(np.sum((y - y.mean()) ** 2))
        if not (cx > 0.0 and cy > 0.0) or sx <= 1e-12 * cx or sy <= 1e-12 * cy:
            return None
        r = float(rx @ ry) / np.sqrt(sx * sy)
        return r if np.isfinite(r) else None

    if not (np.all(np.isfinite(first)) and np.all(np.isfinite(second)) and np.all(np.isfinite(week12))):
        return None
    # correlation between the fall (first baseline reading minus week-12 reading) and the first baseline reading
    fall = first - week12
    r = partial_r(fall, first, [])
    if r is None:
        return None
    return bool(r >= 0.3)


STUDY = Study(
    name="C30",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="dependence of the true fall on the starting pressure set to 0 (was 0.45 mmHg of fall per mmHg of usual pressure): the same term of the fall now comes from a patient variable independent of pressure; mean fall, spread of falls, reading and visit variability kept"),
    },
    controls=[
        Control("permute_second_baseline_across_patients", ["C"], transform=lambda d, rng: {**d, "sbp_baseline_second": _permute_changed(d["sbp_baseline_second"], rng)}),
    ],
)
