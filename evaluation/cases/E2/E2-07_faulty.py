"""E2-07: Driven resonator. The strongest detected spectral peak lies at the drive frequency (within 2 %)."""
import numpy as np

from kapi import Control, Criterion, Premise, Study, World

FREQ = np.linspace(1.0, 100.0, 400)    # Hz
F_DRIVE = 30.0
WIDTH = 0.8
FLOOR = 0.5
DETECT = 8.0                            # detection threshold, in units of the median spectrum
REL_TOL = 0.02


def make_world(height):
    def generate(rng):
        line = height / (1.0 + ((FREQ - F_DRIVE) / WIDTH) ** 2)
        return {"f": FREQ.copy(), "A": line + np.abs(rng.normal(0.0, FLOOR, FREQ.size))}
    return generate


def peak_at_drive(d):
    f, A = d["f"], d["A"]
    detected = A > DETECT * np.median(A)
    if not np.any(detected):
        return None
    i = int(np.argmax(np.where(detected, A, -np.inf)))
    return bool(abs(f[i] - F_DRIVE) / F_DRIVE <= REL_TOL)


def frequency_pulling(d, rng):
    return {"f": d["f"], "A": np.interp(d["f"] / 1.05, d["f"], d["A"])}


def scramble_bins(d, rng):
    return {"f": d["f"], "A": rng.permutation(d["A"])}


STUDY = Study(
    name="E2-07 resonance at the drive frequency",
    criteria=[Criterion("peak_at_drive", peak_at_drive, tolerances={"rel": (REL_TOL, 1.0)})],
    worlds={
        "plus": World(make_world(20.0)),
        "minus": World(make_world(0.0), derived_from="plus", change="drive on -> off (line height 20 -> 0)"),
    },
    premises=[Premise("linear_response", frequency_pulling, "tested", ["peak_at_drive"], magnitude=(0.05, 1.0))],
    controls=[Control("bins_scrambled", ["peak_at_drive"], transform=scramble_bins)],
)
