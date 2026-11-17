"""Phase D mechanical check of the criterion bodies (R2-17; TOOLS_SPEC_D_round2 item 5).

Replaces the part of Phase C's ``mech_check_twins.py`` that the splice design does not cover.  ``assemble.py`` checks the
splice itself; this tool writes the ``MECH_CHECK.json`` that ``FIDELITY_AUDIT_D`` item (d) reads.  It needs no gate and
runs no criterion.

For each body file of a case folder (``faulty_body.py``, ``fixed_body.py``):

1. **Module level** (the rule of ``assemble.module_level_problems``, R2-29): only ``import numpy as np`` and function
   definitions; exactly one function is ``criterion``.
2. **Banned names, numpy file functions, dunder attributes**, exactly as ``check_skeletons_d.static_check`` bans them (the
   constants ``BANNED_NAMES`` and ``BANNED_NP_ATTR`` are imported from it, and the dunder rule is the same line of logic):
   any ``ast.Name`` in ``BANNED_NAMES``; any attribute named in ``BANNED_NP_ATTR`` (load, save, savez, savetxt, loadtxt,
   genfromtxt, fromfile, tofile, memmap); any attribute starting with ``__`` other than ``__init__``.  The scan walks the whole
   tree (``ast.walk``), so decorators and default-argument expressions are covered (T3-4).
3. **Randomness** (T3-3, ported from Phase C's ``evaluation/phase_c/tools/mech_check_twins.py``): the only use of numpy's
   random module is ``np.random.default_rng(<integer literal>)``.  Mirrored: ``numpy_bindings`` (lines 102-109: the names numpy
   is bound to; here ``np`` and ``numpy`` and the alias of any ``import numpy as X``); ``is_numpy_ref`` and
   ``alias_assignments`` (lines 136-151: an Assign, AnnAssign, AugAssign or NamedExpr whose value, or an element of a
   tuple/list value, is a numpy name or ``<numpy>.random`` is an alias assignment); ``is_np_random`` (lines 153-154); the
   ``ok_random`` set (lines 178-181: ``<numpy>.random`` nodes that are the object of ``.default_rng``) and the checks of
   lines 197-204 (``<numpy>.random`` used any other way, and a ``default_rng(...)`` call that is not exactly one integer
   literal with no keyword, are refused).  Beyond Phase C's text: ``default_rng`` captured without being called
   (``f = np.random.default_rng``), a bare name ``default_rng``, and any import other than the module-level
   ``import numpy as np`` (so ``from numpy.random import default_rng`` and ``import numpy.random``, also inside a function)
   are refused as aliasing.  ``rng.random(...)`` on a Generator (a name that is not a numpy binding) is fine.
4. **Decorators** are refused anywhere in the file (T3-4), on functions and classes, nested or not.
5. **Free names, global, signatures** (R3-1, D-R4-1; ported from ``mech_check_twins.py``).  Applied to the whole body file, not
   only to ``criterion``:

   * every name the file loads resolves, by Python's scoping rules (D-R5-1, R3B-1: one scope per function, lambda,
     comprehension and class body), to a parameter or a name bound in the enclosing function (or an enclosing function), a
     module-level function of the file, ``np`` or a Python builtin; anything else is "reads module-level name X" (X is a
     module-level name of the case's skeletons) or "undefined name X", with its line number.  A name bound only inside a
     comprehension, a nested function or as a lambda parameter is not bound in the enclosing function.  The final tests are in
     the order of ``mech_check_twins.check_body`` lines 188-191: the skeleton's names are tested before the builtins, so a
     builtin that a skeleton redefines is "reads module-level name".  (Phase C's flat ``local_names``, lines 78-94, is
     replaced by the scope resolution.)
   * no ``global`` and no ``nonlocal`` anywhere;
   * ``criterion`` has the signature ``(d)``, with no default values, decorators or annotations (``signature_issues``,
     lines 157-168); any other function or lambda may have default values only if they are numbers, strings, ``None``,
     ``True``/``False``, a negated number or tuples of these (mutable or computed defaults are refused).

   The listed-call set is ``SUMMARY_CALLS`` (Phase C's ``DIST_CALLS``, lines 43-44, plus ``isnan`` and ``isfinite``) and
   ``linalg.norm``, with the built-in forms in ``BUILTIN_SUMMARY_CALLS``.

6. **Listed comparisons** (listed for the auditor, not failures; T3-3 (a)): every comparison ``< <= > >= == !=`` in which one
   side contains, anywhere in its expression subtree, a listed call (a name in ``SUMMARY_CALLS`` as ``np.f(...)`` or ``x.f()``,
   ``linalg.norm``, or a name in ``BUILTIN_SUMMARY_CALLS`` as ``f(...)``; D-R5-5), and the
   other side is one of: a numeric literal (an int or float, not a bool or complex), a unary minus or plus of one,
   arithmetic of numeric literals only (``2 * 0.5``, ``1 - 1e-9``), or a bare name.  The entry's ``kind`` is ``"constant"``
   for the first three and ``"name"`` for a bare name.  Both orders count; chained comparisons ``a < f(x) < b`` are read
   pair by pair.  So ``float(np.mean(x)) > 0.3`` and ``np.mean(x) - 1 > 0`` are listed; ``np.mean(x) > np.mean(y)`` and
   ``np.mean(x) > len(y)`` are not.  Each entry has file, line, text (the source of the whole comparison), op, kind, the
   first listed call found (``call``) and every listed call of the call side (``calls``).

For the assembled files (every skeleton of the case that exists: ``reference.py``, ``skeletons/W0.py``,
``skeletons/W1.py``, each with both bodies):

7. The pair assembles (``assemble.assemble``), and the faulty and fixed assemblies differ only inside the body region
   (``assemble.differ_only_in_criterion``).
8. Default ``Budget`` and ``Targets`` and no ``deterministic``: the ``Study(...)`` call of the assembled file has no
   ``budget``, ``targets`` or ``deterministic`` keyword.  (This is an AST check; ``check_skeletons_d.py`` also checks the
   loaded object.)

Output ``MECH_CHECK.json``::

    {"case": <brief id>, "ok": bool, "issues": [...],
     "bodies": {"faulty_body.py": {"issues": [...], "listed_comparisons": [{"file","line","text","op","kind","call","calls"}, ...]}, ...},
     "assembled": {"reference/faulty": {"issues": [...]}, ..., "reference": {"single_difference": bool}}}

Usage:
    py mech_check_bodies.py --case DIR --out MECH_CHECK.json
Exit code 0 if there is no issue (listed comparisons are not issues), 1 if there is at least one, 2 on a usage error.
"""
import argparse
import ast
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from assemble import (AssembleError, assemble, differ_only_in_criterion, module_level_problems,  # noqa: E402
                      top_level_names)
