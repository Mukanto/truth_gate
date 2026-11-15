"""C21: A classifier built from the 50 sensor features separates defective units from sound units with a balanced accuracy (mean of sensitivity and specificity) of at least 0.65 on new units."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

# fixed properties of the 50 features (the same features in every dataset): units and offsets
_SCALE = 0.5 * 2.0 ** (np.arange(50) % 6)
_OFFSET = 10.0 * (np.arange(50) % 4)
# shift of the defective units, in within-class standard deviations, on six features of three sensor channels
_SHIFT = 0.67 * (np.isin(np.arange(50), [3, 7, 14]) * 1.0 - np.isin(np.arange(50), [18, 31, 36]) * 1.0)


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, informative):
    units, features = 1000, 50
    defective = rng.random(units) < 0.15                     # about 15% defective
    channel = rng.normal(0.0, 1.0, (units, 5))               # five sensor channels, ten features each
    x = np.sqrt(0.4) * np.repeat(channel, 10, axis=1) + np.sqrt(0.6) * rng.normal(0.0, 1.0, (units, features))
    x = x + informative * _SHIFT[None, :] * defective[:, None]
    x = x * _SCALE[None, :] + _OFFSET[None, :]
    return {"sensor_features": x.astype(np.float64), "defective": defective}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: sensor_features (1000, 50) float, 50 features (axis 1) computed from the sensor recording of
    each unit (axis 0); defective (1000,) bool, True when the unit is defective.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C21",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the features carry no information about the defect: the shift of defective units on the six informative features set to 0 (was 0.67 SD each, Mahalanobis distance 2); defect rate, feature correlations and scales kept"),
    },
    controls=[
        Control("permute_defective_across_units", ["C"], transform=lambda d, rng: {**d, "defective": _permute_changed(d["defective"], rng)}),
    ],
)
