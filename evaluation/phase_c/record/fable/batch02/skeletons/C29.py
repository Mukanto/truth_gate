"""C29: Across the cell lines, the average expression of the probe sets on the published drug-response signature is higher in the cell lines sensitive to the drug than in the resistant cell lines, by at least 0.5 log2 units (Welch two-sample t test on the per-cell-line signature averages, p < .01)."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _permute_changed(x, rng):
    y = rng.permutation(x)
    while np.array_equal(y, x):
        y = rng.permutation(x)
    return y


def _world(rng, signature_shift):
    probes, lines = 1000, 60
    order = rng.permutation(probes)
    on_signature = np.zeros(probes, dtype=bool)
    on_signature[order[:50]] = True                           # 50 probe sets on the published list
    other_de = np.zeros(probes, dtype=bool)
    other_de[order[50:90]] = True                             # 40 other probe sets that differ by sensitivity
    sensitive = np.zeros(lines, dtype=bool)
    sensitive[rng.permutation(lines)[:25]] = True             # 25 sensitive, 35 resistant
    probe_level = rng.normal(8.0, 1.5, probes)
    array_offset = rng.normal(0.0, 0.15, lines)               # residual array-wide (normalisation) effect
    module = rng.normal(0.0, 0.30, lines)                     # co-regulation of the signature genes
    noise = rng.normal(0.0, 0.6, (probes, lines))
    sig_effect = signature_shift * rng.normal(1.0, 0.375, probes) * on_signature
    other_effect = rng.normal(0.0, 0.8, probes) * other_de    # either direction, same in both worlds
    expression = (
        probe_level[:, None]
        + array_offset[None, :]
        + on_signature[:, None] * module[None, :]
        + (sig_effect + other_effect)[:, None] * sensitive[None, :]
        + noise
    )
    return {"expression": expression.astype(np.float64), "on_signature": on_signature, "sensitive": sensitive}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, 0.8)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, 0.0)


def criterion(d):
    """Data keys: expression (1000, 60) float, log2 expression of each microarray probe set (axis 0) in each cell
    line (axis 1); on_signature (1000,) bool, True if the probe set is on the published drug-response signature
    list; sensitive (60,) bool, True if the cell line is classed as sensitive to the drug, False if resistant.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C29",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="difference of the signature probe sets between sensitive and resistant cell lines set to 0 (was +0.8 log2 on average); co-regulation of the signature, array effects, the 40 other sensitivity-related probe sets and noise kept"),
    },
    controls=[
        Control("permute_sensitive_across_cell_lines", ["C"], transform=lambda d, rng: {**d, "sensitive": _permute_changed(d["sensitive"], rng)}),
        Control("random_signature_same_size", ["C"], transform=lambda d, rng: {**d, "on_signature": _permute_changed(d["on_signature"], rng)}),
    ],
)
