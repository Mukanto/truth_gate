"""Study API (spec section 3): construction validation, return-value rules, resolution test."""

import unittest

import numpy as np

import _helpers  # noqa: F401
from kapi import Budget, Control, Criterion, Premise, Study, StudyError, Targets, World
from kapi.checks import FAILS, HOLDS, UNDEFINED, count_comparisons, is_resolvable, normalize_return
from kapi.study import criterion_component_ids

PLUS = World(lambda rng: {"x": rng.normal(1.0, 1.0, 5)})
MINUS = World(lambda rng: {"x": rng.normal(0.0, 1.0, 5)})


def crit(cid="c", **kw):
    return Criterion(cid, lambda d: True, **kw)


def make(**overrides):
    args = dict(name="t", criteria=[crit()], worlds={"plus": PLUS, "minus": MINUS})
    args.update(overrides)
    return Study(**args)


class TestConstruction(unittest.TestCase):
    def test_minimal_study_is_valid_and_defaults_match_spec(self):
        s = make()
        self.assertEqual(s.regimes, ["all"])
        self.assertFalse(s.deterministic)
        self.assertEqual((s.budget.samples, s.budget.quick_samples, s.budget.base_seed), (200, 20, 20261105))
        self.assertEqual((s.targets.power, s.targets.size, s.targets.alpha_family), (0.8, 0.05, 0.05))
        self.assertEqual((s.allow_paths, s.relational, s.premises, s.controls), ([], [], [], []))

    def test_defaults_are_not_shared_between_instances(self):
        a, b = make(), make()
        self.assertIsNot(a.premises, b.premises)
        self.assertIsNot(a.regimes, b.regimes)

    def test_duplicate_criterion_ids(self):
        with self.assertRaises(StudyError):
            make(criteria=[crit("a"), crit("a")])

    def test_duplicate_component_ids(self):
        with self.assertRaises(StudyError):
            make(criteria=[crit("a", components=["x"]), crit("a:x")])

    def test_duplicate_premise_and_control_ids(self):
        p = Premise("p", lambda d, r: d, "assumed", ["c"])
        with self.assertRaises(StudyError):
            make(premises=[p, p])
        k = Control("k", ["c"], transform=lambda d, r: d)
        with self.assertRaises(StudyError):
            make(controls=[k, k])

    def test_unknown_criterion_in_premise_or_control(self):
        with self.assertRaises(StudyError):
            make(premises=[Premise("p", lambda d, r: d, "tested", ["nope"])])
        with self.assertRaises(StudyError):
            make(controls=[Control("k", ["nope"], transform=lambda d, r: d)])

    def test_missing_plus_or_minus_world(self):
        with self.assertRaises(StudyError):
            make(worlds={"minus": MINUS})
        with self.assertRaises(StudyError):
            make(worlds={"plus": PLUS})

    def test_control_needs_exactly_one_of_transform_or_world(self):
        with self.assertRaises(StudyError):
            make(controls=[Control("k", ["c"])])
        with self.assertRaises(StudyError):
            make(controls=[Control("k", ["c"], transform=lambda d, r: d, world=PLUS)])
        make(controls=[Control("k", ["c"], world=PLUS)])  # valid

    def test_undeclared_regime(self):
        with self.assertRaises(StudyError):
            make(criteria=[crit(regime="late")], regimes=["early"])

    def test_premise_role_must_be_known(self):
        with self.assertRaises(StudyError):
            make(premises=[Premise("p", lambda d, r: d, "maybe", ["c"])])

    def test_conservative_extra_validation(self):
        for bad in (
            dict(criteria=[]),
            dict(budget=Budget(samples=0)),
            dict(budget=Budget(base_seed=-1)),
            dict(targets=Targets(alpha_family=1.5)),
            dict(criteria=[crit(components=[])]),
            dict(allow_paths=["a", "a"]),
            dict(relational=[("a",)]),
            dict(name=""),
        ):
            with self.subTest(bad=bad), self.assertRaises(StudyError):
                make(**bad)


