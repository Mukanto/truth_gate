"""Truth_Gate 0.4, stage (c): command criteria, protocol ``tg-line/1`` (spec 0.6, sections 1.2 and 5).

The external programs here are small Python scripts run with ``sys.executable`` (``FAKE``); the Node tests are in
``test_node_example.py``.  The fake program logs every request line to ``requests.log`` in its working folder, which is
how the tests see what the gate sent and in which folder the program ran.
"""

import contextlib
import hashlib
import io
import json
import os
import shutil
import signal
import sys
import tempfile
import time
import unittest
from unittest import mock

import numpy as np

import _helpers  # noqa: F401  (puts the repository root on sys.path)
from truth_gate import certificate, checks, cli, external, guard, minus
from truth_gate.common import ManifestError
from truth_gate.external import (
    ExternalDied, ExternalEncodingError, ExternalError, ExternalProtocolError, ExternalSession, ExternalTimeout,
    InvalidOutcome, decode_outcome, dumps_line, encode_array, encode_data,
)
from truth_gate.manifest import parse_manifest
from truth_gate.study import Criterion

FAKE = r'''
import json
import os
import sys
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "ok"
arg = sys.argv[2] if len(sys.argv) > 2 else None
count = 0


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def raw(text):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def note(name, value):
    with open(name, "w", encoding="utf-8") as handle:
        json.dump(value, handle)


if mode == "no_hello":
    time.sleep(30)
    sys.exit(0)
if mode == "exit_at_start":
    sys.stderr.write("startup-stderr-line\n")
    sys.exit(3)

for line in sys.stdin:
    with open("requests.log", "a", encoding="utf-8") as handle:
        handle.write(line)
    msg = json.loads(line)
    op = msg["op"]
    if op == "hello":
        if mode == "bad_hello":
            sys.stderr.write("hello-stderr-line\n")
            send({"ok": False, "tg": "tg-line/1", "rid": msg["rid"]})
        elif mode == "wrong_tg":
            send({"ok": True, "tg": "tg-line/2", "rid": msg["rid"]})
        elif mode == "hello_garbage":
            raw("this is not json")
        elif mode == "hello_wrong_rid":
            send({"ok": True, "tg": "tg-line/1", "rid": msg["rid"] + 1})
        else:
            send({"ok": True, "tg": "tg-line/1", "rid": msg["rid"]})
        continue
    if op == "bye":
        break
    count += 1
    rid = msg["rid"]
    if mode == "ok":
        send({"rid": rid, "outcome": "HOLDS"})
    elif mode == "mean":  # HOLDS iff mean(x) > 1.0, UNDEFINED for non-finite values
        xs = [float(v) for v in msg["data"]["x"]]
        if not xs or any(v != v or v in (float("inf"), float("-inf")) for v in xs):
            send({"rid": rid, "outcome": "UNDEFINED"})
        else:
            send({"rid": rid, "outcome": "HOLDS" if sum(xs) / len(xs) > 1.0 else "FAILS"})
    elif mode == "error_once":
        if count == 1:
            sys.stderr.write("error-stderr-line\n")
            send({"rid": rid, "error": "first request is refused"})
        else:
            send({"rid": rid, "outcome": "HOLDS"})
    elif mode == "hang":
        time.sleep(30)
    elif mode == "malformed":
        raw("{this is not json")
    elif mode == "nan_constant":
        raw('{"rid": %d, "outcome": NaN}' % rid)
    elif mode == "not_an_object":
        raw("[1, 2, 3]")
    elif mode == "wrong_rid":
        send({"rid": rid + 5, "outcome": "HOLDS"})
    elif mode == "bool_rid":
        send({"rid": True, "outcome": "HOLDS"})
    elif mode == "missing_rid":
        send({"outcome": "HOLDS"})
    elif mode == "neither":
        send({"rid": rid})
    elif mode == "both":
        send({"rid": rid, "outcome": "HOLDS", "error": "and an error"})
    elif mode == "die":
        if count > int(arg or "1"):
            sys.stderr.write("dying-secret-line\n")
            sys.stderr.flush()
            os._exit(2)
        send({"rid": rid, "outcome": "HOLDS"})
    elif mode == "components":
        send({"rid": rid, "outcome": {"a": "HOLDS", "b": "FAILS", "c": "UNDEFINED"}})
    elif mode == "invalid":
        send({"rid": rid, "outcome": "MAYBE" if count == 1 else "HOLDS"})
    elif mode == "stateful":  # the outcome depends on how often it was asked: not reproducible
        send({"rid": rid, "outcome": "HOLDS" if count % 7 < 4 else "FAILS"})
    elif mode == "env":
        note("env.json", sorted(os.environ))
        note("env_values.json", dict(os.environ))
        send({"rid": rid, "outcome": "HOLDS"})
    elif mode == "isolation":
        note("isolation.json", {
            "cwd_entries": sorted(os.listdir(".")),
            "secret_visible": os.path.exists("secret.txt"),
            "secret_up_one": os.path.exists(os.path.join("..", "secret.txt")),
        })
        send({"rid": rid, "outcome": "HOLDS"})
    else:
        raise SystemExit("unknown mode " + mode)
'''

WORLD_PY = '''
import numpy as np


def plus(rng):
    return {"x": rng.normal(2.0, 1.0, 30)}


def minus(rng):
    return {"x": rng.normal(0.0, 1.0, 30)}


def plus2(rng):
    return {"x": rng.normal(2.0, 1.0, 30), "y": rng.normal(0.0, 1.0, 30)}


def minus2(rng):  # the same x as plus2 under the pairing, only y differs
    return {"x": rng.normal(2.0, 1.0, 30), "y": rng.normal(5.0, 1.0, 30)}


def reads_x(d):
    return bool(np.mean(d["x"]) > 1.0)
'''

