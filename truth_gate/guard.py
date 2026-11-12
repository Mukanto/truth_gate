"""Leak guard (spec section 5.6).

A ``sys.addaudithook`` hook is installed once per process and stays installed;
it acts only while the module-level ``armed`` flag is set.  Use
:func:`armed` as a context manager, which always disarms on exit so that
independent runs in one process do not influence each other.
"""

from __future__ import annotations

import contextlib
import os
import site
import sys
from typing import Iterator, Optional

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# The deprecated ``kapi`` shim package sits next to ``truth_gate``; studies that still say ``from kapi import ...``
# load it while the guard is armed (spec 0.6, section 1.1 item 7).
SHIM_DIR = os.path.join(os.path.dirname(PACKAGE_DIR), "kapi")

# Events intercepted while armed (spec section 5.6).
FILE_EVENTS = frozenset({"open"})
LISTING_EVENTS = frozenset({"os.listdir", "os.scandir"})
OTHER_EVENTS = frozenset(
    {
        "socket.connect",
        "socket.getaddrinfo",
        "subprocess.Popen",
        "os.system",
        "os.exec",
        "os.posix_spawn",
        "os.spawn",
    }
)
INTERCEPTED_EVENTS = FILE_EVENTS | LISTING_EVENTS | OTHER_EVENTS

# Frames of the import machinery; see _import_listing_ok.
_IMPORT_FRAMES = frozenset({"<frozen importlib._bootstrap>", "<frozen importlib._bootstrap_external>"})


class _State:
    """The only global state of Kapi: hook installation, armed flag, allow-list, log."""

    def __init__(self) -> None:
        self.installed = False
        self.armed = False
        self.busy = False
        self.allow_files: set = set()
        self.allow_dirs: tuple = ()
        self.log: list = []
        self.seen: set = set()


_STATE = _State()


def _norm(path) -> str:
    """Case-normalised real path (spec section 5.6: resolved paths)."""
    return os.path.normcase(os.path.realpath(os.fsdecode(path)))


def _under(path: str, directory: str) -> bool:
    base = directory.rstrip("\\/")
    return path == directory or path.startswith(base + os.sep)


def _default_allow_dirs() -> tuple:
    """truth_gate and kapi-shim package dirs, interpreter prefixes and site-packages (spec section 5.6)."""
    dirs = [PACKAGE_DIR, SHIM_DIR, sys.prefix, sys.base_prefix, sys.exec_prefix]
    try:
        dirs.extend(site.getsitepackages())
    except Exception:  # pragma: no cover - exotic interpreters
        pass
    try:
        dirs.append(site.getusersitepackages())
    except Exception:  # pragma: no cover
        pass
    return tuple(sorted({_norm(d) for d in dirs if d}))


def _is_allowed_path(path: str) -> bool:
    st = _STATE
    return path in st.allow_files or any(_under(path, d) for d in st.allow_dirs)


def _sys_path_entries() -> set:
    entries = set()
    for entry in sys.path:
        if isinstance(entry, str):
            entries.add(_norm(entry if entry else os.getcwd()))
    return entries


def _import_listing_ok(frame, path: str) -> bool:
    """Directory listings done by the import machinery on ``sys.path`` entries are not leaks.

    Without this, lazily importing any module would list the working directory
    (a ``sys.path`` entry outside the allow-list) and be reported as a leak.
    Only the frozen importlib frames qualify, and only for ``sys.path`` entries.
    Deliberate spoofing of the frame name is out of scope (README, weaknesses).
    """
    return (
        frame is not None
        and frame.f_code.co_filename in _IMPORT_FRAMES
        and path in _sys_path_entries()
    )


def _event_target(event: str, args: tuple) -> Optional[str]:
    """Human-readable target of an intercepted event; ``None`` means ignore (fd)."""
    if event in FILE_EVENTS:
        target = args[0]
        if isinstance(target, int):
            return None
        return _norm(target)
    if event in LISTING_EVENTS:
        target = args[0] if args else None
        if isinstance(target, int):
            return None
        return _norm(os.getcwd() if target is None else target)
    if event == "socket.connect":
        return repr(args[1])
    if event == "socket.getaddrinfo":
        return repr((args[0], args[1]))
    if event == "os.spawn":
        return repr(args[1])
    return repr(args[0]) if args else ""


def _hook(event: str, args: tuple) -> None:
    st = _STATE
    if not st.armed or st.busy or event not in INTERCEPTED_EVENTS:
        return
    st.busy = True
    try:
        try:
            target = _event_target(event, args)
            if target is None:
                return
            if event in FILE_EVENTS and _is_allowed_path(target):
                return
            if event in LISTING_EVENTS and (
                _is_allowed_path(target) or _import_listing_ok(sys._getframe(1), target)
            ):
                return
        except Exception:
            target = "<unresolvable>"  # fail closed
        key = (event, target)
        if key not in st.seen:
            st.seen.add(key)
            st.log.append({"event": event, "target": target})
    finally:
        st.busy = False
    raise PermissionError(f"kapi leak guard blocked {event}")


def install() -> None:
    """Install the audit hook once per process (spec section 5.6)."""
    if not _STATE.installed:
        sys.addaudithook(_hook)
        _STATE.installed = True


def is_armed() -> bool:
    return _STATE.armed


@contextlib.contextmanager
def armed(study_file: str) -> Iterator[None]:
    """Arm the guard for one run; allow-list starts as the study file itself.

    ``sys.dont_write_bytecode`` is True while armed.  The guard is always
    disarmed on exit; the hook itself stays installed.
    """
    install()
    st = _STATE
    if st.armed:
        raise RuntimeError("leak guard is already armed")
    st.allow_files = {_norm(study_file)}
    st.allow_dirs = _default_allow_dirs()
    st.log = []
    st.seen = set()
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    st.armed = True
    try:
        yield
    finally:
        st.armed = False
        sys.dont_write_bytecode = previous
        st.allow_files = set()
        st.allow_dirs = ()


def allow_file(path: str) -> None:
    """Add an exact file to the allow-list (``Study.allow_paths``, spec section 5.6)."""
    _STATE.allow_files.add(_norm(path))


def take_log() -> list:
    """Return the events recorded so far (``{event, target}``) and start a fresh log."""
    log = list(_STATE.log)
    _STATE.log = []
    _STATE.seen = set()
    return log
