"""The ``pattern_stats`` pass (spec 0.6, section 4, last paragraph) and its place in the run (section 1.2)."""

import json
import os
import shutil
import tempfile
import unittest

import numpy as np

import _helpers
from truth_gate import certificate, guard
from truth_gate.checks import build_plan, evaluate, make_sample, _call
from truth_gate.manifest import build_study, parse_manifest
from truth_gate.passes import QUANTILES
from truth_gate.sampling import sample_count, stream_rng

MANIFESTS = os.path.join(_helpers.ROOT, "tests", "manifests")

WORLD_PY = '''
import numpy as np


def plus(rng):
    return {"x": rng.normal(2.0, 1.0, 25), "y": rng.normal(1.0, 1.0, 25), "grid_y": np.array([0.9, 0.8, 0.6, 0.2])}


def minus(rng):
    return {"x": rng.normal(0.0, 1.0, 25), "y": rng.normal(1.0, 1.0, 25), "grid_y": np.array([0.4, 0.3, 0.2, 0.1])}


def null(rng):
    return {"x": rng.normal(-1.0, 1.0, 25), "y": rng.normal(1.0, 1.0, 25), "grid_y": np.array([0.4, 0.3, 0.2, 0.1])}


def sometimes_nan(rng):
    x = rng.normal(2.0, 1.0, 25)
    if rng.random() < 0.4:
        x[3] = np.nan
    return {"x": x, "y": rng.normal(1.0, 1.0, 25), "grid_y": np.array([0.9, 0.8, 0.6, 0.2])}


def fixed(rng):
    return {"x": np.array([1.0, 2.0, 3.0, 4.0]), "y": np.array([4.0, 3.0, 2.0, 1.0]), "grid_y": np.array([0.9, 0.8, 0.6, 0.2])}
'''


