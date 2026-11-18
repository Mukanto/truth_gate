"""D-032: 240 participants each received either a drug or a vehicle, and each was classified as a responder or not. Some participants carry a gene variant. Claim: the drug raises the proportion of responders more in carriers than in non-carriers, that is, the difference between the two drug-minus-vehicle differences in responder proportion (carriers minus non-carriers) is positive, judged by a one-sided test at the 0.05 level."""
import numpy as np
from truth_gate import Study, Criterion, World, Premise, Control

N_PARTICIPANTS = 240
N_DRUG = 120
P_CARRIER = 0.40
P_VEHICLE = 0.30
P_DRUG_NONCARRIER_PLUS = 0.30
P_DRUG_CARRIER_PLUS = 0.60
P_DRUG_BOTH_MINUS = 0.45


def _world(rng, p_drug_noncarrier, p_drug_carrier):
    carrier = rng.uniform(size=N_PARTICIPANTS) < P_CARRIER
    drug = np.zeros(N_PARTICIPANTS, dtype=bool)
    drug[rng.permutation(N_PARTICIPANTS)[:N_DRUG]] = True
    p_drug = np.where(carrier, p_drug_carrier, p_drug_noncarrier)
    p = np.where(drug, p_drug, P_VEHICLE)
    responder = rng.uniform(size=N_PARTICIPANTS) < p
    return {"responder": responder.astype(bool), "drug": drug, "carrier": carrier}


def plus(rng):
    """The claim is true. Returns exactly the brief's data keys, shapes and dtypes."""
    return _world(rng, P_DRUG_NONCARRIER_PLUS, P_DRUG_CARRIER_PLUS)


def minus(rng):
    """The claim is false (fixed rule below). Same keys, shapes and dtypes."""
    return _world(rng, P_DRUG_BOTH_MINUS, P_DRUG_BOTH_MINUS)


def criterion(d):
    """Data keys: responder (240,) bool, True if the participant met the response criterion;
    drug (240,) bool, True if the participant received the drug, False if the vehicle;
    carrier (240,) bool, True if the participant carries the gene variant.
    Holds when the claim is supported by the data. Written by someone else."""
    raise NotImplementedError


def _break(d, rng):
    lab = np.asarray(d["carrier"], dtype=bool)
    new = lab[rng.permutation(lab.size)]
    if np.array_equal(new, lab):
        new = lab.copy()
        i = int(np.argmax(lab))
        j = int(np.argmax(~lab))
        new[i] = lab[j]
        new[j] = lab[i]
    return {"responder": np.array(d["responder"], dtype=bool), "drug": np.array(d["drug"], dtype=bool), "carrier": new}


STUDY = Study(
    name="D-032",
    criteria=[Criterion("C", criterion)],
    worlds={
        "plus": World(plus),
        "minus": World(minus, derived_from="plus", change="the drug-by-carrier interaction is set to 0: the drug effect is 0.15 in both strata (plus: 0.00 in non-carriers, 0.30 in carriers); vehicle rate, carrier frequency and allocation unchanged"),
    },
    controls=[Control("D-032", ["C"], transform=lambda d, rng: _break(d, rng))],
)
