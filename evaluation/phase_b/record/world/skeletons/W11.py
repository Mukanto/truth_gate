"""W11: Firms with a larger payroll have lower staff turnover rates: across 250 firms, the proportion of variance in the annual turnover rate (leavers per employee) explained by the payroll (R squared of a simple linear regression) is at least 0.1."""
import numpy as np
from kapi import Study, Criterion, World, Premise, Control

N = 250


def _gen(rng, eff):
    lh = np.log(80.0) + 0.9 * rng.standard_normal(N)
    hc = np.maximum(np.round(np.exp(lh)), 5.0)                   # average headcount
    zl = (lh - np.log(80.0)) / 0.9
    wage = np.exp(np.log(0.05) + 0.25 * rng.standard_normal(N))  # millions per employee
    payroll = hc * wage
    rate = 0.17 * np.exp(-eff * 0.6 * zl + 0.25 * rng.standard_normal(N))   # true turnover rate
    leavers = rng.poisson(rate * hc).astype(float)
    return {"leavers": leavers, "headcount": hc, "payroll": payroll}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 1.0)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: leavers (250,) number of employees who left the firm during the year; headcount (250,) average number
    of employees during the year; payroll (250,) total annual payroll, millions of currency units.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_payroll(d, rng):
    return {**d, "payroll": d["payroll"][rng.permutation(N)]}


STUDY = Study(
    name="W11",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="true turnover rate falls with firm size (-0.6 log units per sd of log headcount) -> true rate independent of size; headcount and wage spread, firm heterogeneity and Poisson leaver counts (small firms noisy) unchanged"),
    },
    controls=[Control("permute_payroll", ["C"], transform=permute_payroll)],
)
