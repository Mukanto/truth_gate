"""Phase D classification of a failed clean pass (R2-1; TOOLS_SPEC_D_round2 item 6).  Runs only after the run.

A clean pass of a pair in an arm is a fixed-study verdict of FALSIFIABLE or WEAK (PB section 6).  For a fixed study that did
not pass, this tool assigns the first class that applies, using an estimate that does not come from the certificate's own
200 samples (R2-1: the gate's flag and a rule that reads the same count would be circular).

Inputs: the fixed study file of one arm (the assembled file that was run), its certificate (``body`` or the whole file) and
the package root (the gate at the version that was run).  ``--timeout`` marks a check that ran past the limit (no
certificate is needed then).

Classes, in this order:

* **(e) attrition or no verdict** - a load error, ``K1_UNDEFINED`` (verdict UNDEFINED), verdict UNTESTED, the ``--timeout``
  marker, or ``--attrition CAUSE`` (D-R4-6: an invalid skeleton, a part-B "no" or any other cause the designer gives; it
  needs no certificate and no study file).  The causes are listed.
* **(1) fixed not clean in these worlds** - the fixed twin carries a rate flag (``K2_HIGH_SIZE``, on ``world:minus``, or
  ``HIGH_RATE:<stream>``, on that stream), and for at least one flagged stream s, 1000 fresh samples of s give a fixed-criterion
  holds rate whose 95% two-sided Wilson interval lies entirely above the declared size (``lower > size``).
* **(2) possible false alarm** - there is a rate flag, (1) does not apply, and apart from the rate flags the component carries
  no mandatory flag (``truth_gate.checks.is_mandatory``) and no study-level flag (D-R4-6).  Every fresh interval then includes
  the size or lies below it.
* **(3) fixed weak in plus** - apart from rate flags that (1) did not confirm, the failure flags are only
  ``K2_NO_SEPARATION``, ``K2_HOLDS_UNREACHABLE``, ``K2_LOW_POWER``, ``K4_CONTROL_ALSO_HOLDS`` and ``K5_HOLDS_ON_*`` (D-R4-6).
  The earlier clause "whose stream carries no rate flag" is dropped: (1) runs first, so a rate flag left at this point is one
  the fresh samples did not confirm.  "The failure" is every mandatory flag of the component plus every study-level flag;
  capping flags such as ``K2_LOW_POWER`` give WEAK, which passes, so they cannot be the cause on their own.
* **(4) other** - everything else, listed with its flags (this includes ``K4_NO_CONTROL`` and every other mandatory or
  study-level flag outside the lists above).

Whenever rate flags were sampled and the class is not (1), ``unconfirmed_rate_flags`` lists the sampled streams with their
flags and their ``relation`` (above / includes / below; none is "above" then).  The per-stream ``relation`` is recorded in
``streams`` in every case.

The fresh samples mirror the gate's own stream construction.  The gate builds the samples of a study in
``truth_gate/checks.py``: ``collect`` (lines 520-522) draws the plus sample of index i with
``stream_rng(seed, "world:plus", i)``; ``make_sample`` (lines 430-455) then builds the sample of every other stream from it:
world streams (``world:minus``, ``world:null``) and control worlds are generated with ``rng(sd.name)`` (lines 437-442); a
control transform is applied to a copy of the plus sample with ``rng(sd.name)`` (lines 447-448); a premise mutator is applied
with ``rng("premise-rng:<id>")`` (line 446); the noise, zeros and shuffle probes are applied to a copy of the plus sample with
``rng(name)`` (lines 449-455).  This tool calls those very functions (``build_plan``, ``_call``, ``make_sample``,
``evaluate_detailed``) with one change: ``truth_gate.checks.stream_rng`` is replaced, for the duration of the sampling, by
``lambda base_seed, stream, i: stream_rng(20261117, "classify:" + stream, i)``.  So every gate stream name N becomes
``classify:N`` (the plus sample of index i is ``classify:world:plus``, the stream s itself is ``classify:<s>``), the seed is
20261117 instead of the study's base seed, and nothing else differs.  The criterion is the fixed study's, evaluated by
``checks.evaluate_detailed`` (a ``None`` or an error is not-holds, as in the gate's counts).  The interval is the gate's
``stats.wilson_bounds(k, n, 0.025)``: a one-sided level of 0.025 on each side, i.e. the 95% two-sided Wilson interval.

Output (JSON): ``{"class": "e" | "1" | "2" | "3" | "4" | null, "label", "verdict", "causes": [...] (class e), "flags": [...],
"failure_flags": [...], "size", "seed", "samples", "streams": [{"stream", "flags", "holds", "undefined", "n", "rate",
"interval": [lo, hi], "relation": "above" | "includes" | "below"}], "reasons": [...]}``.  ``class`` is null when the verdict is
FALSIFIABLE or WEAK (a clean pass: nothing to classify).

Usage:
    py clean_pass_class.py --study FIXED_STUDY.py --cert FIXED_CERT.json --package-root DIR [--timeout] [--out OUT.json]
    py clean_pass_class.py --attrition "invalid skeleton" --package-root DIR [--out OUT.json]    (no study, no certificate)
Exit code 0 on a classification (also for a clean pass), 2 on a usage error (unreadable input, failed package root check, a
flagged stream the study does not have, a study with more than one criterion or with components).
"""
import argparse
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from attributable import not_sl_streams  # noqa: E402
from structure_stat import PackageRootError, import_truth_gate, load_study_module  # noqa: E402