SAMPLE = {"x": np.array([1.0, 2.0, 3.0])}


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="tg_ext_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.dir = os.path.join(self.root, "study")
        os.makedirs(self.dir)
        self.write("fake_tg.py", FAKE)
        self.write("w.py", WORLD_PY)
        self.stderr_of_close = ""

    def write(self, name, text, root=None):
        path = os.path.join(root or self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    @staticmethod
    def fake(*args):
        return [sys.executable, "fake_tg.py", *args]

    def study(self, argv, external_table=None, **extra):
        d = {
            "study": {"name": "t"},
            "worlds": {"plus": {"python": "w.py:plus"}, "minus": {"python": "w.py:minus", "change": "mean 2 -> 0"}},
            "criteria": [{"id": "C", "command": argv}],
            "controls": [{"id": "neg", "criteria": ["C"], "mutations": [{"op": "sign_flip", "column": "x"}]}],
            "external": {"uses": ["fake_tg.py"], **(external_table or {})},
        }
        d.update(extra)
        return d

    def parse(self, d, name="truthgate.json"):
        path = self.write(name, json.dumps(d))
        with open(path, "rb") as handle:
            return parse_manifest(path, handle.read())

    def close(self, session):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            session.close()
        self.stderr_of_close += err.getvalue()

    def session(self, argv, external_table=None, start=True, **extra):
        session = ExternalSession(self.parse(self.study(argv, external_table, **extra)))
        self.addCleanup(self.close, session)
        if start:
            err = io.StringIO()
            try:
                with contextlib.redirect_stderr(err):  # a failed start prints the stderr tail of the program
                    session.start()
            finally:
                self.stderr_of_close += err.getvalue()
        return session

    def fn(self, session, argv, cid="C"):
        return session.criterion(cid, argv)

    def check(self, d, *extra):
        path = self.write("truthgate.json", json.dumps(d))
        out = os.path.join(self.root, "cert.json")
        if os.path.exists(out):
            os.remove(out)
        code, stdout, stderr = run_cli("check", path, "--out", out, *extra)
        cert = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as handle:
                cert = json.load(handle)
        return code, stdout, stderr, cert

    @staticmethod
    def requests(session):
        """Every request line the program received, parsed (the program logs them in its working folder)."""
        with open(os.path.join(session.workdir, "requests.log"), encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    @staticmethod
    def note(session, name):
        with open(os.path.join(session.workdir, name), encoding="utf-8") as handle:
            return json.load(handle)


# ---------------------------------------------------------------------------------------------------------------------
# The data codec (spec section 5, "Data codec")
# ---------------------------------------------------------------------------------------------------------------------

class TestCodec(unittest.TestCase):
    def test_non_finite_floats_are_strings(self):
        types, value = encode_array(np.array([1.5, np.nan, np.inf, -np.inf]))
        self.assertEqual(types, {"dtype": "float", "shape": [4]})
        self.assertEqual(value, [1.5, "NaN", "Infinity", "-Infinity"])

    def test_non_finite_floats_inside_nested_arrays(self):
        types, value = encode_array(np.array([[1.0, np.nan], [-np.inf, 4.0]]))
        self.assertEqual(types["shape"], [2, 2])
        self.assertEqual(value, [[1.0, "NaN"], ["-Infinity", 4.0]])

    def test_a_scalar_non_finite_float(self):
        self.assertEqual(encode_array(np.array(np.inf)), ({"dtype": "float", "shape": []}, "Infinity"))
        self.assertEqual(encode_array(np.array(2.5)), ({"dtype": "float", "shape": []}, 2.5))

    def test_finite_floats_round_trip_exactly(self):
        values = np.array([0.1, 1 / 3, 1e-320, 1.7976931348623157e308, -0.0, 5e-324])
        _, value = encode_array(values)
        back = json.loads(json.dumps(value))
        self.assertEqual(back, values.tolist())
        self.assertTrue(np.signbit(back[4]))

    def test_bool_str_and_int_dtypes(self):
        self.assertEqual(encode_array(np.array([True, False])), ({"dtype": "bool", "shape": [2]}, [True, False]))
        self.assertEqual(encode_array(np.array(["a", "é\n\"q\""])), ({"dtype": "str", "shape": [2]}, ["a", "é\n\"q\""]))
        self.assertEqual(encode_array(np.array([1, -2], dtype=np.int64)), ({"dtype": "int", "shape": [2]}, [1, -2]))
        self.assertEqual(encode_array(np.array([7], dtype=np.uint8))[0]["dtype"], "int")  # unsigned counts as int
        self.assertEqual(encode_array(np.array([1.5], dtype=np.float32))[0]["dtype"], "float")

    def test_empty_arrays_keep_their_shape_in_types(self):
        for shape in ((0,), (0, 3), (2, 0), (0, 0)):
            with self.subTest(shape=shape):
                types, value = encode_array(np.zeros(shape))
                self.assertEqual(types, {"dtype": "float", "shape": list(shape)})
                self.assertEqual(value, np.zeros(shape).tolist())
        self.assertEqual(encode_array(np.array([], dtype=bool))[0], {"dtype": "bool", "shape": [0]})
        self.assertEqual(encode_array(np.array([], dtype=str))[0], {"dtype": "str", "shape": [0]})

    def test_nested_arrays(self):
        types, value = encode_array(np.arange(12).reshape(2, 3, 2))
        self.assertEqual(types, {"dtype": "int", "shape": [2, 3, 2]})
        self.assertEqual(value, np.arange(12).reshape(2, 3, 2).tolist())

    def test_the_two_to_the_53_rule(self):
        limit = 2 ** 53
        encode_array(np.array([limit, -limit], dtype=np.int64))  # exactly +-2^53 is allowed
        for bad in (np.array([limit + 1], dtype=np.int64), np.array([-limit - 1], dtype=np.int64),
                    np.array([2 ** 63 - 1], dtype=np.int64), np.array([2 ** 64 - 1], dtype=np.uint64),
                    np.array([[0, limit + 1]], dtype=np.int64)):
            with self.subTest(bad=bad):
                with self.assertRaises(ExternalEncodingError):
                    encode_array(bad)

    def test_unsupported_dtypes_are_encoding_errors(self):
        for bad in (np.array([1 + 2j]), np.array([None, 1], dtype=object), np.array([b"a"]),
                    np.array(["2020-01-01"], dtype="datetime64[D]")):
            with self.subTest(dtype=bad.dtype):
                with self.assertRaises(ExternalEncodingError):
                    encode_array(bad)

    def test_encode_data_reads_every_key_through_items(self):
        recorder = minus.RecordingDict({"x": np.array([1.0]), "y": np.array([2.0])})
        types, payload = encode_data(recorder)
        self.assertEqual(sorted(types), ["x", "y"])
        self.assertTrue(recorder.all_read)  # so that K2_MINUS_UNREAD can never be raised for a command criterion

    def test_a_value_that_is_not_an_array_is_an_encoding_error(self):
        with self.assertRaises(ExternalEncodingError):
            encode_data({"x": [1.0, 2.0]})

    def test_a_line_is_ascii_json_without_raw_newlines(self):
        line = dumps_line({"op": "criterion", "data": {"s": ["é", "a\nb", " "]}})
        self.assertTrue(line.endswith(b"\n"))
        self.assertEqual(line.count(b"\n"), 1)
        line.decode("ascii")
        self.assertEqual(json.loads(line)["data"]["s"], ["é", "a\nb", " "])

    def test_non_finite_numbers_can_never_reach_a_line(self):
        with self.assertRaises(ValueError):
            dumps_line({"x": float("nan")})

    def test_outcome_decoding(self):
        self.assertIs(decode_outcome("HOLDS"), True)
        self.assertIs(decode_outcome("FAILS"), False)
        self.assertIsNone(decode_outcome("UNDEFINED"))
        self.assertEqual(decode_outcome({"a": "HOLDS", "b": "FAILS", "c": "UNDEFINED"}), {"a": True, "b": False, "c": None})
        for odd in ("MAYBE", "holds", True, None, 1, ["HOLDS"]):
            with self.subTest(odd=odd):
                self.assertIsInstance(decode_outcome(odd), InvalidOutcome)
                self.assertIsNone(checks._classify(decode_outcome(odd)))  # the engine files it as BAD_RETURN

    def test_what_the_program_receives(self):
        # The codec is exercised end to end in TestProtocol.test_the_request_as_the_program_sees_it.
        self.assertEqual(external.PROTOCOL, "tg-line/1")


# ---------------------------------------------------------------------------------------------------------------------
# Handshake (spec section 5, "Messages")
# ---------------------------------------------------------------------------------------------------------------------

class TestHandshake(Base):
    def test_a_good_handshake_starts_one_process_and_serves_requests(self):
        argv = self.fake("ok")
        session = self.session(argv)
        self.assertEqual(len(session.procs), 1)
        self.assertIs(self.fn(session, argv)(SAMPLE), True)
        requests = self.requests(session)
        self.assertEqual(requests[0], {"op": "hello", "tg": "tg-line/1", "rid": 0})

    def test_refused_handshakes_are_manifest_errors(self):
        for mode in ("bad_hello", "wrong_tg", "hello_garbage", "hello_wrong_rid"):
            with self.subTest(mode=mode):
                with self.assertRaises(ManifestError) as caught:
                    self.session(self.fake(mode))
                self.assertIn("handshake", str(caught.exception))
                self.assertIn("criteria[0].command", str(caught.exception))

    def test_no_hello_within_the_startup_timeout_is_a_manifest_error_and_the_process_is_killed(self):
        session = ExternalSession(self.parse(self.study(self.fake("no_hello"), {"startup_timeout_s": 1})))
        self.addCleanup(self.close, session)
        began = time.monotonic()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ManifestError) as caught:
            session.start()
        self.assertLess(time.monotonic() - began, 20)
        self.assertIn("handshake", str(caught.exception))
        proc = next(iter(session.procs.values()))
        proc.popen.wait(timeout=10)  # it was killed, not left running
        self.assertIsNotNone(proc.popen.returncode)

    def test_a_program_that_exits_at_start_is_a_manifest_error_and_its_stderr_tail_is_printed(self):
        d = self.study(self.fake("exit_at_start"))
        code, out, err, cert = self.check(d)
        self.assertEqual(code, 4)
        self.assertIsNone(cert)  # no certificate
        self.assertIn("handshake", err)
        self.assertIn("startup-stderr-line", err)  # printed to the terminal ...

    def test_stderr_never_enters_a_certificate(self):
        d = self.study(self.fake("error_once"))
        code, out, err, cert = self.check(d)
        self.assertIsNotNone(cert)
        self.assertNotIn("error-stderr-line", json.dumps(cert))
        self.assertNotIn("error-stderr-line", out)

    def test_a_failed_start_cleans_up_the_working_folder(self):
        session = ExternalSession(self.parse(self.study(self.fake("bad_hello"))))
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(ManifestError):
                session.start()
        self.assertFalse(os.path.exists(session.workdir))

    def test_a_second_command_failing_closes_the_first(self):
        d = self.study(self.fake("ok"))
        d["criteria"].append({"id": "D", "command": self.fake("bad_hello")})
        d["controls"][0]["criteria"] = ["C", "D"]
        session = ExternalSession(self.parse(d))
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(ManifestError) as caught:
                session.start()
        self.assertIn("criteria[1].command", str(caught.exception))
        first = session.procs[tuple(self.fake("ok"))]
        first.popen.wait(timeout=10)
        self.assertIsNotNone(first.popen.returncode)
        self.assertFalse(os.path.exists(session.workdir))


# ---------------------------------------------------------------------------------------------------------------------
# Requests, replies and failures (spec section 5, "Failures")
# ---------------------------------------------------------------------------------------------------------------------

class TestProtocol(Base):
    def test_rids_increase_by_one_with_every_request(self):
        argv = self.fake("ok")
        session = self.session(argv)
        fn = self.fn(session, argv)
        for _ in range(4):
            fn(SAMPLE)
        self.assertEqual([r["rid"] for r in self.requests(session)], [0, 1, 2, 3, 4])
        self.assertEqual([r["op"] for r in self.requests(session)], ["hello"] + ["criterion"] * 4)

    def test_the_request_as_the_program_sees_it(self):
        argv = self.fake("ok")
        session = self.session(argv)
        data = {
            "f": np.array([1.0, np.nan, np.inf, -np.inf]), "b": np.array([True, False]), "s": np.array(["a", "é\n"]),
            "empty": np.zeros((0, 3)), "grid": np.arange(6).reshape(2, 3), "u": np.array([7], dtype=np.uint8),
            "scalar": np.array(2.5),
        }
        self.fn(session, argv, "my_id")(data)
        request = self.requests(session)[-1]
        self.assertEqual(request["op"], "criterion")
        self.assertEqual(request["id"], "my_id")
        self.assertEqual(request["types"], {
            "f": {"dtype": "float", "shape": [4]}, "b": {"dtype": "bool", "shape": [2]},
            "s": {"dtype": "str", "shape": [2]}, "empty": {"dtype": "float", "shape": [0, 3]},
            "grid": {"dtype": "int", "shape": [2, 3]}, "u": {"dtype": "int", "shape": [1]},
            "scalar": {"dtype": "float", "shape": []},
        })
        self.assertEqual(request["data"], {
            "f": [1.0, "NaN", "Infinity", "-Infinity"], "b": [True, False], "s": ["a", "é\n"], "empty": [],
            "grid": [[0, 1, 2], [3, 4, 5]], "u": [7], "scalar": 2.5,
        })
        self.assertEqual(list(request["data"]), list(data))  # key order is the sample's

    def test_the_lines_the_program_receives_are_ascii(self):
        argv = self.fake("ok")
        session = self.session(argv)
        self.fn(session, argv)({"s": np.array(["é", "日本"])})
        with open(os.path.join(session.workdir, "requests.log"), "rb") as handle:
            handle.read().decode("ascii")

    def test_an_encoding_error_makes_the_outcome_undefined_without_costing_a_rid_or_the_process(self):
        argv = self.fake("ok")
        session = self.session(argv)
        fn = self.fn(session, argv)
        fn(SAMPLE)
        with self.assertRaises(ExternalEncodingError):
            fn({"x": np.array([2 ** 53 + 1], dtype=np.int64)})
        self.assertIs(fn({"x": np.array([2 ** 53], dtype=np.int64)}), True)  # the limit itself is fine
        self.assertEqual([r["rid"] for r in self.requests(session)], [0, 1, 2])
        self.assertFalse(session.procs[tuple(argv)].dead)

    def test_an_error_reply_makes_one_outcome_undefined_and_the_process_keeps_serving(self):
        argv = self.fake("error_once")
        session = self.session(argv)
        fn = self.fn(session, argv)
        with self.assertRaises(ExternalError):
            fn(SAMPLE)
        self.assertIs(fn(SAMPLE), True)
        self.assertIs(fn(SAMPLE), True)
        self.assertFalse(session.procs[tuple(argv)].dead)
        self.assertEqual(session.notes()[-1]["note"], "K6_EXTERNAL_UNGUARDED")  # no EXTERNAL_DIED

    def test_an_error_reply_is_recorded_by_the_engine_as_externalerror(self):
        argv = self.fake("error_once")
        session = self.session(argv)
        crit = Criterion("C", self.fn(session, argv))
        outcomes, bad, mismatch, error = checks.evaluate_criterion(crit, checks.Sample(dict(SAMPLE), None))
        self.assertEqual(outcomes, {"C": "UNDEFINED"})
        self.assertEqual(error, "ExternalError")

    def test_a_timeout_kills_the_process_and_every_later_request_is_undefined(self):
        argv = self.fake("hang")
        session = self.session(argv, {"request_timeout_s": 0.5})
        fn = self.fn(session, argv)
        began = time.monotonic()
        with self.assertRaises(ExternalTimeout):
            fn(SAMPLE)
        self.assertLess(time.monotonic() - began, 20)
        proc = session.procs[tuple(argv)]
        proc.popen.wait(timeout=10)  # killed
        self.assertTrue(proc.dead)
        for _ in range(3):
            with self.assertRaises(ExternalDied):
                fn(SAMPLE)
        self.assertEqual([n["note"] for n in session.notes()], ["K6_EXTERNAL_UNGUARDED", "EXTERNAL_DIED"])

    def test_protocol_violations_kill_the_process(self):
        modes = ("malformed", "nan_constant", "not_an_object", "wrong_rid", "bool_rid", "missing_rid", "neither")
        for mode in modes:
            with self.subTest(mode=mode):
                argv = self.fake(mode)
                session = self.session(argv)
                fn = self.fn(session, argv)
                with self.assertRaises(ExternalProtocolError):
                    fn(SAMPLE)
                proc = session.procs[tuple(argv)]
                proc.popen.wait(timeout=10)
                self.assertTrue(proc.dead)
                with self.assertRaises(ExternalDied):
                    fn(SAMPLE)
                self.assertEqual([n["note"] for n in session.notes()], ["K6_EXTERNAL_UNGUARDED", "EXTERNAL_DIED"])

    def test_a_reply_with_both_outcome_and_error_is_an_error(self):
        argv = self.fake("both")
        session = self.session(argv)
        with self.assertRaises(ExternalError):
            self.fn(session, argv)(SAMPLE)
        self.assertFalse(session.procs[tuple(argv)].dead)

    def test_death_is_detected_and_later_requests_are_undefined(self):
        argv = self.fake("die", "1")
        session = self.session(argv)
        fn = self.fn(session, argv)
        self.assertIs(fn(SAMPLE), True)
        with self.assertRaises(ExternalDied):  # it exits without replying to the second request
            fn(SAMPLE)
        with self.assertRaises(ExternalDied):
            fn(SAMPLE)
        self.assertEqual([n["note"] for n in session.notes()], ["K6_EXTERNAL_UNGUARDED", "EXTERNAL_DIED"])
        self.assertEqual(session.notes()[1]["commands"], [argv])

    def test_components_reply(self):
        argv = self.fake("components")
        session = self.session(argv)
        result = self.fn(session, argv)(SAMPLE)
        self.assertEqual(result, {"a": True, "b": False, "c": None})
        crit = Criterion("C", self.fn(session, argv), components=["a", "b", "c"])
        outcomes, bad, mismatch, error = checks.evaluate_criterion(crit, checks.Sample(dict(SAMPLE), None))
        self.assertEqual(outcomes, {"C:a": "HOLDS", "C:b": "FAILS", "C:c": "UNDEFINED"})
        self.assertFalse(mismatch)
        self.assertEqual(bad, set())

    def test_components_with_a_wrong_name_set_are_the_engines_mismatch(self):
        argv = self.fake("components")
        session = self.session(argv)
        crit = Criterion("C", self.fn(session, argv), components=["a", "b", "zzz"])
        outcomes, bad, mismatch, error = checks.evaluate_criterion(crit, checks.Sample(dict(SAMPLE), None))
        self.assertTrue(mismatch)
        self.assertEqual(outcomes["C:zzz"], "UNDEFINED")

    def test_an_invalid_outcome_is_a_bad_return_and_the_process_keeps_serving(self):
        argv = self.fake("invalid")
        session = self.session(argv)
        crit = Criterion("C", self.fn(session, argv))
        sample = checks.Sample(dict(SAMPLE), None)
        outcomes, bad, mismatch, error = checks.evaluate_criterion(crit, sample)
        self.assertEqual((outcomes, bad), ({"C": "UNDEFINED"}, {"C"}))
        outcomes, bad, mismatch, error = checks.evaluate_criterion(crit, sample)
        self.assertEqual((outcomes, bad), ({"C": "HOLDS"}, set()))

    def test_the_read_key_recording_call_is_a_real_request_and_every_key_counts_as_read(self):
        argv = self.fake("ok")
        session = self.session(argv)
        crit = Criterion("C", self.fn(session, argv))
        keys, everything = minus.record_read_keys(crit, {"x": np.array([1.0]), "y": np.array([2.0])})
        self.assertTrue(everything)
        self.assertEqual([r["op"] for r in self.requests(session)], ["hello", "criterion"])

    def test_one_process_per_distinct_argv(self):
        d = self.study(self.fake("ok"))
        d["criteria"].append({"id": "D", "command": self.fake("ok")})
        d["criteria"].append({"id": "E", "command": self.fake("mean")})
        d["controls"][0]["criteria"] = ["C", "D", "E"]
        session = ExternalSession(self.parse(d))
        self.addCleanup(self.close, session)
        session.start()
        self.assertEqual(session.commands(), [self.fake("ok"), self.fake("mean")])
        self.assertEqual(len(session.procs), 2)
        self.fn(session, self.fake("ok"), "C")(SAMPLE)
        self.fn(session, self.fake("ok"), "D")(SAMPLE)
        ok_log = [r for r in self.requests(session) if r["op"] != "hello"]
        self.assertEqual([r["id"] for r in ok_log], ["C", "D"])  # one process served both criteria
        self.assertEqual([r["rid"] for r in ok_log], [1, 2])

    def test_requests_and_a_kill_do_not_trip_the_armed_guard(self):
        argv = self.fake("hang")
        session = self.session(argv, {"request_timeout_s": 0.5})
        fn = self.fn(session, argv)
        with guard.armed(os.path.join(self.dir, "truthgate.json")):
            with self.assertRaises(ExternalTimeout):
                fn(SAMPLE)
            with self.assertRaises(ExternalDied):
                fn(SAMPLE)
            self.assertEqual(guard.take_log(), [])

    @unittest.skipUnless(os.name == "posix", "process groups exist only on POSIX")
    def test_a_posix_kill_reaches_the_process_group(self):
        script = (
            "import os, subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            "open('child.pid', 'w').write(str(child.pid))\n"
            "for line in sys.stdin:\n"
            "    import json\n"
            "    m = json.loads(line)\n"
            "    if m['op'] == 'hello':\n"
            "        print(json.dumps({'ok': True, 'tg': 'tg-line/1', 'rid': m['rid']}), flush=True)\n"
            "    else:\n"
            "        time.sleep(30)\n"
        )
        self.write("grand.py", script)
        argv = [sys.executable, "grand.py"]
        session = self.session(argv, {"uses": ["grand.py"], "request_timeout_s": 0.5})
        with open(os.path.join(session.workdir, "child.pid"), encoding="utf-8") as handle:
            child_pid = int(handle.read())
        with self.assertRaises(ExternalTimeout):
            self.fn(session, argv)(SAMPLE)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(child_pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        else:
            self.fail("the grandchild survived the kill of the process group")


GRAND = r'''
import json
import os
import subprocess
import sys
import time

pid_file, mode = sys.argv[1], sys.argv[2]
# The grandchild inherits standard input and output: it holds both pipes open after this program is killed.
grandchild = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"], stdin=sys.stdin, stdout=sys.stdout)
with open(pid_file, "w", encoding="utf-8") as handle:
    handle.write(str(grandchild.pid))
for line in sys.stdin:
    msg = json.loads(line)
    if msg["op"] == "hello":
        sys.stdout.write(json.dumps({"ok": True, "tg": "tg-line/1", "rid": msg["rid"]}) + "\n")
        sys.stdout.flush()
        if mode == "exit_after_hello":
            os._exit(0)
    elif msg["op"] == "criterion":
        time.sleep(1000)  # never answers: the request times out and the process is killed
    else:
        break
'''


class TestBoundedShutdown(Base):
    """Audit F1 (R-28 neighbourhood, spec 1.2): shutdown and kill never wait on a pipe or on a reader thread."""

    BOUND_S = 12.0  # the grandchild lives 25 s: a shutdown that waits for its pipe cannot meet this

    def setUp(self):
        super().setUp()
        self.write("grand.py", GRAND)
        self.pid_file = os.path.join(self.root, "grandchild.pid")
        self.addCleanup(self.kill_grandchild)

    def grandchild_pid(self):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                with open(self.pid_file, encoding="utf-8") as handle:
                    return int(handle.read())
            except (OSError, ValueError):
                time.sleep(0.05)
        self.fail("the grandchild never reported its pid")

    def kill_grandchild(self):
        """Test hygiene on platforms where the gate cannot reach grandchildren (Windows): kill it by pid."""
        try:
            with open(self.pid_file, encoding="utf-8") as handle:
                pid = int(handle.read())
            os.kill(pid, signal.SIGKILL if hasattr(signal, "SIGKILL") else signal.SIGTERM)
        except (OSError, ValueError):
            pass

    def argv(self, mode="never_answer"):
        return [sys.executable, "grand.py", self.pid_file, mode]

    def test_close_after_a_timeout_returns_in_bounded_time_although_a_grandchild_holds_the_pipes(self):
        argv = self.argv()
        session = self.session(argv, {"uses": ["grand.py"], "request_timeout_s": 0.5})
        with self.assertRaises(ExternalTimeout):
            self.fn(session, argv)(SAMPLE)
        started = time.monotonic()
        self.close(session)
        self.assertLess(time.monotonic() - started, self.BOUND_S)

    def test_check_finishes_and_writes_its_certificate_although_a_grandchild_holds_the_pipes(self):
        d = self.study(self.argv(), {"uses": ["grand.py"], "request_timeout_s": 0.5})
        started = time.monotonic()
        code, _out, _err, cert = self.check(d)
        self.assertLess(time.monotonic() - started, 15.0)  # a bound; the old shutdown waited for the 25 s grandchild
        self.assertIsNotNone(cert)
        self.assertNotEqual(code, 4)
        self.assertIn("EXTERNAL_DIED", [n["note"] for n in cert["body"]["study_notes"]])

    @unittest.skipUnless(os.name == "posix", "process groups exist only on POSIX")
    def test_a_posix_check_leaves_no_grandchild_behind(self):
        d = self.study(self.argv(), {"uses": ["grand.py"], "request_timeout_s": 0.5})
        self.check(d)
        pid = self.grandchild_pid()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.1)
        self.fail("the grandchild survived the kill of the process group")

    @unittest.skipUnless(os.name == "posix", "process groups exist only on POSIX")
    def test_a_posix_kill_signals_the_group_although_the_direct_child_already_exited(self):
        argv = self.argv("exit_after_hello")
        session = self.session(argv, {"uses": ["grand.py"], "request_timeout_s": 0.5})
        pid = self.grandchild_pid()
        proc = session.procs[tuple(argv)]
        proc.popen.wait(timeout=10)  # the direct child is gone, the grandchild still lives in its group
        os.kill(pid, 0)
        proc.kill()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            time.sleep(0.1)
        self.fail("kill() skipped the group because the direct child had already exited")

    def test_the_main_thread_never_closes_a_pipe_of_a_process(self):
        """The Popen pipe objects are closed at launch; the threads own plain descriptors (no lock to wait on)."""
        argv = self.fake("ok")
        session = self.session(argv)
        popen = session.procs[tuple(argv)].popen
        self.assertTrue(popen.stdout.closed)
        self.assertTrue(popen.stdin.closed)
        self.assertEqual(self.fn(session, argv)(SAMPLE), True)


# ---------------------------------------------------------------------------------------------------------------------
# argv resolution (spec section 5, "Process")
# ---------------------------------------------------------------------------------------------------------------------

class TestArgvResolution(Base):
    def test_a_missing_executable_is_a_manifest_error_exit_4_without_a_certificate(self):
        d = self.study(["tg-no-such-program-anywhere", "x"])
        with self.assertRaises(ManifestError) as caught:
            self.session(["tg-no-such-program-anywhere", "x"])
        self.assertIn("criteria[0].command", str(caught.exception))
        self.assertIn("not found", str(caught.exception))
        code, out, err, cert = self.check(d)
        self.assertEqual(code, 4)
        self.assertIsNone(cert)
        self.assertIn("not found", err)

    def test_a_directory_is_not_an_executable(self):
        os.makedirs(os.path.join(self.dir, "adir"))
        with self.assertRaises(ManifestError):
            external.resolve_executable(os.path.join(self.dir, "adir"), "criteria[0].command", self.dir)

    def test_cmd_and_bat_files_are_rejected_on_windows_with_a_hint(self):
        for name in ("tool.cmd", "tool.bat", "TOOL.CMD"):
            with self.subTest(name=name):
                path = self.write(name, "@echo off\r\n")
                os.chmod(path, 0o755)
                with mock.patch.object(external, "IS_WINDOWS", True):
                    with self.assertRaises(ManifestError) as caught:
                        external.resolve_executable(path, "criteria[0].command", self.dir)
                text = str(caught.exception)
                self.assertIn("call the interpreter", text)
                self.assertIn('["node", "criteria.js"]', text)

    def test_other_extensions_are_rejected_on_windows(self):
        path = self.write("tool.vbs", "x")
        os.chmod(path, 0o755)
        with mock.patch.object(external, "IS_WINDOWS", True):
            with self.assertRaisesRegex(ManifestError, r"\.exe or \.com"):
                external.resolve_executable(path, "criteria[0].command", self.dir)

    def test_exe_and_com_pass_the_windows_rule_and_are_realpath_resolved(self):
        for name in ("prog.exe", "prog.com"):
            path = self.write(name, "x")
            os.chmod(path, 0o755)
            with mock.patch.object(external, "IS_WINDOWS", True):
                self.assertEqual(external.resolve_executable(path, "w", self.dir), os.path.realpath(path))

    def test_a_relative_path_with_a_separator_is_relative_to_the_manifest_folder(self):
        path = self.write(os.path.join("bin", "prog.exe"), "x")
        os.chmod(path, 0o755)
        with mock.patch.object(external, "IS_WINDOWS", True):
            self.assertEqual(external.resolve_executable(os.path.join("bin", "prog.exe"), "w", self.dir),
                             os.path.realpath(path))

    def test_a_bare_name_is_resolved_with_the_inherited_path(self):
        bindir = os.path.join(self.root, "bin")
        os.makedirs(bindir)
        path = os.path.join(bindir, "tgprog.exe")
        with open(path, "w") as handle:
            handle.write("x")
        os.chmod(path, 0o755)
        with mock.patch.dict(os.environ, {"PATH": bindir + os.pathsep + os.environ.get("PATH", "")}):
            self.assertEqual(external.resolve_executable("tgprog", "w", self.dir), os.path.realpath(path))

    def test_the_realpath_is_validated_and_hashed_and_the_path_resolved_path_is_launched(self):
        """R-28 (audit F10): ``locate_executable`` returns both, so a symlinked ``python`` keeps its environment."""
        real_dir = os.path.join(self.dir, "real")
        os.makedirs(real_dir)
        real_path = os.path.realpath(self.write(os.path.join("real", "prog.exe"), "x"))
        link_path = os.path.join(self.dir, "bin", "prog.exe")  # stands for a symlink that does not exist here
        os.makedirs(os.path.dirname(link_path))
        with open(link_path, "w") as handle:
            handle.write("y")
        os.chmod(link_path, 0o755)
        with mock.patch.object(external, "IS_WINDOWS", True), \
                mock.patch.object(external.os.path, "realpath", lambda p: real_path if p == link_path else p):
            launch, real = external.locate_executable(link_path, "w", self.dir)
            self.assertEqual(os.path.normcase(launch), os.path.normcase(link_path))
            self.assertEqual(real, real_path)
            self.assertEqual(external.resolve_executable(link_path, "w", self.dir), real_path)

    @unittest.skipUnless(os.name == "posix", "a symlink needs no privilege only on POSIX")
    def test_a_symlinked_program_is_started_through_the_link_and_the_target_is_hashed(self):
        link = os.path.join(self.dir, "pylink")
        os.symlink(sys.executable, link)
        argv = [link, "fake_tg.py", "ok"]
        launched = []
        real_popen = external.subprocess.Popen

        def spy(args, *a, **k):
            launched.append(args[0])
            return real_popen(args, *a, **k)

        with mock.patch.object(external.subprocess, "Popen", spy):
            session = self.session(argv)
        self.assertEqual(launched, [link])
        self.assertEqual(session.commands_record()[0]["sha256"], hashlib.sha256(open(os.path.realpath(sys.executable), "rb").read()).hexdigest())

    def test_the_executable_is_hashed_into_the_certificate_record(self):
        argv = self.fake("ok")
        session = self.session(argv)
        with open(os.path.realpath(sys.executable), "rb") as handle:
            expected = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(session.commands_record(), [{"argv": argv, "sha256": expected}])

    def test_an_executable_that_cannot_be_started_is_a_manifest_error(self):
        path = self.write("notprogram.exe", "this is not an executable")
        os.chmod(path, 0o755)
        with self.assertRaises(ManifestError) as caught:
            self.session([path])
        self.assertIn("criteria[0].command", str(caught.exception))


# ---------------------------------------------------------------------------------------------------------------------
# Working folder and environment (spec section 5, "Process")
# ---------------------------------------------------------------------------------------------------------------------

class TestIsolation(Base):
    def test_the_program_runs_in_a_private_folder_with_only_the_declared_files(self):
        self.write("secret.txt", "the real result")
        self.write("data/table.txt", "uses file")
        self.write("allowed.txt", "allowed file")
        argv = self.fake("isolation")
        d = self.study(argv, {"uses": ["fake_tg.py", "data/table.txt"]})
        d["study"]["allow_paths"] = ["allowed.txt"]
        session = ExternalSession(self.parse(d))
        self.addCleanup(self.close, session)
        session.start()
        self.assertIs(self.fn(session, argv)(SAMPLE), True)
        seen = self.note(session, "isolation.json")
        self.assertFalse(seen["secret_visible"])  # a relative path to a study file does not resolve
        self.assertFalse(seen["secret_up_one"])
        self.assertEqual(sorted(seen["cwd_entries"]), sorted(["fake_tg.py", "data", "allowed.txt", "requests.log"]))
        self.assertTrue(os.path.isfile(os.path.join(session.workdir, "data", "table.txt")))  # relative layout kept
        self.assertNotEqual(os.path.realpath(session.workdir), os.path.realpath(self.dir))

    def test_copies_are_byte_identical_and_hashed(self):
        self.write("data/blob.bin", "x")
        with open(os.path.join(self.dir, "data", "blob.bin"), "wb") as handle:
            handle.write(b"\x00\x01\r\n\xff")
        argv = self.fake("ok")
        d = self.study(argv, {"uses": ["fake_tg.py", "data/blob.bin"]})
        session = ExternalSession(self.parse(d))
        self.addCleanup(self.close, session)
        session.start()
        with open(os.path.join(session.workdir, "data", "blob.bin"), "rb") as handle:
            self.assertEqual(handle.read(), b"\x00\x01\r\n\xff")
        self.assertEqual(session.uses_record, [
            {"path": "data/blob.bin", "sha256": hashlib.sha256(b"\x00\x01\r\n\xff").hexdigest()},
            {"path": "fake_tg.py", "sha256": hashlib.sha256(FAKE.encode("utf-8")).hexdigest()},
        ])

    def test_a_file_outside_the_manifest_folder_is_a_manifest_error(self):
        self.write("outside.txt", "x", root=self.root)
        argv = self.fake("ok")
        d = self.study(argv, {"uses": ["fake_tg.py", "../outside.txt"]})
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ManifestError) as caught:
            ExternalSession(self.parse(d)).start()
        self.assertIn("external.uses[1]", str(caught.exception))
        self.assertIn("inside the manifest's folder", str(caught.exception))

    def test_the_working_folder_is_deleted_after_close(self):
        argv = self.fake("ok")
        session = self.session(argv)
        folder = session.workdir
        self.assertTrue(os.path.isdir(folder))
        self.close(session)
        self.assertFalse(os.path.exists(folder))

    def test_a_failure_to_delete_the_working_folder_is_a_warning(self):
        argv = self.fake("ok")
        session = self.session(argv)
        err = io.StringIO()
        with mock.patch.object(external.shutil, "rmtree", side_effect=OSError("busy")):
            with contextlib.redirect_stderr(err):
                session.close()
        self.assertIn("warning", err.getvalue())
        self.assertIn("could not delete the working folder", err.getvalue())
        shutil.rmtree(session.workdir, ignore_errors=True)


