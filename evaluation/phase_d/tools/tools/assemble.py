"""Phase D assembler (PREREG_PHASE_D section 2.1, TOOLS_SPEC_D section 1).

Splices the body of a criterion (``faulty_body.py`` / ``fixed_body.py``: helper functions plus exactly one
``def criterion(d):``, only ``import numpy as np`` and function definitions at module level) into a skeleton (reference, W-0 or W-1) in place of the skeleton's
placeholder ``def criterion(d): ... raise NotImplementedError``.

What it does
------------
* The skeleton's module-level ``criterion`` must be one function without decorators whose body is an optional docstring
  and exactly one statement, ``raise NotImplementedError``.  Its full line range is replaced by the body's source,
  without the body's own ``import numpy as np`` line (the skeleton imports numpy itself).
* The inserted text is fenced by two comment lines (``BEGIN_MARK`` / ``END_MARK``).  They are what lets
  ``differ_only_in_criterion`` say "only inside the inserted body region" without guessing.  Nothing else is added.
* The result is checked: it parses; it has exactly one module-level ``criterion``; no top-level name is defined by both
  the skeleton and the body; the skeleton's ``STUDY`` still contains ``Criterion("C", criterion)``.
* The body may hold at module level only ``import numpy as np`` and function definitions (R2-29); anything else (another
  import, an assignment, a class, a call, a docstring, ``async def``) is refused, and exactly one of the functions must be
  ``criterion``.  That rule alone does not stop a body from reading the skeleton's globals (``THRESHOLD``, ``N``, ``rng``):
  a function may read any module-level name of the assembled file.  The free-name check of ``mech_check_bodies.py`` does
  that (R3-1, D-R4-2): ``assemble`` calls ``mech_check_bodies.free_name_issues`` on the body, with the skeleton's top-level
  names, and refuses to assemble a body that reads a name that is neither its own parameter or local, nor one of its own
  functions, nor ``np``, nor a builtin.  A decorated module-level function is refused (T3-4); default arguments are not looked at here
  (``mech_check_bodies.py`` bans the names and attributes that matter, on the whole tree).

Usage:  py assemble.py --skeleton S --body B --out OUT [--package-root DIR]
Exit code 0 on success, 1 when the pair cannot be assembled (message on stderr), 2 on a usage error.
``--package-root`` is accepted for uniformity with the other tools; assembling needs no gate, so it is only verified.
"""
import argparse
import ast
import os
import sys

BEGIN_MARK = "# >>> PHASE D INSERTED CRITERION BODY (begin) >>>"
END_MARK = "# <<< PHASE D INSERTED CRITERION BODY (end) <<<"


class AssembleError(Exception):
    """The skeleton and the body cannot be assembled (a rule of TOOLS_SPEC_D section 1 is violated)."""


def _is_raise_not_implemented(stmt):
    return (isinstance(stmt, ast.Raise) and stmt.cause is None and isinstance(stmt.exc, ast.Name)
            and stmt.exc.id == "NotImplementedError")


def _parse(src, what):
    try:
        return ast.parse(src)
    except SyntaxError as e:
        raise AssembleError(f"{what} does not parse: {e}") from e


def _module_criteria(tree):
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "criterion"]


def _placeholder(tree):
    """The skeleton's placeholder ``criterion`` node, after every check of its form."""
    found = _module_criteria(tree)
    if len(found) != 1:
        raise AssembleError(f"the skeleton must have exactly one module-level criterion, found {len(found)}")
    node = found[0]
    if not isinstance(node, ast.FunctionDef):
        raise AssembleError("the skeleton's criterion is not a plain def")
    if node.decorator_list:
        raise AssembleError("the skeleton's criterion has decorators")
    stmts = list(node.body)
    if stmts and isinstance(stmts[0], ast.Expr) and isinstance(stmts[0].value, ast.Constant) \
            and isinstance(stmts[0].value.value, str):
        stmts = stmts[1:]
    if len(stmts) != 1 or not _is_raise_not_implemented(stmts[0]):
        raise AssembleError("the skeleton's criterion must be an optional docstring and exactly one statement, "
                            "raise NotImplementedError")
    return node


def _top_level_names(tree, skip=None):
    """Names bound at module level (functions, classes, assignment targets, imports), excluding the node ``skip``."""
    names = set()

    def targets(t):
        if isinstance(t, ast.Name):
            names.add(t.id)
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                targets(e)
        elif isinstance(t, ast.Starred):
            targets(t.value)

    for n in tree.body:
        if n is skip:
            continue
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                targets(t)
        elif isinstance(n, (ast.AnnAssign, ast.AugAssign)):
            targets(n.target)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                names.add((a.asname or a.name).split(".")[0])
    return names


def module_level_problems(tree):
    """The statements of a body's module level that are neither ``import numpy as np`` nor a function definition.

    Returns ``[(line, description), ...]``.  This is the one rule of R2-29 (CRITERION_AUTHOR_D, the draft and the checks
    all say it the same way): a body file holds ``import numpy as np`` and function definitions, nothing else, so that
    nothing runs when the assembled study is imported.  A module docstring, an assignment, a class, an
    ``if``, a call, any other import, ``async def`` and a decorated function (T3-4) are all refused.
    """
    out = []
    for n in tree.body:
        if isinstance(n, ast.FunctionDef):
            if n.decorator_list:  # T3-4: a decorator runs code when the study is imported
                out.append((n.lineno, "decorated FunctionDef"))
            continue
        if isinstance(n, ast.Import) and [(a.name, a.asname) for a in n.names] == [("numpy", "np")]:
            continue
        out.append((n.lineno, type(n).__name__))
    return out


top_level_names = _top_level_names  # D-R4-1: public name, used by mech_check_bodies