SEED = 20261117
SAMPLES = 1000
WILSON_A = 0.025  # one-sided level of each bound: the two-sided 95% interval
LABELS = {
    "e": "attrition or no verdict",
    "1": "fixed not clean in these worlds",
    "2": "possible false alarm",
    "3": "fixed weak in plus",
    "4": "other",
}
CLEAN_VERDICTS = ("FALSIFIABLE", "WEAK")
WEAK_PLUS_FLAGS = ("K2_NO_SEPARATION", "K2_HOLDS_UNREACHABLE", "K2_LOW_POWER")


class ClassifyError(Exception):
    """The inputs cannot be classified (a usage error)."""


def rate_flag_streams(flags):
    """``{stream: [flags]}`` of the rate flags of a component: ``K2_HIGH_SIZE`` -> ``world:minus``, ``HIGH_RATE:<s>`` -> s."""
    out = {}
    for f in flags:
        if f == "K2_HIGH_SIZE":
            out.setdefault("world:minus", []).append(f)
        elif f.startswith("HIGH_RATE:"):
            out.setdefault(f[len("HIGH_RATE:"):], []).append(f)
    return out


def relative_flag_streams(flag, counts, bounds):
    """Streams of a relative flag, or ``None`` if the flag is not one.

    The relative flags are exactly ``K4_CONTROL_ALSO_HOLDS`` and the ``K5_HOLDS_ON_*`` flags (T3-2).  The other ``K4_*``
    flags are not (``K4_NO_CONTROL`` goes to class (4); ``K4_WAIVED`` and ``K4_INCONCLUSIVE`` are capping and never cause a
    failure).  A ``K5_HOLDS_ON_*`` flag that is not one of the four the gate raises maps to no stream.

    The stream-valued flags map as in ``attributable.streams_of``; ``K4_CONTROL_ALSO_HOLDS`` and ``K5_HOLDS_ON_SHUFFLE`` go
    through the bounds condition (``upper(s) >= lower(plus)``, the gate's SL rule).
    """
    if flag == "K4_CONTROL_ALSO_HOLDS":
        return not_sl_streams(counts, bounds, "control:")
    if flag == "K5_HOLDS_ON_NOISE":
        return ["probe:noise"]
    if flag == "K5_HOLDS_ON_DEGENERATE":
        return ["probe:zeros"]
    if flag == "K5_HOLDS_ON_NULL":
        return ["world:null"]
    if flag == "K5_HOLDS_ON_SHUFFLE":
        return not_sl_streams(counts, bounds, "probe:shuffle:")
    if flag.startswith("K5_HOLDS_ON_"):
        return []
    return None


def wilson_interval(k, n):
    """The gate's Wilson bounds at the one-sided level 0.025 (a two-sided 95% interval): ``(lower, upper)``."""
    from truth_gate.stats import wilson_bounds
    return wilson_bounds(k, n, WILSON_A)