class TestEnvironment(Base):
    ALLOWED = {"PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMROOT", "TEMP", "TMP", "LANG",
               "TG_PROTOCOL"}
    ADDED_BY_PYTHON = {"LC_CTYPE", "__PYVENV_LAUNCHER__", "PYTHONUTF8", "PYTHONIOENCODING"}

    def names_seen(self, external_table=None):
        argv = self.fake("env")
        session = self.session(argv, external_table)
        self.fn(session, argv)(SAMPLE)
        return {n.upper() for n in self.note(session, "env.json")}, self.note(session, "env_values.json")

    def test_an_arbitrary_variable_is_not_passed_and_the_protocol_variables_are(self):
        with mock.patch.dict(os.environ, {"TG_TEST_SECRET": "s3cret"}):
            names, values = self.names_seen()
        self.assertNotIn("TG_TEST_SECRET", names)
        self.assertLessEqual(names, self.ALLOWED | self.ADDED_BY_PYTHON)
        values = {k.upper(): v for k, v in values.items()}
        self.assertEqual(values["TG_PROTOCOL"], "tg-line/1")
        self.assertEqual(values["LANG"], "C.UTF-8")
        self.assertEqual(values["PATH"], os.environ["PATH"])  # current values, not defaults

    def test_a_name_listed_in_external_env_is_passed_with_its_current_value(self):
        with mock.patch.dict(os.environ, {"TG_TEST_LISTED": "visible", "TG_TEST_OTHER": "hidden"}):
            names, values = self.names_seen({"env": ["TG_TEST_LISTED", "TG_TEST_NOT_SET"]})
        self.assertIn("TG_TEST_LISTED", names)
        self.assertNotIn("TG_TEST_OTHER", names)
        self.assertNotIn("TG_TEST_NOT_SET", names)  # a listed name that is not set is simply absent
        self.assertEqual({k.upper(): v for k, v in values.items()}["TG_TEST_LISTED"], "visible")

    def test_the_environment_builder_alone(self):
        with mock.patch.dict(os.environ, {"PATH": "p", "ZZZ": "1", "KEEP": "k"}, clear=True):
            env = external.build_env(["KEEP", "ABSENT"])
        self.assertEqual(env, {"PATH": "p", "KEEP": "k", "LANG": "C.UTF-8", "TG_PROTOCOL": "tg-line/1"})

    def test_invalid_env_names_are_validation_errors(self):
        for bad in ("", "A=B"):
            with self.subTest(bad=bad):
                with self.assertRaises(ManifestError):
                    self.parse(self.study(self.fake("ok"), {"env": [bad]}))


