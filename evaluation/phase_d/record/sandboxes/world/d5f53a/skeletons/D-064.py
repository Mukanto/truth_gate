"""D-064: Expression profiles together with clinical covariates predict tumour response in new patients: the Pearson correlation between predicted and observed response is at least 0.30."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PAT = 80
N_GENES = 1500
N_COV = 8
N_MOD = 8
GENES_PER_MOD = 125                       # genes 0..999 belong to 8 modules, genes 1000..1499 to none
N_BATCH = 4
BATCH_SD = 0.2                            # batch shift per gene (log2)
OFFSET_SD = 0.1                           # per-sample normalisation offset (log2)
MODULE_OF_GENE = np.concatenate([np.repeat(np.arange(N_MOD), GENES_PER_MOD),
                                 np.zeros(N_GENES - N_MOD * GENES_PER_MOD, dtype=int)])
IN_MODULE = np.arange(N_GENES) < N_MOD * GENES_PER_MOD
# response signal = 0.45 proliferation + 0.40 immune - 0.30 tumour size - 0.15 performance status (latent scale)
W_PROLIF = 0.45
W_IMMUNE = 0.40
W_SIZE = -0.30
W_ECOG = -0.15
COV_PROLIF_SIZE = 0.5 * 0.45
SIGNAL_VAR = (W_PROLIF ** 2 + W_IMMUNE ** 2 + W_SIZE ** 2 + W_ECOG ** 2
              + 2.0 * W_PROLIF * W_SIZE * COV_PROLIF_SIZE)
R_SIGNAL = 0.6                            # correlation of response with its full latent signal (oracle)
RESP_MEAN = 30.0                          # mean percentage shrinkage
RESP_SD = 25.0


def _latents(rng, n):
    aggr = rng.standard_normal(n)                                  # latent tumour aggressiveness
    f = rng.standard_normal((n, N_MOD))                            # module scores
    f[:, 0] = 0.5 * aggr + np.sqrt(0.75) * f[:, 0]                 # proliferation follows aggressiveness
    f[:, 2] = 0.4 * f[:, 1] + np.sqrt(0.84) * f[:, 2]              # stromal co-varies with immune
    e = rng.standard_normal((n, 7))
    size = 0.45 * aggr + np.sqrt(1.0 - 0.45 ** 2) * e[:, 0]
    stage = 0.60 * aggr + 0.80 * e[:, 1]
    grade = 0.55 * aggr + np.sqrt(1.0 - 0.55 ** 2) * e[:, 2]
    nodal = 0.50 * aggr + np.sqrt(0.75) * e[:, 3]
    age = e[:, 4]
    ecog = 0.3 * age + np.sqrt(0.91) * e[:, 5]
    albumin = -0.3 * ecog + np.sqrt(0.91) * e[:, 6]
    female = rng.random(n) < 0.5
    signal = W_PROLIF * f[:, 0] + W_IMMUNE * f[:, 1] + W_SIZE * size + W_ECOG * ecog
    return {"f": f, "size": size, "stage": stage, "grade": grade, "nodal": nodal, "age": age,
            "ecog": ecog, "albumin": albumin, "female": female, "signal": signal / np.sqrt(SIGNAL_VAR)}


def _clinical(lat):
    raw = np.column_stack([
        62.0 + 10.0 * lat["age"],                                              # age (years)
        np.exp(np.log(32.0) + 0.5 * lat["size"]),                              # tumour size (mm)
        1.0 + (lat["grade"] > -0.4) + (lat["grade"] > 0.8),                    # grade 1-3
        1.0 + (lat["stage"] > -0.6) + (lat["stage"] > 0.3) + (lat["stage"] > 1.1),  # stage 1-4
        (lat["nodal"] > 0.3).astype(np.float64),                               # nodal involvement
        (lat["ecog"] > 0.6).astype(np.float64) + (lat["ecog"] > 1.6),          # performance status 0-2
        lat["female"].astype(np.float64),                                      # sex
        40.0 + 4.0 * lat["albumin"],                                           # albumin (g/L)
    ]).astype(np.float64)
    mean = raw.mean(axis=0)
    sd = raw.std(axis=0)
    return (raw - mean) / np.where(sd > 0, sd, 1.0)


def _generate(rng, use_copy):
    lat = _latents(rng, N_PAT)
    lat_copy = _latents(rng, N_PAT)                                # independent patients from the same population
    mu = rng.uniform(3.0, 12.0, N_GENES)
    gsd = rng.uniform(0.3, 1.2, N_GENES)
    load = np.where(IN_MODULE, rng.uniform(0.35, 0.8, N_GENES), 0.0)
    sign = np.where(rng.random(N_GENES) < 0.8, 1.0, -1.0)
    batch = rng.permutation(np.repeat(np.arange(N_BATCH), N_PAT // N_BATCH))
    batch_eff = BATCH_SD * rng.standard_normal((N_BATCH, N_GENES))
    offset = OFFSET_SD * rng.standard_normal(N_PAT)
    eps = rng.standard_normal((N_PAT, N_GENES))
    expr = (mu + gsd * (sign * load * lat["f"][:, MODULE_OF_GENE] + np.sqrt(1.0 - load ** 2) * eps)
            + batch_eff[batch] + offset[:, None])
    noise = rng.standard_normal(N_PAT)
    signal = lat_copy["signal"] if use_copy else lat["signal"]
    response = RESP_MEAN + RESP_SD * (R_SIGNAL * signal + np.sqrt(1.0 - R_SIGNAL ** 2) * noise)
    response = np.clip(response, -50.0, 100.0)
    return {
        "expression": np.asarray(expr, dtype=np.float64),
        "clinical": np.asarray(_clinical(lat), dtype=np.float64),
        "response": np.asarray(response, dtype=np.float64),
    }


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes.

    Response depends on a proliferation module and an immune module (each 125 genes, plus correlated modules) and
    on tumour size and performance status; the full latent signal has correlation 0.6 with response. Genes form
    8 co-expression modules, with batch and per-sample offsets; clinical covariates share a latent aggressiveness
    factor with the proliferation module."""
    return _generate(rng, False)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes.

    Response's signal part belongs to independent patients from the same population, so neither expression nor
    clinical covariates carry information about response; all marginal distributions and the expression-clinical
    structure are as in plus."""
    return _generate(rng, True)


def criterion(d):
    """Data keys: expression (80, 1500) float, log2 expression of gene g in patient i's tumour sample;
    clinical (80, 8) float, standardised clinical covariates of patient i (columns: age, tumour size, grade, stage,
    nodal involvement, performance status, sex, albumin; each column z-scored in the sample); response (80,) float,
    percentage tumour shrinkage of patient i after treatment (at most 100). Rows of all three keys are the same
    patients.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _permute_response(d, rng):
    resp = d["response"]
    order = rng.permutation(resp.shape[0])
    if np.array_equal(order, np.arange(resp.shape[0])):
        order = np.roll(order, 1)
    return {**d, "response": resp[order]}


STUDY = Study(
    name="D-064",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus",
                       change="predictive link (expression, clinical) -> response set to none: response's signal part comes from independent patients (same distribution)"),
    },
    controls=[Control("response_permuted_across_patients", ["C"], transform=_permute_response)],
    relational=[("expression", "response")],
)
