"""``truth-gate explain FLAG``: what a flag or study note means, what usually causes it, and the protocol rule behind it
(spec 0.6, section 9).

The *kind* of a name (mandatory, capping, info, study-level, ...) is read from the flag tables of ``checks.py`` and
``external.py``, never repeated here.  The texts are ours; the rule numbers refer to ``protocol/PROTOCOL.md``
(``§1.5`` is rule 5 of section 1, "Before the run").
"""

from __future__ import annotations

from typing import Optional

from . import checks
from .external import NOTE_DIED, NOTE_UNGUARDED
from .k8 import FLAG_INCONCLUSIVE, FLAG_NOT_INVARIANT, FLAG_SOME_CHANGES
from .minus import FLAG_IDENTICAL, FLAG_UNREAD
from .passes import SUGGESTED_UNREVIEWED

NOTES = (NOTE_UNGUARDED, NOTE_DIED)
FAMILIES = ("HIGH_RATE:", "K5_INCONCLUSIVE:", "K1_ABSTAINED:", "K1_ABSTAINED_MAJORITY:")  # a flag name is the prefix plus the stream or probe name

# name -> (meaning, usual cause, protocol rule)
EXPLANATIONS: dict = {
    "K1_UNDEFINED": (
        "The component's verdict is UNDEFINED. Two causes, and the certificate shows which: (1) a failure: an outcome on "
        "the plus, minus or null world was UNDEFINED because something went wrong (`counts` has hard_undefined > 0 on one "
        "of these streams); (2) the criterion abstained (returned UNDEFINED itself) on more than half of the plus samples, "
        "so it is not a test of the claim in the world where the claim is true (hard_undefined is 0 and "
        "2 * (undefined - hard_undefined) > n on world:plus).",
        "(1) The criterion raised an exception (a pattern's missing key included), a world failed to generate data, the "
        "criterion returned something other than a bool or None (a NaN, a number, a string), a declared component is "
        "missing from the returned dict, or a command program answered an error, timed out or died. "
        "(2) A guard that returns None on most plus samples (an empty selection, a threshold the plus data rarely reach). "
        "A deliberate None on at most half of the plus samples is not a cause: see K1_ABSTAINED.",
        "§1.10 (smoke test: the criterion must be defined on synthetic input) and §1.3 (the pre-registration says what "
        "UNDEFINED means).",
    ),
    "K1_ABSTAINED:": (
        "Information only: the criterion returned UNDEFINED itself (None, a pattern's UNDEFINED, a command's UNDEFINED) on "
        "some samples of the stream named after the colon (world:plus, world:minus or world:null). It counts as no claim "
        "(not as HOLDS) and does not make the verdict UNDEFINED.",
        "A guard in the criterion (`if selection.size == 0: return None`), or a pattern whose selection is empty on the "
        "samples of that world. Look at `counts`: undefined minus hard_undefined is the number of abstentions.",
        "§1.10 (the criterion must be defined where it is meant to be evaluated) and §1.5 (UNDEFINED is not a pass).",
    ),
    "K1_ABSTAINED_MAJORITY:": (
        "Capping: the criterion returned UNDEFINED itself on more than half of the samples of the minus or null world "
        "(named after the colon), so it has not shown that it fails where the claim is false. The verdict is capped at WEAK.",
        "A guard that fires in the world without the effect (for example 'no peak found: return None'), or a broken world "
        "(NaN data, a wrong dtype, an always empty selection) on which the criterion abstains. In deterministic mode one "
        "abstention on minus or null is a rate of 1.",
        "§1.5 (a control cannot pass by being UNDEFINED) and §1.10.",
    ),
    "K2_HOLDS_UNREACHABLE": (
        "The criterion never holds in the plus world.",
        "The plus world does not contain the claim, a threshold lies beyond anything the plus world produces, or the "
        "criterion has a bug that makes HOLDS impossible (a unit error, a wrong comparison).",
        "§1.10 (reachability: the criterion must be able to hold) and §1.1 (the tautology question).",
    ),
    "K2_FAILS_UNREACHABLE": (
        "The criterion holds in every minus sample, so it can never fail where the claim is false.",
        "The criterion is decided by definitions or by something the minus world does not change; the minus world is too weak.",
        "§1.10 (reachability: the criterion must be able to fail), §1.1 and §1.7.",
    ),
    "K2_NO_SEPARATION": (
        "The plus and minus worlds are not statistically separated: the criterion's holds-rate does not differ enough between them.",
        "The minus world changes too little or the wrong thing, the criterion reads data the change does not touch, or "
        "there are too few samples.",
        "§1.7 (the minus world changes the data the criterion reads) and §1.10.",
    ),
    "K2_UNRESOLVABLE": (
        "A declared tolerance or premise magnitude (value, scale) is zero, not finite, or so small that scale + value "
        "equals scale in float64.",
        "A tolerance far below the numerical resolution (for example 1e-25 on a quantity of size 1).",
        "§1.9 (tolerances sit above the numerical resolution and the noise ceiling).",
    ),
    FLAG_IDENTICAL: (
        "The minus sample is identical to the plus sample (exact equality), so the criterion's falsifiability is unknown; "
        "the verdict is UNTESTED unless a mandatory flag applies.",
        "The minus world ignores its declared change, or a mutation changes nothing in the data.",
        "§1.7 (the minus world changes the data the criterion reads).",
    ),
    FLAG_UNREAD: (
        "Information only: the minus world changed only keys that the criterion does not read.",
        "The change is in a column the criterion never uses.",
        "§1.7.",
    ),
    "K2_LOW_POWER": (
        "The criterion holds in the plus world significantly less often than targets.power.",
        "The plus world is noisy or small, or the threshold sits close to the plus distribution.",
        "§1.16 (compute the power of every confirmatory test for the expected effect).",
    ),
    "K2_HIGH_SIZE": (
        "The criterion holds in the minus world significantly more often than targets.size (the declared alpha).",
        "A criterion that is easy to satisfy when the claim is false (a loose threshold, a weak minus world).",
        "§1.5 (a criterion needs a case that can make it fail) and §1.16.",
    ),
    "HIGH_RATE:": (
        "A control, probe, premise, null or shuffle stream (named after the colon) holds significantly more often than "
        "targets.size.",
        "A control that breaks the theory only a little, a probe the criterion survives, or a criterion that is "
        "satisfied by many kinds of data.",
        "§1.5 (a negative control is mandatory, and every criterion needs one that can make it fail).",
    ),
    "K3_PREMISE_NOT_TESTED": (
        "A premise declared `tested` does not significantly lower the holds-rate, or its magnitude is unresolvable.",
        "The criterion is insensitive to the premise it claims to depend on, or the mutation is too small to matter.",
        "§1.4 (a sensitivity arm for interpretations that can change the verdict) and §1.9.",
    ),
    "K3_INCONCLUSIVE": (
        "More than 50% of the premise-mutated samples are UNDEFINED, so the premise test says nothing.",
        "The premise mutation breaks the data so that the criterion crashes; crashing must not count as sensitivity.",
        "§1.5 (a control cannot pass by being UNDEFINED).",
    ),
    "K4_NO_CONTROL": (
        "No control lists this criterion and there is no waiver.",
        "No `[[controls]]` entry names the criterion, or its `criteria` list is empty.",
        "§1.5 (a negative control is mandatory; every criterion needs a control that can make it fail).",
    ),
    "K4_WAIVED": (
        "The criterion carries a `control_waiver`; the reason is printed in the certificate and the verdict is capped at WEAK.",
        "A deliberate decision not to declare a control.",
        "§1.5 and §5 (a flag is not filled with a cosmetic control; if it is rejected, the reason is written down).",
    ),
    "K4_CONTROL_ALSO_HOLDS": (
        "A listed control is not significantly lower than plus: the criterion also holds when the theory is broken.",
        "The control does not break what the criterion reads, or the criterion cannot tell the theory from its violation.",
        "§1.5 (if the control also holds, the result is only an existence demonstration).",
    ),
    "K4_INCONCLUSIVE": (
        "More than 50% of a control's samples are UNDEFINED.",
        "The control's transformation produces data on which the criterion crashes.",
        "§1.5 (a control cannot pass by being UNDEFINED).",
    ),
    "K5_HOLDS_ON_NOISE": (
        "The criterion holds on i.i.d. N(0, 1) noise of the same shape as the plus data.",
        "A vacuous criterion: it is decided by the shape of the data, by a definition or by a tolerance that noise satisfies.",
        "§1.1 (the tautology question) and §1.5.",
    ),
    "K5_HOLDS_ON_DEGENERATE": (
        "The criterion holds on all-zero data.",
        "A vacuous criterion (a comparison that is true when everything is zero, an empty selection treated as success).",
        "§1.1 (the tautology question) and §1.5.",
    ),
    "K5_HOLDS_ON_NULL": (
        "The declared `null` world is not significantly lower than plus.",
        "The criterion is satisfied when there is no effect at all.",
        "§1.5 and §1.1.",
    ),
    "K5_HOLDS_ON_SHUFFLE": (
        "The criterion survives shuffling a declared `relational` pair (one array permuted relative to the other).",
        "The criterion does not actually use the relation it claims to test.",
        "§1.1 (the tautology question) and §1.5.",
    ),
    "K5_INCONCLUSIVE:": (
        "More than 50% of the samples of a vacuity probe (named after the colon) are UNDEFINED.",
        "The criterion crashes on probe data, so the probe cannot show whether it holds.",
        "§1.5 (a control cannot pass by being UNDEFINED).",
    ),
    "K6_LEAK_ATTEMPT": (
        "Study-level: the study or a criterion tried to read a file, list a folder, use the network or start a process "
        "that the leak guard blocks.",
        "A criterion that reads a results file, imports an unlisted helper module or opens data it was not given.",
        "§1.11 (blindness: nobody computes the real result before the freeze) and §1.10.",
    ),
    "K6_NONREPRODUCIBLE": (
        "Study-level: two evaluations in one process gave different results.",
        "Unseeded randomness (the global numpy generator, `random`), hidden state in a world or a criterion, or an "
        "external program that carries state between requests.",
        "No rule names it; it protects §1.12 (the frozen run must be the run that was checked) and §1.11.",
    ),
    "K7_REGIME_UNCOVERED": (
        "Study-level: a declared regime has no criterion.",
        "A regime was listed in `[study] regimes` and no criterion carries it.",
        "§1.3 (the verdict mapping gives every combination of criterion outcomes exactly one verdict).",
    ),
    "K7_COMPONENT_MISMATCH": (
        "Study-level: a criterion returned keys different from its declared components.",
        "A missing or extra component name in the return value (a missing component is UNDEFINED).",
        "§1.3 (every outcome is defined in the pre-registration).",
    ),
    "NONDETERMINISTIC": (
        "Study-level, deterministic mode only: a user-derived stream gave different outcomes at sample indices 0, 1 and 2.",
        "The study says `deterministic = true` but a world, premise or control draws random numbers.",
        "§1.10 and §1.12 (a deterministic study must give the same data at every index).",
    ),
    "BAD_RETURN": (
        "Information only: the criterion returned something other than a bool or None; it counts as UNDEFINED.",
        "A numpy value of the wrong type, a string, a number.",
        "§1.10 (the criterion must be defined).",
    ),
    FLAG_NOT_INVARIANT: (
        "K8, mandatory: a transformation that the study declares to leave the criterion's outcome unchanged (an "
        "invariance, or the built-in row permutation of `rows_exchangeable`) changes the outcome too often: the Wilson "
        "lower bound of the change rate exceeds targets.size in the plus or the minus world.",
        "The criterion depends on something it should not: row order (a criterion that reads the first rows of an "
        "exchangeable table), units, or labels.",
        "No protocol rule names invariance; the closest is §1.1 (the criterion should be decided by the claim and the "
        "data, not by incidental properties).",
    ),
    FLAG_SOME_CHANGES: (
        "K8, information only: at least one outcome changed under an invariance, but the change rate is not significantly "
        "above targets.size.",
        "A criterion that is nearly, but not exactly, invariant (a threshold close to the statistic's distribution).",
        "No protocol rule names invariance; see K8_NOT_INVARIANT (closest: §1.1).",
    ),
    FLAG_INCONCLUSIVE: (
        "K8, capping: more than 50% of the before/after pairs of an invariance have an UNDEFINED side in the plus or the "
        "minus world, so the invariance test says little.",
        "The transformation breaks the data (a row operation on data without the needed keys) or the criterion crashes on it.",
        "See K8_NOT_INVARIANT; and §1.5 (UNDEFINED is not a pass).",
    ),
    SUGGESTED_UNREVIEWED: (
        "Capping, on every component: a declaration still carries `origin = \"suggested\"`, so it was written by "
        "`truth-gate suggest` and nobody has reviewed it. The verdict is capped at WEAK, and the GitHub Action fails.",
        "A manifest straight from `suggest`. Review each declaration against your theory, then delete its `origin` key.",
        "§4 (a proposal is not the author's approval) and the Roles section (the author owns the decisions).",
    ),
    NOTE_UNGUARDED: (
        "Study note (never affects a verdict): the study has command criteria, which run in other programs that the "
        "leak guard cannot see. The table, the Action summary and the badge show it.",
        "A `command = [...]` criterion (R, Julia, Node, any language).",
        "§1.11 and §5 (what automated checkers cannot see); also the non-claim about external programs.",
    ),
    NOTE_DIED: (
        "Study note: an external program died, timed out or broke the protocol during the run; every later request to it "
        "was UNDEFINED (the effect reaches the verdict through K1).",
        "A crash in the criterion program, a timeout (`request_timeout_s`), or a malformed reply line.",
        "§1.10 (the criterion must be defined).",
    ),
}