# ---------------------------------------------------------------------------------------------------------------------
# Whole runs (spec sections 1.2, 5 and 9)
# ---------------------------------------------------------------------------------------------------------------------

class TestWholeRuns(Base):
    def test_a_command_criterion_gives_the_same_counts_as_the_equivalent_pattern(self):
        argv = self.fake("mean")
        code, out, err, cert = self.check(self.study(argv))
        pattern = self.study(argv)
        pattern["criteria"] = [{"id": "C", "pattern": "threshold", "x": "x", "stat": "mean", "op": ">", "value": 1.0}]
        del pattern["external"]
        code_p, out_p, err_p, cert_p = self.check(pattern)
        self.assertEqual(code, code_p, out + err)
        a, b = cert["body"], cert_p["body"]
        self.assertEqual(a["verdict"], b["verdict"])
        self.assertEqual(a["components"][0]["counts"], b["components"][0]["counts"])
        self.assertEqual(a["components"][0]["flags"], b["components"][0]["flags"])
        self.assertEqual(a["leak_log"], [])  # nothing was blocked: requests and replies are not file or socket events
        self.assertEqual(certificate.validate_envelope(cert), [])

    def test_the_certificate_records_commands_uses_and_notes(self):
        argv = self.fake("mean")
        code, out, err, cert = self.check(self.study(argv))
        body = cert["body"]
        record = body["manifest"]
        with open(os.path.realpath(sys.executable), "rb") as handle:
            exe_sha = hashlib.sha256(handle.read()).hexdigest()
        self.assertEqual(record["commands"], [{"argv": argv, "sha256": exe_sha}])
        self.assertEqual(record["uses_files"], [{"path": "fake_tg.py", "sha256": hashlib.sha256(FAKE.encode()).hexdigest()}])
        self.assertEqual(body["study_notes"], [{"note": "K6_EXTERNAL_UNGUARDED", "commands": [argv]}])
        self.assertIn("command", json.dumps(record["parsed"]))
        text = json.dumps(cert)
        self.assertNotIn(os.path.realpath(sys.executable), text)  # no machine path in the hashed body

    def test_the_table_output_ends_with_the_study_notes(self):
        argv = self.fake("mean")
        code, out, err, cert = self.check(self.study(argv))
        table = cli.format_table(cert["body"]).splitlines()
        self.assertEqual(table[-2], "study notes:")
        self.assertTrue(table[-1].startswith("  K6_EXTERNAL_UNGUARDED: "))
        self.assertIn("fake_tg.py mean", table[-1])
        self.assertIn(table[-1], out)
        # ... and the lines before the notes are the 0.3 table
        self.assertTrue(table[-3].startswith("mode: full"))

    def test_a_python_study_prints_no_notes(self):
        code, out, err = run_cli("check", os.path.join(_helpers.ROOT, "examples", "01_tautology", "fixed.py"),
                                 "--out", os.path.join(self.root, "py.json"))
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("study notes", out)

    def test_a_manifest_without_a_command_has_no_notes_and_no_session(self):
        d = self.study(self.fake("ok"))
        d["criteria"] = [{"id": "C", "python": "w.py:reads_x"}]
        del d["external"]
        code, out, err, cert = self.check(d)
        self.assertEqual(cert["body"]["study_notes"], [])
        self.assertEqual(cert["body"]["manifest"]["commands"], [])
        self.assertNotIn("study notes", out)

    def test_a_timeout_inside_a_run_is_undefined_with_the_note_and_the_stderr_tail_on_the_terminal(self):
        code, out, err, cert = self.check(self.study(self.fake("hang"), {"request_timeout_s": 0.5}))
        body = cert["body"]
        self.assertEqual(code, 3)
        self.assertEqual(body["verdict"], "UNDEFINED")
        self.assertIn("K1_UNDEFINED", body["components"][0]["flags"])
        self.assertEqual([n["note"] for n in body["study_notes"]], ["K6_EXTERNAL_UNGUARDED", "EXTERNAL_DIED"])
        errors = body["components"][0]["errors"]["world:plus"]
        self.assertEqual(sum(v for k, v in errors.items() if k in ("ExternalTimeout", "ExternalDied")), 200)
        self.assertIn("ExternalTimeout", errors)
        self.assertIn("EXTERNAL_DIED", out)
        self.assertIn("external program failed", err)  # printed after the guard was disarmed

    def test_death_inside_a_run(self):
        code, out, err, cert = self.check(self.study(self.fake("die", "50")))
        body = cert["body"]
        self.assertEqual((code, body["verdict"]), (3, "UNDEFINED"))
        self.assertIn("EXTERNAL_DIED", [n["note"] for n in body["study_notes"]])
        self.assertIn("ExternalDied", json.dumps(body["components"][0]["errors"]))
        self.assertIn("dying-secret-line", err)  # the last stderr lines of a failed process reach the terminal ...
        self.assertNotIn("dying-secret-line", json.dumps(cert))  # ... and never the certificate

    def test_state_in_the_program_shows_up_as_nonreproducible(self):
        code, out, err, cert = self.check(self.study(self.fake("stateful")))
        self.assertIn("K6_NONREPRODUCIBLE", cert["body"]["study_flags"])

    def test_minus_unread_is_never_raised_for_a_command_criterion(self):
        worlds = {"plus": {"python": "w.py:plus2"}, "minus": {"python": "w.py:minus2", "change": "y 0 -> 5"}}
        python_study = self.study(self.fake("ok"), worlds=worlds)
        python_study["criteria"] = [{"id": "C", "python": "w.py:reads_x"}]
        del python_study["external"]
        code, out, err, cert = self.check(python_study)
        self.assertIn("K2_MINUS_UNREAD", cert["body"]["components"][0]["flags"])  # the Python criterion reads only x
        command_study = self.study(self.fake("mean"), worlds=worlds)
        code, out, err, cert = self.check(command_study)
        comp = cert["body"]["components"][0]
        self.assertNotIn("K2_MINUS_UNREAD", comp["flags"])
        self.assertEqual(comp["minus_check"]["read_keys"], "ALL")

    def test_verify_reruns_a_command_study(self):
        d = self.study(self.fake("mean"))
        code, out, err, cert = self.check(d)
        out_path = os.path.join(self.root, "cert.json")
        code, out, err = run_cli("verify", out_path, os.path.join(self.dir, "truthgate.json"))
        self.assertEqual(code, 0, out + err)

    def test_the_processes_and_the_working_folder_are_gone_after_a_run(self):
        before = {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_external_")}
        self.check(self.study(self.fake("mean")))
        after = {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_external_")}
        self.assertEqual(after - before, set())

    def test_a_manifest_error_in_a_command_study_starts_nothing(self):
        d = self.study(self.fake("mean"))
        d["zzz"] = 1
        before = {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_external_")}
        code, out, err, cert = self.check(d)
        after = {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_external_")}
        self.assertEqual(code, 4)
        self.assertEqual(after - before, set())

    def test_a_study_error_after_the_start_is_exit_3_and_still_cleans_up(self):
        d = self.study(self.fake("mean"))
        d["controls"][0]["criteria"] = ["nope"]  # 0.3's own validation: a control for an unknown criterion
        before = {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_external_")}
        code, out, err, cert = self.check(d)
        after = {n for n in os.listdir(tempfile.gettempdir()) if n.startswith("truth_gate_external_")}
        self.assertEqual(code, 3)
        self.assertEqual(cert["body"]["verdict"], "UNDEFINED")
        self.assertEqual([n["note"] for n in cert["body"]["study_notes"]], ["K6_EXTERNAL_UNGUARDED"])
        self.assertEqual(after - before, set())

    def test_the_command_key_is_no_longer_refused_as_unimplemented(self):
        spec = self.parse(self.study(self.fake("ok")))
        self.assertEqual(spec.criteria[0].kind, "command")


if __name__ == "__main__":
    unittest.main()