from check_skeletons_d import BANNED_NAMES, BANNED_NP_ATTR  # noqa: E402

BODY_FILES = ("faulty_body.py", "fixed_body.py")
SKELETONS = (("reference", "reference.py"), ("W0", os.path.join("skeletons", "W0.py")),
             ("W1", os.path.join("skeletons", "W1.py")))
DIST_CALLS = {"mean", "var", "std", "ptp", "allclose", "isclose", "count_nonzero", "unique", "all", "any", "median",
              "nanmean", "nanstd", "nanvar", "array_equal", "sum", "max", "min", "abs"}  # D-R4-1: mech_check_twins.py lines 43-44
SUMMARY_CALLS = DIST_CALLS | {"isnan", "isfinite"}  # D-R4-1 (linalg.norm is handled in summary_call_name)
BUILTIN_SUMMARY_CALLS = {"min", "max", "all", "any", "sum", "abs", "len"}  # D-R4-1
COMPARE_OPS = (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq)
OP_TEXT = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}
STUDY_FORBIDDEN_KEYWORDS = ("budget", "targets", "deterministic")


def summary_call_name(node):
    """The name of the summary call that ``node`` itself is (``"mean"``, ``"linalg.norm"``, ...), or ``None``."""
    if not isinstance(node, ast.Call):
        return None
    f = node.func
    if isinstance(f, ast.Attribute):
        if f.attr in SUMMARY_CALLS:
            return f.attr
        if f.attr == "norm" and isinstance(f.value, ast.Attribute) and f.value.attr == "linalg":
            return "linalg.norm"
        return None
    if isinstance(f, ast.Name) and f.id in BUILTIN_SUMMARY_CALLS:
        return f.id
    return None


