"""Self-check of the skeletons: static rules, loading, shapes, dtypes, timing, controls, paired plus/minus structure.
No criterion analysis is written or run here."""
import ast
import json
import sys
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "pkg"))
import numpy as np  # noqa: E402
from truth_gate import Study  # noqa: E402

FORBIDDEN = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
             "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__"}
NP_FILE = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
STUDY_KW = {"name", "criteria", "worlds", "controls", "premises", "relational"}
BASE_SEED = 20261105


def static_check(path, claim_line):
    src = path.read_text(encoding="utf-8")
    errs = []
    if "np.random" in src or "numpy.random" in src:
        errs.append("np.random used")
    tree = ast.parse(src)
    doc = ast.get_docstring(tree, clean=False)
    if doc != claim_line:
        errs.append("docstring mismatch")
    for i, node in enumerate(tree.body):
        if i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
            continue
        errs.append(f"top-level node {type(node).__name__} at line {node.lineno}")
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if len(imports) != 2:
        errs.append(f"{len(imports)} import lines")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN:
            errs.append(f"forbidden name {node.id}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                errs.append(f"dunder attribute {node.attr}")
            if node.attr in NP_FILE:
                errs.append(f"numpy file function {node.attr}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "World":
                kws = {k.arg for k in node.keywords}
                ok = (len(node.args) == 1 and not kws) or (len(node.args) == 1 and kws == {"derived_from", "change"})
                if not ok:
                    errs.append("World call form")
            if node.func.id == "Study":
                bad = {k.arg for k in node.keywords} - STUDY_KW
                if bad:
                    errs.append(f"Study keywords {bad}")
    return errs, src


def stream_rng(name, i):
    return np.random.default_rng(np.random.SeedSequence([BASE_SEED, zlib.crc32(name.encode()), i]))


def check_data(d, keys, label, errs):
    if not isinstance(d, dict) or set(d) != set(keys):
        errs.append(f"{label}: keys {sorted(d) if isinstance(d, dict) else type(d)}")
        return
    for k, spec in keys.items():
        a = d[k]
        if not isinstance(a, np.ndarray):
            errs.append(f"{label}:{k} not ndarray")
            continue
        if tuple(a.shape) != tuple(spec["dims"]):
            errs.append(f"{label}:{k} shape {a.shape} != {spec['dims']}")
        want = np.bool_ if spec["dtype"] == "bool" else np.float64
        if a.dtype != want:
            errs.append(f"{label}:{k} dtype {a.dtype}")
        if a.dtype != np.bool_ and not np.all(np.isfinite(a)):
            errs.append(f"{label}:{k} non-finite")
        if max(a.shape) > 2000 or a.size > 2_000_000:
            errs.append(f"{label}:{k} too large")


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, (time.perf_counter() - t0) * 1000.0


def main():
    batch = json.loads((HERE / "BATCH.json").read_text(encoding="utf-8"))
    n_draws = 30
    for brief in batch:
        bid = brief["id"]
        keys = {k["key"]: k for k in brief["data_keys"]}
        path = HERE / "skeletons" / f"{bid}.py"
        errs, src = static_check(path, f"{bid}: {brief['claim']}")
        mod = {"__name__": "skel"}
        exec(compile(src, str(path), "exec"), mod)  # load the skeleton (constructs and validates STUDY)
        study = mod["STUDY"]
        assert isinstance(study, Study)
        if study.name != bid:
            errs.append("study name")
        worlds = study.worlds
        tmax = 0.0
        changed_keys = set()
        diff_stats = {}
        for i in range(n_draws):
            dp, t = timed(worlds["plus"].generate, stream_rng("world:plus", i)); tmax = max(tmax, t)
            check_data(dp, keys, f"plus[{i}]", errs)
            dm, t = timed(worlds["minus"].generate, stream_rng("world:minus", i)); tmax = max(tmax, t)
            check_data(dm, keys, f"minus[{i}]", errs)
            dpair = worlds["minus"].generate(stream_rng("world:plus", i))  # paired, as the identical-minus check does
            dp2 = worlds["plus"].generate(stream_rng("world:plus", i))
            for k in keys:
                if not np.array_equal(dp[k], dp2[k]):
                    errs.append(f"plus not reproducible for seed {i}, key {k}")
                if not np.array_equal(dp[k], dpair[k]):
                    changed_keys.add(k)
                    if dp[k].dtype != np.bool_:
                        diff_stats.setdefault(k, []).append(float(np.std(dp[k] - dpair[k])))
            for c in study.controls:
                dc, t = timed(c.transform, dp, stream_rng(f"control:{c.id}", i)); tmax = max(tmax, t)
                check_data(dc, keys, f"control {c.id}[{i}]", errs)
                if isinstance(dc, dict) and all(np.array_equal(dc[k], dp[k]) for k in keys if k in dc):
                    errs.append(f"control {c.id} left data unchanged on draw {i}")
        extra = ""
        if bid == "D-052":
            dp = worlds["plus"].generate(stream_rng("world:plus", 0))
            dm = worlds["minus"].generate(stream_rng("world:plus", 0))
            dd = dp["post"] - dm["post"]
            extra = f"post diff young {np.unique(np.round(dd[dp['young']], 9))} old {np.unique(np.round(dd[~dp['young']], 9))}"
        if bid == "D-056":
            dp = worlds["plus"].generate(stream_rng("world:plus", 0))
            dm = worlds["minus"].generate(stream_rng("world:plus", 0))
            lr = np.log(dp["oxygen_uptake"] / dm["oxygen_uptake"])
            extra = f"log ratio per group {np.round(lr.mean(axis=1), 9)} (sd {np.round(lr.std(axis=1), 12)})"
        print(f"{bid}: errors={sorted(set(errs)) if errs else 'none'}; max call {tmax:.1f} ms; "
              f"keys changed plus->minus (paired) {sorted(changed_keys)}; "
              f"sd of paired difference {({k: round(float(np.mean(v)), 4) for k, v in diff_stats.items()})} {extra}")


if __name__ == "__main__":
    main()
