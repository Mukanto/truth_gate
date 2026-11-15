"""C43: In women treated for osteoporosis, first-year responders keep gaining more bone than first-year non-responders: women whose bone mineral density rose over the first year (from the start of treatment to the first 12-month scan) gain at least 0.5 percentage points more over the second year (percentage change from the second 12-month scan to the 24-month scan) than women whose density fell over the first year, and a one-sided Welch t test of that difference between the two groups of women is significant at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_WOMEN = 600
BMD_MEAN = 0.72        # g/cm2 at the start of treatment
BMD_SD = 0.09
YEAR1_MEAN = 2.5       # true percentage change over the first year
YEAR1_SD = 2.5
YEAR2_MEAN = 1.0       # true percentage change over the second year
CARRY = 0.4            # percentage points of second-year change per point of first-year change
YEAR2_OWN_SD = 1.0     # second-year variation unrelated to the first year
SCAN_CV = 0.015        # precision error of a single scan (relative)


def _scan(rng, true_bmd):
    return true_bmd * (1.0 + rng.normal(0.0, SCAN_CV, true_bmd.shape))


def _cohort(rng, carried):
    start = np.clip(rng.normal(BMD_MEAN, BMD_SD, N_WOMEN), 0.45, None)
    year1 = rng.normal(YEAR1_MEAN, YEAR1_SD, N_WOMEN)
    unrelated = rng.normal(YEAR1_MEAN, YEAR1_SD, N_WOMEN)
    source = year1 if carried else unrelated
    year2 = YEAR2_MEAN + CARRY * (source - YEAR1_MEAN) + rng.normal(0.0, YEAR2_OWN_SD, N_WOMEN)
    month12 = start * (1.0 + year1 / 100.0)
    month24 = month12 * (1.0 + year2 / 100.0)
    return {
        "bmd_start": _scan(rng, start).astype(np.float64),
        "bmd_m12_scan1": _scan(rng, month12).astype(np.float64),
        "bmd_m12_scan2": _scan(rng, month12).astype(np.float64),
        "bmd_m24": _scan(rng, month24).astype(np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _cohort(rng, True)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _cohort(rng, False)


def _reassign_second_year(d, rng):
    # each woman's second-year record (second 12-month scan and 24-month scan, kept together) goes to another woman
    order = rng.permutation(N_WOMEN)
    return {**d, "bmd_m12_scan2": d["bmd_m12_scan2"][order], "bmd_m24": d["bmd_m24"][order]}


def criterion(d):
    """Data keys: bmd_start, float (600,), bone mineral density of each woman at the start of treatment (g/cm2);
    bmd_m12_scan1, float (600,), bone mineral density at the 12-month visit, first of two scans taken at that visit
    (g/cm2); bmd_m12_scan2, float (600,), bone mineral density at the 12-month visit, second of two scans taken at
    that visit (g/cm2); bmd_m24, float (600,), bone mineral density at the 24-month visit (g/cm2).
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="C43",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the dependence of a woman's true second-year change on her true first-year change is set to 0 (second-year changes keep their mean and variance)"),
    },
    controls=[Control("reassign_second_year_records", ["C"], transform=_reassign_second_year)],
)
