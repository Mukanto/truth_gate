"""External programs for ``command`` criteria: protocol ``tg-line/1`` (spec 0.6, sections 1.2 and 5).

This is the only module of the package that imports ``subprocess`` (spec section 1.1, item 8).

Life cycle, as in spec section 1.2:

* :meth:`ExternalSession.start` runs **before** the leak guard is armed.  It resolves and hashes every executable, copies
  the ``[external] uses`` files and the ``allow_paths`` into a fresh working folder, starts one process per distinct
  argv and completes the handshake.  Any failure is a :class:`~truth_gate.common.ManifestError` (exit code 4).
* During the run the engine calls the function returned by :meth:`ExternalSession.criterion`.  Every call is one
  request; its failures are exceptions (``ExternalError``, ``ExternalTimeout`` ...) that the 0.3 engine turns into an
  UNDEFINED outcome, recording only the exception name.  Nothing here starts a process, so the armed guard is not
  triggered (killing one is allowed).
* :meth:`ExternalSession.close` runs **after** the guard is disarmed: ``bye``, wait 5 s, kill the rest, print the stderr
  tails of failed processes, delete the working folder.

Standard error never enters the certificate.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import queue
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Optional

import numpy as np

from .common import fail, is_int

PROTOCOL = "tg-line/1"
PASSED_ENV = ("PATH", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "SYSTEMROOT", "TEMP", "TMP")
MAX_INTEGER = 2 ** 53  # spec section 5, data codec: integers outside +-2^53 are an encoding error
BYE_WAIT_S = 5.0
REAP_JOIN_S = 1.0  # a reader or writer thread may stay blocked (a grandchild holds the pipe): never wait long
STDERR_TAIL_LINES = 20
IS_WINDOWS = os.name == "nt"  # a module attribute so that tests can exercise the Windows rules everywhere

NOTE_UNGUARDED = "K6_EXTERNAL_UNGUARDED"
NOTE_DIED = "EXTERNAL_DIED"

_DTYPE_NAMES = {"b": "bool", "i": "int", "u": "int", "f": "float", "U": "str"}
_OUTCOMES = {"HOLDS": True, "FAILS": False, "UNDEFINED": None}


# --------------------------------------------------------------------------
# Outcome exceptions: the engine records ``type(exc).__name__`` (spec section 5, "Failures")
# --------------------------------------------------------------------------

class ExternalError(Exception):
    """The program replied ``{"rid": k, "error": ...}``: this outcome is UNDEFINED, the process keeps serving."""


class ExternalTimeout(Exception):
    """No reply within ``request_timeout_s``: the process was killed."""


class ExternalProtocolError(Exception):
    """A reply that is not JSON, has a wrong or missing ``rid`` or carries neither ``outcome`` nor ``error``."""


class ExternalDied(Exception):
    """The process is no longer running (it exited, was killed, or an earlier request failed fatally)."""


class ExternalEncodingError(Exception):
    """The sample cannot be encoded for the protocol (an unsupported dtype or an integer outside +-2^53)."""


class InvalidOutcome:
    """A reply value that is none of the three outcome strings: the 0.3 engine files it as ``BAD_RETURN``."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f"InvalidOutcome({self.value!r})"


# --------------------------------------------------------------------------
# Data codec (gate to program), spec section 5
# --------------------------------------------------------------------------

