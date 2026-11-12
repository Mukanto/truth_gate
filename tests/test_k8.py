"""Truth_Gate 0.4, stage (d): K8, invariance (spec 0.6, sections 1.1, 7 and 14.1).

K8 is a separate pass after the two evaluations: its own Bonferroni family, its own random streams, flags added after
the 0.3 suppression rules.  The tests recompute pair counts and change counts independently from the engine's
``stream_rng`` and the mutation library, so they also pin the stream convention ``k8:<invariance>:<world>`` at the
sample (or draw) index.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

import _helpers
from test_external import FAKE
from truth_gate import certificate, checks, cli, guard
from truth_gate.k8 import BUILTIN_ID, K8_FLAGS, STATEMENT, k8_rng
from truth_gate.mutations import apply_mutations
from truth_gate.sampling import stream_rng
from truth_gate.stats import wilson_lower

A4 = os.path.join(_helpers.ROOT, "evaluation", "phase_a", "a4")
SEED = 20261105

WORLD_PY = '''
import sys
import numpy as np


def plus(rng):
    return {"x": rng.normal(1.4, 1.0, 40)}


def minus(rng):
    return {"x": rng.normal(0.0, 1.0, 40)}


def plus_low(rng):  # never reaches a first-ten mean above 1
    return {"x": rng.normal(-1.0, 1.0, 40)}


def plus_mild(rng):  # first-ten mean 1.74: the first-ten criterion changes under permutation only now and then
    return {"x": rng.normal(1.74, 1.0, 40)}


def fixed_plus(rng):  # deterministic: no draws; the first ten values are large, the rest are small
    return {"x": np.array([2.0] * 10 + [0.5] * 30)}


def fixed_minus(rng):
    return {"x": np.array([0.2] * 40)}


def first10_mean(d):
    return bool(np.mean(d["x"][:10]) > 1.0)


def first_positive_then_mean(d):  # UNDEFINED when the first value is negative: permutation makes UNDEFINED pairs
    if d["x"][0] < 0:
        return None
    return bool(np.mean(d["x"]) > 1.0)


def two_parts(d):
    return {"a": bool(np.mean(d["x"][:10]) > 1.0), "b": bool(np.mean(d["x"]) > 1.0)}


def counted(d):  # counts its calls in sys._tg_calls and leaks once, when asked to (sys._tg_leak_at)
    sys._tg_calls = getattr(sys, "_tg_calls", 0) + 1
    if sys._tg_calls == getattr(sys, "_tg_leak_at", -1):
        open(sys._tg_leak_file)
    return bool(np.mean(d["x"]) > 1.0)
'''


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def threshold(cid="C", x_index=None, **kw):
    d = {"id": cid, "pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0, **kw}
    if x_index is not None:
        d["x_index"] = x_index
    return d


FIRST_TEN = list(range(10))


class K8Case(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_k8_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.write("w.py", WORLD_PY)

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def base(self, criteria=None, exchangeable=True, invariances=None, plus="plus", minus="minus", **extra):
        d = {
            "study": {"name": "k8"},
            "data": {"rows_exchangeable": exchangeable, "rows": ["x"]},
            "worlds": {"plus": {"python": f"w.py:{plus}"}, "minus": {"python": f"w.py:{minus}", "change": "mean 1.4 -> 0"}},
            "criteria": criteria if criteria is not None else [threshold(x_index=FIRST_TEN)],
            "controls": [{"id": "negated", "criteria": [c["id"] for c in (criteria or [threshold()])],
                          "mutations": [{"op": "sign_flip", "column": "x"}]}],
        }
        if invariances:
            d["invariances"] = invariances
        d.update(extra)
        return d

    def path(self, d, name="truthgate.json"):
        return self.write(name, json.dumps(d))

    def run_body(self, d, quick=False):
        return certificate.run_gate(self.path(d), quick=quick)["body"]

    def cli_run(self, d, *extra):
        out = os.path.join(self.dir, "cert.json")
        if os.path.exists(out):
            os.remove(out)
        code, stdout, stderr = run_cli("check", self.path(d), "--out", out, *extra)
        cert = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as handle:
                cert = json.load(handle)
        return code, stdout, stderr, cert

    @staticmethod
    def comp(body, cid="C"):
        return next(c for c in body["components"] if c["id"] == cid)


def permute_invariance(iid="order", criteria=("C",), reason="the rows are exchangeable"):
    return {"id": iid, "criteria": list(criteria), "reason": reason, "mutations": [{"op": "permute_rows"}]}


# ---------------------------------------------------------------------------------------------------------------------
# The flags and the verdict
# ---------------------------------------------------------------------------------------------------------------------

class TestFlagsAndVerdict(K8Case):
    def test_flag_classes(self):
        self.assertTrue(checks.is_mandatory("K8_NOT_INVARIANT"))
        self.assertTrue(checks.is_capping("K8_INCONCLUSIVE"))
        self.assertFalse(checks.is_mandatory("K8_SOME_CHANGES") or checks.is_capping("K8_SOME_CHANGES"))
        self.assertEqual(checks.component_verdict({"K8_NOT_INVARIANT"}), "NOT_FALSIFIABLE")
        self.assertEqual(checks.component_verdict({"K8_INCONCLUSIVE"}), "WEAK")
        self.assertEqual(checks.component_verdict({"K8_SOME_CHANGES"}), "FALSIFIABLE")
        self.assertEqual(checks.component_verdict({"K1_UNDEFINED", "K8_NOT_INVARIANT"}), "UNDEFINED")
        self.assertEqual(checks.component_verdict({"K2_MINUS_IDENTICAL", "K8_NOT_INVARIANT"}), "NOT_FALSIFIABLE")
        self.assertEqual(set(K8_FLAGS), {"K8_NOT_INVARIANT", "K8_SOME_CHANGES", "K8_INCONCLUSIVE"})

    def test_the_faulty_twin_is_not_falsifiable_because_of_k8_alone(self):
        body = self.run_body(self.base())
        comp = self.comp(body)
        self.assertEqual(body["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(comp["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(comp["flags"], ["K8_NOT_INVARIANT"])
        self.assertEqual([f for f in comp["flags"] if checks.is_mandatory(f)], ["K8_NOT_INVARIANT"])
        self.assertEqual(body["study_flags"], [])
        plus = body["k8"][BUILTIN_ID]["C"]["plus"]
        minus = body["k8"][BUILTIN_ID]["C"]["minus"]
        self.assertGreater(plus["changes"], 0)
        self.assertGreater(plus["wilson_lower"], body["study"]["targets"]["size"])
        self.assertEqual(minus["changes"], 0)

    def test_the_fixed_twin_is_falsifiable_without_a_k8_flag(self):
        body = self.run_body(self.base(criteria=[threshold()]))
        self.assertEqual(body["verdict"], "FALSIFIABLE")
        self.assertEqual(self.comp(body)["flags"], [])
        for world in ("plus", "minus"):
            self.assertEqual(body["k8"][BUILTIN_ID]["C"][world]["changes"], 0)
            self.assertEqual(body["k8"][BUILTIN_ID]["C"][world]["undefined"], 0)

    def test_the_planted_pair_files_of_the_evaluation_folder_give_the_pre_registered_outcome(self):
        faulty = certificate.run_gate(os.path.join(A4, "faulty", "truthgate.toml"))["body"]
        fixed = certificate.run_gate(os.path.join(A4, "fixed", "truthgate.toml"))["body"]
        self.assertEqual((faulty["verdict"], self.comp(faulty)["flags"]), ("NOT_FALSIFIABLE", ["K8_NOT_INVARIANT"]))
        self.assertEqual((fixed["verdict"], self.comp(fixed)["flags"]), ("FALSIFIABLE", []))

    def test_some_changes_is_information_and_does_not_change_the_verdict(self):
        body = self.run_body(self.base(plus="plus_mild"))
        comp = self.comp(body)
        rec = body["k8"][BUILTIN_ID]["C"]["plus"]
        self.assertGreater(rec["changes"], 0)
        self.assertLessEqual(rec["wilson_lower"], body["study"]["targets"]["size"])
        self.assertEqual(comp["flags"], ["K8_SOME_CHANGES"])
        self.assertEqual(comp["verdict"], "FALSIFIABLE")
        self.assertEqual(body["verdict"], "FALSIFIABLE")

    def test_inconclusive_when_more_than_half_of_the_pairs_are_undefined(self):
        # the mutation names a column the data do not have: every transformed sample fails to build
        inv = {"id": "ghost", "criteria": ["C"], "reason": "a transformation that cannot be applied",
               "mutations": [{"op": "scale", "column": "nope", "factor": 2}]}
        body = self.run_body(self.base(criteria=[threshold()], exchangeable=False, invariances=[inv]))
        comp = self.comp(body)
        for world in ("plus", "minus"):
            rec = body["k8"]["ghost"]["C"][world]
            self.assertEqual((rec["pairs"], rec["undefined"], rec["defined"], rec["changes"]), (200, 200, 0, 0))
        self.assertEqual(comp["flags"], ["K8_INCONCLUSIVE"])
        self.assertEqual(comp["verdict"], "WEAK")
        self.assertEqual(body["verdict"], "WEAK")

    def test_undefined_pairs_are_counted_apart(self):
        d = self.base(criteria=[{"id": "C", "python": "w.py:first_positive_then_mean"}])
        d["controls"] = [{"id": "negated", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}]
        body = self.run_body(d)
        rec = body["k8"][BUILTIN_ID]["C"]["minus"]  # minus data are N(0, 1): the first value is often negative
        self.assertGreater(rec["undefined"], 0)
        self.assertEqual(rec["pairs"], 200)
        self.assertEqual(rec["defined"] + rec["undefined"], rec["pairs"])
        self.assertEqual(rec["wilson_lower"], round(wilson_lower(rec["changes"], rec["defined"], rec["level"]), 12))

    def test_k8_flags_are_never_suppressed_by_the_0_3_rules(self):
        # the plus world is moved far below the threshold: plus never holds (K2_HOLDS_UNREACHABLE, so the 0.3 cascade suppression is active),
        # while the minus world holds for about 90% of the samples and changes under row permutation
        d = self.base(plus="plus_low", minus="plus")
        d["worlds"]["minus"]["change"] = "mean -1 -> 1.4"
        body = self.run_body(d)
        comp = self.comp(body)
        self.assertIn("K2_HOLDS_UNREACHABLE", comp["flags"])
        self.assertEqual(comp["suppressed_by"], "K2_HOLDS_UNREACHABLE")
        self.assertIn("K8_NOT_INVARIANT", comp["flags"])
        self.assertNotIn("K8_NOT_INVARIANT", comp["suppressed"])
        self.assertGreater(body["k8"][BUILTIN_ID]["C"]["minus"]["wilson_lower"], 0.05)


# ---------------------------------------------------------------------------------------------------------------------
# The separate family
# ---------------------------------------------------------------------------------------------------------------------

class TestFamily(K8Case):
    def test_m_k8_counts_two_tests_per_invariance_and_component_and_level_is_alpha_over_m(self):
        # invariance 1 lists C and D, invariance 2 lists D, and the built-in one covers C and D: 5 pairs
        criteria = [threshold("C", x_index=FIRST_TEN), threshold("D")]
        inv = [permute_invariance("one", ("C", "D")), permute_invariance("two", ("D",))]
        d = self.base(criteria=criteria, invariances=inv, targets={"alpha_family": 0.04})
        body = self.run_body(d)
        self.assertEqual(body["m_k8"], 2 * 5)
        records = [rec for inv_id in body["k8"].values() for comp in inv_id.values() for rec in comp.values()]
        self.assertEqual(len(records), 5 * 2)  # five pairs, two worlds each
        for rec in records:
            self.assertAlmostEqual(rec["level"], 0.04 / 10, places=15)
            self.assertAlmostEqual(rec["wilson_lower"], wilson_lower(rec["changes"], rec["defined"], 0.04 / 10), places=11)
        self.assertEqual(sorted(body["k8"]), sorted([BUILTIN_ID, "one", "two"]))
        self.assertEqual(sorted(body["k8"]["one"]), ["C", "D"])
        self.assertEqual(sorted(body["k8"]["two"]), ["D"])
        self.assertEqual(body["k8_statement"], STATEMENT)
        self.assertEqual(STATEMENT, "study-wide family-wise error rate at most 2 · alpha_family")

    def test_components_are_separate_pairs(self):
        d = self.base(criteria=[{"id": "P", "python": "w.py:two_parts", "components": ["a", "b"]}], exchangeable=False,
                      invariances=[permute_invariance("order", ("P",))])
        d["controls"][0]["criteria"] = ["P"]
        body = self.run_body(d)
        self.assertEqual(body["m_k8"], 2 * 2)
        self.assertEqual(sorted(body["k8"]["order"]), ["P:a", "P:b"])
        self.assertIn("K8_NOT_INVARIANT", self.comp(body, "P:a")["flags"])  # the first-ten component reads the order
        self.assertNotIn("K8_NOT_INVARIANT", self.comp(body, "P:b")["flags"])

    def test_the_k1_k7_family_is_untouched(self):
        with_k8 = self.run_body(self.base(criteria=[threshold()]))
        without = self.run_body(self.base(criteria=[threshold()], exchangeable=False))
        self.assertEqual(with_k8["m_comparisons"], without["m_comparisons"])
        self.assertEqual(with_k8["alpha_per_bound"], without["alpha_per_bound"])
        self.assertNotEqual(with_k8["m_k8"], with_k8["m_comparisons"])

    def test_without_k8_the_fields_are_empty_and_there_is_no_statement(self):
        body = self.run_body(self.base(exchangeable=False))
        self.assertEqual(body["k8"], {})
        self.assertEqual(body["m_k8"], 0)
        self.assertNotIn("k8_statement", body)
        self.assertEqual(self.comp(body)["flags"], [])


# ---------------------------------------------------------------------------------------------------------------------
# K1-K7 are unchanged
# ---------------------------------------------------------------------------------------------------------------------

def k17_part(body):
    """Everything K1-K7 produce: the body without the K8 fields, the K8 flags and the verdicts that K8 can move."""
    comps = []
    for comp in body["components"]:
        part = {k: v for k, v in comp.items() if k not in ("flags", "verdict")}
        part["flags"] = [f for f in comp["flags"] if not f.startswith("K8_")]
        comps.append(part)
    return {
        "components": comps,
        **{k: body[k] for k in ("study_flags", "study_flag_details", "m_comparisons", "alpha_per_bound", "premise_map",
                                "leak_log", "probe_unchanged_keys", "mode", "python_version", "numpy_version")},
    }


class TestK1ToK7Unchanged(K8Case):
    def test_stochastic_study_with_and_without_an_invariance(self):
        for criteria, label in (([threshold(x_index=FIRST_TEN)], "k8 flag raised"), ([threshold()], "no k8 flag")):
            with self.subTest(label):
                without = self.run_body(self.base(criteria=criteria, exchangeable=False))
                with_inv = self.run_body(self.base(criteria=criteria, exchangeable=True,
                                                   invariances=[permute_invariance()]))
                self.assertEqual(k17_part(with_inv), k17_part(without))
                if label == "no k8 flag":  # nothing moved: the whole component and the verdict are the same
                    self.assertEqual(with_inv["components"], without["components"])
                    self.assertEqual(with_inv["verdict"], without["verdict"])

    def test_deterministic_study_with_and_without_an_invariance(self):
        det = {"study": {"name": "k8", "deterministic": True}, "budget": {"samples": 25, "quick_samples": 5}}
        without = self.run_body(self.base(exchangeable=False, plus="fixed_plus", minus="fixed_minus", **det))
        with_inv = self.run_body(self.base(exchangeable=True, plus="fixed_plus", minus="fixed_minus", **det))
        self.assertEqual(k17_part(with_inv), k17_part(without))
        self.assertNotIn("NONDETERMINISTIC", with_inv["study_flags"])

    def test_quick_mode_too(self):
        without = self.run_body(self.base(exchangeable=False), quick=True)
        with_inv = self.run_body(self.base(exchangeable=True), quick=True)
        self.assertEqual(k17_part(with_inv), k17_part(without))


# ---------------------------------------------------------------------------------------------------------------------
# Pair counts and random streams, recomputed independently
# ---------------------------------------------------------------------------------------------------------------------

def world_sample(world, kind, i):
    """The counted sample ``i`` of the world, from the engine's seeds (the world functions of ``WORLD_PY``)."""
    ns: dict = {}
    exec(WORLD_PY, ns)
    return ns[kind](stream_rng(SEED, f"world:{world}", i))


