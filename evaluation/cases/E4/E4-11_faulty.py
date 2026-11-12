"""E4-11: Observational cohort. Treatment improves the outcome given baseline severity (one-sided t test on the treatment coefficient, declared alpha 0.05)."""
import numpy as np

from kapi import Control, Criterion, Study, Targets, World

N = 200
EFFECT = 0.3
SEVERITY_ON_TREAT = -1.5    # healthier patients are treated more often
SEVERITY_ON_Y = -1.0
ALPHA = 0.05
T_CRIT = 1.6527             # one-sided t quantile, df = 197


def make_world(effect):
    def generate(rng):
        s = rng.normal(0.0, 1.0, N)
        treat = (rng.random(N) < 1.0 / (1.0 + np.exp(-SEVERITY_ON_TREAT * s))).astype(float)
        y = effect * treat + SEVERITY_ON_Y * s + rng.normal(0.0, 1.0, N)
        y_nc = SEVERITY_ON_Y * s + rng.normal(0.0, 1.0, N)          # negative-control outcome
        return {"severity": s, "treat": treat, "y": y, "y_nc": y_nc}
    return generate


def treat_t(y, columns):
    X = np.column_stack([np.ones_like(y)] + columns)
    with np.errstate(all="ignore"):
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        resid = y - X @ beta
        s2 = resid @ resid / (y.size - X.shape[1])
        cov = s2 * np.linalg.pinv(X.T @ X)
        return beta[1] / np.sqrt(cov[1, 1])


def treatment_helps(d):
    return bool(treat_t(d["y"], [d["treat"]]) > T_CRIT)


def negative_control_outcome(d, rng):
    out = dict(d)
    out["y"] = d["y_nc"]
    return out


STUDY = Study(
    name="E4-11 observational treatment effect",
    criteria=[Criterion("treatment_helps", treatment_helps)],
    worlds={
        "plus": World(make_world(EFFECT)),
        "minus": World(make_world(0.0), derived_from="plus", change="treatment effect 0.3 -> 0 (assignment unchanged)"),
    },
    controls=[Control("negative_control_outcome", ["treatment_helps"], transform=negative_control_outcome)],
    targets=Targets(size=ALPHA),
)