def _non_finite_to_strings(value: Any) -> Any:
    if isinstance(value, list):
        return [_non_finite_to_strings(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")
    return value


def encode_array(array: np.ndarray) -> tuple:
    """``({"dtype": ..., "shape": [...]}, nested list)`` of one array (spec section 5, "Data codec")."""
    name = _DTYPE_NAMES.get(array.dtype.kind)
    if name is None:
        raise ExternalEncodingError(f"unsupported dtype {array.dtype}")
    if array.dtype.kind in "iu" and array.size:
        if int(array.max()) > MAX_INTEGER or int(array.min()) < -MAX_INTEGER:
            raise ExternalEncodingError("an integer outside +-2^53 cannot be sent without losing precision")
    value = array.tolist()
    if array.dtype.kind == "f" and array.size and not bool(np.all(np.isfinite(array))):
        value = _non_finite_to_strings(value)
    return {"dtype": name, "shape": [int(n) for n in array.shape]}, value


def encode_data(data: Any) -> tuple:
    """``(types, data)`` for a sample.  Reads every key through ``items()``, so that the read-key recording of 0.3
    (``RecordingDict``) sees all keys as read (spec section 5, "Read-key recording")."""
    types: dict = {}
    payload: dict = {}
    for key, array in data.items():
        if not isinstance(array, np.ndarray):
            raise ExternalEncodingError(f"key {key!r} is not an array")
        types[key], payload[key] = encode_array(array)
    return types, payload


def decode_outcome(value: Any) -> Any:
    """Map the reply's ``outcome`` to what the 0.3 engine expects (True / False / None, or a dict of them).

    A value that is none of the three outcome strings becomes an :class:`InvalidOutcome`, which the engine reports as
    ``BAD_RETURN`` (an UNDEFINED outcome); the process keeps serving.
    """
    def one(item: Any) -> Any:
        if isinstance(item, str) and item in _OUTCOMES:
            return _OUTCOMES[item]
        return InvalidOutcome(item)

    if isinstance(value, dict):
        return {str(k): one(v) for k, v in value.items()}
    return one(value)


def _reject_constant(name: str):
    raise ValueError(f"non-standard JSON constant {name}")


def dumps_line(message: dict) -> bytes:
    """One protocol line: compact JSON, ASCII only (so it is valid UTF-8 whatever the program's locale), ``\\n``."""
    return (json.dumps(message, ensure_ascii=True, allow_nan=False, separators=(",", ":")) + "\n").encode("ascii")


# --------------------------------------------------------------------------
# Executables and the environment
# --------------------------------------------------------------------------

def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_executable(argv0: str, where: str, base_dir: str) -> tuple:
    """``(launch_path, real_path)`` of ``argv[0]`` (spec section 5, "Process"; R-28).

    ``launch_path`` is what the inherited ``PATH`` resolves (absolute, symlinks kept: a symlinked ``python`` of a virtual
    environment must stay the path the process is started with, or the environment is lost).  ``real_path`` is its
    ``os.path.realpath``: the file that is validated and hashed into the certificate.

    A relative name that contains a path separator is taken relative to the manifest's folder (spec section 3: paths
    are relative to the manifest).  The real file must be readable; on Windows an ``.exe`` or ``.com``.
    """
    candidate = argv0
    if (os.sep in argv0 or (os.altsep and os.altsep in argv0)) and not os.path.isabs(argv0):
        candidate = os.path.join(base_dir, argv0)
    found = shutil.which(candidate)
    if found is None:
        fail(where, f"executable not found on PATH (or not executable): {argv0}")
    if not os.path.isabs(found):
        found = os.path.join(os.getcwd(), found)
    real = os.path.realpath(found)
    if not os.path.isfile(real) or not os.access(real, os.R_OK):
        fail(where, f"the executable is not a readable file: {argv0}")
    if IS_WINDOWS:
        ext = os.path.splitext(real)[1].lower()
        if ext in (".cmd", ".bat"):
            fail(where, f"{argv0} resolves to a {ext} file, which cannot be started directly; call the interpreter "
                        "instead (for example [\"node\", \"criteria.js\"])")
        if ext not in (".exe", ".com"):
            fail(where, f"on Windows the executable must be an .exe or .com file: {argv0}")
    return found, real


def resolve_executable(argv0: str, where: str, base_dir: str) -> str:
    """The realpath of ``argv[0]`` (see :func:`locate_executable`); the file that is validated and hashed."""
    return locate_executable(argv0, where, base_dir)[1]


def build_env(extra_names: list) -> dict:
    """The restricted environment of spec section 5: nothing else than these variables is passed."""
    env: dict = {}
    for name in tuple(PASSED_ENV) + tuple(extra_names):
        if name in os.environ:
            env[name] = os.environ[name]
    env["LANG"] = "C.UTF-8"
    env["TG_PROTOCOL"] = PROTOCOL
    return env


# --------------------------------------------------------------------------
# One process
# --------------------------------------------------------------------------

_EOF = object()  # the reader saw the end of the process's standard output
_BROKEN = object()  # the writer could not write to the process's standard input


class _Process:
    """One external program with its reader and writer threads (spec section 5)."""

    def __init__(self, argv: list, executable: str, exe_sha256: str, request_timeout_s: float) -> None:
        self.argv = list(argv)
        self.executable = executable
        self.exe_sha256 = exe_sha256
        self.request_timeout_s = request_timeout_s
        self.next_rid = 0
        self.dead = False  # not usable any more (killed, died, or closed)
        self.died_in_run = False  # killed or found dead before the orderly shutdown: the note EXTERNAL_DIED
        self.failed = False  # its standard error tail is printed after the guard
        self.popen: Optional[subprocess.Popen] = None
        self.stderr_file = None
        self._replies: queue.Queue = queue.Queue()
        self._writes: queue.Queue = queue.Queue()
        self._read_fd = -1
        self._write_fd = -1
        self._reader: Optional[threading.Thread] = None
        self._writer: Optional[threading.Thread] = None

    # -- life cycle --------------------------------------------------------

    def launch(self, env: dict, cwd: str) -> None:
        self.stderr_file = tempfile.TemporaryFile()
        kwargs: dict = {}
        if not IS_WINDOWS:
            kwargs["start_new_session"] = True  # a kill reaches the whole process group
        self.popen = subprocess.Popen(  # noqa: S603 - argv list, never a shell
            [self.executable] + self.argv[1:], cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.stderr_file, close_fds=True, **kwargs,
        )
        # The two threads work on *duplicated* descriptors and the Popen pipe objects are closed right away.  A
        # closing call on a buffered pipe waits for the lock of a thread that is blocked in a read or a write, and a
        # grandchild that inherited the pipe keeps that read or write blocked for ever (audit F1); with plain integer
        # descriptors the main thread never touches a pipe again, so no shutdown path can wait on one.  Each thread
        # closes its own descriptor when it ends.
        self._read_fd = os.dup(self.popen.stdout.fileno())
        self._write_fd = os.dup(self.popen.stdin.fileno())
        self.popen.stdout.close()
        self.popen.stdin.close()
        self._reader = threading.Thread(target=self._read_loop, name="tg-reader", daemon=True)
        self._writer = threading.Thread(target=self._write_loop, name="tg-writer", daemon=True)
        self._reader.start()
        self._writer.start()

    def _read_loop(self) -> None:
        fd = self._read_fd
        pending = b""
        try:
            while True:
                chunk = os.read(fd, 1 << 16)
                if not chunk:
                    break
                pending += chunk
                *lines, pending = pending.split(b"\n")
                for line in lines:
                    self._replies.put(line + b"\n")
            if pending:
                self._replies.put(pending)  # an unterminated last line, as readline() would return it
        except (OSError, ValueError):
            pass
        self._replies.put(_EOF)
        try:
            os.close(fd)
        except OSError:
            pass

    def _write_loop(self) -> None:
        fd = self._write_fd
        try:
            while True:
                item = self._writes.get()
                if item is None:
                    break
                view = memoryview(item)
                while len(view):
                    view = view[os.write(fd, view[:1 << 20]):]
        except (OSError, ValueError):
            self._replies.put(_BROKEN)
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def kill(self) -> None:
        """Kill the process (the group on POSIX); never starts anything, so the armed guard allows it.

        On POSIX the group is signalled even if the direct child has already exited: a grandchild may still be in it,
        and a group id is not reused while a member lives.  Bounded: nothing here waits.
        """
        self.dead = True
        self._writes.put(None)
        popen = self.popen
        if popen is None:
            return
        try:
            if hasattr(os, "killpg") and not IS_WINDOWS:
                try:
                    os.killpg(popen.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    if popen.poll() is None:
                        popen.kill()
            elif popen.poll() is None:
                popen.kill()
        except OSError:
            pass

    def _fatal(self) -> None:
        """A request failed in a way that ends the process: kill it, remember it (note ``EXTERNAL_DIED``)."""
        self.died_in_run = True
        self.failed = True
        self.kill()

    # -- one request/reply exchange ---------------------------------------

    def _exchange(self, message: dict, timeout: float) -> dict:
        """Send ``message``, return the reply object whose ``rid`` matches.  Any anomaly kills the process."""
        rid = message["rid"]
        self._writes.put(dumps_line(message))
        try:
            item = self._replies.get(timeout=timeout)
        except queue.Empty:
            self._fatal()
            raise ExternalTimeout(f"no reply within {timeout} s") from None
        if item is _EOF or item is _BROKEN:
            self._fatal()
            raise ExternalDied("the external program ended without replying")
        try:
            reply = json.loads(item.decode("utf-8"), parse_constant=_reject_constant)
        except (UnicodeDecodeError, ValueError):
            self._fatal()
            raise ExternalProtocolError("the reply is not a JSON line") from None
        if not isinstance(reply, dict) or not is_int(reply.get("rid")) or reply["rid"] != rid:
            self._fatal()
            raise ExternalProtocolError("the reply has a wrong or missing rid")
        return reply

    def handshake(self, startup_timeout_s: float) -> None:
        """``hello`` within ``startup_timeout_s`` (spec section 5, "Messages"); raises one of the outcome exceptions."""
        rid = self.next_rid
        self.next_rid += 1
        reply = self._exchange({"op": "hello", "tg": PROTOCOL, "rid": rid}, startup_timeout_s)
        if reply.get("ok") is not True or reply.get("tg") != PROTOCOL:
            self._fatal()
            raise ExternalProtocolError(f"the handshake reply is not {{\"ok\": true, \"tg\": \"{PROTOCOL}\"}}")

    def call(self, criterion_id: str, data: Any) -> Any:
        """One ``criterion`` request.  Returns True / False / None (or a dict of them) for the 0.3 engine."""
        if self.dead:
            raise ExternalDied("the external program is not running")
        types, payload = encode_data(data)  # an encoding error costs no rid
        rid = self.next_rid
        self.next_rid += 1
        reply = self._exchange(
            {"op": "criterion", "id": criterion_id, "rid": rid, "types": types, "data": payload},
            self.request_timeout_s,
        )
        if "error" in reply:
            raise ExternalError("the external program reported an error")
        if "outcome" not in reply:
            self._fatal()
            raise ExternalProtocolError("the reply has neither outcome nor error")
        return decode_outcome(reply["outcome"])

    def send_bye(self) -> None:
        if self.dead:
            return
        rid = self.next_rid
        self.next_rid += 1
        self._writes.put(dumps_line({"op": "bye", "rid": rid}))
        self._writes.put(None)  # then close standard input

    # -- shutdown ----------------------------------------------------------

    def reap(self) -> None:
        """After the process has exited or been killed: wait for it, bounded, and give the threads a moment.

        Never blocks on a pipe: a thread that is still blocked (a grandchild holds the pipe) is a daemon thread that
        owns its descriptor and closes it itself when it ends; the main thread does not wait for it (audit F1).
        """
        if self.popen is None:
            return
        try:
            self.popen.wait(timeout=BYE_WAIT_S)
        except subprocess.TimeoutExpired:
            pass
        for thread in (self._writer, self._reader):
            if thread is not None:
                thread.join(timeout=REAP_JOIN_S)

    def stderr_tail(self) -> list:
        if self.stderr_file is None:
            return []
        try:
            self.stderr_file.seek(0)
            text = self.stderr_file.read().decode("utf-8", errors="replace")
        except (OSError, ValueError):
            return []
        return text.splitlines()[-STDERR_TAIL_LINES:]

    def close_stderr(self) -> None:
        if self.stderr_file is not None:
            try:
                self.stderr_file.close()
            except OSError:
                pass


# --------------------------------------------------------------------------
# The session: every command of a manifest
# --------------------------------------------------------------------------

class ExternalSession:
    """All external processes of one manifest run (spec section 1.2)."""

    def __init__(self, manifest: Any) -> None:
        self.manifest = manifest
        self.workdir: Optional[str] = None
        self.procs: dict = {}  # tuple(argv) -> _Process, in order of first appearance
        self.uses_record: list = []
        self.closed = False

    # -- before the guard --------------------------------------------------

    @staticmethod
    def needed(manifest: Any) -> bool:
        return any(c.kind == "command" for c in manifest.criteria)

    def start(self) -> None:
        """Resolve, hash, copy, start and handshake.  Raises ``ManifestError`` (exit 4); cleans up after itself."""
        try:
            self._start()
        except BaseException:
            self.close()
            raise

    def _start(self) -> None:
        manifest = self.manifest
        first: dict = {}  # argv -> where of its first criterion
        for i, crit in enumerate(manifest.criteria):
            if crit.kind == "command":
                first.setdefault(tuple(crit.argv), f"criteria[{i}].command")
        resolved = {}
        for argv, where in first.items():
            exe = resolve_executable(argv[0], where, manifest.directory)
            try:
                digest = sha256_file(exe)
            except OSError as exc:
                fail(where, f"cannot read the executable {argv[0]} ({type(exc).__name__})")
            resolved[argv] = (exe, digest)
        self.workdir = tempfile.mkdtemp(prefix="truth_gate_external_")
        self._copy_files()
        env = build_env(manifest.external["env"])
        startup = manifest.external["startup_timeout_s"]
        request = manifest.external["request_timeout_s"]
        for argv, where in first.items():
            exe, digest = resolved[argv]
            proc = _Process(list(argv), exe, digest, request)
            self.procs[argv] = proc
            try:
                proc.launch(env, self.workdir)
            except OSError as exc:
                fail(where, f"cannot start {argv[0]} ({type(exc).__name__}: {exc})")
            try:
                proc.handshake(startup)
            except (ExternalTimeout, ExternalProtocolError, ExternalDied) as exc:
                proc.dead = True
                proc.died_in_run = False
                proc.failed = True
                fail(where, f"handshake with {argv[0]} failed: {exc}")

    def _copy_files(self) -> None:
        """``[external] uses`` and ``allow_paths`` into the working folder, with their relative layout, hashed."""
        manifest = self.manifest
        base = os.path.realpath(manifest.directory)
        entries: dict = {}  # relative path -> (where, declared, is_use)
        for i, declared in enumerate(manifest.external["uses"]):
            entries.setdefault(self._relative(declared, f"external.uses[{i}]", base), (declared, True))
        for i, declared in enumerate(manifest.allow_paths):
            rel = self._relative(declared, f"study.allow_paths[{i}]", base)
            if rel not in entries:
                entries[rel] = (declared, False)
        used: dict = {}
        for rel, (declared, is_use) in sorted(entries.items()):
            source = os.path.realpath(declared if os.path.isabs(declared) else os.path.join(manifest.directory, declared))
            with open(source, "rb") as handle:
                raw = handle.read()
            target = os.path.join(self.workdir, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as handle:
                handle.write(raw)
            try:
                shutil.copymode(source, target)
            except OSError:
                pass
            if is_use:
                used[declared] = hashlib.sha256(raw).hexdigest()
        self.uses_record = sorted(({"path": p, "sha256": h} for p, h in used.items()), key=lambda r: r["path"])

    def _relative(self, declared: str, where: str, base: str) -> str:
        source = os.path.realpath(declared if os.path.isabs(declared) else os.path.join(self.manifest.directory, declared))
        try:
            rel = os.path.relpath(source, base)
        except ValueError:
            rel = ".."
        if rel == ".." or rel.startswith(".." + os.sep) or os.path.isabs(rel):
            fail(where, f"{declared}: a file copied into the working folder must lie inside the manifest's folder "
                        "(the working folder keeps the relative layout)")
        return rel

    # -- during the run ----------------------------------------------------

    def criterion(self, criterion_id: str, argv: list):
        """The function the engine calls for a command criterion."""
        proc = self.procs[tuple(argv)]

        def fn(data: Any) -> Any:
            return proc.call(criterion_id, data)

        return fn

    def commands(self) -> list:
        """Distinct argv lists, in order of first appearance."""
        return [list(argv) for argv in self.procs]

    def commands_record(self) -> list:
        """``manifest.commands`` of the certificate: argv and the SHA-256 of the executable (spec section 11)."""
        return [{"argv": list(argv), "sha256": proc.exe_sha256} for argv, proc in self.procs.items()]

    def notes(self) -> list:
        """The study notes (spec section 5): ``K6_EXTERNAL_UNGUARDED`` and, if a process was lost, ``EXTERNAL_DIED``."""
        out = [{"note": NOTE_UNGUARDED, "commands": self.commands()}]
        died = [list(argv) for argv, proc in self.procs.items() if proc.died_in_run]
        if died:
            out.append({"note": NOTE_DIED, "commands": died})
        return out

    # -- after the guard ---------------------------------------------------

    def close(self) -> None:
        """``bye``, wait 5 s, kill the rest, print the stderr tails of failed processes, delete the working folder."""
        if self.closed:
            return
        self.closed = True
        live = [p for p in self.procs.values() if not p.dead and p.popen is not None]
        for proc in live:
            proc.send_bye()
        deadline = time.monotonic() + BYE_WAIT_S
        for proc in live:
            try:
                proc.popen.wait(timeout=max(0.0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                proc.failed = True
                proc.kill()
            else:
                if proc.popen.returncode != 0:
                    proc.failed = True
        for proc in self.procs.values():
            if not proc.dead:
                proc.dead = True
            proc.kill()  # whatever is left (idempotent)
            proc.reap()
        for proc in self.procs.values():
            if proc.failed:
                self._print_tail(proc)
            proc.close_stderr()
        if self.workdir is not None:
            try:
                shutil.rmtree(self.workdir)
            except OSError as exc:
                sys.stderr.write(f"truth-gate: warning: could not delete the working folder {self.workdir} "
                                 f"({type(exc).__name__})\n")

    @staticmethod
    def _print_tail(proc: _Process) -> None:
        lines = proc.stderr_tail()
        sys.stderr.write(f"truth-gate: external program failed: {shlex.join(proc.argv)}\n")
        if lines:
            sys.stderr.write(f"truth-gate: last {len(lines)} line(s) of its standard error:\n")
            for line in lines:
                sys.stderr.write(f"  | {line}\n")
        else:
            sys.stderr.write("truth-gate: (its standard error was empty)\n")