def first10(data):
    return bool(np.mean(data["x"][:10]) > 1.0)


class TestPairsAndStreams(K8Case):
    def expected_stochastic(self, plus_kind, minus_kind, n, inv_id=BUILTIN_ID):
        out = {}
        for world, kind in (("plus", plus_kind), ("minus", minus_kind)):
            changes = 0
            for i in range(n):
                sample = world_sample(world, kind, i)
                rng = stream_rng(SEED, f"k8:{inv_id}:{world}", i)
                moved = apply_mutations(sample, [{"op": "permute_rows"}], rng, ("x",))
                changes += first10(sample) != first10(moved)
            out[world] = changes
        return out

    def test_stochastic_pairs_and_changes_equal_a_direct_recomputation(self):
        body = self.run_body(self.base())
        expected = self.expected_stochastic("plus", "minus", 200)
        for world in ("plus", "minus"):
            rec = body["k8"][BUILTIN_ID]["C"][world]
            self.assertEqual(rec["pairs"], 200)
            self.assertEqual(rec["changes"], expected[world], world)
        self.assertGreater(expected["plus"], 0)

    def test_quick_mode_uses_the_quick_sample_count(self):
        body = self.run_body(self.base(), quick=True)
        expected = self.expected_stochastic("plus", "minus", 20)
        for world in ("plus", "minus"):
            rec = body["k8"][BUILTIN_ID]["C"][world]
            self.assertEqual((rec["pairs"], rec["changes"]), (20, expected[world]))
        self.assertEqual(body["mode"], "quick")

    def test_a_declared_invariance_draws_from_its_own_stream(self):
        d = self.base(exchangeable=False, invariances=[permute_invariance("my_order")])
        body = self.run_body(d)
        expected = self.expected_stochastic("plus", "minus", 200, "my_order")
        self.assertEqual(body["k8"]["my_order"]["C"]["plus"]["changes"], expected["plus"])
        self.assertEqual(k8_rng(SEED, "my_order", "plus", 3).integers(1 << 30),
                         stream_rng(SEED, "k8:my_order:plus", 3).integers(1 << 30))

    def test_deterministic_study_evaluates_one_sample_and_draws_budget_samples_transformations(self):
        det = {"study": {"name": "k8", "deterministic": True}, "budget": {"samples": 25, "quick_samples": 5}}
        d = self.base(plus="fixed_plus", minus="fixed_minus", **det)
        full = self.run_body(d)
        quick = self.run_body(d, quick=True)
        ns: dict = {}
        exec(WORLD_PY, ns)
        for body, n in ((full, 25), (quick, 5)):
            for world, kind in (("plus", "fixed_plus"), ("minus", "fixed_minus")):
                sample = ns[kind](None)
                changes = 0
                for j in range(n):
                    moved = apply_mutations(sample, [{"op": "permute_rows"}], stream_rng(SEED, f"k8:{BUILTIN_ID}:{world}", j),
                                            ("x",))
                    changes += first10(sample) != first10(moved)
                rec = body["k8"][BUILTIN_ID]["C"][world]
                self.assertEqual((rec["pairs"], rec["changes"]), (n, changes), (world, n))
        self.assertGreater(full["k8"][BUILTIN_ID]["C"]["plus"]["changes"], 20)  # most permutations move the large values
        self.assertEqual(full["components"][0]["counts"]["world:plus"]["n"], 1)  # K1-K7 still see one sample

    def test_k8_draws_do_not_enter_the_determinism_check(self):
        det = {"study": {"name": "k8", "deterministic": True}, "budget": {"samples": 25, "quick_samples": 5}}
        body = self.run_body(self.base(plus="fixed_plus", minus="fixed_minus", **det))
        self.assertIn("K8_NOT_INVARIANT", self.comp(body)["flags"])
        self.assertNotIn("NONDETERMINISTIC", body["study_flags"])
        self.assertNotIn("NONDETERMINISTIC", body["study_flag_details"])

    def test_declared_mutations_of_a_deterministic_study_still_use_the_declaration_generator(self):
        # K8's transformation draws are a different matter (spec 7); an invariance with a random op must not make the
        # study NONDETERMINISTIC either
        det = {"study": {"name": "k8", "deterministic": True}, "budget": {"samples": 25, "quick_samples": 5}}
        inv = {"id": "noisy", "criteria": ["C"], "reason": "a little noise must not matter",
               "mutations": [{"op": "noise", "column": "x", "sd": 0.01}]}
        body = self.run_body(self.base(criteria=[threshold()], exchangeable=False, invariances=[inv],
                                       plus="fixed_plus", minus="fixed_minus", **det))
        self.assertNotIn("NONDETERMINISTIC", body["study_flags"])
        self.assertEqual(body["k8"]["noisy"]["C"]["plus"]["pairs"], 25)


