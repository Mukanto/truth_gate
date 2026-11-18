"""D-071: Across patients, oxygen delivery and oxygen consumption are positively correlated: the Pearson correlation coefficient between them is at least 0.4."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 120
CO_MEDIAN = 5.4
CO_TRUE_SD = 0.225
CO_ERR_SD = 0.15
CA_MEDIAN = 17.0
CA_TRUE_SD = 0.1367
CA_ERR_SD = 0.03
CO_CA_CORR = -0.12
VO2_MEDIAN = 250.0
VO2_TRUE_SD = 0.205
VO2_ERR_SD = 0.08
CV_ASSAY_SD = 0.3


def _gen(rng, rho):
    z1 = rng.standard_normal(N_PAT)
    z2 = rng.standard_normal(N_PAT)
    co_true = CO_MEDIAN * np.exp(CO_TRUE_SD * z1)
    ca_true = CA_MEDIAN * np.exp(CA_TRUE_SD * (CO_CA_CORR * z1 + np.sqrt(1.0 - CO_CA_CORR ** 2) * z2))
    co_obs = co_true * np.exp(CO_ERR_SD * rng.standard_normal(N_PAT))
    ca_obs = ca_true * np.exp(CA_ERR_SD * rng.standard_normal(N_PAT))
    ldo = np.log(co_true * ca_true)
    zdo = (ldo - ldo.mean()) / ldo.std()
    eps = rng.standard_normal(N_PAT)
    vo2_true = VO2_MEDIAN * np.exp(VO2_TRUE_SD * (rho * zdo + np.sqrt(1.0 - rho ** 2) * eps))
    cv_true = ca_true - vo2_true / (10.0 * co_true)
    cv_obs = np.maximum(cv_true + CV_ASSAY_SD * rng.standard_normal(N_PAT), 2.0)
    vo2_obs = vo2_true * np.exp(VO2_ERR_SD * rng.standard_normal(N_PAT))
    return {
        "cardiac_output": np.asarray(co_obs, dtype=float),
        "arterial_o2_content": np.asarray(ca_obs, dtype=float),
        "venous_o2_content": np.asarray(cv_obs, dtype=float),
        "vo2_expired_gas": np.asarray(vo2_obs, dtype=float),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _gen(rng, 0.75)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _gen(rng, 0.0)


def criterion(d):
    """Data keys: cardiac_output (120,) float, L/min;
    arterial_o2_content (120,) float, mL O2 per dL of arterial blood;
    venous_o2_content (120,) float, mL O2 per dL of mixed venous blood;
    vo2_expired_gas (120,) float, oxygen consumption from expired-gas analysis, mL/min.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def permute_vo2(d, rng):
    out = {k: np.asarray(v, dtype=float) for k, v in d.items()}
    perm = rng.permutation(out["vo2_expired_gas"].shape[0])
    out["vo2_expired_gas"] = out["vo2_expired_gas"][perm]
    return out


STUDY = Study(
    name="D-071",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="correlation between log true oxygen delivery and log true oxygen consumption set from 0.75 to 0 (consumption variance kept)"),
    },
    controls=[Control("permute_vo2", ["C"], transform=permute_vo2)],
)
