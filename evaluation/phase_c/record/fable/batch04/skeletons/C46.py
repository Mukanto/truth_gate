"""C46: In a symptom checklist of eight items, the score on item 1 identifies patients with a high total on items 2 to 8: the AUC of the item 1 score for patients whose total over items 2 to 8 is at least 12, against all other patients, is at least 0.65."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PATIENTS = 300
N_ITEMS = 8
# Loading of each item on the common symptom-severity factor (item 1 first).
LOADINGS = np.array([0.66, 0.70, 0.62, 0.72, 0.58, 0.68, 0.64, 0.60])
# Cut points on the latent item response for scoring 1, 2 and 3 points; one row per item.
CUTS = np.array([
    [-0.70, 0.20, 1.10],
    [-0.80, 0.10, 1.00],
    [-0.60, 0.30, 1.20],
    [-0.75, 0.20, 1.05],
    [-0.65, 0.25, 1.15],
    [-0.70, 0.15, 1.10],
    [-0.60, 0.30, 1.25],
    [-0.75, 0.20, 1.10],
])


def _generate(rng, item1_shares_factor):
    severity = rng.normal(size=(N_PATIENTS, 1))
    unique = rng.normal(size=(N_PATIENTS, N_ITEMS))
    unrelated = rng.normal(size=N_PATIENTS)
    factor = np.repeat(severity, N_ITEMS, axis=1)
    if not item1_shares_factor:
        factor[:, 0] = unrelated
    response = factor * LOADINGS + np.sqrt(1.0 - LOADINGS ** 2) * unique
    points = (response[:, :, None] > CUTS[None, :, :]).sum(axis=2)
    return {"item_scores": points.astype(np.float64)}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _generate(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _generate(rng, False)


def permute_item1(d, rng):
    scores = d["item_scores"].copy()
    scores[:, 0] = scores[rng.permutation(scores.shape[0]), 0]
    return {**d, "item_scores": scores}


def criterion(d):
    """Data keys: item_scores, float array of shape (300, 8) = (patients, items): points (0 to 3) scored by each
    patient on each of the eight checklist items; columns are in checklist order, item 1 first (column 0).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C46",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="item 1 no longer loads on the severity factor shared by items 2 to 8: its score is unrelated to the total over items 2 to 8 (same item 1 score distribution, items 2 to 8 unchanged)"),
    },
    controls=[Control("permute_item1_across_patients", ["C"], transform=permute_item1)],
)