def summary_calls_in(node):
    """Names of the summary calls anywhere in the expression subtree of ``node`` (``ast.walk`` order)."""
    return [n for n in (summary_call_name(c) for c in ast.walk(node)) if n is not None]


def is_numeric_literal(node):
    """An int or float literal (not a bool, not complex)."""
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool)


def is_literal_arithmetic(node):
    """A numeric literal, a unary minus or plus, or arithmetic whose leaves are numeric literals only."""
    if is_numeric_literal(node):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return is_literal_arithmetic(node.operand)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
        return is_literal_arithmetic(node.left) and is_literal_arithmetic(node.right)
    return False


def other_side_kind(node):
    """``"constant"`` (literal, unary minus, arithmetic of literals), ``"name"`` (a bare name) or ``None``."""
    if is_literal_arithmetic(node):
        return "constant"
    if isinstance(node, ast.Name):
        return "name"
    return None


def listed_comparisons(tree, src, file):
    """Every comparison of a side that contains a summary call with a constant or a bare name (see the module docstring)."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        for op, right in zip(node.ops, node.comparators):
            if isinstance(op, COMPARE_OPS):
                for call_side, other in ((left, right), (right, left)):
                    calls = summary_calls_in(call_side)
                    kind = other_side_kind(other)
                    if calls and kind is not None:
                        out.append({"file": file, "line": node.lineno,
                                    "text": " ".join((ast.get_source_segment(src, node) or "").split()),
                                    "op": OP_TEXT[type(op)], "kind": kind, "call": calls[0], "calls": calls})
                        break
            left = right
    return sorted(out, key=lambda e: (e["line"], e["text"], e["op"]))


def banned_issues(tree):
    """Banned names, numpy file functions and dunder attributes, as ``check_skeletons_d.static_check`` bans them."""
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            issues.append(f"name {node.id} (line {node.lineno})")
        elif isinstance(node, ast.Attribute):
            if node.attr in BANNED_NP_ATTR:
                issues.append(f"attribute .{node.attr} (line {node.lineno})")
            if node.attr.startswith("__") and node.attr != "__init__":
                issues.append(f"dunder attribute .{node.attr} (line {node.lineno})")
    return issues


def numpy_bindings(tree):
    """Names bound to numpy by the module's imports (``import numpy`` -> numpy, ``import numpy as X`` -> X).
    Mirrors ``mech_check_twins.numpy_bindings`` (lines 102-109)."""
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == "numpy":
                    names.add(a.asname or "numpy")
    return names


def is_numpy_ref(v, npn):
    """A bare numpy binding name or ``<numpy binding>.random`` (``mech_check_twins.is_numpy_ref``, lines 136-138)."""
    return (isinstance(v, ast.Name) and v.id in npn) or (
        isinstance(v, ast.Attribute) and v.attr == "random" and isinstance(v.value, ast.Name) and v.value.id in npn)


def alias_assignments(root, npn):
    """Assign / AnnAssign / AugAssign / NamedExpr nodes whose value (or an element of a tuple/list value) is a numpy
    reference (``mech_check_twins.alias_assignments``, lines 141-151)."""
    out = []
    for n in ast.walk(root):
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)) and n.value is not None:
            vals = list(n.value.elts) if isinstance(n.value, (ast.Tuple, ast.List)) else [n.value]
            if any(is_numpy_ref(e, npn) for e in vals):
                out.append(n)
    return out


def is_np_random(x, npn):
    """``<numpy binding>.random`` (``mech_check_twins.is_np_random``, lines 153-154)."""
    return isinstance(x, ast.Attribute) and x.attr == "random" and isinstance(x.value, ast.Name) and x.value.id in npn


def call_name(c):
    f = c.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def randomness_issues(tree):
    """The Phase C randomness rule over the whole tree (see the module docstring, item 3)."""
    npn = numpy_bindings(tree) | {"np", "numpy"}
    issues = []
    ok_random, called = set(), set()
    for x in ast.walk(tree):  # mech_check_twins.py lines 178-181
        if isinstance(x, ast.Attribute) and x.attr == "default_rng" and is_np_random(x.value, npn):
            ok_random.add(id(x.value))
        if isinstance(x, ast.Call):
            called.add(id(x.func))
    aliases = alias_assignments(tree, npn)
    for x in ast.walk(tree):
        if isinstance(x, ast.Attribute) and is_np_random(x, npn) and id(x) not in ok_random:  # lines 197-198
            issues.append(f"{x.value.id}.random used other than as {x.value.id}.random.default_rng (line {x.lineno})")
        if x in aliases:  # line 199
            issues.append(f"numpy alias assignment `{ast.unparse(x)}` (line {x.lineno})")
        if isinstance(x, ast.Call) and call_name(x) == "default_rng":  # lines 201-204
            ok = len(x.args) == 1 and isinstance(x.args[0], ast.Constant) and type(x.args[0].value) is int and not x.keywords
            if not ok:
                issues.append(f"default_rng without a single int literal seed (line {x.lineno})")
        if isinstance(x, ast.Attribute) and x.attr == "default_rng" and id(x) not in called:
            issues.append(f"default_rng captured without being called (line {x.lineno})")
        if isinstance(x, ast.Name) and x.id == "default_rng":
            issues.append(f"bare name default_rng (line {x.lineno})")
    for n in ast.walk(tree):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            if not (isinstance(n, ast.Import) and [(a.name, a.asname) for a in n.names] == [("numpy", "np")]
                    and n in tree.body):
                issues.append(f"import other than the module-level 'import numpy as np' (line {n.lineno})")
    return issues


def decorator_issues(tree):
    """Decorators anywhere in the file, on functions and classes, nested or not."""
    return [f"decorator on {n.name} (line {n.lineno})" for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.decorator_list]


_COMPREHENSIONS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)  # D-R5-1


def _arg_names(args):  # D-R5-1
    """Every parameter name of an ``ast.arguments``."""
    out = {a.arg for a in args.args + args.kwonlyargs + getattr(args, "posonlyargs", [])}
    if args.vararg:
        out.add(args.vararg.arg)
    if args.kwarg:
        out.add(args.kwarg.arg)
    return out


def _header_exprs(fn):  # D-R5-1
    """The expressions of a function header, evaluated in the enclosing scope: decorators, defaults, annotations."""
    args = fn.args
    out = list(fn.decorator_list) + list(args.defaults) + [d for d in args.kw_defaults if d is not None]
    out += [a.annotation for a in args.args + args.kwonlyargs + getattr(args, "posonlyargs", []) if a.annotation is not None]
    for extra in (args.vararg, args.kwarg):
        if extra is not None and extra.annotation is not None:
            out.append(extra.annotation)
    if fn.returns is not None:
        out.append(fn.returns)
    return out


def _bound_in_scope(roots):  # D-R5-1
    """Names bound in one scope: the statements or expressions ``roots`` without descending into nested scopes.

    A nested ``def`` or ``class`` binds its own name here (its header expressions are looked at, its body is not); a lambda
    binds nothing here; a comprehension binds nothing here, except that a walrus target inside it binds here (Python's rule);
    the first iterable of a comprehension is evaluated here.
    """
    bound = set()
    stack = list(roots)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bound.add(n.name)
            stack.extend(_header_exprs(n))
            continue
        if isinstance(n, ast.ClassDef):
            bound.add(n.name)
            stack.extend(list(n.decorator_list) + list(n.bases) + [k.value for k in n.keywords])
            continue
        if isinstance(n, ast.Lambda):
            stack.extend(list(n.args.defaults) + [d for d in n.args.kw_defaults if d is not None])
            continue
        if isinstance(n, _COMPREHENSIONS):
            for sub in ast.walk(n):
                if isinstance(sub, ast.NamedExpr) and isinstance(sub.target, ast.Name):
                    bound.add(sub.target.id)
            stack.append(n.generators[0].iter)
            continue
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            bound.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound.add(n.name)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and n.name:
            bound.add(n.name)
        elif isinstance(n, ast.MatchMapping) and n.rest:
            bound.add(n.rest)
        stack.extend(ast.iter_child_nodes(n))
    return bound


class _Scope:  # D-R5-1
    """One Python scope: a function, a lambda, a comprehension, a class body or the module."""

    def __init__(self, kind, bound, parent):
        self.kind, self.bound, self.parent = kind, set(bound), parent


def free_name_issues(tree, skeleton_names=()):  # D-R5-1 (replaces the flat ``local_names`` of D-R4-1)
    """Every name the file loads must resolve, by Python's scoping rules, to one of: a parameter or a name bound in the
    enclosing function, lambda, comprehension or class body, or in an enclosing function; a module-level function of the body
    file; ``np``; a Python builtin.  Anything else is "reads module-level name X" (X is a top-level name of the skeleton, given in
    ``skeleton_names``) or "undefined name X", with its line number.

    One scope per function, lambda, comprehension and class body: a name bound only inside a comprehension, a nested function
    or as a lambda parameter is not bound in the enclosing function.  The order of the final tests is that of
    ``mech_check_twins.check_body`` (lines 188-191): after the scopes, the file's own module-level functions and ``np`` are
    allowed, then the skeleton's names are tested **before** the builtins, so that a builtin a skeleton redefines (``max``) is
    "reads module-level name".  A class body's names are not visible from the scopes nested in it (Python's rule).  Default
    values, decorators and annotations are evaluated in the enclosing scope.
    """
    import builtins
    skeleton_names = set(skeleton_names)
    allowed_module = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))} \
        | {"np"} | numpy_bindings(tree)
    issues = []

    def resolves_in_scopes(name, scope):
        s, first = scope, True
        while s is not None:
            if not (s.kind == "class" and not first) and name in s.bound:
                return True
            s, first = s.parent, False
        return False

    def load(name_node, scope):
        name = name_node.id
        if resolves_in_scopes(name, scope) or name in allowed_module:
            return
        if name in skeleton_names:
            issues.append(f"reads module-level name {name} (line {name_node.lineno})")
        elif not hasattr(builtins, name):
            issues.append(f"undefined name {name} (line {name_node.lineno})")

    def visit_all(nodes, scope):
        for n in nodes:
            visit(n, scope)

    def visit(n, scope):
        if isinstance(n, ast.Name):
            if isinstance(n.ctx, ast.Load):
                load(n, scope)
            return
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_all(_header_exprs(n), scope)
            fs = _Scope("function", _arg_names(n.args) | _bound_in_scope(n.body), scope)
            visit_all(n.body, fs)
            return
        if isinstance(n, ast.Lambda):
            visit_all(list(n.args.defaults) + [d for d in n.args.kw_defaults if d is not None], scope)
            ls = _Scope("lambda", _arg_names(n.args) | _bound_in_scope([n.body]), scope)
            visit(n.body, ls)
            return
        if isinstance(n, _COMPREHENSIONS):
            visit(n.generators[0].iter, scope)  # the first iterable is evaluated in the enclosing scope
            targets = set()
            for g in n.generators:
                targets |= _bound_in_scope([g.target])
            cs = _Scope("comprehension", targets, scope)
            for i, g in enumerate(n.generators):
                if i > 0:
                    visit(g.iter, cs)
                visit_all(g.ifs, cs)
            visit_all([n.key, n.value] if isinstance(n, ast.DictComp) else [n.elt], cs)
            return
        if isinstance(n, ast.ClassDef):
            visit_all(list(n.decorator_list) + list(n.bases) + [k.value for k in n.keywords], scope)
            cs = _Scope("class", _bound_in_scope(n.body), scope)
            visit_all(n.body, cs)
            return
        visit_all(ast.iter_child_nodes(n), scope)

    module = _Scope("module", set(), None)
    for n in tree.body:
        visit(n, module)
    return issues


def global_issues(tree):  # D-R4-1
    """``global`` and ``nonlocal`` anywhere in the file."""
    return [f"{type(n).__name__.lower()} statement (line {n.lineno})" for n in ast.walk(tree)
            if isinstance(n, (ast.Global, ast.Nonlocal))]


def is_literal_default(node):  # D-R4-1
    """A number, a string, ``None``, ``True``/``False``, a negated number, or a tuple of these."""
    if isinstance(node, ast.Constant):
        return node.value is None or isinstance(node.value, (bool, int, float, complex, str))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return isinstance(node.operand, ast.Constant) and isinstance(node.operand.value, (int, float, complex)) \
            and not isinstance(node.operand.value, bool)
    if isinstance(node, ast.Tuple):
        return all(is_literal_default(e) for e in node.elts)
    return False


def criterion_signature_issues(fn):  # D-R4-1
    """mech_check_twins.signature_issues (lines 157-168): ``criterion`` is ``(d)``, with no defaults, decorators or annotations."""
    a = fn.args
    out = []
    if [p.arg for p in a.args] != ["d"] or a.vararg or a.kwarg or a.kwonlyargs or getattr(a, "posonlyargs", []):
        out.append("signature is not (d)")
    if a.defaults or a.kw_defaults:
        out.append("signature has default values")
    if fn.decorator_list:
        out.append("criterion has decorators")
    if fn.returns is not None or any(p.annotation is not None for p in a.args + a.kwonlyargs):
        out.append("signature has annotations")
    return out


def signature_issues(tree):  # D-R4-1
    """Signature problems of every function and lambda: ``criterion`` as above; any other function may have default values
    only if they are literals (numbers, strings, None, True/False, tuples of these); mutable or computed defaults are refused."""
    issues = []
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        is_crit = isinstance(n, ast.FunctionDef) and n.name == "criterion" and n in tree.body
        if is_crit:
            issues += [f"criterion: {m} (line {n.lineno})" for m in criterion_signature_issues(n)]
            continue
        name = "lambda" if isinstance(n, ast.Lambda) else n.name
        for d in list(n.args.defaults) + [d for d in n.args.kw_defaults if d is not None]:
            if not is_literal_default(d):
                issues.append(f"{name}: default value {ast.unparse(d)!r} is not a literal (line {d.lineno})")
    return issues


def check_body(src, file, skeleton_names=()):  # D-R4-1
    """``{"issues": [...], "listed_comparisons": [...]}`` for one body source text.  ``skeleton_names`` are the module-level
    names of the skeleton the body is spliced into (they turn "undefined name" into "reads module-level name")."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"issues": [f"syntax error: {e}"], "listed_comparisons": []}
    issues = [f"module level: {what} at line {line} (only 'import numpy as np' and function definitions are allowed)"
              for line, what in module_level_problems(tree)]
    crit = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "criterion"]
    if len(crit) != 1:
        issues.append(f"exactly one function must be criterion, found {len(crit)}")
    issues += banned_issues(tree)
    issues += randomness_issues(tree)
    issues += decorator_issues(tree)
    issues += free_name_issues(tree, skeleton_names)  # D-R4-1
    issues += global_issues(tree)  # D-R4-1
    issues += signature_issues(tree)  # D-R4-1
    return {"issues": list(dict.fromkeys(issues)), "listed_comparisons": listed_comparisons(tree, src, file)}


