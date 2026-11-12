"""Truth_Gate 0.4, stage (c): the Node example and Node programs speaking ``tg-line/1`` (spec 0.6, sections 5 and 13).

Cross-language tests run when ``node`` is on ``PATH`` and are skipped (and reported as skipped) otherwise.
"""

import hashlib
import json
import os
import shutil
import tempfile
import unittest

import numpy as np

import _helpers
from test_external import SAMPLE, Base, run_cli
from truth_gate.external import ExternalError, ExternalTimeout

NODE = shutil.which("node")
EXAMPLE = os.path.join(_helpers.ROOT, "examples", "node_criterion")

PROGRAM = r"""
'use strict';
const { serve } = require('./tg_line');
serve({
  C(d, types) {
    if (d.x.length === 4 && Number.isNaN(d.x[1]) && d.x[2] === Infinity && d.x[3] === -Infinity) return 'HOLDS';
    return 'FAILS';
  },
  fails_with_error() { throw new Error('boom'); },
  comps(d) { return { a: 'HOLDS', b: 'FAILS', c: 'UNDEFINED' }; },
  shapes(d, types) {
    return JSON.stringify(types.empty.shape) === '[0,3]' && d.empty.length === 0 && d.s[0] === 'é\n' &&
      d.b[0] === true && types.n.dtype === 'int' && d.n[1][2] === 5 ? 'HOLDS' : 'FAILS';
  },
});
"""

SILENT = r"""
'use strict';
const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });
let first = true;
rl.on('line', (line) => {
  const msg = JSON.parse(line);
  if (msg.op === 'hello') process.stdout.write(JSON.stringify({ ok: true, tg: 'tg-line/1', rid: msg.rid }) + '\n');
  // never answers a criterion request
});
"""


@unittest.skipUnless(NODE, "node is not on PATH: the Node tests are skipped")
class TestNodeProgram(Base):
    def setUp(self):
        super().setUp()
        shutil.copyfile(os.path.join(EXAMPLE, "tg_line.js"), os.path.join(self.dir, "tg_line.js"))
        self.write("prog.js", PROGRAM)
        self.write("silent.js", SILENT)
        self.argv = ["node", "prog.js"]
        self.table = {"uses": ["prog.js", "tg_line.js", "silent.js"]}

    def test_outcomes_and_the_decoding_of_non_finite_floats(self):
        session = self.session(self.argv, self.table)
        fn = self.fn(session, self.argv, "C")
        self.assertIs(fn({"x": np.array([1.0, np.nan, np.inf, -np.inf])}), True)
        self.assertIs(fn({"x": np.array([1.0, 2.0, 3.0, 4.0])}), False)
        self.assertIs(session.procs[tuple(self.argv)].dead, False)

    def test_a_thrown_error_is_an_error_reply_and_the_process_keeps_serving(self):
        session = self.session(self.argv, self.table)
        with self.assertRaises(ExternalError):
            self.fn(session, self.argv, "fails_with_error")(SAMPLE)
        with self.assertRaises(ExternalError):  # an id the program does not know
            self.fn(session, self.argv, "nobody")(SAMPLE)
        self.assertIs(self.fn(session, self.argv, "C")({"x": np.array([1.0, 2.0, 3.0, 4.0])}), False)

    def test_components(self):
        session = self.session(self.argv, self.table)
        self.assertEqual(self.fn(session, self.argv, "comps")(SAMPLE), {"a": True, "b": False, "c": None})

    def test_shapes_strings_and_integers_arrive_intact(self):
        session = self.session(self.argv, self.table)
        data = {"empty": np.zeros((0, 3)), "s": np.array(["é\n", "x"]), "b": np.array([True]),
                "n": np.arange(6).reshape(2, 3)}
        self.assertIs(self.fn(session, self.argv, "shapes")(data), True)

    def test_a_silent_node_program_times_out_and_is_killed(self):
        argv = ["node", "silent.js"]
        session = self.session(argv, {**self.table, "request_timeout_s": 1})
        with self.assertRaises(ExternalTimeout):
            self.fn(session, argv)(SAMPLE)
        session.procs[tuple(argv)].popen.wait(timeout=10)

    def test_bye_ends_a_node_program_cleanly(self):
        session = self.session(self.argv, self.table)
        self.fn(session, self.argv, "C")(SAMPLE)
        self.close(session)
        proc = session.procs[tuple(self.argv)]
        self.assertEqual(proc.popen.returncode, 0)
        self.assertFalse(proc.failed)
        self.assertNotIn("external program failed", self.stderr_of_close)

    def test_the_executable_hash_is_the_hash_of_the_resolved_node(self):
        session = self.session(self.argv, self.table)
        with open(os.path.realpath(NODE), "rb") as handle:
            expected = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(session.commands_record(), [{"argv": self.argv, "sha256": expected}])


@unittest.skipUnless(NODE, "node is not on PATH: the Node tests are skipped")
class TestNodeExampleStudy(unittest.TestCase):
    def test_the_example_manifest_runs_and_is_falsifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "node_example.json")
            code, stdout, stderr = run_cli("check", os.path.join(EXAMPLE, "truthgate.toml"), "--out", out)
            self.assertEqual(code, 0, stdout + stderr)
            with open(out, encoding="utf-8") as handle:
                body = json.load(handle)["body"]
            code2, stdout2, stderr2 = run_cli("verify", out, os.path.join(EXAMPLE, "truthgate.toml"))
            self.assertEqual(code2, 0, stdout2 + stderr2)
        self.assertEqual(body["verdict"], "FALSIFIABLE")
        self.assertEqual(body["leak_log"], [])
        self.assertEqual(body["study_notes"], [{"note": "K6_EXTERNAL_UNGUARDED", "commands": [["node", "criterion.js"]]}])
        record = body["manifest"]
        self.assertEqual([f["path"] for f in record["uses_files"]], ["criterion.js", "tg_line.js"])
        for entry in record["uses_files"]:
            with open(os.path.join(EXAMPLE, entry["path"]), "rb") as handle:
                self.assertEqual(entry["sha256"], hashlib.sha256(handle.read()).hexdigest())
        self.assertEqual(record["commands"][0]["argv"], ["node", "criterion.js"])
        self.assertIn("study notes:", stdout)


if __name__ == "__main__":
    unittest.main()
