import copy
import json
import os
import tempfile
import unittest

import common
import toy_case
from structure_stat import (PackageRootError, StatisticError, import_truth_gate, load_study_module, structure_stat)

SEED = 20261117


def toy_module(phi):
    return load_study_module(toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": phi}, "reference.py", "test")


class StructureStatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_truth_gate(common.PKG)
        cls.mod = toy_module(0.9)
        cls.private = toy_case.private(0.9)

    def test_result_fields_and_values(self):
        r = structure_stat(self.mod, self.private, "minus", 60, SEED, common.PKG)
        self.assertEqual(set(r), {"mean", "sd", "values_head", "share_beyond_half"})
        self.assertEqual(len(r["values_head"]), 5)
        self.assertAlmostEqual(r["mean"], 0.9, delta=0.08)  # sample lag-1 autocorrelation of an AR(1) with phi 0.9
        self.assertGreater(r["sd"], 0)
        self.assertEqual(r["share_beyond_half"], 1.0)  # all samples are far beyond 0.45

    def test_first_values_come_from_the_named_stream(self):
        from truth_gate.sampling import stream_rng
        r = structure_stat(self.mod, self.private, "plus", 7, SEED, common.PKG)
        for i, v in enumerate(r["values_head"]):
            d = self.mod.STUDY.worlds["plus"].generate(stream_rng(SEED, "structure:plus", i))
            y = d["y"] - d["y"].mean()
            self.assertEqual(v, float(y[1:] @ y[:-1] / (y @ y)))
        # another seed or world gives other numbers
        self.assertNotEqual(r["values_head"], structure_stat(self.mod, self.private, "plus", 7, SEED + 1, common.PKG)["values_head"])
        self.assertNotEqual(r["values_head"], structure_stat(self.mod, self.private, "minus", 7, SEED, common.PKG)["values_head"])

    def test_deterministic(self):
        a = structure_stat(self.mod, self.private, "minus", 20, SEED, common.PKG)
        b = structure_stat(self.mod, self.private, "minus", 20, SEED, common.PKG)
        self.assertEqual(a, b)

    def test_share_threshold_and_direction(self):
        # values: first lag-1 autocorrelations are ~0.9; the half-way point is null + 0.5 (note - null)
        p = copy.deepcopy(self.private)
        s = p["structure_statistic"]
        mean = structure_stat(self.mod, self.private, "minus", 100, SEED, common.PKG)["mean"]
        s["note_value"] = 2 * mean  # half-way point = the mean: some samples reach it, some do not
        share_g = structure_stat(self.mod, p, "minus", 100, SEED, common.PKG)["share_beyond_half"]
        s["direction"] = "less"
        share_l = structure_stat(self.mod, p, "minus", 100, SEED, common.PKG)["share_beyond_half"]
        self.assertAlmostEqual(share_g + share_l, 1.0, places=9)  # no sample sits exactly on the boundary
        self.assertTrue(0.0 < share_g < 1.0)
        # a non-zero null shifts the half-way point: null mean-0.1, note mean+0.1
        s.update(direction="greater", null_value=mean - 0.1, note_value=mean + 0.1)  # half-way point = mean
        r = structure_stat(self.mod, p, "minus", 100, SEED, common.PKG)
        vals = structure_stat(self.mod, self.private, "minus", 100, SEED, common.PKG)  # same samples, same statistic
        self.assertEqual(r["mean"], vals["mean"])
        self.assertTrue(0.0 < r["share_beyond_half"] < 1.0)

    def test_set_by_brief(self):
        p = toy_case.private(0.9, set_by_brief=True)
        r = structure_stat(self.mod, p, "minus", 10, SEED, common.PKG)
        self.assertEqual(set(r), {"set_by_brief", "mean"})
        self.assertIs(r["set_by_brief"], True)

    def test_statistic_must_be_a_finite_float(self):
        for code, what in (("def stat(d):\n    return float('nan')\n", "nan"),
                           ("def stat(d):\n    return float('inf')\n", "inf"),
                           ("def stat(d):\n    return 'x'\n", "string"),
                           ("def stat(d):\n    return None\n", "None"),
                           ("def stat(d):\n    return d['missing']\n", "KeyError"),
                           ("def stat(d):\n    return math.pi\n", "no math in the globals"),
                           ("x = 1\n", "no stat"),
                           ("def stat(d:\n", "syntax error")):
            with self.subTest(what):
                p = copy.deepcopy(self.private)
                p["structure_statistic"]["code"] = code
                with self.assertRaises(StatisticError):
                    structure_stat(self.mod, p, "minus", 3, SEED, common.PKG)

    def test_statistic_cannot_change_the_sample(self):
        p = copy.deepcopy(self.private)
        p["structure_statistic"]["code"] = "def stat(d):\n    d['y'][:] = 0.0\n    return float(d['y'].sum()) + 1.0\n"
        a = structure_stat(self.mod, p, "minus", 3, SEED, common.PKG)
        self.assertEqual(a["values_head"], [1.0, 1.0, 1.0])

    def test_bad_arguments(self):
        with self.assertRaises(ValueError):
            structure_stat(self.mod, self.private, "null", 5, SEED, common.PKG)
        with self.assertRaises(ValueError):
            structure_stat(self.mod, self.private, "minus", 0, SEED, common.PKG)

    def test_unique_module_names_per_call(self):
        a, b = toy_module(0.5), toy_module(0.5)
        self.assertNotEqual(a.__name__, b.__name__)

    def test_package_root_must_hold_the_gate(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(PackageRootError):
                import_truth_gate(t)  # the gate is already imported from elsewhere
        self.assertIs(import_truth_gate(common.PKG), import_truth_gate(common.PKG))


class StructureStatCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.study = os.path.join(self.tmp.name, "reference.py")
        self.private = os.path.join(self.tmp.name, "PRIVATE.json")
        with open(self.study, "w", encoding="utf-8", newline="\n") as f:
            f.write(toy_case.REFERENCE % {"claim": toy_case.CLAIM, "phi": 0.9})
        with open(self.private, "w", encoding="utf-8") as f:
            json.dump(toy_case.private(0.9), f)

    def args(self, **over):
        a = {"--study": self.study, "--private": self.private, "--world": "minus", "--samples": 30, "--seed": SEED,
             "--package-root": common.PKG}
        a.update(over)
        return [x for kv in a.items() for x in kv]

    def test_cli_prints_json_equal_to_the_function(self):
        r = common.run_tool("structure_stat.py", *self.args())
        self.assertEqual(r.returncode, 0, r.stderr)
        import_truth_gate(common.PKG)
        expected = structure_stat(toy_module(0.9), toy_case.private(0.9), "minus", 30, SEED, common.PKG)
        self.assertEqual(json.loads(r.stdout), expected)

    def test_cli_usage_errors(self):
        self.assertEqual(common.run_tool("structure_stat.py", *self.args(**{"--world": "null"})).returncode, 2)
        self.assertEqual(common.run_tool("structure_stat.py", *self.args(**{"--study": self.study + ".x"})).returncode, 2)
        self.assertEqual(common.run_tool("structure_stat.py", *self.args(**{"--package-root": self.tmp.name})).returncode, 2)
        self.assertEqual(common.run_tool("structure_stat.py", *self.args(**{"--samples": 0})).returncode, 2)

    def test_cli_uncomputable_statistic_exits_1(self):
        p = toy_case.private(0.9)
        p["structure_statistic"]["code"] = "def stat(d):\n    return float('nan')\n"
        with open(self.private, "w", encoding="utf-8") as f:
            json.dump(p, f)
        r = common.run_tool("structure_stat.py", *self.args())
        self.assertEqual(r.returncode, 1)
        self.assertIn("non-finite", r.stderr)


if __name__ == "__main__":
    unittest.main()