def relation(lo, hi, size):
    """``"above"`` if the interval lies entirely above the size, ``"below"`` if entirely below, else ``"includes"``."""
    if lo > size:
        return "above"
    if hi < size:
        return "below"
    return "includes"


def fresh_streams(study, streams, samples=SAMPLES, seed=SEED):
    """Fresh samples of the named streams of ``study`` (see the module docstring); one record per stream."""
    from truth_gate import checks, sampling
    if len(study.criteria) != 1 or study.criteria[0].components is not None:
        raise ClassifyError("the study must have exactly one criterion without components")
    plan = {sd.name: sd for sd in checks.build_plan(study)}
    missing = sorted(s for s in streams if s not in plan)
    if missing:
        raise ClassifyError(f"the study has no stream {missing} (its streams: {sorted(plan)})")
    crit = study.criteria[0]
    real = checks.stream_rng

    def redirected(base_seed, stream, i):
        return sampling.stream_rng(seed, "classify:" + stream, i)

    out = []
    checks.stream_rng = redirected
    try:
        for s in streams:
            sd = plan[s]
            holds = undefined = 0
            for i in range(samples):
                plus = checks._call(study.worlds["plus"].generate, checks.stream_rng(study.budget.base_seed, "world:plus", i))
                sample = checks.make_sample(study, sd, i, plus)
                outcome = checks.evaluate_detailed(crit, sample).outcomes[crit.id]
                if outcome == checks.HOLDS:
                    holds += 1
                elif outcome == checks.UNDEFINED:
                    undefined += 1
            lo, hi = wilson_interval(holds, samples)
            out.append({"stream": s, "holds": holds, "undefined": undefined, "n": samples, "rate": holds / samples,
                        "interval": [lo, hi], "relation": relation(lo, hi, study.targets.size)})
    finally:
        checks.stream_rng = real
    return out


def _component(body):
    comps = body.get("components") or []
    if len(comps) != 1:
        raise ClassifyError(f"expected one component in the certificate, found {len(comps)}")
    return comps[0]