# ---------------------------------------------------------------------------------------------------------------------
# The built-in invariance, validation and exit codes
# ---------------------------------------------------------------------------------------------------------------------

class TestBuiltInAndValidation(K8Case):
    def test_rows_exchangeable_adds_the_builtin_invariance_for_every_criterion(self):
        criteria = [threshold("C"), threshold("D", value=0.5)]
        body = self.run_body(self.base(criteria=criteria))
        self.assertEqual(sorted(body["k8"][BUILTIN_ID]), ["C", "D"])
        self.assertEqual(body["m_k8"], 4)
        self.assertEqual(body["mutations"]["invariances"], [{"id": BUILTIN_ID, "ops": ["permute_rows"]}])

    def test_the_builtin_invariance_cannot_be_removed(self):
        # there is no manifest key that removes it; a user invariance only adds to it, and its id is reserved
        body = self.run_body(self.base(invariances=[permute_invariance("mine")]))
        self.assertEqual(sorted(body["k8"]), sorted([BUILTIN_ID, "mine"]))
        clash = permute_invariance(BUILTIN_ID)
        code, out, err, cert = self.cli_run(self.base(invariances=[clash]))
        self.assertEqual(code, 3)
        self.assertIn("duplicate invariance id", cert["body"]["load_error"]["message"])

    def test_without_rows_exchangeable_there_is_no_builtin_invariance(self):
        body = self.run_body(self.base(exchangeable=False, invariances=[permute_invariance("mine")]))
        self.assertEqual(sorted(body["k8"]), ["mine"])

    def test_rows_exchangeable_needs_row_aligned_keys(self):
        d = self.base()
        d["data"] = {"rows_exchangeable": True}
        code, out, err, cert = self.cli_run(d)
        self.assertEqual(code, 4)
        self.assertIn("row-aligned", err)
        self.assertIsNone(cert)

    def test_study_level_problems_are_a_certificate_with_exit_3(self):
        for label, inv, message in (
            ("unknown criterion", permute_invariance("i", ("Z",)), "unknown criterion 'Z'"),
            ("criterion twice", permute_invariance("i", ("C", "C")), "lists a criterion twice"),
        ):
            with self.subTest(label):
                code, out, err, cert = self.cli_run(self.base(exchangeable=False, invariances=[inv]))
                self.assertEqual(code, 3, err)
                self.assertEqual(cert["body"]["load_error"]["type"], "StudyError")
                self.assertIn(message, cert["body"]["load_error"]["message"])
        two = [permute_invariance("i"), permute_invariance("i")]
        code, out, err, cert = self.cli_run(self.base(exchangeable=False, invariances=two))
        self.assertEqual(code, 3)
        self.assertIn("duplicate invariance id", cert["body"]["load_error"]["message"])

    def test_the_certificate_is_valid_and_reproducible(self):
        d = self.base()
        first = certificate.run_gate(self.path(d))
        second = certificate.run_gate(self.path(d))
        self.assertEqual(certificate.validate_envelope(first), [])
        self.assertEqual(first["body_sha256"], second["body_sha256"])
        self.assertNotIn("K6_NONREPRODUCIBLE", first["body"]["study_flags"])
        cert = os.path.join(self.dir, "c.json")
        self.assertEqual(run_cli("check", self.path(d), "--out", cert)[0], 2)
        code, out, err = run_cli("verify", cert, self.path(d))
        self.assertEqual(code, 0, out + err)

    def test_the_cli_table_shows_the_k8_flag(self):
        code, out, err, cert = self.cli_run(self.base())
        self.assertEqual(code, 2)
        self.assertIn("K8_NOT_INVARIANT", out)


