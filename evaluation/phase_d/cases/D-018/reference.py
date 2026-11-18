"""D-018: Sensor measurements classify the disease status of newly recruited subjects: the area under the ROC curve of the classification is at least 0.70."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

S = 16
R = 60
V = 10
ICC = 0.30
LINK = (0.8, 0.0, 0.8, 0.7, 0.0, 0.0, 0.7, 0.0, 0.7, 0.0)
SGN = (1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0, 1.0, 1.0)
PHI = 0.70
VAR_AR = 0.20
VAR_SH = 0.15
VAR_W = 0.35


def gen(rng):
    """Subject effects (share ICC of each variable's variance) of which the LINK variables carry the subject's
    disease status with correlation LINK; within subject: AR(1) drift over the records, a shared record factor
    and white measurement error. Half of the subjects are diseased."""
    lab = np.zeros(S, dtype=bool)
    lab[:S // 2] = True
    lab = lab[rng.permutation(S)]
    a = 2.0 * lab.astype(float) - 1.0
    link = np.array(LINK)
    sg = np.array(SGN)
    u = rng.normal(size=(S, V))
    u = link * sg * a[:, None] + np.sqrt(1.0 - link ** 2) * u
    z = rng.normal(size=(S, R, V))
    ar = np.empty((S, R, V))
    ar[:, 0] = z[:, 0]
    for t in range(1, R):
        ar[:, t] = PHI * ar[:, t - 1] + np.sqrt(1.0 - PHI ** 2) * z[:, t]
    q = rng.normal(size=(S, R, 1))
    white = rng.normal(size=(S, R, V))
    within = np.sqrt(VAR_AR) * ar + np.sqrt(VAR_SH) * q * sg + np.sqrt(VAR_W) * white
    col = np.arange(V)
    x = 1.5 * np.sin(1.3 * col) + (1.0 + 0.3 * np.cos(2.1 * col)) * (np.sqrt(ICC) * u[:, None, :] + within)
    other = lab[rng.permutation(S)]
    return x, lab, other


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    x, lab, _ = gen(rng)
    return {"measurements": x, "diseased": lab}


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    x, _, lab = gen(rng)
    return {"measurements": x, "diseased": lab}


def control(d, rng):
    """Permutes the disease status across the subjects."""
    out = {k: np.array(v) for k, v in d.items()}
    old = d["diseased"]
    new = old
    for _ in range(50):
        new = old[rng.permutation(S)]
        if not np.array_equal(new, old):
            break
    out["diseased"] = new
    return out


def criterion(d):
    """Data keys: measurements (subjects, records, variables) float64: sensor measurements of each recording of each subject; diseased (subjects,) bool: True if the subject has the disease.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


STUDY = Study(
    name="D-018",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the disease status is replaced by that of other subjects (independent of the measurements); half diseased, subject effects and all distributions unchanged"),
    },
    controls=[Control("D-018", ["C"], transform=control)],
)