def classify_clean_pass(study_module, body, package_root, timeout=False, samples=SAMPLES, seed=SEED, attrition=None):  # D-R4-6
    """Classify one fixed study that did not pass (see the module docstring).  ``body`` is the certificate body (or ``None``
    when ``timeout`` is true or ``attrition`` is given); ``attrition`` is a cause the designer gives (an invalid skeleton, a
    part-B "no", ...), which needs no certificate and no study."""
    import_truth_gate(package_root)
    res = {"class": None, "label": None, "verdict": None, "causes": [], "flags": [], "failure_flags": [],
           "size": None, "seed": seed, "samples": samples, "streams": [], "reasons": [],
           "unconfirmed_rate_flags": []}  # D-R4-6

    def done(cls, why):
        res["class"], res["label"] = cls, LABELS.get(cls)
        res["reasons"].append(why)
        return res

    # --- (e) attrition or no verdict
    if attrition:  # D-R4-6
        res["causes"].append(attrition)  # D-R4-6
    if timeout:
        res["causes"].append("timeout")
    if body is not None:
        res["verdict"] = body.get("verdict")
        if body.get("load_error"):
            le = body["load_error"]
            res["causes"].append(f"load error: {le.get('type')}" if isinstance(le, dict) else "load error")
        elif not (body.get("components") or []):
            res["causes"].append("load error: no component in the certificate")
        else:
            flags_all = [f for c in body["components"] for f in c["flags"]]
            if "K1_UNDEFINED" in flags_all:
                res["causes"].append("K1_UNDEFINED")
            elif body["verdict"] == "UNDEFINED":
                res["causes"].append("verdict UNDEFINED")
            if body["verdict"] == "UNTESTED":
                res["causes"].append("UNTESTED")
    elif not timeout and not attrition:  # D-R4-6
        raise ClassifyError("a certificate is required unless --timeout or --attrition is given")
    if res["causes"]:
        return done("e", "attrition or no verdict: " + "; ".join(res["causes"]))
    if body["verdict"] in CLEAN_VERDICTS:
        res["reasons"].append(f"verdict {body['verdict']}: a clean pass, nothing to classify")
        return res

    comp = _component(body)
    flags = list(comp["flags"])
    counts, bounds = comp["counts"], comp.get("bounds") or {}
    study_flags = list(body.get("study_flags") or [])
    import_truth_gate(package_root)
    from truth_gate.checks import is_mandatory
    failure = [f for f in flags if is_mandatory(f)] + study_flags
    res["flags"], res["failure_flags"] = flags, failure

    # --- (1) and (2): the rate flags, with fresh samples
    rates = rate_flag_streams(flags)
    non_rate_failure = [f for f in failure if f not in {x for fl in rates.values() for x in fl}]  # D-R4-6
    if rates:
        fresh = fresh_streams(study_module.STUDY, sorted(rates), samples, seed)
        res["size"] = study_module.STUDY.targets.size
        for rec in fresh:
            rec["flags"] = rates[rec["stream"]]
        res["streams"] = fresh
        if any(r["relation"] == "above" for r in fresh):
            above = [r["stream"] for r in fresh if r["relation"] == "above"]
            return done("1", f"the fresh 95% interval lies above the size {res['size']} on {above}")
        res["unconfirmed_rate_flags"] = [{"stream": r["stream"], "flags": r["flags"], "relation": r["relation"]} for r in fresh]  # D-R4-6
        rel = {r["stream"]: r["relation"] for r in fresh}
        if not non_rate_failure:  # D-R4-6: (2) needs the rate flags to be the whole failure
            return done("2", f"no flagged stream has a fresh 95% interval above the size {res['size']}: {rel}")
        res["reasons"].append(f"rate flags not confirmed by the fresh samples: {rel}")  # D-R4-6

    # --- (3) fixed weak in plus: apart from rate flags that (1) did not confirm, only the listed flags (D-R4-6)
    not_allowed = [f for f in non_rate_failure if f not in WEAK_PLUS_FLAGS and relative_flag_streams(f, counts, bounds) is None]
    if non_rate_failure and not not_allowed:
        return done("3", "the failure comes only from " + ", ".join(sorted(set(non_rate_failure)))
                    + (" (and rate flags the fresh samples did not confirm)" if rates else ""))

    # --- (4) other
    return done("4", "other; flags " + ", ".join(flags) + ("; study flags " + ", ".join(study_flags) if study_flags else ""))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Classify a failed clean pass of one fixed study (Phase D, after the run).")
    ap.add_argument("--study", metavar="FILE", help="the fixed study file of the arm (as it was run); optional with --attrition")  # D-R4-6
    ap.add_argument("--cert", metavar="CERT.json", help="its certificate (required unless --timeout)")
    ap.add_argument("--package-root", required=True, metavar="DIR")
    ap.add_argument("--timeout", action="store_true", help="the check ran past the time limit (class e)")
    ap.add_argument("--attrition", metavar="CAUSE",  # D-R4-6
                    help="a cause the designer gives (an invalid skeleton, a part-B no, ...): class e, no certificate needed")
    ap.add_argument("--out", metavar="OUT.json")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    try:
        import_truth_gate(a.package_root)
    except PackageRootError as e:
        print(f"package root check failed: {e}", file=sys.stderr)
        return 2
    try:
        if not a.study and not a.attrition:  # D-R4-6
            raise ClassifyError("--study is required unless --attrition is given")  # D-R4-6
        module = None  # D-R4-6
        if a.study:  # D-R4-6
            with open(a.study, encoding="utf-8") as f:  # D-R4-6
                src = f.read()  # D-R4-6
            module = load_study_module(src, a.study, "fixed")  # D-R4-6
        body = None
        if a.cert:
            with open(a.cert, encoding="utf-8") as f:
                cert = json.load(f)
            body = cert.get("body", cert)
        res = classify_clean_pass(module, body, a.package_root, timeout=a.timeout, attrition=a.attrition)  # D-R4-6
    except (OSError, ValueError, KeyError, TypeError, ClassifyError) as e:
        print(f"clean_pass_class: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