def known_names() -> list:
    return sorted(EXPLANATIONS)


def lookup(name: str) -> Optional[str]:
    """The key of ``EXPLANATIONS`` that explains ``name``: an exact name, or a family prefix (``HIGH_RATE:probe:noise``)."""
    token = name.strip()
    upper = token.upper()
    for key in EXPLANATIONS:
        if upper == key.upper():
            return key
    for family in FAMILIES:
        stem = family.rstrip(":")
        if upper == stem or upper.startswith(family):
            return family
    return None


def kind_of(key: str) -> str:
    """Kind of a flag or note, from the code's own tables."""
    if key in NOTES:
        return "study note (never affects a verdict)"
    if key == "K1_UNDEFINED":
        return "flag, component verdict UNDEFINED"
    if key in checks.UNTESTED_FLAGS:
        return "flag, component verdict UNTESTED"
    if checks.is_mandatory(key):
        return "flag, mandatory (component verdict NOT_FALSIFIABLE)"
    if checks.is_capping(key):
        return "flag, capping (component verdict at most WEAK)"
    if key in checks.STUDY_LEVEL_FLAGS:
        return "flag, study-level (study verdict at least NOT_FALSIFIABLE)"
    if (key in checks.INFORMATIONAL_FLAGS or key in checks.INFORMATIONAL_FLAGS_SCHEMA2
            or key.startswith(checks.INFORMATIONAL_PREFIXES)):
        return "flag, information only"
    return "flag"


def explain(name: str) -> Optional[str]:
    """The text printed by ``truth-gate explain NAME``, or ``None`` for an unknown name."""
    key = lookup(name)
    if key is None:
        return None
    meaning, cause, rule = EXPLANATIONS[key]
    if key in FAMILIES:
        shown = name.strip() if name.strip().upper().startswith(key) else key + "<name>"
    else:
        shown = key
    return (
        f"{shown}  [{kind_of(key)}]\n"
        f"  Meaning:        {meaning}\n"
        f"  Usual cause:    {cause}\n"
        f"  Protocol rule:  {rule}\n"
        "  Reference:      docs/GATE.md (flag table), protocol/PROTOCOL.md (rules)"
    )