class TestComponents(unittest.TestCase):
    def test_component_ids(self):
        self.assertEqual(criterion_component_ids(crit("a")), ["a"])
        self.assertEqual(criterion_component_ids(crit("a", components=["x", "y"])), ["a:x", "a:y"])

    def test_comparison_count(self):
        # one component: 1 separation + 1 control + 2 probes = 4
        self.assertEqual(count_comparisons(make(controls=[Control("k", ["c"], transform=lambda d, r: d)])), 4)
        # + tested premise + null + one relational pair = 4 + 1 + 1 + 1
        s = make(
            controls=[Control("k", ["c"], transform=lambda d, r: d)],
            premises=[Premise("p", lambda d, r: d, "tested", ["c"]), Premise("q", lambda d, r: d, "assumed", ["c"])],
            worlds={"plus": PLUS, "minus": MINUS, "null": MINUS},
            relational=[("x", "x")],
        )
        self.assertEqual(count_comparisons(s), 7)
        # two components double the count
        self.assertEqual(count_comparisons(make(criteria=[crit(components=["a", "b"])])), 2 * 3)


class TestReturnValues(unittest.TestCase):
    def outcome(self, value):
        outs, bad, mism = normalize_return(crit(), value)
        return outs["c"], bool(bad), mism

    def test_true_false_none(self):
        self.assertEqual(self.outcome(True), (HOLDS, False, False))
        self.assertEqual(self.outcome(np.bool_(True)), (HOLDS, False, False))
        self.assertEqual(self.outcome(False), (FAILS, False, False))
        self.assertEqual(self.outcome(np.bool_(False)), (FAILS, False, False))
        self.assertEqual(self.outcome(None), (UNDEFINED, False, False))

    def test_other_types_are_bad_return(self):
        for value in (1, 0, 1.0, float("nan"), "yes", [True], np.float64(1.0), np.array([True])):
            self.assertEqual(self.outcome(value), (UNDEFINED, True, False), repr(value))

    def test_components_exact_keys(self):
        c = crit("a", components=["x", "y"])
        outs, bad, mism = normalize_return(c, {"x": True, "y": False})
        self.assertEqual(outs, {"a:x": HOLDS, "a:y": FAILS})
        self.assertFalse(mism or bad)

    def test_components_missing_extra_and_bad(self):
        c = crit("a", components=["x", "y"])
        outs, _, mism = normalize_return(c, {"x": True})
        self.assertEqual((outs["a:y"], mism), (UNDEFINED, True))
        outs, _, mism = normalize_return(c, {"x": True, "y": True, "z": True})
        self.assertEqual((outs["a:x"], outs["a:y"], mism), (HOLDS, HOLDS, True))
        outs, bad, mism = normalize_return(c, {"x": 3, "y": None})
        self.assertEqual((outs["a:x"], outs["a:y"], bad, mism), (UNDEFINED, UNDEFINED, {"a:x"}, False))

    def test_components_non_dict_returns(self):
        c = crit("a", components=["x", "y"])
        outs, bad, mism = normalize_return(c, True)
        self.assertEqual((set(outs.values()), bad, mism), ({UNDEFINED}, {"a:x", "a:y"}, True))
        outs, bad, mism = normalize_return(c, None)
        self.assertEqual((set(outs.values()), bad, mism), ({UNDEFINED}, set(), False))


class TestResolution(unittest.TestCase):
    def test_resolvable(self):
        self.assertTrue(is_resolvable(1e-6, 1.0))
        self.assertTrue(is_resolvable(-0.5, 2.0))
        self.assertTrue(is_resolvable(1e-300, 0.0))  # nothing to absorb against a zero scale

    def test_unresolvable(self):
        self.assertFalse(is_resolvable(0.0, 1.0))
        self.assertFalse(is_resolvable(1e-25, 1.0))
        self.assertFalse(is_resolvable(1e-17, 1.0))  # below half an ulp at scale 1
        self.assertFalse(is_resolvable(float("nan"), 1.0))
        self.assertFalse(is_resolvable(float("inf"), 1.0))
        self.assertFalse(is_resolvable(1.0, float("inf")))
        self.assertFalse(is_resolvable(1.0, float("nan")))
        self.assertFalse(is_resolvable("abc", 1.0))
        self.assertFalse(is_resolvable(None, 1.0))

    def test_ulp_boundary(self):
        self.assertTrue(is_resolvable(2.3e-16, 1.0))  # > ulp/2 (1.11e-16) and rounds up
        self.assertFalse(is_resolvable(1.0e-16, 1.0))


if __name__ == "__main__":
    unittest.main()
