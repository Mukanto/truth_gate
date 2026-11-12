"""Identical-minus check (spec 0.5, delta 1): exact equality, read-key recording, flags and suppression.

Pure helpers.  The evaluation driver in ``checks.py`` decides which two samples are compared (delta 1.1) and builds
the component record; this module only answers three questions about two samples:

* are they identical (delta 1.2, ``samples_identical``)?
* which top-level keys does a criterion read (delta 1.3, ``RecordingDict`` and ``record_read_keys``)?
* which flags follow (delta 1.4, ``analyse``)?
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

import numpy as np

from .sampling import copy_data

FLAG_IDENTICAL = "K2_MINUS_IDENTICAL"
FLAG_UNREAD = "K2_MINUS_UNREAD"
ALL_KEYS = "ALL"
# Delta 1.5: flags that carry no information when minus equals plus.
SUPPRESSIBLE_WHEN_IDENTICAL = frozenset({"K2_FAILS_UNREACHABLE", "K2_NO_SEPARATION", "K2_HIGH_SIZE"})

_NUMBER_LIKE = (np.ndarray, np.generic, bool, int, float, complex)


# --------------------------------------------------------------------------
# Delta 1.2: exact recursive equality
# --------------------------------------------------------------------------

def _equal(a: Any, b: Any) -> bool:
    if isinstance(a, _NUMBER_LIKE) and isinstance(b, _NUMBER_LIKE):
        x, y = np.asarray(a), np.asarray(b)
        if x.shape != y.shape or x.dtype != y.dtype:
            return False
        if x.dtype.kind in "fc":
            return bool(np.array_equal(x, y, equal_nan=True))
        return bool(np.array_equal(x, y))
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_equal(a[k], b[k]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if type(a) is not type(b) or len(a) != len(b):
            return False
        return all(_equal(x, y) for x, y in zip(a, b))
    result = a == b
    return isinstance(result, bool) and result


def values_equal(a: Any, b: Any) -> bool:
    """Exact equality of two values (spec 0.5 delta 1.2).

    numpy arrays and Python numbers: same shape, same dtype and ``numpy.array_equal`` (``equal_nan=True`` for float
    and complex dtypes).  ``dict``: same keys and equal values.  ``list``/``tuple``: same container type, same length
    and equal items.  Anything else: ``a == b`` must be a plain ``True``.  An exception, or a result that is not a
    plain ``bool``, counts as *not equal*.
    """
    try:
        return _equal(a, b)
    except Exception:
        return False


def samples_identical(a: Mapping, b: Mapping) -> bool:
    """Same set of keys and equal values under ``values_equal`` (delta 1.2)."""
    if set(a.keys()) != set(b.keys()):
        return False
    return all(values_equal(a[k], b[k]) for k in a)


def changed_keys(a: Mapping, b: Mapping) -> list:
    """Sorted keys whose values differ, plus keys present in only one sample (delta 3)."""
    keys = set(a.keys()) ^ set(b.keys())
    keys |= {k for k in set(a.keys()) & set(b.keys()) if not values_equal(a[k], b[k])}
    return sorted(str(k) for k in keys)


# --------------------------------------------------------------------------
# Delta 1.3: read-key recording
# --------------------------------------------------------------------------

class RecordingDict(dict):
    """``dict`` that records which top-level keys user code reads.

    Access through ``__getitem__``, ``get`` and ``__contains__`` records the key.  Any other access (``__iter__``,
    ``keys``, ``items``, ``values``, ``copy``, ``len``, ``dict(d)``, ``**d``, ``==``, mutation, ...) sets
    ``all_read``.  Used only on the extra recording calls of delta 1.3; counted evaluations receive plain dicts.
    """

    def __init__(self, data: Mapping):
        super().__init__(data)
        self.read: set = set()
        self.all_read: bool = False

    def __getitem__(self, key):
        self.read.add(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)

    def __contains__(self, key):
        self.read.add(key)
        return super().__contains__(key)


def _mark_all(name: str):
    base = getattr(dict, name)

    def method(self, *args, **kwargs):
        self.all_read = True
        return base(self, *args, **kwargs)

    method.__name__ = name
    return method


for _name in (
    "__iter__", "keys", "items", "values", "copy", "__len__", "__eq__", "__ne__", "__repr__", "__reversed__",
    "__or__", "__ror__", "__ior__", "__setitem__", "__delitem__", "pop", "popitem", "setdefault", "update", "clear",
):
    setattr(RecordingDict, _name, _mark_all(_name))
del _name


def record_read_keys(criterion, data: Mapping) -> tuple:
    """Call ``criterion.fn`` once on a recording copy of ``data``.  Returns ``(keys_read, all_read)``.

    The outcome is discarded.  If the call raises, the keys recorded so far are kept and ``all_read`` is True
    (conservative: it can only suppress ``K2_MINUS_UNREAD``).
    """
    recorder = RecordingDict(copy_data(dict(data)))
    try:
        criterion.fn(recorder)
    except Exception:
        recorder.all_read = True
    return set(recorder.read), recorder.all_read


# --------------------------------------------------------------------------
# Delta 1.4: per-criterion result
# --------------------------------------------------------------------------

def analyse(criteria, plus: Optional[Mapping], minus: Optional[Mapping], paired: bool) -> dict:
    """Identical-minus analysis for every criterion: ``{criterion id: {"minus_check": {...}, "flags": set}}``.

    ``plus`` and ``minus`` are the two compared samples (delta 1.1), or ``None`` when one could not be generated; then
    nothing is compared or recorded (not identical, empty ``read_keys`` and ``changed_keys``, no flag).
    ``minus_check`` has the certificate fields ``identical``, ``read_keys`` (sorted list or ``"ALL"``),
    ``changed_keys`` and ``paired``.  The flags are ``K2_MINUS_IDENTICAL`` or ``K2_MINUS_UNREAD`` (delta 1.4).
    """
    usable = plus is not None and minus is not None
    identical = bool(usable and samples_identical(plus, minus))
    changed = changed_keys(plus, minus) if usable else []
    out = {}
    for crit in criteria:
        read: set = set()
        everything = False
        if usable:
            for data in (plus, minus):
                keys, whole = record_read_keys(crit, data)
                read |= keys
                everything = everything or whole
        flags = set()
        if identical:
            flags.add(FLAG_IDENTICAL)
        elif usable and not everything and read and all(
            k in plus and k in minus and values_equal(plus[k], minus[k]) for k in read
        ):
            flags.add(FLAG_UNREAD)
        out[crit.id] = {
            "minus_check": {
                "identical": identical,
                "read_keys": ALL_KEYS if everything else sorted(str(k) for k in read),
                "changed_keys": list(changed),
                "paired": bool(paired),
            },
            "flags": flags,
        }
    return out