def _strip_numpy_import(body_src, body_tree):
    """Body source lines without its ``import numpy as np`` statement(s).  Any other import is refused."""
    lines = body_src.splitlines()
    drop = set()
    for n in body_tree.body:
        if isinstance(n, ast.Import) and [(a.name, a.asname) for a in n.names] == [("numpy", "np")]:
            drop.update(range(n.lineno - 1, n.end_lineno))
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            raise AssembleError(f"the body imports something other than 'import numpy as np' (line {n.lineno})")
    return [ln for i, ln in enumerate(lines) if i not in drop]


def _study_uses_criterion_c(tree):
    """True if a module-level ``STUDY`` contains the call ``Criterion("C", criterion)`` (exactly those two arguments)."""
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STUDY" for t in n.targets):
            for c in ast.walk(n.value):
                if (isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "Criterion"
                        and not c.keywords and len(c.args) == 2
                        and isinstance(c.args[0], ast.Constant) and c.args[0].value == "C"
                        and isinstance(c.args[1], ast.Name) and c.args[1].id == "criterion"):
                    return True
    return False


def assemble(skeleton_src: str, body_src: str) -> str:
    """Splice ``body_src`` into ``skeleton_src`` (see the module docstring).  Raises ``AssembleError``."""
    if BEGIN_MARK in skeleton_src or END_MARK in skeleton_src:
        raise AssembleError("the skeleton already contains an insertion marker")
    sk_tree = _parse(skeleton_src, "the skeleton")
    node = _placeholder(sk_tree)
    if not _study_uses_criterion_c(sk_tree):
        raise AssembleError('the skeleton\'s STUDY does not refer to Criterion("C", criterion)')

    body_tree = _parse(body_src, "the body")
    bad = module_level_problems(body_tree)
    if bad:
        raise AssembleError("the body may hold only 'import numpy as np' and function definitions at module level; found "
                            + ", ".join(f"{what} at line {line}" for line, what in bad))
    if len(_module_criteria(body_tree)) != 1:
        raise AssembleError("the body must define exactly one module-level criterion")
    here = os.path.dirname(os.path.abspath(__file__))  # D-R4-2 (a script run with -I has no script folder on sys.path)
    if here not in sys.path:  # D-R4-2
        sys.path.insert(0, here)  # D-R4-2
    from mech_check_bodies import free_name_issues  # D-R4-2 (imported here: mech_check_bodies imports this module)
    free = free_name_issues(body_tree, _top_level_names(sk_tree, skip=node))  # D-R4-2
    if free:  # D-R4-2
        raise AssembleError("the body reads names it does not define (free names): " + "; ".join(free))  # D-R4-2
    body_lines = _strip_numpy_import(body_src, body_tree)
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()
    if not body_lines:
        raise AssembleError("the body is empty")

    # No duplicate top-level names between the skeleton (without its placeholder) and the body.
    clash = (_top_level_names(sk_tree, skip=node) & _top_level_names(body_tree)) - {"np"}
    if clash:
        raise AssembleError(f"top-level names defined by both the skeleton and the body: {sorted(clash)}")

    sk_lines = skeleton_src.splitlines()
    before = sk_lines[: node.lineno - 1]
    after = sk_lines[node.end_lineno:]
    out = before + [BEGIN_MARK] + body_lines + [END_MARK] + after
    result = "\n".join(out) + "\n"

    tree = _parse(result, "the assembled file")
    if len(_module_criteria(tree)) != 1:
        raise AssembleError("the assembled file does not have exactly one module-level criterion")
    if not _study_uses_criterion_c(tree):
        raise AssembleError('the assembled file\'s STUDY does not refer to Criterion("C", criterion)')
    return result


def _split_region(src):
    """``(outside, inside)`` of an assembled file: its text with the region removed, and the region's lines."""
    lines = src.splitlines()
    begins = [i for i, ln in enumerate(lines) if ln == BEGIN_MARK]
    ends = [i for i, ln in enumerate(lines) if ln == END_MARK]
    if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
        raise AssembleError("not an assembled file: it needs exactly one begin and one end marker, in order")
    return lines[: begins[0]] + lines[ends[0] + 1:], lines[begins[0] + 1: ends[0]]


def differ_only_in_criterion(study_a_src: str, study_b_src: str) -> bool:
    """True if two assembled files are identical outside the inserted body region (they may differ, or not, inside it).

    Both files must carry exactly one marker pair (otherwise ``AssembleError``).  The position of the region is part of
    "outside": a region that moved is a difference.
    """
    la, lb = study_a_src.splitlines(), study_b_src.splitlines()
    out_a, _ = _split_region(study_a_src)
    out_b, _ = _split_region(study_b_src)
    if out_a != out_b:
        return False
    return la.index(BEGIN_MARK) == lb.index(BEGIN_MARK)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Splice a criterion body into a skeleton (Phase D).")
    ap.add_argument("--skeleton", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--package-root", default=None, help="optional; verified only (no gate is needed)")
    a = ap.parse_args(argv)
    sys.dont_write_bytecode = True
    if a.package_root is not None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from structure_stat import import_truth_gate, PackageRootError
        try:
            import_truth_gate(a.package_root)
        except PackageRootError as e:
            print(f"package root check failed: {e}", file=sys.stderr)
            return 2
    try:
        with open(a.skeleton, encoding="utf-8") as f:
            sk = f.read()
        with open(a.body, encoding="utf-8") as f:
            bd = f.read()
    except OSError as e:
        print(f"cannot read input: {e}", file=sys.stderr)
        return 2
    try:
        out = assemble(sk, bd)
    except AssembleError as e:
        print(f"assemble: {e}", file=sys.stderr)
        return 1
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