# ---------------------------------------------------------------------------------------------------------------------
# The guard and external programs
# ---------------------------------------------------------------------------------------------------------------------

class TestGuardAndExternal(K8Case):
    def test_the_k8_pass_runs_under_the_armed_guard(self):
        secret = self.write("secret.txt", "not for the criterion")
        d = self.base(criteria=[{"id": "C", "python": "w.py:counted"}], exchangeable=False)
        sys._tg_calls = 0
        certificate.run_gate(self.path(d))
        calls_without = sys._tg_calls
        d = self.base(criteria=[{"id": "C", "python": "w.py:counted"}], exchangeable=True)
        sys._tg_calls = 0
        certificate.run_gate(self.path(d))
        self.assertGreater(sys._tg_calls, calls_without)  # K8 called the criterion
        sys._tg_calls, sys._tg_leak_at, sys._tg_leak_file = 0, calls_without + 1, secret
        self.addCleanup(lambda: [delattr(sys, n) for n in ("_tg_calls", "_tg_leak_at", "_tg_leak_file")
                                 if hasattr(sys, n)])
        body = certificate.run_gate(self.path(d))["body"]
        self.assertIn("K6_LEAK_ATTEMPT", body["study_flags"])
        self.assertTrue(any(e["event"] == "open" for e in body["leak_log"]))
        self.assertEqual(body["verdict"], "NOT_FALSIFIABLE")
        self.assertFalse(guard._STATE.armed)

    def test_a_command_criterion_is_asked_by_the_k8_pass_too(self):
        self.write("fake_tg.py", FAKE)
        d = self.base(criteria=[{"id": "C", "command": [sys.executable, "fake_tg.py", "mean"]}])
        d["external"] = {"uses": ["fake_tg.py"]}
        body = self.run_body(d, quick=True)
        self.assertEqual([n["note"] for n in body["study_notes"]], ["K6_EXTERNAL_UNGUARDED"])
        rec = body["k8"][BUILTIN_ID]["C"]["plus"]
        self.assertEqual((rec["pairs"], rec["changes"], rec["undefined"]), (20, 0, 0))  # the mean ignores the order
        self.assertEqual(body["verdict"], "FALSIFIABLE", body["components"])


if __name__ == "__main__":
    unittest.main()
