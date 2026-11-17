"""The designer's hand-written outcomes for tests/acceptance_d (D-R4-9, R3-6).

``tests/acceptance_d/EXPECTED.json`` is written by the designer, not by a tool.  Its schema::

    {"<folder>": {"attributable": bool, "generic": bool, "declared": bool, "qualifying_streams": [sorted list]},
     "_note": "keys that start with an underscore are notes and are ignored"}

This test runs ``attributable.py`` (the command-line tool) on every folder of ``tests/acceptance_d`` and compares those four
fields with the entry.  A folder without an entry fails (one failure per folder).  The tool's rule is not changed to fit the
entries: a difference is a finding.
"""
import json
import os
import unittest

import common

ROOT = os.path.join(common.HERE, "acceptance_d")
FIELDS = ("attributable", "generic", "declared", "qualifying_streams")


def folders():
    return sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)))


def entries():
    with open(os.path.join(ROOT, "EXPECTED.json"), encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def run_attributable(folder):
    d = os.path.join(ROOT, folder)
    r = common.run_tool("attributable.py", "--faulty", os.path.join(d, "faulty.json"), "--fixed", os.path.join(d, "fixed.json"),
                        "--expected-file", os.path.join(d, "expected_flags.json"), "--case", folder)
    if r.returncode != 0:
        raise AssertionError(f"attributable.py failed on {folder}: {r.stderr}")
    out = json.loads(r.stdout)
    return {"attributable": out["attributable"], "generic": out["generic"], "declared": out["declared"],
            "qualifying_streams": sorted(q["stream"] for q in out["qualifying"])}


class AcceptanceExpectedTests(unittest.TestCase):
    def test_every_folder_has_an_entry_that_the_tool_reproduces(self):
        exp = entries()
        for folder in folders():
            with self.subTest(folder):
                self.assertIn(folder, exp, f"{folder} has no entry in EXPECTED.json")
                entry = exp[folder]
                self.assertEqual(set(entry), set(FIELDS), f"{folder}: an entry has exactly the four fields")
                self.assertEqual(entry["qualifying_streams"], sorted(entry["qualifying_streams"]))
                got = run_attributable(folder)
                self.assertEqual({k: entry[k] for k in FIELDS}, got, folder)

    def test_no_entry_for_a_folder_that_does_not_exist(self):
        self.assertEqual(sorted(set(entries()) - set(folders())), [])

    def test_the_note_keys_are_ignored(self):
        with open(os.path.join(ROOT, "EXPECTED.json"), encoding="utf-8") as f:
            raw = json.load(f)
        self.assertEqual(set(raw) - set(entries()), {k for k in raw if k.startswith("_")})


if __name__ == "__main__":
    unittest.main()
