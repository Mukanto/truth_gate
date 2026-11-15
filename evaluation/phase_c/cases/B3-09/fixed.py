"""C04: Across critically ill patients, whole-body oxygen uptake measured by expired-gas analysis is positively correlated with systemic oxygen delivery (cardiac output times arterial oxygen content): the Pearson correlation is at least 0.3."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control


def _gen(rng, rho):
    n = 60
    co = 6.0 * np.exp(rng.normal(0.0, 0.25, n))                 # true cardiac output, L/min
    ca = np.clip(rng.normal(13.5, 2.0, n), 8.0, 20.0)           # true arterial O2 content, mL/dL
    do2 = co * ca * 10.0                                        # true O2 delivery, mL/min
    z = (do2 - do2.mean()) / do2.std()
    vo2 = 240.0 + 40.0 * (rho * z + np.sqrt(1.0 - rho * rho) * rng.normal(0.0, 1.0, n))   # true uptake
    cv = np.maximum(ca - vo2 / (co * 10.0), 1.0)                # venous content follows the Fick relation
    return {
        "cardiac_output": co * (1.0 + 0.10 * rng.normal(0.0, 1.0, n)),       # thermodilution error
        "arterial_o2_content": ca * (1.0 + 0.02 * rng.normal(0.0, 1.0, n)),
        "venous_o2_content": cv * (1.0 + 0.03 * rng.normal(0.0, 1.0, n)),
        "o2_uptake_expired": vo2 * (1.0 + 0.05 * rng.normal(0.0, 1.0, n)),   # independent gas measurement
    }


def plus(rng):
    """The claim is true: true uptake correlates 0.70 with true delivery (about 0.6 between measurements)."""
    return _gen(rng, 0.70)


def minus(rng):
    """The claim is false: uptake does not depend on delivery; measurement errors and Fick relation as in plus."""
    return _gen(rng, 0.0)


def _permute_uptake(d, rng):
    n = d["o2_uptake_expired"].shape[0]
    return {**d, "o2_uptake_expired": d["o2_uptake_expired"][rng.permutation(n)]}


def criterion(d):
    """Data keys: cardiac_output, float (60 patients,), cardiac output by thermodilution in L/min;
    arterial_o2_content, float (60,), arterial blood oxygen content in mL O2 per dL; venous_o2_content,
    float (60,), mixed venous blood oxygen content in mL O2 per dL; o2_uptake_expired, float (60,), whole-body
    oxygen uptake from expired-gas analysis in mL/min.
    Holds when the claim is supported by the data. Written by someone else."""
    co = np.asarray(d["cardiac_output"], dtype=float)
    ca = np.asarray(d["arterial_o2_content"], dtype=float)
    cv = np.asarray(d["venous_o2_content"], dtype=float)
    vo2_expired = np.asarray(d["o2_uptake_expired"], dtype=float)

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

    if not (np.all(np.isfinite(co)) and np.all(np.isfinite(ca)) and np.all(np.isfinite(cv)) and np.all(np.isfinite(vo2_expired))):
        return None
    # correlation between oxygen delivery and the uptake measured by expired-gas analysis
    delivery = co * ca
    r = partial_r(delivery, vo2_expired, [])
    if r is None:
        return None
    return bool(r >= 0.3)


STUDY = Study(
    name="C04",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="dependence of true oxygen uptake on true oxygen delivery set to zero (correlation 0)"),
    },
    controls=[Control("permute_uptake_across_patients", ["C"], transform=_permute_uptake)],
)
