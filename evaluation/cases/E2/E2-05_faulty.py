"""E2-05: Stimulus-response coupling. The response tracks the stimulus: Pearson r > 0.5 over 50 trials."""
import numpy as np

from kapi import Control, Criterion, Study, World

N = 50
COUPLING = 1.0
R_MIN = 0.5


def make_world(coupling=COUPLING):
    def generate(rng):
        x = rng.normal(0.0, 1.0, N)
        y = COUPLING * x + rng.normal(0.0, 1.0, N)
        return {"x": x, "y": y}
    return generate


def correlated(d):
    x = d["x"] - d["x"].mean()
    y = d["y"] - d["y"].mean()
    with np.errstate(all="ignore"):
        r = np.sum(x * y) / np.sqrt(np.sum(x * x) * np.sum(y * y))
    return bool(r > R_MIN)


def shuffle_response(d, rng):
    return {"x": d["x"], "y": rng.permutation(d["y"])}


STUDY = Study(
    name="E2-05 stimulus-response coupling",
    criteria=[Criterion("correlated", correlated, tolerances={"r_min": (R_MIN, 1.0)})],
    worlds={
        "plus": World(make_world()),
        "minus": World(make_world(coupling=0.0), derived_from="plus", change="coupling 1.0 -> 0"),
    },
    controls=[Control("response_shuffled", ["correlated"], transform=shuffle_response)],
    relational=[("x", "y")],
)