def threshold(cid="C", **kw):
    return {"id": cid, "pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0, **kw}


def manifest(criteria, plus="plus", minus="minus", deterministic=False, null=None, **extra):
    d = {
        "study": {"name": "t", "deterministic": deterministic},
        "worlds": {"plus": {"python": f"w.py:{plus}"}, "minus": {"python": f"w.py:{minus}", "change": "c"}},
        "criteria": criteria,
        "controls": [{"id": "neg", "criteria": [c["id"] for c in criteria],
                      "mutations": [{"op": "sign_flip", "column": "x"}]}],
    }
    if null:
        d["worlds"]["null"] = {"python": f"w.py:{null}"}
    d.update(extra)
    return d


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tg_pstats_")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        with open(os.path.join(self.dir, "w.py"), "w", encoding="utf-8") as handle:
            handle.write(WORLD_PY)

    def path(self, d):
        path = os.path.join(self.dir, "truthgate.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(d, handle)
        return path

    def body(self, d, quick=False):
        return certificate.run_gate(self.path(d), quick=quick)["body"]

    def study_of(self, path):
        with open(path, "rb") as handle:
            return build_study(parse_manifest(path, handle.read()))

    def samples(self, path, quick=False):
        """Samples of the plus / minus / null streams exactly as the engine makes them: {stream label: [data]}."""
        study = self.study_of(path)
        n = sample_count(study.deterministic, study.budget.samples, study.budget.quick_samples, quick)
        indices = range(1) if study.deterministic else range(n)
        out = {}
        for sd in (sd for sd in build_plan(study) if sd.kind == "world"):
            out[sd.ref] = []
        for i in indices:
            plus = _call(study.worlds["plus"].generate, stream_rng(study.budget.base_seed, "world:plus", i))
            for sd in (sd for sd in build_plan(study) if sd.kind == "world"):
                out[sd.ref].append(make_sample(study, sd, i, plus).data)
        return out

    @staticmethod
    def quantiles(values):
        return [float(v) for v in np.quantile(np.asarray(values, dtype=np.float64), QUANTILES)]

    def stat_of(self, entry):
        return [entry["q05"], entry["q50"], entry["q95"]]


class TestEqualsADirectRecomputation(Base):
    def test_difference_of_the_example_manifest(self):
        path = os.path.join(MANIFESTS, "trial_run.toml")
        body = certificate.run_gate(path)["body"]
        part = body["pattern_stats"]["C1"]["parts"][""]
        samples = self.samples(path)
        for stream in ("plus", "minus"):
            diffs = []
            for data in samples[stream]:
                y, g = data["yield"], data["group"]
                diffs.append(float(np.mean(y[g == "treated"]) - np.mean(y[g == "control"])))
            entry = part["streams"][stream]["difference"]
            self.assertEqual(entry["n_finite"], 200)
            self.assertEqual(self.stat_of(entry), self.quantiles(diffs))
        self.assertEqual(part["pattern"], "difference")
        self.assertEqual(part["thresholds"], {"op": ">=", "value": 0.5, "paired": False})
        self.assertNotIn("null", part["streams"])  # no null world declared

    def test_quick_mode_uses_the_quick_sample_count(self):
        path = self.path(manifest([threshold()]))
        body = certificate.run_gate(path, quick=True)["body"]
        entry = body["pattern_stats"]["C"]["parts"][""]["streams"]["plus"]["stat"]
        self.assertEqual(entry["n_finite"], 20)
        direct = [float(np.mean(d["x"])) for d in self.samples(path, quick=True)["plus"]]
        self.assertEqual(self.stat_of(entry), self.quantiles(direct))

    def test_threshold_with_the_null_world_and_the_same_samples_k1_k7_saw(self):
        path = self.path(manifest([threshold()], null="null"))
        body = certificate.run_gate(path)["body"]
        streams = body["pattern_stats"]["C"]["parts"][""]["streams"]
        self.assertEqual(sorted(streams), ["minus", "null", "plus"])
        samples = self.samples(path)
        for stream in ("plus", "minus", "null"):
            direct = [float(np.mean(d["x"])) for d in samples[stream]]
            self.assertEqual(self.stat_of(streams[stream]["stat"]), self.quantiles(direct))
        # the counted HOLDS of the engine agree with the statistic crossing the threshold
        comp = body["components"][0]
        self.assertEqual(comp["counts"]["world:plus"]["holds"], sum(float(np.mean(d["x"])) > 1.0 for d in samples["plus"]))
        self.assertEqual(comp["counts"]["world:null"]["holds"], sum(float(np.mean(d["x"])) > 1.0 for d in samples["null"]))

    def test_deterministic_study_uses_sample_index_zero_only(self):
        path = self.path(manifest([threshold(stat="max", value=1.0)], plus="fixed", minus="fixed", deterministic=True))
        body = certificate.run_gate(path)["body"]
        entry = body["pattern_stats"]["C"]["parts"][""]["streams"]["plus"]["stat"]
        self.assertEqual(entry, {"n_finite": 1, "q05": 4.0, "q50": 4.0, "q95": 4.0})

    def test_undefined_samples_are_excluded(self):
        path = self.path(manifest([threshold()], plus="sometimes_nan"))
        body = certificate.run_gate(path)["body"]
        entry = body["pattern_stats"]["C"]["parts"][""]["streams"]["plus"]["stat"]
        samples = self.samples(path)["plus"]
        defined = [float(np.mean(d["x"])) for d in samples if np.all(np.isfinite(d["x"]))]
        self.assertTrue(0 < len(defined) < 200)
        self.assertEqual(entry["n_finite"], len(defined))
        self.assertEqual(self.stat_of(entry), self.quantiles(defined))
        comp = body["components"][0]
        self.assertEqual(comp["counts"]["world:plus"]["undefined"], 200 - len(defined))  # the engine saw the same samples

    def test_quantiles_are_float64_without_rounding(self):
        body = self.body(manifest([threshold()]))
        entry = body["pattern_stats"]["C"]["parts"][""]["streams"]["plus"]["stat"]
        for key in ("q05", "q50", "q95"):
            self.assertIsInstance(entry[key], float)
        direct = [float(np.mean(d["x"])) for d in self.samples(self.path(manifest([threshold()])))["plus"]]
        self.assertEqual(entry["q50"], float(np.quantile(np.asarray(direct), 0.5)))
        self.assertNotEqual(entry["q50"], round(entry["q50"], 6))


class TestStructure(Base):
    def test_parts_of_combinators_are_keyed_by_position_path(self):
        inner = {"pattern": "any_of", "of": [
            {"pattern": "threshold", "x": "x", "stat": "min", "op": ">", "value": 0.0},
            {"pattern": "threshold", "x": "y", "stat": "max", "op": "<", "value": 9.0}]}
        crit = {"id": "K", "pattern": "all_of", "of": [
            {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}, inner]}
        path = self.path(manifest([crit]))
        body = certificate.run_gate(path)["body"]
        parts = body["pattern_stats"]["K"]["parts"]
        self.assertEqual(sorted(parts), ["0", "1.0", "1.1"])
        samples = self.samples(path)["plus"]
        direct = {"0": [np.mean(d["x"]) for d in samples], "1.0": [np.min(d["x"]) for d in samples],
                  "1.1": [np.max(d["y"]) for d in samples]}
        for path_key, values in direct.items():
            self.assertEqual(self.stat_of(parts[path_key]["streams"]["plus"]["stat"]), self.quantiles(values), path_key)
        self.assertEqual(parts["1.1"]["thresholds"], {"op": "<", "value": 9.0})

    def test_an_out_of_range_index_drops_only_that_leaf_from_the_statistics(self):
        """R-32 (audit F4): the other parts of the combinator keep their values; the bad leaf has none."""
        crit = {"id": "K", "pattern": "any_of", "of": [
            {"pattern": "threshold", "x": "x", "x_index": [0, 99], "stat": "mean", "op": ">", "value": 1.0},
            {"pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}]}
        body = self.body(manifest([crit]))
        parts = body["pattern_stats"]["K"]["parts"]
        self.assertEqual(parts["0"]["streams"]["plus"], {})  # every sample of this leaf was UNDEFINED
        self.assertEqual(parts["1"]["streams"]["plus"]["stat"]["n_finite"], 200)
        comp = body["components"][0]
        self.assertEqual(comp["counts"]["world:plus"]["undefined"], 0)  # any_of: the second leaf decides, Kleene

    def test_every_pattern_reports_its_statistics_and_thresholds(self):
        crits = [
            {"id": "ratio", "pattern": "ratio_band", "a": "x", "b": "y", "stat": "mean", "lo": 0.5, "hi": 5.0},
            {"id": "within", "pattern": "within", "a": "x", "b": "y", "tol": 3.0, "stat": "mean"},
            {"id": "within_all", "pattern": "within", "a": "x", "b": "y", "tol": 9.0, "mode": "all"},
            {"id": "rate", "pattern": "rate", "condition": {"column": "x", "op": ">", "value": 0.0}, "op": ">", "value": 0.5},
            {"id": "ci", "pattern": "ci_excludes", "x": "x", "stat": "mean", "side": "above", "value": 0.0, "B": 200},
            {"id": "ci2", "pattern": "ci_excludes", "a": "x", "b": "y", "side": "above", "value": 0.0, "B": 200},
            {"id": "lt", "pattern": "largest_true", "grid": [1, 2, 3, 4], "y": "grid_y", "op": ">=", "threshold": 0.5,
             "compare_to": {"value": 3}, "cmp": "=="},
            {"id": "mono", "pattern": "monotone", "x": "x", "y": "y", "direction": "increasing", "tol": 100.0},
            {"id": "diff", "pattern": "difference", "a": "x", "b": "y", "stat": "mean", "op": ">", "value": 0.0, "paired": True},
        ]
        d = manifest(crits)
        d["controls"] = []
        body = self.body(d)
        stats = body["pattern_stats"]
        expected = {
            "ratio": ("ratio_band", ["ratio"], {"lo": 0.5, "hi": 5.0}),
            "within": ("within", ["abs_difference"], {"tol": 3.0, "mode": "stat"}),
            "within_all": ("within", ["max_abs_difference"], {"tol": 9.0, "mode": "all"}),
            "rate": ("rate", ["rate"], {"op": ">", "value": 0.5, "condition": {"column": "x", "op": ">", "value": 0.0}}),
            "ci": ("ci_excludes", ["ci_hi", "ci_lo"], {"side": "above", "value": 0.0, "level": 0.95}),
            "ci2": ("ci_excludes", ["ci_hi", "ci_lo"], {"side": "above", "value": 0.0, "level": 0.95}),
            "lt": ("largest_true", ["largest", "reference"], None),
            "mono": ("monotone", ["max_backward_step"], {"direction": "increasing", "strict": False, "tol": 100.0}),
            "diff": ("difference", ["difference"], {"op": ">", "value": 0.0, "paired": True}),
        }
        self.assertEqual(sorted(stats), sorted(expected))
        for cid, (name, stat_names, thresholds) in expected.items():
            with self.subTest(cid=cid):
                part = stats[cid]["parts"][""]
                self.assertEqual(part["pattern"], name)
                self.assertEqual(sorted(part["streams"]["plus"]), stat_names)
                if thresholds is not None:
                    self.assertEqual(part["thresholds"], thresholds)
                for stream in ("plus", "minus"):
                    for entry in part["streams"][stream].values():
                        self.assertEqual(sorted(entry), ["n_finite", "q05", "q50", "q95"])
        self.assertEqual(stats["lt"]["parts"][""]["thresholds"]["grid"], [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(stats["lt"]["parts"][""]["streams"]["plus"]["reference"]["q50"], 3.0)
        self.assertEqual(stats["lt"]["parts"][""]["streams"]["plus"]["largest"]["q50"], 3.0)

    def test_python_criteria_have_no_pattern_stats(self):
        d = manifest([{"id": "P", "python": "w.py:crit_missing"}, threshold("T")])
        d["controls"] = []
        # the python criterion is not a pattern: only T is recorded
        with open(os.path.join(self.dir, "w.py"), "a", encoding="utf-8") as handle:
            handle.write("\n\ndef crit_missing(d):\n    return bool(np.mean(d['x']) > 1.0)\n")
        body = self.body(d)
        self.assertEqual(sorted(body["pattern_stats"]), ["T"])

    def test_no_pattern_criteria_gives_an_empty_record(self):
        with open(os.path.join(self.dir, "w.py"), "a", encoding="utf-8") as handle:
            handle.write("\n\ndef crit(d):\n    return bool(np.mean(d['x']) > 1.0)\n")
        d = manifest([{"id": "P", "python": "w.py:crit"}])
        self.assertEqual(self.body(d)["pattern_stats"], {})

    def test_load_error_certificates_carry_an_empty_pattern_stats(self):
        d = manifest([threshold()])
        d["criteria"] = []
        body = self.body(d)
        self.assertEqual(body["verdict"], "UNDEFINED")
        self.assertEqual(body["pattern_stats"], {})


class TestThePassNeverChangesTheEngineOutput(Base):
    def test_components_equal_a_plain_evaluation_of_the_same_study(self):
        path = self.path(manifest([threshold(), threshold("C2", stat="max")], null="null"))
        body = certificate.run_gate(path)["body"]
        with open(path, "rb") as handle:
            spec = parse_manifest(path, handle.read())
        with guard.armed(path):
            result = evaluate(build_study(spec), False)
        self.assertEqual(body["components"], certificate.jsonable(result["components"]))
        self.assertEqual(body["m_comparisons"], result["m_comparisons"])
        self.assertEqual(body["premise_map"], certificate.jsonable(result["premise_map"]))

    def test_pattern_stats_is_added_after_the_reproducibility_comparison(self):
        body = self.body(manifest([threshold()]))
        self.assertNotIn("K6_NONREPRODUCIBLE", body["study_flags"])
        self.assertIn("pattern_stats", body)
        self.assertEqual(certificate.validate_envelope(certificate.make_envelope(body)), [])

    def test_a_leak_inside_the_passes_is_logged_and_flagged(self):
        """The third guard log (taken after the passes) is appended to ``leak_log`` (spec 1.2)."""
        secret = os.path.join(self.dir, "secret.txt")
        with open(secret, "w", encoding="utf-8") as handle:
            handle.write("data")
        with open(os.path.join(self.dir, "w.py"), "a", encoding="utf-8") as handle:
            handle.write(
                "\n\nCALLS = [0]\n\n\ndef counting(rng):\n    CALLS[0] += 1\n    if CALLS[0] == 7:  # the first call of the passes\n"
                f"        open({secret!r}).read()\n    return {{'x': np.array([1.0, 2.0, 3.0, 4.0]), 'y': np.array([4.0, 3.0, 2.0, 1.0])}}\n"
            )
        d = manifest([threshold(stat="max")], plus="counting", minus="fixed", deterministic=True)
        body = self.body(d)
        # a deterministic study calls plus three times per evaluation: calls 1-6 belong to the two evaluations
        self.assertIn("K6_LEAK_ATTEMPT", body["study_flags"])
        self.assertEqual([os.path.basename(e["target"]) for e in body["leak_log"]], ["secret.txt"])
        self.assertNotIn("K6_NONREPRODUCIBLE", body["study_flags"])
        self.assertEqual(body["verdict"], "NOT_FALSIFIABLE")
        self.assertEqual(body["pattern_stats"]["C"]["parts"][""]["streams"]["plus"], {})  # the sample could not be made


if __name__ == "__main__":
    unittest.main()
