"""Certificate structure and definedness in stochastic and deterministic modes (spec sections 7, 11)."""

import copy
import hashlib
import json
import os
import unittest

import _helpers
from _helpers import body, run_toy, toy_path
import kapi
from kapi import certificate

SPEC_BODY_FIELDS = (
    "kapi_version", "spec_version", "python_version", "numpy_version", "mode", "study",
    "m_comparisons", "alpha_per_bound", "components", "premise_map", "study_flags", "leak_log",
    "verdict", "non_claims",
)
SPEC_STUDY_FIELDS = (
    "name", "module_sha256", "allowed_files", "deterministic", "budget", "targets", "regimes",
    "worlds", "premises", "controls", "criteria",
)

DEFINED_TOYS = (
    "toy_good", "toy_good_det", "toy_lowpower", "toy_components_ok", "toy_undefined_none",
    "toy_dup_ids", "toy_import_leak", "toy_leak_open", "toy_nonreproducible", "toy_det_waived",
)


class TestEnvelope(unittest.TestCase):
    def test_envelope_shape_and_validation(self):
        for toy in DEFINED_TOYS:
            env = run_toy(toy)
            self.assertEqual(set(env), {"body", "body_sha256", "created_utc"}, toy)
            self.assertEqual(certificate.validate_envelope(env), [], toy)

    def test_body_has_all_spec_fields(self):
        b = body("toy_good")
        for field in SPEC_BODY_FIELDS:
            self.assertIn(field, b)
        for field in SPEC_STUDY_FIELDS:
            self.assertIn(field, b["study"])
        self.assertEqual(set(b["components"][0]), {"id", "regime", "verdict", "flags", "counts", "bounds", "errors", "unresolvable", "minus_check"})

    def test_timestamp_is_outside_the_hashed_body(self):
        env = run_toy("toy_good")
        self.assertNotIn("created_utc", env["body"])
        changed = dict(env, created_utc="1999-01-01T00:00:00Z")
        self.assertEqual(certificate.validate_envelope(changed), [])
        self.assertEqual(certificate.body_sha256(changed["body"]), env["body_sha256"])

    def test_hash_is_sha256_of_canonical_json(self):
        env = run_toy("toy_good")
        canonical = json.dumps(env["body"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(), env["body_sha256"])
        self.assertEqual(len(env["body_sha256"]), 64)

    def test_hash_survives_a_json_roundtrip(self):
        for toy in DEFINED_TOYS:
            env = run_toy(toy)
            loaded = json.loads(json.dumps(env, ensure_ascii=False))
            self.assertEqual(certificate.body_sha256(loaded["body"]), env["body_sha256"], toy)

    def test_tampering_is_detected(self):
        env = copy.deepcopy(run_toy("toy_good"))
        env["body"]["verdict"] = "WEAK"
        self.assertTrue(any("body_sha256" in p for p in certificate.validate_envelope(env)))
        env2 = copy.deepcopy(run_toy("toy_good"))
        del env2["body"]["leak_log"]
        self.assertTrue(certificate.validate_envelope(env2))
        env3 = copy.deepcopy(run_toy("toy_good"))
        env3["body"]["created_utc"] = "x"
        self.assertTrue(certificate.validate_envelope(env3))
        self.assertTrue(certificate.validate_envelope([]))

    def test_canonical_json_rules(self):
        self.assertEqual(certificate.canonical_json({"b": 1, "a": "ı"}), '{"a":"ı","b":1}')
        with self.assertRaises(ValueError):
            certificate.canonical_json({"x": float("nan")})
        self.assertEqual(certificate.jsonable({"v": (1.0, float("inf"), float("nan"))}), {"v": [1.0, "inf", "nan"]})


class TestContents(unittest.TestCase):
    def test_versions_and_non_claims(self):
        b = body("toy_good")
        self.assertEqual(b["kapi_version"], kapi.__version__)
        self.assertEqual(b["spec_version"], "0.5")
        self.assertEqual(len(b["non_claims"]), 3)
        self.assertIn("does not mean the hypothesis is true", b["non_claims"][0])
        self.assertTrue(b["known_limitations"])

    def test_mode_full_quick_and_counts(self):
        self.assertEqual(body("toy_good")["mode"], "full")
        self.assertEqual(body("toy_good")["components"][0]["counts"]["world:plus"]["n"], 100)
        quick = body("toy_good", quick=True)
        self.assertEqual(quick["mode"], "quick")
        self.assertEqual(quick["components"][0]["counts"]["world:plus"]["n"], 20)
        self.assertNotEqual(run_toy("toy_good")["body_sha256"], run_toy("toy_good", quick=True)["body_sha256"])

    def test_study_declarations_are_recorded(self):
        s = body("toy_good")["study"]
        self.assertEqual(s["name"], "toy_good")
        self.assertEqual(s["budget"], {"samples": 100, "quick_samples": 20, "base_seed": 20261105})
        self.assertEqual(s["targets"], {"power": 0.8, "size": 0.05, "alpha_family": 0.05})
        self.assertEqual(s["worlds"]["minus"], {"derived_from": "plus", "change": "mean 2 -> 0"})
        self.assertEqual(s["premises"], [{"id": "shift", "role": "tested", "criteria": ["mean_gt_1"], "magnitude": [2.0, 2.0]}])
        self.assertEqual(s["controls"], [{"id": "negate", "kind": "transform", "criteria": ["mean_gt_1"]}])
        self.assertEqual(s["criteria"][0]["tolerances"], {"gap": [0.5, 1.0]})
        self.assertEqual(s["regimes"], ["all"])
        with open(toy_path("toy_good"), "rb") as handle:
            self.assertEqual(s["module_sha256"], hashlib.sha256(handle.read()).hexdigest())

    def test_waiver_and_control_kind_world_recorded(self):
        self.assertIn("no meaningful negative control", body("toy_waived")["study"]["criteria"][0]["control_waiver"])
        self.assertEqual(body("toy_control_world")["study"]["controls"][0]["kind"], "world")

    def test_bonferroni_fields(self):
        b = body("toy_good")
        # 1 separation + 1 tested premise + 1 control + noise + zeros + null = 6 comparisons
        self.assertEqual(b["m_comparisons"], 6)
        self.assertAlmostEqual(b["alpha_per_bound"], 0.05 / 12)

    def test_bounds_and_premise_map(self):
        b = body("toy_good")
        c = b["components"][0]
        self.assertEqual(set(c["bounds"]), set(c["counts"]))
        for bound in c["bounds"].values():
            self.assertLessEqual(bound["lower"], bound["upper"])
        self.assertEqual(c["counts"]["world:plus"], {"holds": 100, "undefined": 0, "n": 100})
        self.assertEqual(b["premise_map"], {"shift": {"mean_gt_1": 1.0}})

    def test_expected_streams_present(self):
        streams = set(body("toy_good")["components"][0]["counts"])
        self.assertEqual(
            streams,
            {"world:plus", "world:minus", "world:null", "premise:shift", "control:negate", "probe:noise", "probe:zeros"},
        )
        shuffle = set(body("toy_shuffle_good")["components"][0]["counts"])
        self.assertIn("probe:shuffle:a,b", shuffle)

    def test_probe_notes_list_unchanged_keys(self):
        self.assertEqual(body("toy_good")["probe_unchanged_keys"], {"noise": [], "zeros": []})

    def test_allowed_files_are_hashed(self):
        entries = body("toy_allowed_file")["study"]["allowed_files"]
        with open(os.path.join(_helpers.TOYS, "allowed_data.txt"), "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(entries, [{"path": "allowed_data.txt", "sha256": digest}])
        self.assertEqual(body("toy_good")["study"]["allowed_files"], [])


class TestDefinedness(unittest.TestCase):
    def test_stochastic_and_deterministic_modes_compute(self):
        stochastic, deterministic = body("toy_good"), body("toy_good_det")
        self.assertFalse(stochastic["study"]["deterministic"])
        self.assertTrue(deterministic["study"]["deterministic"])
        counts = deterministic["components"][0]["counts"]
        self.assertTrue(all(v["n"] == 1 for v in counts.values()))
        self.assertEqual(deterministic["components"][0]["bounds"], {})
        self.assertEqual(counts["world:plus"], {"holds": 1, "undefined": 0, "n": 1})
        self.assertEqual(counts["world:minus"], {"holds": 0, "undefined": 0, "n": 1})

    def test_same_inputs_same_hash(self):
        for toy in ("toy_good", "toy_good_det", "toy_lowpower", "toy_components_ok", "toy_shuffle_good",
                    "toy_undefined_none", "toy_dup_ids", "toy_leak_open", "toy_import_leak"):
            first = kapi.run_gate(toy_path(toy))
            second = kapi.run_gate(toy_path(toy))
            self.assertEqual(first["body_sha256"], second["body_sha256"], toy)

    def test_hash_does_not_depend_on_working_directory(self):
        here = os.getcwd()
        try:
            os.chdir(os.path.dirname(_helpers.ROOT))
            other = kapi.run_gate(toy_path("toy_good"))
        finally:
            os.chdir(here)
        self.assertEqual(other["body_sha256"], run_toy("toy_good")["body_sha256"])

    def test_nonreproducible_study_gets_different_hashes(self):
        a = kapi.run_gate(toy_path("toy_nonreproducible"))["body_sha256"]
        b = kapi.run_gate(toy_path("toy_nonreproducible"))["body_sha256"]
        self.assertNotEqual(a, b)

    def test_changed_study_changes_hash(self):
        self.assertNotEqual(run_toy("toy_good")["body_sha256"], run_toy("toy_high_rate")["body_sha256"])

    def test_missing_study_file(self):
        with self.assertRaises(FileNotFoundError):
            kapi.run_gate(os.path.join(_helpers.TOYS, "does_not_exist.py"))


if __name__ == "__main__":
    unittest.main()