def study_keyword_issues(src):
    """Issues for the ``Study(...)`` call of an assembled file: ``budget``, ``targets`` or ``deterministic`` given."""
    tree = ast.parse(src)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Study"]
    if len(calls) != 1:
        return [f"{len(calls)} Study(...) calls (expected 1)"]
    return [f"Study(...) has a {k.arg} keyword (default Budget, Targets and deterministic are required)"
            for k in calls[0].keywords if k.arg in STUDY_FORBIDDEN_KEYWORDS]


def check_case(case_dir):
    """The full report of one case folder.  Raises ``OSError`` / ``ValueError`` / ``KeyError`` for unreadable input."""
    with open(os.path.join(case_dir, "brief.json"), encoding="utf-8") as f:
        case_id = json.load(f)["id"]
    texts = {}
    for name in BODY_FILES:
        with open(os.path.join(case_dir, name), encoding="utf-8") as f:
            texts[name] = f.read()
    report = {"case": case_id, "ok": True, "issues": [], "bodies": {}, "assembled": {}}
    skeleton_names = set()  # D-R4-1: the module-level names of the case's skeletons
    for _arm, rel in SKELETONS:  # D-R4-1
        sk_path = os.path.join(case_dir, rel)  # D-R4-1
        if os.path.isfile(sk_path):  # D-R4-1
            try:  # D-R4-1
                with open(sk_path, encoding="utf-8") as f:  # D-R4-1
                    skeleton_names |= top_level_names(ast.parse(f.read()))  # D-R4-1
            except SyntaxError:  # D-R4-1
                pass  # reported when the skeleton is assembled
    for name in BODY_FILES:
        res = check_body(texts[name], name, skeleton_names)  # D-R4-1
        report["bodies"][name] = res
        report["issues"] += [f"{name}: {i}" for i in res["issues"]]
    for arm, rel in SKELETONS:
        path = os.path.join(case_dir, rel)
        if not os.path.isfile(path):
            if arm == "reference":
                report["issues"].append("reference.py is missing")
            continue
        with open(path, encoding="utf-8") as f:
            skeleton = f.read()
        built = {}
        for twin, name in (("faulty", "faulty_body.py"), ("fixed", "fixed_body.py")):
            key = f"{arm}/{twin}"
            try:
                built[twin] = assemble(skeleton, texts[name])
            except AssembleError as e:
                report["assembled"][key] = {"issues": [f"does not assemble: {e}"]}
                report["issues"].append(f"{key}: does not assemble: {e}")
                continue
            issues = study_keyword_issues(built[twin])
            report["assembled"][key] = {"issues": issues}
            report["issues"] += [f"{key}: {i}" for i in issues]
        if len(built) == 2:
            same = differ_only_in_criterion(built["faulty"], built["fixed"])
            report["assembled"][arm] = {"single_difference": same}
            if not same:
                report["issues"].append(f"{arm}: the faulty and fixed assemblies differ outside the body region")
    report["ok"] = not report["issues"]
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mechanical check of the criterion bodies of one Phase D case.")
    ap.add_argument("--case", required=True, metavar="DIR")
    ap.add_argument("--out", required=True, metavar="MECH_CHECK.json")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    try:
        report = check_case(a.case)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"mech_check_bodies: cannot read the case: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    n = sum(len(b["listed_comparisons"]) for b in report["bodies"].values())
    print(f"{report['case']}: {'OK' if report['ok'] else 'ISSUES'}; {n} listed comparison(s)")
    for i in report["issues"]:
        print(f"    - {i}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
